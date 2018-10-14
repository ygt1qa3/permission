from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template
from hamlish_jinja import HamlishExtension
from werkzeug import ImmutableDict

class FlaskWithHamlish(Flask):
    jinja_options = ImmutableDict(extensions=[HamlishExtension])

app = FlaskWithHamlish('kskp_perm')
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://dev:secret@0.0.0.0:5432/dev"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'hogehoge'

db = SQLAlchemy(app)
