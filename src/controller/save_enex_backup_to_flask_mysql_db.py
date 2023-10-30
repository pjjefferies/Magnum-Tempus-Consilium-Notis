import datetime as dt
from enum import Enum, auto
from typing import Optional

from box import Box
from flask import Flask  # , render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)

# from sqlalchemy.sql import func

from src.controller.load_import_data import load_enex_backup
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


class NoteType(Enum):
    TASK = auto()
    REFERENCE_NOTE = auto()
    PROJECT = auto()
    UNKNOWN = auto()


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    title: Mapped[str] = mapped_column(db.String(MAX_TITLE_LEN), default="")
    body_text: Mapped[str] = mapped_column(db.String(MAX_BODY_TEXT_LEN), default="")
    created: Mapped[dt.datetime] = mapped_column(
        db.DateTime, default=dt.datetime.now(dt.UTC)
    )
    updated: Mapped[dt.datetime] = mapped_column(
        db.DateTime, default=dt.datetime.now(dt.UTC)
    )
    reminder_time: Mapped[Optional[dt.datetime]] = mapped_column(
        db.DateTime, default=None
    )

    where_tag: Mapped["WhereTag"] = db.relationship(
        "WhereTag",
        secondary="task_where_tags_association",
        back_populates="tasks",
    )
    when_tag: Mapped["WhenTag"] = db.relationship(
        "WhenTag", secondary="task_when_tags_association", back_populates="tasks"
    )
    reference_tags: Mapped[list["ReferenceTag"]] = db.relationship(
        "ReferenceTag",
        secondary="task_reference_tags_association",
        back_populates="tasks",
    )
    projects: Mapped[list["Project"]] = db.relationship(
        "Project", secondary="project_task_association", back_populates="tasks"
    )

    def __repr__(self) -> str:
        return (
            f"Task: id: {self.id}, title: {self.title}, created: {self.created}, "
            f"updated: {self.updated}, "
            f"reminder_time: {self.reminder_time}, where_tag: {self.where_tag}, "
            f"when_tag: {self.when_tag}, body_text[:16]: {self.body_text[:16]}, "
            f"Projects: {[a_project.title for a_project in self.projects]}"
        )


class WhereTag(Base):
    __tablename__ = "where_tags_table"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(MAX_TAG_NAME_LEN), nullable=False)
    tasks: Mapped[list["Task"]] = db.relationship(
        "Task",
        secondary="task_where_tags_association",
        back_populates="where_tag",
    )

    def __repr__(self) -> str:
        return f"WhereTag: id: {self.id}, name: {self.name}"


task_where_tags = db.Table(
    "task_where_tags_association",
    Base.metadata,
    db.Column("task_id", db.Integer, db.ForeignKey("tasks.id", ondelete="CASCADE")),
    db.Column(
        "where_tag_id",
        db.Integer,
        db.ForeignKey("where_tags_table.id", ondelete="CASCADE"),
    ),
)


class WhenTag(Base):
    __tablename__ = "when_tags"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(MAX_TAG_NAME_LEN))
    tasks: Mapped[list["Task"]] = db.relationship(
        "Task", secondary="task_when_tags_association", back_populates="when_tag"
    )

    def __repr__(self) -> str:
        return f"WhenTag: id: {self.id}, name: {self.name}"


task_when_tags = db.Table(
    "task_when_tags_association",
    Base.metadata,
    db.Column("task_id", db.Integer, db.ForeignKey("tasks.id", ondelete="CASCADE")),
    db.Column(
        "when_tag_id", db.Integer, db.ForeignKey("when_tags.id", ondelete="CASCADE")
    ),
)


class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    title: Mapped[str] = mapped_column(db.String(MAX_TITLE_LEN), default="")
    created: Mapped[dt.datetime] = mapped_column(
        db.DateTime, default=dt.datetime.now(dt.UTC)
    )
    updated: Mapped[dt.datetime] = mapped_column(
        db.DateTime, default=dt.datetime.now(dt.UTC)
    )
    reminder_time: Mapped[Optional[dt.datetime]] = mapped_column(
        db.DateTime, default=None
    )
    body_text: Mapped[str] = mapped_column(db.String(MAX_BODY_TEXT_LEN), default="")
    reference_tags: Mapped[list["ReferenceTag"]] = db.relationship(
        "ReferenceTag",
        secondary="note_reference_tags_association",
        back_populates="notes",
    )

    def __repr__(self) -> str:
        return (
            f"Note: id: {self.id}, title: {self.title}, created: {self.created}, "
            f"updated: {self.updated}, reminder_time: {self.reminder_time}, "
            f"reference_tags: {[a_tag.name for a_tag in self.reference_tags]}, "
            f"body_text[:16]: {self.body_text[:16]}"
        )


