import re

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..database import get_session
from ..models import Author, User
from ..schemas import AuthorOut, ProfileUpdateIn
from ..security import get_current_user
from ..serializers import author_to_out

router = APIRouter()


def _normalize_github(value: str) -> str | None:
    v = re.sub(r"^https?://(www\.)?", "", value.strip()).rstrip("/")
    if not v:
        return None
    if v.startswith("github.com/"):
        return v
    return "github.com/" + v.split("/")[-1]  # treat a bare token as a username


@router.patch("/me/author", response_model=AuthorOut)
def update_my_profile(
    body: ProfileUpdateIn,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    """Update the signed-in user's public author profile (headline, bio, GitHub)."""
    if not user.author_handle:
        raise HTTPException(status_code=400, detail="User has no author profile.")
    author = session.get(Author, user.author_handle)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found.")

    if body.title is not None:
        author.title = body.title.strip()
    if body.bio is not None:
        author.bio = body.bio.strip()
    if body.github is not None:
        author.github = _normalize_github(body.github)

    session.add(author)
    session.commit()
    session.refresh(author)
    return author_to_out(author)
