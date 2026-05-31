import re
from datetime import date, datetime, timezone
from html import escape

import nh3
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..database import get_session
from ..models import Article, Bookmark, Discipline, Like, User
from ..schemas import (
    ArticleOut,
    BookmarkResult,
    CreateArticleIn,
    CreateArticleResult,
    LikeResult,
)
from ..security import get_current_user
from ..serializers import enrich_articles
from ..utils import slugify
from .notifications import create_notification

router = APIRouter()


def _unique_slug(title: str, session: Session) -> str:
    base = slugify(title, fallback="untitled")
    candidate = base
    n = 1
    while session.exec(select(Article).where(Article.slug == candidate)).first():
        n += 1
        candidate = f"{base}-{n}"
    return candidate


# Safe subset of tags the rich-text editor can produce. Everything else is
# stripped — the result is rendered as HTML on the client (dangerouslySetInnerHTML).
_ALLOWED_TAGS = {
    "p", "br", "strong", "b", "em", "i", "u", "s", "a",
    "h2", "h3", "ul", "ol", "li", "blockquote", "code", "pre", "img", "hr",
}
_ALLOWED_ATTRS = {
    # nh3 manages the "rel" attribute itself (link_rel), so don't list it here.
    "a": {"href", "title", "target"},
    "img": {"src", "alt", "title"},
}


# A real HTML tag: "<" + optional "/" + a letter, ending in ">". Matches
# <p>, </p>, <br/>, <a href=...> but NOT prose/code like "a < b" or "i<n;".
_HTML_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")


def _plain_to_html(body: str) -> str:
    """Escape plain text and wrap paragraphs, so angle-bracketed prose/code is
    preserved rather than stripped."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    return "".join(f"<p>{escape(p)}</p>" for p in paragraphs)


def _sanitize_body(body: str) -> str:
    """If the body contains real HTML tags (the WYSIWYG editor sends HTML),
    sanitize with nh3; otherwise treat it as plain text and escape it. This
    avoids both stored XSS and silent content loss for tag-free input."""
    if _HTML_TAG_RE.search(body):
        return nh3.clean(body, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS)
    return _plain_to_html(body)


def _text_from_html(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


@router.post("/articles", response_model=CreateArticleResult)
def create_article(
    body: CreateArticleIn,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    if not body.title.strip() or not body.body.strip():
        raise HTTPException(status_code=400, detail="Title and body are required.")
    if not user.author_handle:
        raise HTTPException(status_code=400, detail="User has no author profile.")

    discipline = session.get(Discipline, body.disciplineSlug)
    if not discipline:
        raise HTTPException(status_code=400, detail="Unknown discipline.")

    content_html = _sanitize_body(body.body)
    text = _text_from_html(content_html)
    if not text:
        raise HTTPException(status_code=400, detail="Article body is empty.")
    words = len(text.split())
    article = Article(
        slug=_unique_slug(body.title, session),
        title=body.title.strip(),
        excerpt=text[:200].rstrip() + ("…" if len(text) > 200 else ""),
        content_html=content_html,
        discipline_slug=discipline.slug,
        category=discipline.name,
        author_handle=user.author_handle,
        published_at=date.today().isoformat(),
        reading_minutes=max(1, round(words / 200)),
        likes=0,
        cover_icon=discipline.icon,
        cover_tone="indigo",
        cover_image_url=None,
        status="draft" if body.status == "draft" else "published",
        visibility=body.visibility,
        featured_image=body.featuredImage,
        tags=body.tags[:5],
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    session.add(article)
    session.commit()
    return CreateArticleResult(slug=article.slug, title=article.title, status=article.status)


@router.get("/me/drafts", response_model=list[ArticleOut])
def my_drafts(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    drafts = list(
        session.exec(
            select(Article).where(
                Article.author_handle == user.author_handle,
                Article.status == "draft",
            )
        ).all()
    )
    drafts.sort(key=lambda a: a.created_at, reverse=True)
    return enrich_articles(drafts, session, user)


@router.get("/me/bookmarks", response_model=list[ArticleOut])
def my_bookmarks(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    rows = session.exec(select(Bookmark).where(Bookmark.user_id == user.id)).all()
    ids = [r.article_id for r in rows]
    if not ids:
        return []
    # Only return articles the viewer may still see: published+public, or their
    # own (a bookmarked article the author later unpublished must not leak).
    articles = [
        a
        for a in session.exec(select(Article).where(Article.id.in_(ids))).all()
        if (a.status == "published" and a.visibility == "public")
        or a.author_handle == user.author_handle
    ]
    return enrich_articles(articles, session, user)


def _get_article_or_404(slug: str, session: Session) -> Article:
    article = session.exec(select(Article).where(Article.slug == slug)).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.post("/articles/{slug}/like", response_model=LikeResult)
def like_article(
    slug: str,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    article = _get_article_or_404(slug, session)
    if not session.get(Like, (user.id, article.id)):
        session.add(Like(user_id=user.id, article_id=article.id))
        article.likes += 1
        session.add(article)
        create_notification(session, actor=user, article=article, type_="like")
        session.commit()
        session.refresh(article)
    return LikeResult(likes=article.likes, liked=True)


@router.delete("/articles/{slug}/like", response_model=LikeResult)
def unlike_article(
    slug: str,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    article = _get_article_or_404(slug, session)
    existing = session.get(Like, (user.id, article.id))
    if existing:
        session.delete(existing)
        article.likes = max(0, article.likes - 1)
        session.add(article)
        session.commit()
        session.refresh(article)
    return LikeResult(likes=article.likes, liked=False)


@router.post("/articles/{slug}/bookmark", response_model=BookmarkResult)
def bookmark_article(
    slug: str,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    article = _get_article_or_404(slug, session)
    if not session.get(Bookmark, (user.id, article.id)):
        session.add(Bookmark(user_id=user.id, article_id=article.id))
        create_notification(session, actor=user, article=article, type_="bookmark")
        session.commit()
    return BookmarkResult(bookmarked=True)


@router.delete("/articles/{slug}/bookmark", response_model=BookmarkResult)
def unbookmark_article(
    slug: str,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    article = _get_article_or_404(slug, session)
    existing = session.get(Bookmark, (user.id, article.id))
    if existing:
        session.delete(existing)
        session.commit()
    return BookmarkResult(bookmarked=False)
