from sqlmodel import Session, select

from .models import Article, Author, Bookmark, Discipline, Like, User
from .schemas import ArticleOut, AuthorOut, AuthorStats, CoverOut, DisciplineOut


def author_to_out(author: Author) -> AuthorOut:
    return AuthorOut(
        handle=author.handle,
        name=author.name,
        title=author.title,
        bio=author.bio,
        avatarUrl=author.avatar_url,
        avatarColor=author.avatar_color,
        github=author.github,
        stats=AuthorStats(
            engagements=author.engagements,
            followers=author.followers,
            following=author.following,
        ),
    )


def discipline_to_out(discipline: Discipline) -> DisciplineOut:
    return DisciplineOut(
        slug=discipline.slug,
        name=discipline.name,
        description=discipline.description,
        icon=discipline.icon,
    )


def article_to_out(
    article: Article,
    author: Author,
    discipline: Discipline,
    *,
    liked: bool = False,
    bookmarked: bool = False,
) -> ArticleOut:
    return ArticleOut(
        slug=article.slug,
        title=article.title,
        excerpt=article.excerpt,
        contentHtml=article.content_html,
        discipline=discipline_to_out(discipline),
        category=article.category,
        author=author_to_out(author),
        publishedAt=article.published_at,
        readingMinutes=article.reading_minutes,
        likes=article.likes,
        tags=article.tags,
        coverImageUrl=article.cover_image_url,
        cover=CoverOut(icon=article.cover_icon, tone=article.cover_tone),
        status=article.status,
        liked=liked,
        bookmarked=bookmarked,
    )


def enrich_articles(
    articles: list[Article],
    session: Session,
    viewer: User | None,
    *,
    authors: dict[str, Author] | None = None,
) -> list[ArticleOut]:
    """Attach author/discipline + the viewer's like/bookmark state to a set of
    articles, batching all lookups (no N+1). Callers may pass a preloaded
    `authors` dict to avoid re-querying it."""
    if authors is None:
        authors = {a.handle: a for a in session.exec(select(Author)).all()}
    disciplines = {d.slug: d for d in session.exec(select(Discipline)).all()}

    liked: set[str] = set()
    bookmarked: set[str] = set()
    if viewer:
        liked = {
            row.article_id
            for row in session.exec(select(Like).where(Like.user_id == viewer.id)).all()
        }
        bookmarked = {
            row.article_id
            for row in session.exec(
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
