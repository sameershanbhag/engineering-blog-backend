from .models import Article, Author, Discipline
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
