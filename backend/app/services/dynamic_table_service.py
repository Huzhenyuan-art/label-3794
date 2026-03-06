from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import JSON, Column, DateTime, Integer, MetaData, String, Table, delete, select

from ..errors import ApiError
from ..extensions import db


BJ_TZ = ZoneInfo("Asia/Shanghai")


def _now() -> datetime:
    return datetime.now(BJ_TZ).replace(tzinfo=None)


def _table_definition(table_name: str, metadata: MetaData) -> Table:
    return Table(
        table_name,
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("record_key", String(128), nullable=False, unique=True, index=True),
        Column("payload", JSON, nullable=False),
        Column("created_at", DateTime, nullable=False, default=_now),
        Column("updated_at", DateTime, nullable=False, default=_now),
    )


def ensure_dynamic_table(table_name: str) -> None:
    metadata = MetaData()
    table = _table_definition(table_name, metadata)
    metadata.create_all(bind=db.engine, tables=[table], checkfirst=True)


def drop_dynamic_table(table_name: str) -> None:
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=db.engine)
    table.drop(bind=db.engine, checkfirst=True)


def _load_table(table_name: str) -> Table:
    metadata = MetaData()
    try:
        return Table(table_name, metadata, autoload_with=db.engine)
    except Exception as exc:
        raise ApiError(404, "业务数据表不存在") from exc


def list_records(table_name: str, limit: int, offset: int):
    table = _load_table(table_name)
    stmt = select(table).limit(limit).offset(offset).order_by(table.c.id.desc())
    rows = db.session.execute(stmt).mappings().all()
    return rows


def get_record(table_name: str, record_id: int):
    table = _load_table(table_name)
    stmt = select(table).where(table.c.id == record_id)
    row = db.session.execute(stmt).mappings().first()
    if not row:
        raise ApiError(404, "记录不存在")
    return row


def create_record(table_name: str, record_key: str, payload: dict):
    table = _load_table(table_name)
    existing = db.session.execute(select(table.c.id).where(table.c.record_key == record_key)).first()
    if existing:
        raise ApiError(409, "record_key 已存在")

    stmt = table.insert().values(record_key=record_key, payload=payload, created_at=_now(), updated_at=_now())
    result = db.session.execute(stmt)
    db.session.commit()
    return get_record(table_name, result.inserted_primary_key[0])


def update_record(table_name: str, record_id: int, record_key: str | None, payload: dict | None):
    table = _load_table(table_name)
    current = get_record(table_name, record_id)

    if record_key and record_key != current["record_key"]:
        conflict = db.session.execute(
            select(table.c.id).where(table.c.record_key == record_key, table.c.id != record_id)
        ).first()
        if conflict:
            raise ApiError(409, "record_key 已存在")

    update_payload = {
        "record_key": record_key or current["record_key"],
        "payload": payload if payload is not None else current["payload"],
        "updated_at": _now(),
    }
    db.session.execute(table.update().where(table.c.id == record_id).values(**update_payload))
    db.session.commit()
    return get_record(table_name, record_id)


def delete_record_by_id(table_name: str, record_id: int) -> None:
    table = _load_table(table_name)
    db.session.execute(delete(table).where(table.c.id == record_id))
    db.session.commit()
