from . import db
import uuid
# from sqlalchemy.dialects.postgresql import JSONB

class Users(db.Model):
    """
    Usersモデル
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(256), unique=True)
    password = db.Column(db.String(64))
    projects_create = db.Column(db.Boolean)
    users_projects = db.relationship('UserProjects')

    def __init__(self, username, email, password, projects_create):
        self.name = username
        self.email = email
        self.password = password
        self.projects_create = projects_create

class Projects(db.Model):
    """
    Projectsモデル
    """
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64))
    uuid = db.Column(db.String(256), unique=True)
    creator_id = db.Column(db.Integer)
    users_projects = db.relationship('UserProjects')
    flows = db.relationship('Flows')

    def __init__(self, name, uuid, creator_id):
        self.name = name
        self.uuid = uuid
        self.creator_id = creator_id

class Flows(db.Model):
    """
    Flowsモデル
    """
    __tablename__ = 'flows'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # flow_json = db.Column(JSONB)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    creator_id = db.Column(db.Integer)

    def __init__(self, flow_json, project_id, creator_id):
        self.flow_json = flow_json
        self.project_id = project_id
        self.creator_id = creator_id

class UserProjects(db.Model):
    """
    UserProjectsモデル
    """
    __tablename__ = 'user_projects'
    __table_args__ = (
        db.PrimaryKeyConstraint('user_id', 'project_id'),
    )
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    project_delete = db.Column(db.Boolean, default=True)
    flow_create = db.Column(db.Boolean, default=True)
    flow_delete = db.Column(db.Boolean, default=True)
    flow_update = db.Column(db.Boolean, default=True)
    flow_execute = db.Column(db.Boolean, default=True)
    flow_read = db.Column(db.Boolean, default=True)

    def __init__(self, project_id, user_id):
        self.user_id = user_id
        self.project_id = project_id


def create_user(name, email, password, projects_create=True):
    """
    ユーザを作成する
    """
    user = Users(name, email, password, projects_create)
    db.session.add(user)
    db.session.commit()

def get_user_by_id(id):
    """
    ユーザのIDからユーザ情報を取得する
    """
    user = db.session.query(Users).filter_by(id=id).first()
    return user

def check_can_create_projects(user_id):
    """
    指定したユーザがプロジェクトを作成できるかのチェック
    デコレータでいいかも
    """
    user = get_user_by_id(user_id)
    return user.projects_create

def create_project(project_name, user_id):
    """
    プロジェクトを作成する
    それと同時にユーザ×プロジェクトも作成する
    """
    # プロジェクト作成
    project = Projects(project_name, str(uuid.uuid4()), user_id)
    db.session.add(project)
    db.session.commit()

    # ユーザ×プロジェクト作成
    userproject = UserProjects(project.id, user_id)
    db.session.add(userproject)

    db.session.commit()

def get_readable_projects_by_user_id(user_id):
    """
    自分が閲覧できるプロジェクト一覧を取得する
    """
    # projects = db.session.query(Projects).filter(Projects.id.in_(db.session.query(UserProjects.project_id).filter(UserProjects.user_id==user_id)))
    projects = db.session.query(Projects, UserProjects) \
                                .join(UserProjects, Projects.id==UserProjects.project_id) \
                                .add_columns(Projects.name, Projects.id, Projects.uuid, Projects.creator_id, UserProjects.project_delete) \
                                .filter(UserProjects.user_id==user_id)
    return projects

def get_all_projects():
    """
    全てのプロジェクトを取得する
    """
    projects = db.session.query(Projects).all()
    return projects

def delete_project_by_uuid(project_uuid):
    """
    指定したプロジェクトを削除する
    ユーザ×プロジェクトも削除する
    """
    project = db.session.query(Projects).filter_by(uuid=project_uuid).first()
    db.session.query(UserProjects).filter_by(project_id=project.id).delete()
    db.session.delete(project)
    db.session.commit()

def get_user_projects(user_id, project_uuid):
    """
    指定したユーザ×プロジェクト情報を取得する
    """
    user = get_user_by_id(user_id)
    project = db.session.query(Projects).filter_by(uuid=project_uuid).first()
    userproject = db.session.query(UserProjects).filter_by(project_id=project.id, user_id=user.id).first()
    return userproject

def check_can_delete_projects(user_id, project_uuid):
    """
    指定したユーザが指定したプロジェクト情報を削除できるかの判定
    デコレータでいいかも
    """
    userproject = get_user_projects(user_id, project_uuid)
    return userproject.project_delete

def get_flows_by_project_uuid(project_uuid):
    pass
