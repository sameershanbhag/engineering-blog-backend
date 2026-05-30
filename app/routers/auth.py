import hashlib

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlmodel import Session, select

from ..config import settings
from ..database import get_session
from ..models import Author, User
from ..schemas import AuthResponse, AuthUserOut, LoginIn, OAuthIn, RegisterIn
from ..security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from ..utils import slugify

router = APIRouter(prefix="/auth", tags=["auth"])

_AVATAR_COLORS = [
    "bg-indigo-600",
    "bg-emerald-600",
    "bg-cyan-700",
    "bg-violet-600",
    "bg-rose-600",
    "bg-amber-600",
]


def _unique_handle(base: str, session: Session) -> str:
    handle = slugify(base, sep="_", fallback="engineer")
    candidate = handle
    n = 1
    while session.get(Author, candidate):
        n += 1
        candidate = f"{handle}_{n}"
    return candidate


def _create_author(name: str, email: str, image: str | None, session: Session) -> Author:
    handle = _unique_handle(name or email.split("@")[0], session)
    # Deterministic across processes/restarts (unlike builtin hash()).
    digest = int(hashlib.sha256(email.encode()).hexdigest(), 16)
    color = _AVATAR_COLORS[digest % len(_AVATAR_COLORS)]
    author = Author(
        handle=handle,
        name=name or email.split("@")[0],
        title="Community Member",
        bio="",
        avatar_url=image,
        avatar_color=color,
        engagements=0,
        followers=0,
        following=0,
    )
    session.add(author)
    return author


def _to_auth_user(user: User) -> AuthUserOut:
    return AuthUserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        image=user.image,
        handle=user.author_handle,
    )


def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(user=_to_auth_user(user), accessToken=create_access_token(user.id))


@router.post("/register", response_model=AuthResponse)
def register(body: RegisterIn, session: Session = Depends(get_session)):
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    existing = session.exec(select(User).where(User.email == body.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    author = _create_author(body.name, body.email, None, session)
    user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        provider="credentials",
        author_handle=author.handle,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return _auth_response(user)


@router.post("/login", response_model=AuthResponse)
def login(body: LoginIn, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == body.email)).first()
    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return _auth_response(user)


def _require_internal_secret(x_internal_secret: str | None = Header(default=None)) -> None:
    """Guard /auth/oauth: only the trusted frontend (which holds the shared
    secret) may federate an OAuth identity into a backend token. Without this,
    anyone could POST an arbitrary email and mint a token for that account."""
    expected = settings.internal_api_secret
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OAuth federation is not configured (INTERNAL_API_SECRET unset).",
        )
    if not x_internal_secret or x_internal_secret != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Forbidden")


@router.post("/oauth", response_model=AuthResponse)
def oauth(
    body: OAuthIn,
    session: Session = Depends(get_session),
    _: None = Depends(_require_internal_secret),
):
    """Federate an OAuth sign-in (from NextAuth) into a backend user + token.
    Gated by the internal shared secret (see _require_internal_secret)."""
    user = session.exec(select(User).where(User.email == body.email)).first()
    if user is None:
        author = _create_author(body.name, body.email, body.image, session)
        user = User(
            name=body.name,
            email=body.email,
            image=body.image,
            provider=body.provider,
            author_handle=author.handle,
        )
        session.add(user)
    else:
        # Keep the latest profile image from the provider.
        if body.image:
            user.image = body.image
        session.add(user)
    session.commit()
    session.refresh(user)
    return _auth_response(user)


@router.get("/me", response_model=AuthUserOut)
def me(user: User = Depends(get_current_user)):
    return _to_auth_user(user)
