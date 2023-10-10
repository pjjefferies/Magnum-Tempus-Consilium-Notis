import datetime as dt
from typing import Optional

from box import Box
from sqlalchemy import create_engine
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import select
from sqlalchemy import String
from sqlalchemy.orm import Session
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

# from sqlalchemy.orm import relationship

from src.load_import_data import load_enex_backup
from src.config.config_main import load_config
from src.config.config_logging import logger

cfg: Box = load_config()

MAX_TITLE_LEN: int = cfg.DATABASE.MAX_FIELD_LIMITS.TITLE
MAX_TAG_NAME_LEN: int = cfg.DATABASE.MAX_FIELD_LIMITS.TAG_NAME
MAX_BODY_TEXT_LEN: int = cfg.DATABASE.MAX_FIELD_LIMITS.BODY_TEXT
MAX_IMAGE_FILENAME_LEN: int = cfg.DATABASE.MAX_FIELD_LIMITS.IMAGE_FILENAME
MAX_IMAGE_DATA_LEN: int = cfg.DATABASE.MAX_FIELD_LIMITS.IMAGE_DATA
WHEN_TAGS: list[str] = cfg.DATABASE.TAGS.WHEN
WHERE_TAGS: list[str] = cfg.DATABASE.TAGS.WHERE


class Base(DeclarativeBase):
    pass


class Where_Tag(Base):
    __tablename__ = "where_tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(MAX_TAG_NAME_LEN))

    def __repr__(self) -> str:
        return f"[id: {self.id}, name: {self.name}]"


class When_Tag(Base):
    __tablename__ = "when_tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(MAX_TAG_NAME_LEN))

    def __repr__(self) -> str:
        return f"[id: {self.id}, name: {self.name}]"


