import uuid

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def _uuid() -> str:
    return uuid.uuid4().hex


class Discipline(SQLModel, table=True):
    slug: str = Field(primary_key=True)
    name: str
    description: str
    icon: str


class Author(SQLModel, table=True):
    handle: str = Field(primary_key=True)
    name: str
    title: str
    bio: str = ""
    avatar_url: str | None = None
    avatar_color: str = "bg-indigo-600"
    github: str | None = None
    engagements: int = 0
    followers: int = 0
    following: int = 0


class User(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
    password_hash: str | None = None  # null for OAuth-only accounts
    image: str | None = None
    provider: str = "credentials"  # credentials | github | google
    author_handle: str | None = Field(default=None, foreign_key="author.handle")


class Article(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    slug: str = Field(index=True, unique=True)
    title: str
    excerpt: str = ""
    content_html: str = ""
    discipline_slug: str = Field(foreign_key="discipline.slug")
    category: str = ""
    author_handle: str = Field(foreign_key="author.handle")
    published_at: str = ""  # ISO date (YYYY-MM-DD)
    reading_minutes: int = 5
    likes: int = 0  # base count; per-user likes tracked in Like
    cover_icon: str = "code"
    cover_tone: str = "dark"
    cover_image_url: str | None = None
    status: str = "published"  # published | draft
    visibility: str = "public"  # public | unlisted | draft
    featured_image: bool = False
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: str = ""


class Notification(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)  # recipient
    type: str  # like | bookmark
    actor_handle: str
    actor_name: str
    actor_avatar_url: str | None = None
    actor_avatar_color: str = "bg-indigo-600"
    article_slug: str
    article_title: str
    read: bool = Field(default=False, index=True)
    created_at: str = ""


class Like(SQLModel, table=True):
    user_id: str = Field(foreign_key="user.id", primary_key=True)
    article_id: str = Field(foreign_key="article.id", primary_key=True)


class Bookmark(SQLModel, table=True):
    user_id: str = Field(foreign_key="user.id", primary_key=True)
    article_id: str = Field(foreign_key="article.id", primary_key=True)
