from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..database import get_session
from ..models import Article, Author, Bookmark, Discipline, Like, User
from ..schemas import ArticleOut, AuthorOut, DisciplineOut, TopicOut
from ..security import get_optional_user
from ..serializers import article_to_out, author_to_out, discipline_to_out

router = APIRouter()


def _enrich(
    articles: list[Article],
    session: Session,
    viewer: User | None,
) -> list[ArticleOut]:
    """Attach author/discipline + viewer like/bookmark state to a set of articles."""
    authors = {a.handle: a for a in session.exec(select(Author)).all()}
    disciplines = {d.slug: d for d in session.exec(select(Discipline)).all()}

    liked: set[str] = set()
    bookmarked: set[str] = set()
    if viewer:
        liked = {
            l.article_id
            for l in session.exec(select(Like).where(Like.user_id == viewer.id)).all()
        }
        bookmarked = {
            b.article_id
            for b in session.exec(
                select(Bookmark).where(Bookmark.user_id == viewer.id)
            ).all()
        }

    out: list[ArticleOut] = []
    for art in articles:
        author = authors.get(art.author_handle)
        discipline = disciplines.get(art.discipline_slug)
        if not author or not discipline:
            continue
        out.append(
            article_to_out(
                art,
                author,
                discipline,
                liked=art.id in liked,
                bookmarked=art.id in bookmarked,
            )
        )
    return out


@router.get("/articles", response_model=list[ArticleOut])
def list_articles(
    discipline: str | None = None,
    q: str | None = None,
    session: Session = Depends(get_session),
    viewer: User | None = Depends(get_optional_user),
):
    stmt = select(Article).where(Article.status == "published")
    if discipline:
        stmt = stmt.where(Article.discipline_slug == discipline)
    articles = list(session.exec(stmt).all())

    if q:
        needle = q.strip().lower()
        authors = {a.handle: a for a in session.exec(select(Author)).all()}
        articles = [
            a
            for a in articles
            if needle
            in " ".join(
                [
                    a.title,
                    a.excerpt,
                    a.category,
                    authors.get(a.author_handle).name if authors.get(a.author_handle) else "",
                    *a.tags,
                ]
            ).lower()
        ]

    # Newest first.
    articles.sort(key=lambda a: a.published_at, reverse=True)
    return _enrich(articles, session, viewer)


@router.get("/articles/{slug}", response_model=ArticleOut)
def get_article(
    slug: str,
    session: Session = Depends(get_session),
    viewer: User | None = Depends(get_optional_user),
):
    article = session.exec(select(Article).where(Article.slug == slug)).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Drafts are visible only to their author.
    if article.status != "published":
        owner = viewer and viewer.author_handle == article.author_handle
        if not owner:
            raise HTTPException(status_code=404, detail="Article not found")

    return _enrich([article], session, viewer)[0]


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
        session.exec(
            select(Article).where(
                Article.status == "published", Article.slug != slug
            )
        ).all()
    )
    # Prefer same discipline.
    others.sort(key=lambda a: (a.discipline_slug != article.discipline_slug, a.published_at))
    return _enrich(others[:limit], session, viewer)


@router.get("/disciplines", response_model=list[DisciplineOut])
def list_disciplines(session: Session = Depends(get_session)):
    disciplines = session.exec(select(Discipline)).all()
    return [discipline_to_out(d) for d in disciplines]


@router.get("/topics/trending", response_model=list[TopicOut])
def trending_topics(session: Session = Depends(get_session)):
    counter: Counter[str] = Counter()
    for art in session.exec(select(Article).where(Article.status == "published")).all():
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
            select(Article).where(
                Article.author_handle == handle, Article.status == "published"
            )
        ).all()
    )
    articles.sort(key=lambda a: a.published_at, reverse=True)
    return _enrich(articles, session, viewer)
