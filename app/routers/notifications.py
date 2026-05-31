from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlmodel import Session, col, select

from ..database import get_session
from ..models import Article, Author, Notification, User
from ..schemas import NotificationOut, NotificationsOut
from ..security import get_current_user

router = APIRouter()

_MAX_FEED = 30  # how many notifications the dropdown / feed shows


def create_notification(
    session: Session,
    *,
    actor: User,
    article: Article,
    type_: str,
) -> None:
    """Notify an article's author that `actor` liked/bookmarked it. No-ops when
    the actor is the author, the author isn't a real user (seed data), or an
    identical notification already exists (so like/unlike/like doesn't spam)."""
    recipient_handle = article.author_handle
    if not actor.author_handle or actor.author_handle == recipient_handle:
        return
    recipient = session.exec(
        select(User).where(User.author_handle == recipient_handle)
    ).first()
    if recipient is None:
        return

    duplicate = session.exec(
        select(Notification).where(
            Notification.user_id == recipient.id,
            Notification.actor_handle == actor.author_handle,
            Notification.article_slug == article.slug,
            Notification.type == type_,
        )
    ).first()
    if duplicate is not None:
        return

    actor_author = session.get(Author, actor.author_handle)
    session.add(
        Notification(
            user_id=recipient.id,
            type=type_,
            actor_handle=actor.author_handle,
            actor_name=actor_author.name if actor_author else actor.name,
            actor_avatar_url=actor_author.avatar_url if actor_author else None,
            actor_avatar_color=(
                actor_author.avatar_color if actor_author else "bg-indigo-600"
            ),
            article_slug=article.slug,
            article_title=article.title,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    )


def _to_out(n: Notification) -> NotificationOut:
    return NotificationOut(
        id=n.id,
        type=n.type,
        actorName=n.actor_name,
        actorHandle=n.actor_handle,
        actorAvatarUrl=n.actor_avatar_url,
        actorAvatarColor=n.actor_avatar_color,
        articleSlug=n.article_slug,
        articleTitle=n.article_title,
        read=n.read,
        createdAt=n.created_at,
    )


@router.get("/me/notifications", response_model=NotificationsOut)
def list_notifications(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    rows = list(
        session.exec(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(col(Notification.created_at).desc())
            .limit(_MAX_FEED)
        ).all()
    )
    unread = len(
        session.exec(
            select(Notification).where(
                Notification.user_id == user.id, Notification.read == False  # noqa: E712
            )
        ).all()
    )
    return NotificationsOut(items=[_to_out(n) for n in rows], unreadCount=unread)


@router.post("/me/notifications/read")
def mark_all_read(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    rows = session.exec(
        select(Notification).where(
            Notification.user_id == user.id, Notification.read == False  # noqa: E712
        )
    ).all()
    for n in rows:
        n.read = True
        session.add(n)
    session.commit()
    return {"ok": True, "marked": len(rows)}
