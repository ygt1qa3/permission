from . import db
import uuid
# from sqlalchemy.dialects.postgresql import JSONB

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
    # リレーション
    projects_creatable = db.Column(db.Boolean)
    # グループにプロジェクト作成権限はいらないかも。
    # グループにはユーザ（DB上に存在する）が所属する。
    # また、ユーザにはプロジェクト作成に関する権限が設定されており、
    # ユーザの権限がグループの権限より優先されることから、グループに所属しているいないに関わらずユーザのプロジェクト作成権限が存在するのでそれが使われる。

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
    # カラム
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # flow_json = db.Column(JSONB)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    creator_id = db.Column(db.Integer)
    # リレーション

    def __init__(self, flow_json, project_id, creator_id):
        self.flow_json = flow_json
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
    updatable_flows = db.Column(db.Boolean, default=True)
    executable_flows = db.Column(db.Boolean, default=True)
    readable_flows = db.Column(db.Boolean, default=True)

    def __init__(self, user_id, project_id, deletable_project=True, creatable_flows=True,
                 deletable_flows=True, updatable_flows=True, executable_flows=True, readable_flows=True):
        self.user_id = user_id
        self.project_id = project_id
        self.deletable_project = deletable_project
        self.creatable_flows = creatable_flows
        self.deletable_flows = deletable_flows
        self.updatable_flows = updatable_flows
        self.executable_flows = executable_flows
        self.readable_flows = readable_flows

class GroupPermissionsProject(db.Model):
    """
    GroupPermissionsProjectモデル
    """
    __tablename__ = 'grouppermissions_project'
    __table_args__ = (
        db.PrimaryKeyConstraint('group_id', 'project_id'),
    )
    # カラム
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    deletable_project = db.Column(db.Boolean, default=False)
    creatable_flows = db.Column(db.Boolean, default=False)
    deletable_flows = db.Column(db.Boolean, default=False)
    updatable_flows = db.Column(db.Boolean, default=False)
    executable_flows = db.Column(db.Boolean, default=True)
    readable_flows = db.Column(db.Boolean, default=True)

    # グループの初期パーミッションをlinuxのディレクトリの初期パーミッションと同じにするなら、
    # linuxは初期umaskが022でグループのパーミッションは5(r-x)になるので、
    # できることは、プロジェクト配下の「フロー一覧が見える、フローデザイナが見える、フローが実行できる」となり
    # それ以外はFalseになる、とりあえずこの方向で。

    def __init__(self, group_id, project_id, deletable_project=False, creatable_flows=False,
                 deletable_flows=False, updatable_flows=False, executable_flows=True, readable_flows=True):
        self.group_id = group_id
        self.project_id = project_id
        self.deletable_project = deletable_project
        self.creatable_flows = creatable_flows
        self.deletable_flows = deletable_flows
        self.updatable_flows = updatable_flows
        self.executable_flows = executable_flows
        self.readable_flows = readable_flows

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

def update_user_email_by_old_email(new_email, old_email):
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
        grouppermission_project = GroupPermissionsProject(user.group_id, project.id)
        db.session.add(grouppermission_project)

    # コミット
    db.session.commit()

def grant_user_to_project(user_id, project_id, deletable_project=True, creatable_flows=True,
                               deletable_flows=True, updatable_flows=True, executable_flows=True, readable_flows=True):
    """
    指定したユーザとプロジェクトに対する権限を新規作成する
    """
    userpermission_project = UserPermissions_Project(user_id, project_id,
                                                    deletable_project,
                                                    creatable_flows, deletable_flows, updatable_flows, executable_flows, readable_flows)
    db.session.add(userpermission_project)
    db.session.commit()

def get_readable_projects_by_user_id(user_id):
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
    db.session.query(GroupPermissionsProject).filter_by(project_id=project.id).delete()
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

def get_readable_projects_by_group_id(group_id):
    """
    指定したグループが閲覧できるプロジェクト一覧を取得する
    """
    projects = db.session.query(Projects, GroupPermissionsProject) \
                                .join(GroupPermissionsProject, Projects.id==GroupPermissionsProject.project_id) \
                                .filter(GroupPermissionsProject.group_id==group_id)
    return projects

def grant_group_to_project(group_id, project_id, deletable_project=False, creatable_flows=False,
                                deletable_flows=False, updatable_flows=False, executable_flows=True, readable_flows=True):
    """
    指定したグループとプロジェクトに対する権限を新規作成する
    """
    grouppermission_project = GroupPermissionsProject(group_id, project_id,
                                                      deletable_project,
                                                      creatable_flows, deletable_flows, updatable_flows, executable_flows, readable_flows)
    db.session.add(grouppermission_project)
    db.session.commit()

def get_grouppermissions_project(group_id, project_id):
    """
    指定したグループ×プロジェクトを返す
    """
    userproject = db.session.query(GroupPermissionsProject).filter_by(project_id=project_id, group_id=group_id).first()
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
    GroupPermissionsProjectとProjectsを結合したもの
    2つの結果を基に作成している

    ユーザのパーミッションの方が優先なので、
    まずUserPermissions_ProjectとProjectsを結合したものを、返すリストに設定し
    GroupPermissionsProjectにのみ設定されているプロジェクト情報を
    返すリストに付け足している
    """
    projects = []
    project_id_list = []

    # ユーザ権限がついたプロジェクトを取得する
    projects_additional_user_permissions = get_readable_projects_by_user_id(user_id)
    for project in projects_additional_user_permissions:
        project_id_list.append(project.Projects.id)
        projects.append(make_projects_dict_from_result(project))

    # グループに所属しているか
    group = get_group_from_user_id(user_id)
    if group is None:
        return projects

    # グループ権限がついたプロジェクトを取得する
    projects_additional_group_permissions = get_readable_projects_by_group_id(group.id)
    if projects_additional_group_permissions is None:
        return projects

    # ユーザ×プロジェクトに存在しないプロジェクトを新規に追加する
    for project in projects_additional_group_permissions:
        project_dict = make_projects_dict_from_result(project)
        if not project_dict.get('id') in project_id_list:
            projects.append(project_dict)

    return projects

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

def get_flows_by_project_uuid(project_uuid):
    pass
