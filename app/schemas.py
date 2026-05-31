from pydantic import BaseModel, EmailStr

# Response field names are camelCase to match the frontend TypeScript types in
# Blog/src/lib/types.ts exactly, so the client consumes them with no mapping.


class DisciplineOut(BaseModel):
    slug: str
    name: str
    description: str
    icon: str


class AuthorStats(BaseModel):
    engagements: int
    followers: int
    following: int


class AuthorOut(BaseModel):
    handle: str
    name: str
    title: str
    bio: str
    avatarUrl: str | None = None
    avatarColor: str
    github: str | None = None
    stats: AuthorStats


class CoverOut(BaseModel):
    icon: str
    tone: str


class ArticleOut(BaseModel):
    slug: str
    title: str
    excerpt: str
    contentHtml: str
    discipline: DisciplineOut
    category: str
    author: AuthorOut
    publishedAt: str
    readingMinutes: int
    likes: int
    tags: list[str]
    coverImageUrl: str | None = None
    cover: CoverOut
    status: str = "published"
    # Per-viewer interaction state (present when authenticated).
    liked: bool = False
    bookmarked: bool = False


class TopicOut(BaseModel):
    tag: str
    count: int


# ---- Auth ----


class AuthUserOut(BaseModel):
    id: str
    name: str
    email: str
    image: str | None = None
    handle: str | None = None  # the user's author profile handle


class AuthResponse(BaseModel):
    user: AuthUserOut
    accessToken: str


class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class OAuthIn(BaseModel):
    provider: str
    providerAccountId: str
    email: EmailStr
    name: str
    image: str | None = None


# ---- Write / interactions ----


class CreateArticleIn(BaseModel):
    title: str
    body: str
    disciplineSlug: str
    tags: list[str] = []
    visibility: str = "public"
    featuredImage: bool = False
    status: str = "published"  # published | draft


class CreateArticleResult(BaseModel):
    slug: str
    title: str
    status: str


class LikeResult(BaseModel):
    likes: int
    liked: bool


class BookmarkResult(BaseModel):
    bookmarked: bool


# ---- Notifications ----


class NotificationOut(BaseModel):
    id: str
    type: str  # like | bookmark
    actorName: str
    actorHandle: str
    actorAvatarUrl: str | None = None
    actorAvatarColor: str
    articleSlug: str
    articleTitle: str
    read: bool
    createdAt: str


class NotificationsOut(BaseModel):
    items: list[NotificationOut]
    unreadCount: int
