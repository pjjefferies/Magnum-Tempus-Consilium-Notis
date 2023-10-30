

 # TBD to simplify save_enex_backup_to_flask_mysql_db.py


def add_tasks_to_db(tasks: list[])

with app.app_context():
        for task in tasks:
            logger.debug(msg=f"{task['title']=}")
            this_note_where_tag: str = ""
            this_note_when_tag: str = ""
            this_tag: str
            empty_tags: list[str] = []
            for this_tag in task.get("tags", empty_tags):
                if not this_note_where_tag:  # find first where_tag
                    if this_tag in WHERE_TAGS:
                        this_note_where_tag = this_tag
                if not this_note_when_tag:  # find first when_tag
                    if this_tag in WHEN_TAGS:
                        this_note_when_tag = this_tag
            logger.debug(msg=f"{this_note_where_tag=}, {this_note_when_tag=}")

            a_task = Task(
                title=task.get("title", ""),
                created=dt.datetime.fromisoformat(
                    task.get("created", dt.datetime.now(dt.UTC))
                ),
                updated=dt.datetime.fromisoformat(
                    task.get("updated", dt.datetime.now(dt.UTC))
                ),
                body_text=task.get("content", ""),
            )
            logger.debug(msg=f"{a_task=}")

            # Add Where Tag  to Where_Tag if doesn't exist yet
            logger.debug(msg=f"{this_note_where_tag=}")
            where_tag_in_db: Optional[WhereTag] = None
            if this_note_where_tag:
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
                a_task.where_tag = db.session.scalars(
                    select(WhereTag).where(WhereTag.name == this_note_where_tag)
                ).first()
                logger.debug(
                    msg=f"Added {this_note_where_tag} to Task as where_tag={a_task.where_tag}"
                )
                logger.debug(msg=f"{a_task.where_tag=}")

            # Add When Tag to When_Tag if doesn't exist yet
            when_tag_in_db: Optional[WhenTag] = None
            if this_note_when_tag:
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
                a_task.when_tag = db.session.scalars(
                    select(WhenTag).where(WhenTag.name == this_note_when_tag)
                ).first()
                logger.debug(
                    msg=f"Added {this_note_when_tag} to Task as when_tag_id={a_task.when_tag}"
                )
                logger.debug(msg=f"{a_task.when_tag=}")

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