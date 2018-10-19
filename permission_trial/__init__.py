from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template
from hamlish_jinja import HamlishExtension
from werkzeug import ImmutableDict
from flask_admin import Admin

class FlaskWithHamlish(Flask):
    jinja_options = ImmutableDict(extensions=[HamlishExtension])

app = Flask('kskp')
admin = Admin(app, name='microblog', template_mode='bootstrap3')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://dev:test@0.0.0.0:5432/dev"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'hogehoge'

db = SQLAlchemy(app)
