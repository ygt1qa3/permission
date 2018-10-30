from . import db
import uuid
import inspect
import sqlalchemy
import json
import ast
from sqlalchemy import TypeDecorator, types
from sqlalchemy.dialects.postgresql import JSONB

# sqlalchemyのgithubを見ると、sqliteのjsonを追加したものが最新ソースに上がっているが
# 最新版のsqlalchemy(2018/10/23現在：ver1.2.12)にはまだ更新されていない模様（Pyplのpkgが更新されていない？）
# 下記importがエラーになる
# from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.dialects.sqlite import BLOB

class Json(TypeDecorator):
    """
    unittestのsqlite用Jsonクラス
    jsonを受け取り、DBにはStringで保存、使うときはjsonに再び変換して返す
    """
    @property
    def python_type(self):
        return object

    impl = types.String

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_literal_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        try:
            return ast.literal_eval(value)
        except (ValueError, TypeError):
            return None

class Users(db.Model):
    """
    Usersモデル
    """
    __tablename__ = 'users'
    # カラム
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.ForeignKey('groups.id'))
    name = db.Column(db.String(64))
    email = db.Column(db.String(256), unique=True)
    password = db.Column(db.String(64))
    projects_creatable = db.Column(db.Boolean)
    # リレーション
    userpermissions_project = db.relationship('UserPermissions_Project')
    userpermissions_flow = db.relationship('UserPermissions_Flow')

    def __init__(self, username, email, password, projects_creatable):
        self.name = username
        self.email = email
        self.password = password
        self.projects_creatable = projects_creatable

class Groups(db.Model):
    """
    Groupsモデル
    """
    __tablename__ = 'groups'
    # カラム
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64))
    projects_creatable = db.Column(db.Boolean)
    # グループにプロジェクト作成権限はいらないかも。
    # グループにはユーザ（DB上に存在する）が所属する。
    # また、ユーザにはプロジェクト作成に関する権限が設定されており、
    # ユーザの権限がグループの権限より優先されることから、グループに所属しているいないに関わらずユーザのプロジェクト作成権限が存在するのでそれが使われる。
    # →入れておく

    # リレーション
    grouppermissions_project = db.relationship('GroupPermissions_Project')
    grouppermissions_flow = db.relationship('GroupPermissions_Flow')

    def __init__(self, group_name, projects_creatable):
        self.name = group_name
        self.projects_creatable = projects_creatable

class Projects(db.Model):
    """
    Projectsモデル
    """
    __tablename__ = 'projects'
    # カラム
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64))
    uuid = db.Column(db.String(256), unique=True)
    creator_id = db.Column(db.Integer)
    # リレーション
    userpermissions_project = db.relationship('UserPermissions_Project')
    grouppermissions_project = db.relationship('GroupPermissions_Project')
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

    def get_flow_json_column_type(db_name):
        if db_name == 'postgresql':
            return db.Column(JSONB)
        elif db_name == 'sqlite':
            return db.Column(Json)
        else:
            return db.Column(db.JSON)

    # カラム
    # id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 一応既存のkskpの合わせるためにflow_uuidを主キーにしてみる
    uuid = db.Column(db.String, primary_key=True)
    json = get_flow_json_column_type(db.engine.name)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    creator_id = db.Column(db.Integer)
    # リレーション
    userpermissions_flow = db.relationship('UserPermissions_Flow')
    grouppermissions_flow = db.relationship('GroupPermissions_Flow')

    def __init__(self, flow_uuid, flow_json, project_id, creator_id):
        self.uuid = flow_uuid
        self.json = flow_json
        self.project_id = project_id
        self.creator_id = creator_id

class UserPermissions_Project(db.Model):
    """
    UserPermissions_Projectモデル
    """
    __tablename__ = 'userpermissions_project'
    __table_args__ = (
        db.PrimaryKeyConstraint('user_id', 'project_id'),
    )
    # カラム
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    deletable_project = db.Column(db.Boolean, default=True)
    creatable_flows = db.Column(db.Boolean, default=True)
    deletable_flows = db.Column(db.Boolean, default=True)
    readable_flows = db.Column(db.Boolean, default=True)

    def __init__(self, user_id, project_id, deletable_project=True, creatable_flows=True,
                 deletable_flows=True, readable_flows=True):
        self.user_id = user_id
        self.project_id = project_id
        self.deletable_project = deletable_project
        self.creatable_flows = creatable_flows
        self.deletable_flows = deletable_flows
        self.readable_flows = readable_flows

