from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..database import get_session
from ..models import Article, Author, Discipline, User
from ..schemas import ArticleOut, AuthorOut, DisciplineOut, TopicOut
from ..security import get_optional_user
from ..serializers import author_to_out, discipline_to_out, enrich_articles

router = APIRouter()


def _public_listable(stmt):
    """Articles that belong in public listings: published AND public visibility.
    (Unlisted articles are reachable by direct link but never listed.)"""
    return stmt.where(Article.status == "published", Article.visibility == "public")


@router.get("/articles", response_model=list[ArticleOut])
def list_articles(
    discipline: str | None = None,
    q: str | None = None,
    session: Session = Depends(get_session),
    viewer: User | None = Depends(get_optional_user),
):
    stmt = _public_listable(select(Article))
    if discipline:
        stmt = stmt.where(Article.discipline_slug == discipline)
    articles = list(session.exec(stmt).all())

    # Load authors once; reused for both the q-filter and enrichment.
    authors = {a.handle: a for a in session.exec(select(Author)).all()}

    if q:
        needle = q.strip().lower()
        articles = [
            a
            for a in articles
            if needle
            in " ".join(
                [
                    a.title,
                    a.excerpt,
                    a.category,
                    authors[a.author_handle].name if a.author_handle in authors else "",
                    *a.tags,
                ]
            ).lower()
        ]

    articles.sort(key=lambda a: a.published_at, reverse=True)
    return enrich_articles(articles, session, viewer, authors=authors)


@router.get("/articles/{slug}", response_model=ArticleOut)
def get_article(
    slug: str,
    session: Session = Depends(get_session),
    viewer: User | None = Depends(get_optional_user),
):
    article = session.exec(select(Article).where(Article.slug == slug)).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Drafts are visible only to their author; unlisted is reachable by link.
    if article.status != "published":
        owner = viewer and viewer.author_handle == article.author_handle
        if not owner:
            raise HTTPException(status_code=404, detail="Article not found")

    return enrich_articles([article], session, viewer)[0]


@router.get("/articles/{slug}/related", response_model=list[ArticleOut])
def related_articles(
    slug: str,
    limit: int = 3,
    session: Session = Depends(get_session),
    viewer: User | None = Depends(get_optional_user),
):
    article = session.exec(select(Article).where(Article.slug == slug)).first()
    if not article:
        return []
    others = list(
        session.exec(_public_listable(select(Article)).where(Article.slug != slug)).all()
    )
    # Newest first, then (stable) same-discipline first.
    others.sort(key=lambda a: a.published_at, reverse=True)
    others.sort(key=lambda a: a.discipline_slug != article.discipline_slug)
    return enrich_articles(others[:limit], session, viewer)


@router.get("/disciplines", response_model=list[DisciplineOut])
def list_disciplines(session: Session = Depends(get_session)):
    disciplines = session.exec(select(Discipline)).all()
    return [discipline_to_out(d) for d in disciplines]


@router.get("/topics/trending", response_model=list[TopicOut])
def trending_topics(session: Session = Depends(get_session)):
    counter: Counter[str] = Counter()
    for art in session.exec(_public_listable(select(Article))).all():
        counter.update(art.tags)
    return [TopicOut(tag=tag, count=count) for tag, count in counter.most_common(5)]


@router.get("/contributors/top", response_model=list[AuthorOut])
def top_contributors(session: Session = Depends(get_session)):
    authors = session.exec(
        select(Author).order_by(Author.followers.desc()).limit(3)
    ).all()
    return [author_to_out(a) for a in authors]


@router.get("/authors/{handle}", response_model=AuthorOut)
def get_author(handle: str, session: Session = Depends(get_session)):
    author = session.get(Author, handle)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author_to_out(author)


@router.get("/authors/{handle}/articles", response_model=list[ArticleOut])
def author_articles(
    handle: str,
    session: Session = Depends(get_session),
    viewer: User | None = Depends(get_optional_user),
):
    articles = list(
        session.exec(
            _public_listable(select(Article)).where(Article.author_handle == handle)
        ).all()
    )
    articles.sort(key=lambda a: a.published_at, reverse=True)
    return enrich_articles(articles, session, viewer)
