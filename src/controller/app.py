from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from sqlalchemy.sql import text

from src.controller.save_enex_backup_to_flask_mysql_db import Task

# this variable, db, will be used for all SQLAlchemy commands
db = SQLAlchemy()
# create the app
app = Flask(__name__)
# change string to the name of your database; add path if necessary
database_pathname: str = "../../../data/database/notes_data.db"
db_name = f"sqlite+pysqlite:///{database_pathname}"

app.config["SQLALCHEMY_DATABASE_URI"] = db_name
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

# initialize the app with Flask-SQLAlchemy
db.init_app(app)


# NOTHING BELOW THIS LINE NEEDS TO CHANGE
# this route will test the database connection - and nothing more
@app.route("/")
def testdb():
    try:
        result = db.session.scalars(select(Task)).all()
        return "<h1>It works.</h1>/p<p>{results}</p>"
    except Exception as e:
        # e holds description of the error
        error_text = "<p>The error:<br>" + str(e) + "</p>"
        hed = "<h1>Something is broken.</h1>"
        return hed + error_text


if __name__ == "__main__":
    app.run(debug=True)