class ReferenceTag(Base):
    __tablename__ = "reference_tags"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String(MAX_TAG_NAME_LEN))
    notes: Mapped[list["Note"]] = db.relationship(
        "Note",
        secondary="note_reference_tags_association",
        back_populates="reference_tags",
    )
    tasks: Mapped[list["Task"]] = db.relationship(
        "Task",
        secondary="task_reference_tags_association",
        back_populates="reference_tags",
    )

    def __repr__(self) -> str:
        return f"ReferenceTag: id: {self.id}, name: {self.name}"


notes_reference_tags = db.Table(
    "note_reference_tags_association",
    Base.metadata,
    db.Column("note_id", db.Integer, db.ForeignKey("notes.id", ondelete="CASCADE")),
    db.Column(
        "reference_tag_id",
        db.Integer,
        db.ForeignKey("reference_tags.id", ondelete="CASCADE"),
    ),
)

tasks_reference_tags = db.Table(
    "task_reference_tags_association",
    Base.metadata,
    db.Column("task_id", db.Integer, db.ForeignKey("tasks.id", ondelete="CASCADE")),
    db.Column(
        "reference_tag_id",
        db.Integer,
        db.ForeignKey("reference_tags.id", ondelete="CASCADE"),
    ),
)


class Resource(Base):
    __tablename__ = "resources"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    file_name: Mapped[str] = mapped_column(db.String(MAX_TITLE_LEN))
    hash: Mapped[str] = mapped_column(db.String(MAX_TITLE_LEN))
    data: Mapped[str] = mapped_column(db.String(MAX_IMAGE_DATA_LEN))
    mime: Mapped[str] = mapped_column(db.String(MAX_TITLE_LEN))
    width: Mapped[int] = mapped_column(db.Integer, nullable=True)
    height: Mapped[int] = mapped_column(db.Integer, nullable=True)

    def __repr__(self) -> str:
        return (
            f"Resource: id: {self.id}, file_name: {self.file_name}, hash: {self.hash}, "
            f"mime: {self.mime}, width: {self.width}, "
            f"height: {self.height}, data[:16]: {self.data[:16]}"
        )


class Project(Base):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    title: Mapped[str] = mapped_column(db.String(MAX_TITLE_LEN))
    created: Mapped[dt.datetime] = mapped_column(
        db.DateTime, default=dt.datetime.now(dt.UTC)
    )
    updated: Mapped[dt.datetime] = mapped_column(
        db.DateTime, default=dt.datetime.now(dt.UTC)
    )
    tasks: Mapped[list["Task"]] = db.relationship(
        "Task", secondary="project_task_association", back_populates="projects"
    )

    def __repr__(self) -> str:
        return (
            f"Project: id: {self.id}, title: {self.title}, created: {self.created}, "
            f"updated: {self.updated}, tasks: {[a_task.title for a_task in self.tasks]}"
        )


project_tasks = db.Table(
    "project_task_association",
    Base.metadata,
    db.Column(
        "project_id", db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE")
    ),
    db.Column("task_id", db.Integer, db.ForeignKey("tasks.id", ondelete="CASCADE")),
)