class GroupPermissions_Project(db.Model):
    """
    GroupPermissions_Projectモデル
    """
    __tablename__ = 'grouppermissions_project'
    __table_args__ = (
        db.PrimaryKeyConstraint('group_id', 'project_id'),
    )
    # カラム
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    # プロジェクトを削除できるか
    deletable_project = db.Column(db.Boolean, default=False)
    # 配下にフローを作成できるか
    creatable_flows = db.Column(db.Boolean, default=False)
    # 配下のフローを削除できるか
    deletable_flows = db.Column(db.Boolean, default=False)
    # 配下のフロー一覧の表示
    readable_flows = db.Column(db.Boolean, default=True)

    # グループの初期パーミッションをlinuxのディレクトリの初期パーミッションと同じにするなら、
    # linuxは初期umaskが022でグループのパーミッションは5(r-x)になるので、
    # できることは、プロジェクト配下の「フロー一覧が見える」となり
    # それ以外はFalseになる、とりあえずこの方向で。

    def __init__(self, group_id, project_id, deletable_project=False, creatable_flows=False,
                 deletable_flows=False, readable_flows=True):
        self.group_id = group_id
        self.project_id = project_id
        self.deletable_project = deletable_project
        self.creatable_flows = creatable_flows
        self.deletable_flows = deletable_flows
        self.readable_flows = readable_flows

class UserPermissions_Flow(db.Model):
    """
    UserPermissions_Flowモデル
    """
    __tablename__ = 'userpermissions_flow'
    __table_args__ = (
        db.PrimaryKeyConstraint('user_id', 'flow_uuid'),
    )
    # カラム
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    flow_uuid = db.Column(db.String, db.ForeignKey('flows.uuid'))
    # フローデザイナへアクセスできるか
    readable_flow = db.Column(db.Boolean, default=True)
    # フローを編集できるか
    updatable_flow = db.Column(db.Boolean, default=True)
    # フローを実行できるか
    executable_flow = db.Column(db.Boolean, default=True)

    # linuxでは初期パーミッションはユーザ（所有者）の場合は、実行許可を除く６だが
    # 流石に実行できるべきであるので７（全て許可）にしておく

    def __init__(self, user_id, flow_uuid, updatable_flow=True,
                 readable_flow=True, executable_flow=True):
        self.user_id = user_id
        self.flow_uuid = flow_uuid
        self.updatable_flow = updatable_flow
        self.readable_flow = readable_flow
        self.executable_flow = executable_flow

class GroupPermissions_Flow(db.Model):
    """
    GroupPermissions_Flowモデル
    """
    __tablename__ = 'grouppermissions_flow'
    __table_args__ = (
        db.PrimaryKeyConstraint('group_id', 'flow_uuid'),
    )
    # カラム
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    flow_uuid = db.Column(db.String, db.ForeignKey('flows.uuid'))
    updatable_flow = db.Column(db.Boolean, default=False)
    readable_flow = db.Column(db.Boolean, default=True)
    executable_flow = db.Column(db.Boolean, default=True)

    # linuxでは初期パーミッションはグループの場合は、読み取り可能のみの４だが
    # 実行もできた方がいいと思い（実行後は結果ができるだけなので、大きな悪影響はないと思われるため）
    # とりあえず５（実行とフローデザイナ閲覧）にしておく

    def __init__(self, group_id, flow_uuid, updatable_flow=False,
                 readable_flow=True, executable_flow=True):
        self.group_id = group_id
        self.flow_uuid = flow_uuid
        self.updatable_flow = updatable_flow
        self.readable_flow = readable_flow
        self.executable_flow = executable_flow

def create_user(name, email, password, projects_creatable=True):
    """
    ユーザを作成する
    プロジェクト作成権限はとりあえず、デフォルトでTrueに。
    """
    user = Users(name, email, password, projects_creatable)
    db.session.add(user)
    db.session.commit()

def get_user_by_id(user_id):
    """
    ユーザのIDからユーザ情報を取得する
    """
    user = db.session.query(Users).filter_by(id=user_id).first()
    return user

def replace_user_email_with_old_email(new_email, old_email):
    """
    ユーザのemailを更新する
    """
    user = db.session.query(Users).filter_by(email=old_email).first()
    user.email = new_email
    db.session.add(user)
    db.session.commit()

