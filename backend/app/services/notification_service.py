from ..extensions import db
from ..models import Notification, beijing_now


NOTIFICATION_TYPES = {
    "UPLOAD_FAILED": "upload_failed",
    "ACCOUNT_LOCKED": "account_locked",
    "SQL_ERROR": "sql_error",
}


def create_notification(
    notification_type: str,
    title: str,
    content: str,
    admin_id: int | None = None,
) -> Notification:
    notification = Notification(
        type=notification_type,
        title=title,
        content=content,
        admin_id=admin_id,
    )
    db.session.add(notification)
    db.session.commit()
    return notification


def get_unread_count(admin_id: int | None = None) -> int:
    query = Notification.query.filter_by(is_read=False)
    if admin_id is not None:
        query = query.filter(
            (Notification.admin_id == admin_id) | (Notification.admin_id.is_(None))
        )
    return query.count()


def get_notifications(
    admin_id: int | None = None,
    only_unread: bool = False,
    limit: int = 50,
) -> list[Notification]:
    query = Notification.query
    if admin_id is not None:
        query = query.filter(
            (Notification.admin_id == admin_id) | (Notification.admin_id.is_(None))
        )
    if only_unread:
        query = query.filter_by(is_read=False)
    return query.order_by(Notification.created_at.desc()).limit(limit).all()


def mark_as_read(notification_id: int, admin_id: int | None = None) -> Notification | None:
    query = Notification.query.filter_by(id=notification_id)
    if admin_id is not None:
        query = query.filter(
            (Notification.admin_id == admin_id) | (Notification.admin_id.is_(None))
        )
    notification = query.first()
    if not notification:
        return None
    notification.is_read = True
    notification.read_at = beijing_now()
    db.session.commit()
    return notification


def mark_all_as_read(admin_id: int | None = None) -> int:
    query = Notification.query.filter_by(is_read=False)
    if admin_id is not None:
        query = query.filter(
            (Notification.admin_id == admin_id) | (Notification.admin_id.is_(None))
        )
    count = query.update(
        {Notification.is_read: True, Notification.read_at: beijing_now()},
        synchronize_session=False,
    )
    db.session.commit()
    return count