def save_enex_backup_to_mysql_db(*, enex_backup_pathname: str, database_pathname: str):
    # engine = create_engine(f"sqlite+pysqlite:///{database_pathname}", echo=True)

    """
    What kind of database are we communicating with? This is the sqlite portion above,
    which links in SQLAlchemy to an object known as the dialect.
    The Python DBAPI is a third party driver that SQLAlchemy uses to interact with a
    particular database. In this case, we’re using the name pysqlite, which in modern
    Python use is the sqlite3 standard library interface for SQLite.
    """
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite+pysqlite:///{database_pathname}"
    # app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Load Data from ENEX file(s)
    notes, resources = load_enex_backup(filepath=enex_backup_pathname, logger=logger)

    # Add all Where and When Tags to their respective databases if they're not there already
    # Remvoe the adding of them for each note below
    # For Tags in note that are not in Where or When tags, add tag as Reference Tag or something like that

    with app.app_context():
        for note in notes:
            logger.debug(msg=f"{note['title']=}")
            logger.debug(msg=f"{note.keys()=}")
            note_type: NoteType = NoteType.REFERENCE_NOTE  # default
            this_note_where_tag: str = ""
            this_note_when_tag: str = ""
            this_note_reference_tags: set[str] = set()
            this_tag: str
            empty_tags: list[str] = []
            for this_tag in note.get("tags", empty_tags):
                if not this_note_where_tag:  # find first where_tag
                    if this_tag in WHERE_TAGS:
                        this_note_where_tag = this_tag
                        continue
                if not this_note_when_tag:  # find first when_tag
                    if this_tag in WHEN_TAGS:
                        this_note_when_tag = this_tag
                        continue
                if this_tag not in WHERE_TAGS and this_tag not in WHEN_TAGS:
                    this_note_reference_tags.add(this_tag)

            logger.debug(msg=f"{this_note_where_tag=}, {this_note_when_tag=}")

            # Add Where Tag  to WhereTag if doesn't exist yet
            logger.debug(msg=f"{this_note_where_tag=}")
            where_tag_in_db: Optional[WhereTag] = None
            if this_note_where_tag:
                note_type = NoteType.TASK  # If there is a Where Tag, this is a task
                where_tag_in_db = db.session.scalars(
                    select(WhereTag).where(WhereTag.name == this_note_where_tag)
                ).first()
                logger.debug(msg=f"{where_tag_in_db=}")
                if where_tag_in_db is None:
                    logger.debug(msg=f"Adding {this_note_where_tag} to WhereTag")
                    new_where_tag = WhereTag(name=this_note_where_tag)
                    db.session.add(new_where_tag)
                    db.session.commit()
                    logger.debug(msg=f"Let's check if new_where_tag has been added...")
                    where_tag_query1_5 = db.session.scalars(
                        select(WhereTag).where(WhereTag.name == this_note_where_tag)
                    ).first()
                    logger.debug(msg=f"{where_tag_query1_5=}")

            # Add Where Tag to Task if there is one
            if this_note_where_tag:
                this_note_where_tag = db.session.scalars(
                    select(WhereTag).where(WhereTag.name == this_note_where_tag)
                ).first()
            else:
                this_note_where_tag = None

            # Add When Tag to WhenTag if doesn't exist yet
            when_tag_in_db: Optional[WhenTag] = None
            if this_note_when_tag:
                note_type = NoteType.TASK  # If there is a When Tag, this is a task
                when_tag_in_db = db.session.scalars(
                    select(WhenTag).where(WhenTag.name == this_note_when_tag)
                ).first()
                logger.debug(msg=f"{when_tag_in_db=}")
                if when_tag_in_db is None:
                    logger.debug(msg=f"Adding {this_note_when_tag} to WhenTag")
                    new_when_tag = WhenTag(name=this_note_when_tag)
                    db.session.add(new_when_tag)
                    db.session.commit()
                    logger.debug(msg=f"Let's check if new_when_tag has been added...")
                    when_tag_in_db1_5 = db.session.scalars(
                        select(WhenTag).where(WhenTag.name == this_note_when_tag)
                    ).first()
                    logger.debug(msg=f"{when_tag_in_db1_5=}")

            # Add When Tag to Task if there is one
            if this_note_when_tag:
                new_when_tag = db.session.scalars(
                    select(WhenTag).where(WhenTag.name == this_note_when_tag)
                ).first()
            else:
                this_note_when_tag = None

            # Add Reference Tag to ReferenceTag if doesn't exist yet
            reference_tag_in_db: Optional[ReferenceTag] = None
            reference_tags_in_note: list[ReferenceTag] = []
            a_tag: str
            for a_tag in this_note_reference_tags:
                reference_tag_in_db = db.session.scalars(
                    select(ReferenceTag).where(ReferenceTag.name == a_tag)
                ).first()
                logger.debug(msg=f"{reference_tag_in_db=}")
                if reference_tag_in_db is None:
                    logger.debug(msg=f"Adding {a_tag} to ReferenceTag")
                    new_reference_tag = ReferenceTag(name=a_tag)
                    db.session.add(new_reference_tag)
                    db.session.commit()
                    logger.debug(
                        msg=f"Let's check if new_reference_tag has been added..."
                    )
                    reference_tag_in_db = db.session.scalars(
                        select(ReferenceTag).where(ReferenceTag.name == a_tag)
                    ).first()
                    logger.debug(msg=f"{reference_tag_in_db=}")

                # Add Reference Tag to Note
                reference_tags_in_note.append(reference_tag_in_db)

            try:
                created_dt: dt.datetime = dt.datetime.fromisoformat(note["created"])
            except (TypeError, KeyError):
                created_dt = dt.datetime.now(dt.UTC)
            try:
                updated_dt: dt.datetime = dt.datetime.fromisoformat(note["updated"])
            except (TypeError, KeyError):
                updated_dt = dt.datetime.now(dt.UTC)
            try:
                reminder_dt: Optional[dt.datetime] = dt.datetime.fromisoformat(
                    note["reminder-time"]
                )
            except (TypeError, KeyError):
                reminder_dt = None

            match note_type:
                case NoteType.TASK:
                    a_task = Task(
                        title=note.get("title", ""),
                        created=created_dt,
                        updated=updated_dt,
                        body_text=note.get("content", ""),
                        reminder_time=reminder_dt,
                    )
                    logger.debug(msg=f"{a_task=}")

                    task_exists: bool = db.session.scalars(
                        select(Task).where(
                            Task.title == a_task.title
                            and Task.body_text == a_task.body_text
                            and Task.when_tag == a_task.when_tag
                            and Task.where_tag == a_task.where_tag
                        )
                    ).first()
                    if not task_exists:
                        db.session.add(a_task)
                        db.session.commit()
                case NoteType.REFERENCE_NOTE:
                    a_note = Note(
                        title=note.get("title", ""),
                        created=created_dt,
                        updated=updated_dt,
                        body_text=note.get("content", ""),
                        reference_tags=reference_tags_in_note,
                        reminder_time=reminder_dt,
                    )
                    logger.debug(msg=f"{a_note=}")

                    note_exists: bool = db.session.scalars(
                        select(Note).where(
                            Note.title == a_note.title
                            and Note.body_text == a_note.body_text
                            and Note.reference_tags == a_note.reference_tags
                        )
                    ).first()
                    if not note_exists:
                        db.session.add(a_note)
                        db.session.commit()
                case _:
                    pass

            logger.debug(msg=f"Task added. Let's see if it's correct...")
            task1 = db.session.scalars(
                select(Task).where(Task.title == note["title"])
            ).first()
            logger.debug(msg=f"{task1=}")
            task_list = db.session.scalars(select(Task)).all()
            logger.debug(msg=f"Current number of tasks: {len(task_list)=}")

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

            resource_exists: bool = db.session.scalars(
                select(Resource).where(Resource.hash == a_resource.hash)
            ).first()
            if not resource_exists:
                db.session.add(a_resource)
                db.session.commit()

        resource_list = db.session.scalars(select(Resource)).all()
        logger.debug(msg=f"Current number of resources: {len(resource_list)=}")

        logger.debug(msg=f"Let's see what's in database...")
        tasks_in_db = db.session.scalars(select(Task)).all()
        logger.debug(msg=f"{tasks_in_db=}")
        logger.debug(msg=f"There are {len(tasks_in_db)} tasks in the database")

        notes_in_db = db.session.scalars(select(Note)).all()
        logger.debug(msg=f"{notes_in_db=}")
        logger.debug(msg=f"There are {len(notes_in_db)} notes in the database")

        resources_in_db = db.session.scalars(
            select(Resource).order_by(Resource.file_name)
        ).all()
        logger.debug(msg=f"There are {len(resources_in_db)} resources in the database")


if __name__ == "__main__":
    # database_pathname: str = "data/database/notes_data.db"
    database_pathname: str = "../../../data/database/notes_data.db"
    enex_backup_pathname: str = "data/import_data/Test Export Tasks (2023-10-20).enex"

    save_enex_backup_to_mysql_db(
        enex_backup_pathname=enex_backup_pathname, database_pathname=database_pathname
    )