def get_projects_creatable_by_user_id(user_id):
    """
    指定したユーザがプロジェクトを作成できるかのチェック
    """
    user = get_user_by_id(user_id)
    return user.projects_creatable

def create_project(project_name, user_id):
    """
    プロジェクトを作成する
    それと同時にユーザ×プロジェクトも作成する
    また、ユーザがグループに所属していた場合、グループ×プロジェクトも作成する
    """
    # プロジェクト作成
    project = Projects(project_name, str(uuid.uuid4()), user_id)
    db.session.add(project)
    db.session.commit()

    # ユーザ×プロジェクト作成
    userpermission_project = UserPermissions_Project(user_id, project.id)
    db.session.add(userpermission_project)

    # ユーザがグループに所属していた場合、グループ×プロジェクトも作成する
    user = get_user_by_id(user_id)
    if not user.group_id is None:
        grouppermission_project = GroupPermissions_Project(user.group_id, project.id)
        db.session.add(grouppermission_project)

    # コミット
    db.session.commit()

def create_flow(flow_name, user, project, flow_uuid=None):
    """
    新規フローを作成し、DBに保存する
    それと同時にユーザ×フローも作成する
    また、ユーザがグループに所属していた場合、グループ×フローも作成する
    """
    if flow_uuid is None:
        flow_uuid = str(uuid.uuid4())

    def make_flow_json(flow_name, project_id):
        """
        新規フローのJSONを作成する
        """
        data = {
            'proejctId': project_id,
            'label': flow_name,
            'ports': [[],[]],
            'params': [],
            'description': ""
        }
        return json.dumps(data)

    # flowのjsonを作成する
    flow_json = make_flow_json(flow_name, project.id)

    # flowデータを作成する
    flow = Flows(flow_uuid, flow_json, project.id, user.id)
    db.session.add(flow)

    # ユーザ×フロー作成
    userpermission_flow = UserPermissions_Flow(user.id, flow_uuid)
    db.session.add(userpermission_flow)

    # グループ×フロー
    if not user.group_id is None:
        grouppermission_flow = GroupPermissions_Flow(user.group_id, flow_uuid)
        db.session.add(grouppermission_flow)

    # コミット
    db.session.commit()

def fetch_flow_by_uuid(flow_uuid):
    """
    指定したフローのモデルオブジェクトを返す
    """
    flow = db.session.query(Flows).filter_by(uuid=flow_uuid).first()
    return flow

def update_flow(flow_uuid, data):
    """
    フローを更新する
    """
    # flow_uuidを元にflowのjsonを取得
    flow = db.session.query(Flows).filter(Flows.uuid==flow_uuid).first()
    # JSON文字列で取得されるので一旦dictに変更してupdate、json文字列に戻して更新している
    json_dict = json.loads(flow.json)
    json_dict.update(data)
    flow.json = json.dumps(json_dict)
    db.session.commit()

def delete_flow_by_uuid(flow_uuid):
    """
    フローを削除する
    ユーザ×フローとグループ×フローも削除する
    """
    flow = fetch_flow_by_uuid(flow_uuid)
    db.session.query(UserPermissions_Flow).filter_by(flow_uuid=flow_uuid).delete()
    db.session.query(GroupPermissions_Flow).filter_by(flow_uuid=flow_uuid).delete()
    db.session.delete(flow)

    try:
        db.session.commit()
    except:
        return False

    return True

def fetch_readable_flows_by_project_id_and_user_id(project_id, user_id):
    """
    指定したプロジェクトが持ち、指定したユーザが見れるフロー一覧の内容リストをuuidを付け加えて返す
    """
    flows = db.session.query(Flows, UserPermissions_Flow) \
                                .join(UserPermissions_Flow, Flows.uuid==UserPermissions_Flow.flow_uuid) \
                                .filter(UserPermissions_Flow.user_id==user_id, Flows.project_id==project_id)

    return flows

def fetch_readable_flows_by_project_id_and_group_id(project_id, group_id):
    """
    指定したプロジェクトが持ち、指定したグループが見れるフロー一覧の内容リストをuuidを付け加えて返す
    """
    flows = db.session.query(Flows, GroupPermissions_Flow) \
                                .join(GroupPermissions_Flow, Flows.uuid==GroupPermissions_Flow.flow_uuid) \
                                .filter(GroupPermissions_Flow.group_id==group_id, Flows.project_id==project_id)

    return flows