class Reference_Tag(Base):
    __tablename__ = "reference_tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(MAX_TAG_NAME_LEN))


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(MAX_TITLE_LEN), default="")
    created: Mapped[DateTime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    updated: Mapped[DateTime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    where_tag_id: Mapped[int] = mapped_column(
        ForeignKey("where_tags.id"), nullable=True
    )
    when_tag_id: Mapped[int] = mapped_column(ForeignKey("when_tags.id"), nullable=True)
    body_text: Mapped[str] = mapped_column(String(MAX_BODY_TEXT_LEN), default="")

    def __repr__(self) -> str:
        return (
            f"[id: {self.id}, title: {self.title}, created: {self.created}, "
            f"updated: {self.updated}, where_tag_id: {self.where_tag_id}, "
            f"when_tag_id: {self.when_tag_id}, body_text: {self.body_text[:16]}"
        )


class Resource(Base):
    __tablename__ = "resources"
    id: Mapped[int] = mapped_column(primary_key=True)
    file_name: Mapped[str] = mapped_column(String(MAX_TITLE_LEN))
    hash: Mapped[str] = mapped_column(String(MAX_TITLE_LEN))
    data: Mapped[str] = mapped_column(String(MAX_IMAGE_DATA_LEN))
    mime: Mapped[str] = mapped_column(String(MAX_TITLE_LEN))
    width: Mapped[int] = mapped_column()
    height: Mapped[int] = mapped_column()

    def __repr__(self) -> str:
        return (
            f"[id: {self.id}, title: {self.file_name}, created: {self.hash}, "
            f"updated: {self.mime}, where_tag_id: {self.width}, "
            f"when_tag_id: {self.height}, body_text: {self.data[:16]}"
        )


class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(MAX_TITLE_LEN), default="")
    created: Mapped[DateTime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    updated: Mapped[DateTime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    reference_tag_id: Mapped[int] = mapped_column(
        ForeignKey("reference_tags.id"), nullable=True
    )
    body_text: Mapped[str] = mapped_column(String(MAX_BODY_TEXT_LEN), default="")


"""
class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(MAX_TITLE_LEN))
    created: Mapped[DateTime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    updated: Mapped[DateTime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    task_ids: Mapped[list[int]] = mapped_column(ForeignKey("reference_tags.id"))
"""


def save_enex_backup_to_mysql_db(*, enex_backup_pathname: str, database_pathname: str):
    engine = create_engine(f"sqlite+pysqlite:///{database_pathname}", echo=True)
    """
    What kind of database are we communicating with? This is the sqlite portion above,
    which links in SQLAlchemy to an object known as the dialect.
    The Python DBAPI is a third party driver that SQLAlchemy uses to interact with a
    particular database. In this case, we’re using the name pysqlite, which in modern
    Python use is the sqlite3 standard library interface for SQLite.
    """
    Base.metadata.create_all(engine)

    # Add all Where and When Tags to their respective databases if they're not there already
    # Remvoe the adding of them for each note below
    # For Tags in note that are not in Where or When tags, add tag as Reference Tag or something like that

    

    tasks, resources = load_enex_backup(filepath=enex_backup_pathname, logger=logger)

    with Session(engine) as session:
        for task in tasks:
            logger.debug(msg=f"{task['title']=}")
            where_tag: str = ""
            when_tag: str = ""
            tag: str
            for tag in task.get("tags", []):
                if not where_tag:
                    if tag in WHERE_TAGS:
                        where_tag = tag
                if not when_tag:
                    if tag in WHEN_TAGS:
                        when_tag = tag

            a_task = Task(
                title=task.get("title", ""),
                created=dt.datetime.fromisoformat(task.get("created", None)),
                updated=dt.datetime.fromisoformat(task.get("updated", None)),
                body_text=task.get("content", ""),
            )

            # Add Where Tag  to Where_Tag if doesn't exist yet
            logger.debug(msg=f"{where_tag=}")
            where_tag_in_db: Optional[Where_Tag] = None
            if where_tag:
                where_tag_query1 = select(Where_Tag).where(Where_Tag.name == where_tag)
                where_tag_in_db = bool(session.execute(where_tag_query1).one_or_none())
                logger.debug(msg=f"{where_tag_in_db=}")
                if not where_tag_in_db:
                    logger.debug(msg=f"Adding {where_tag} to Where_Tag")
                    new_where_tag = Where_Tag(name=where_tag)
                    session.add(new_where_tag)
                    session.commit()
                    logger.debug(msg=f"Let's check if new_where_tag has been added...")
                    where_tag_query1_5 = select(Where_Tag)
                    where_tag_in_db1_5 = session.execute(where_tag_query1_5).all()
                    logger.debug(msg=f"{where_tag_in_db1_5=}")

            # Add Where Tag to Task if there is one
            if where_tag:
                where_tag_query2 = select(Where_Tag).where(Where_Tag.name == where_tag)
                a_task.where_tag_id = session.execute(where_tag_query2).first()[0].id
                logger.debug(
                    msg=f"Added {where_tag} to Task as where_tag_id={a_task.where_tag_id}"
                )
                logger.debug(msg=f"{a_task.where_tag_id=}")

            # Add When Tag to When_Tag if doesn't exist yet
            # logger.debug(msg=f"181:{when_tag=}")
            when_tag_in_db: Optional[When_Tag] = None
            if when_tag:
                # logger.debug(msg=f"184:We have a when_tag: {when_tag}")
                when_tag_query1 = select(When_Tag).where(When_Tag.name == when_tag)
                when_tag_in_db = bool(session.execute(when_tag_query1).one_or_none())
                # logger.debug(msg=f"{when_tag_in_db=}")
                if not when_tag_in_db:
                    logger.debug(msg=f"189:Adding {when_tag} to When_Tag")
                    new_when_tag = When_Tag(name=when_tag)
                    session.add(new_when_tag)
                    session.commit()
                    logger.debug(msg=f"Let's check if new_when_tag has been added...")
                    when_tag_query1_5 = select(When_Tag)
                    when_tag_in_db1_5 = session.execute(when_tag_query1_5).all()
                    logger.debug(msg=f"{when_tag_in_db1_5=}")

            # Add When Tag to Task if there is one
            if when_tag:
                when_tag_query2 = select(When_Tag).where(When_Tag.name == when_tag)
                a_task.when_tag_id = session.execute(when_tag_query2).first()[0].id
                logger.debug(
                    msg=f"Added {when_tag} to Task as when_tag_id={a_task.when_tag_id}"
                )
                logger.debug(msg=f"{a_task.when_tag_id=}")

            session.add(a_task)
            session.commit()

            # logger.debug(msg=f"Task added. Let's see if it's correct...")
            # task1_query = select(Task).where(Task.title == task["title"])
            # task1 = session.execute(task1_query).first()[0]
            # logger.debug(msg=f"{task1}")

        for resource in resources:
            logger.debug(msg=f"{resource['file_name']=}")

            a_resource = Resource(
                file_name=resource["file_name"],
                hash=resource["hash"],
                mime=resource["mime"],
                width=resource["width"],
                height=resource["height"],
                data=resource["data"],
            )

            session.add(a_resource)
            session.commit()

    # Let's see what's in database
    with Session(engine) as session:
        query = select(Task)
        tasks_in_db = session.execute(query).all()
        logger.debug(msg=f"There are {len(tasks_in_db)} tasks in the database")

        query = select(Resource)
        resources_in_db = session.execute(query).all()
        logger.debug(msg=f"There are {len(resources_in_db)} resources in the database")


if __name__ == "__main__":
    database_pathname: str = "data/database/notes_data.db"
    enex_backup_pathname: str = "data/import_data/Evernote_Actions_2023-08-09.enex"

    save_enex_backup_to_mysql_db(
        enex_backup_pathname=enex_backup_pathname, database_pathname=database_pathname
    )