def get_flow_by_flow_items(flow_items):
    """
    指定したフローの要素からフローを取得する
    使う道があるかどうかわからない
    """
    pass

def grant_user_to_project(user_id, project_id, deletable_project=True, creatable_flows=True,
                               deletable_flows=True, updatable_flows=True, executable_flows=True, readable_flows=True):
    """
    指定したユーザとプロジェクトに対する権限を新規作成する
    """
    userpermission_project = UserPermissions_Project(user_id, project_id,
                                                    deletable_project,
                                                    creatable_flows, deletable_flows, readable_flows)
    db.session.add(userpermission_project)
    db.session.commit()

def fetch_readable_projects_by_user_id(user_id):
    """
    指定したユーザが閲覧できるプロジェクト一覧を取得する
    """
    # projects = db.session.query(Projects).filter(Projects.id.in_(db.session.query(UserPermissions_Project.project_id).filter(UserPermissions_Project.user_id==user_id)))
    projects = db.session.query(Projects, UserPermissions_Project) \
                                .join(UserPermissions_Project, Projects.id==UserPermissions_Project.project_id) \
                                .filter(UserPermissions_Project.user_id==user_id)
    return projects

def get_all_projects():
    """
    全てのプロジェクトを取得する
    """
    projects = db.session.query(Projects).all()
    return projects

def delete_project_and_permission(user_id, project_uuid):
    """
    指定したプロジェクトを削除する
    ユーザの操作として削除するので、権限を考慮する
    """
    # 権限の取得
    project_permission = get_permissions_project(user_id, project_uuid)

    if project_permission is None:
        # 指定したユーザと所属しているグループ、プロジェクトの間にはなんの権限もない
        return False

    if project_permission.deletable_project:
        if delete_project_by_uuid(project_uuid):
            return True
    return False

def delete_project_by_uuid(project_uuid):
    """
    指定したプロジェクトを削除する
    ユーザ×プロジェクトも削除する
    グループ×プロジェクトも削除する
    """
    project = db.session.query(Projects).filter_by(uuid=project_uuid).first()
    db.session.query(UserPermissions_Project).filter_by(project_id=project.id).delete()
    db.session.query(GroupPermissions_Project).filter_by(project_id=project.id).delete()
    db.session.delete(project)

    try:
        db.session.commit()
    except:
        return False

    return True

def get_userpermissions_project(user_id, project_id):
    """
    指定したユーザ×プロジェクト情報を取得する
    """
    userproject = db.session.query(UserPermissions_Project).filter_by(project_id=project_id, user_id=user_id).first()
    return userproject

def create_group(name, projects_creatable=True):
    """
    グループを作成する
    """
    group = Groups(name, projects_creatable)
    db.session.add(group)
    db.session.commit()

def delete_group_by_id(group_id):
    """
    指定したグループを削除する
    """
    group = get_group_by_id(group_id)
    db.session.delete(group)
    db.session.commit()

def get_group_by_id(id):
    """
    グループのIDからユーザ情報を取得する
    """
    group = db.session.query(Groups).filter_by(id=id).first()
    return group

def get_group_from_user_id(user_id):
    """
    指定したユーザが所属しているグループを取得する
    """
    user = get_user_by_id(user_id)
    group = get_group_by_id(user.group_id)
    return group

def assign_user_to_group(user_id, group_id):
    """
    指定したユーザを指定したグループに所属させる
    すでに所属していた場合は上書きする（ひとまずの仕様）
    """
    user = get_user_by_id(user_id)
    user.group_id = group_id
    db.session.add(user)
    db.session.commit()

def fetch_readable_projects_by_group_id(group_id):
    """
    指定したグループが閲覧できるプロジェクト一覧を取得する
    """
    projects = db.session.query(Projects, GroupPermissions_Project) \
                                .join(GroupPermissions_Project, Projects.id==GroupPermissions_Project.project_id) \
                                .filter(GroupPermissions_Project.group_id==group_id)
    return projects

def grant_group_to_project(group_id, project_id, deletable_project=False, creatable_flows=False,
                                deletable_flows=False, readable_flows=True):
    """
    指定したグループとプロジェクトに対する権限を新規作成する
    """
    grouppermission_project = GroupPermissions_Project(group_id, project_id,
                                                      deletable_project,
                                                      creatable_flows, deletable_flows, readable_flows)
    db.session.add(grouppermission_project)
    db.session.commit()

def get_grouppermissions_project(group_id, project_id):
    """
    指定したグループ×プロジェクトを返す
    """
    userproject = db.session.query(GroupPermissions_Project).filter_by(project_id=project_id, group_id=group_id).first()
    return userproject

def get_permissions_project(user_id, project_uuid):
    """
    適切なプロジェクト権限を返す
    ユーザ権限が存在する場合はそちらを優先する
    返す権限が存在しなければ、Noneを返す（とりあえず）
    """
    # プロジェクトを取得
    project = db.session.query(Projects).filter_by(uuid=project_uuid).first()

    # ユーザ×プロジェクトがあればそれを返す
    userpermission_project = get_userpermissions_project(user_id, project.id)
    if not userpermission_project is None:
        return userpermission_project

    # グループに所属しているか調べる
    group = get_group_from_user_id(user_id)
    # 所属していなければ、返す権限が存在しないのでNoneを返す
    if group is None:
        return None

    # ユーザ×プロジェクトがなく、グループ×プロジェクトがあればそれを返す
    grouppermission_project = get_grouppermissions_project(group.id, project.id)
    if not grouppermission_project is None:
        return grouppermission_project

    return None

def get_projects_with_permission(user_id):
    """
    プロジェクト一覧を権限付きで返す

    UserPermissions_ProjectとProjectsを結合したもの
    GroupPermissions_ProjectとProjectsを結合したもの
    2つの結果を基に作成している

    ユーザのパーミッションの方が優先なので、
    まずUserPermissions_ProjectとProjectsを結合したものを、返すリストに設定し
    GroupPermissions_Projectにのみ設定されているプロジェクト情報を
    返すリストに付け足している
    """
    projects = []
    project_id_list = []

    # ユーザ権限がついたプロジェクトを取得する
    projects_additional_user_permissions = fetch_readable_projects_by_user_id(user_id)
    for project in projects_additional_user_permissions:
        project_id_list.append(project.Projects.id)
        projects.append(make_projects_dict_from_result(project))

    # グループに所属しているか
    group = get_group_from_user_id(user_id)
    if group is None:
        return projects

    # グループ権限がついたプロジェクトを取得する
    projects_additional_group_permissions = fetch_readable_projects_by_group_id(group.id)
    if projects_additional_group_permissions is None:
        return projects

    # ユーザ×プロジェクトに存在しないプロジェクトを新規に追加する
    for project in projects_additional_group_permissions:
        project_dict = make_projects_dict_from_result(project)
        if not project_dict.get('id') in project_id_list:
            projects.append(project_dict)
    return projects

def get_flows_with_permission(project_id, user_id):
    """
    フロー一覧を権限付きで返す
    """
    flows = []
    flow_uuid_list = []

    # ユーザ権限がついたフローを取得する
    flows_additional_user_permissions = fetch_readable_flows_by_project_id_and_user_id(project_id, user_id)
    for flow in flows_additional_user_permissions:
        flow_uuid_list.append(flow.Flows.uuid)
        flows.append(make_projects_dict_from_flows_result(flow))

    # グループに所属しているか
    group = get_group_from_user_id(user_id)
    if group is None:
        return flows

    # グループ権限がついたフローを取得する
    flows_additional_group_permissions = fetch_readable_flows_by_project_id_and_group_id(project_id, group.id)
    if flows_additional_group_permissions is None:
        return flows

    # ユーザ×プロジェクトに存在しないフローを新規に追加する
    for flow in flows_additional_group_permissions:
        flow_dict = make_projects_dict_from_flows_result(flow)
        if not flow_dict.get('uuid') in flow_uuid_list:
            flows.append(flow_dict)

    return flows

def make_projects_dict_from_result(result):
    """
    指定したsqlalchemyのresultオブジェクトをdictに変換する
    """
    dict = {}
    for table_model in result:
        dict.update(
            { column.name : getattr(table_model, column.name) \
                           for column in table_model.__table__.columns }
        )
    return dict

def make_projects_dict_from_flows_result(result):
    """
    指定したsqlalchemyのflowsのresultオブジェクトをdictに変換する
    jsonは文字列で取得されるため、dictに変換している
    """
    dict = {}
    for table_model in result:
        dict.update(
            { column.name : json.loads(getattr(table_model, column.name)) if column.name == 'json' else getattr(table_model, column.name) \
                           for column in table_model.__table__.columns }
        )
    return dict
