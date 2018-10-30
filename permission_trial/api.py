import uuid
import time
import hashlib
import pathlib
import json
from flask import Flask, render_template, url_for, redirect, request, session, flash
from flask_mail import Mail, Message
from . import app
from .models import (
    Users,
    Projects,
    UserPermissions_Project,
    Flows,
    db,
    get_user_by_id,
    replace_user_email_with_old_email,
    get_projects_with_permission,
    get_projects_creatable_by_user_id,
    create_project,
    delete_project_and_permission,
    get_flows_with_permission,
    get_permissions_project,
    create_flow,
    make_projects_dict_from_result
    )
from .profile import (
    notify_change_of_email,
    update_password
)

TEST_USER1_ID = '1'
TEST_USER2_ID = '2'

email_sender = Mail(app)
CONFIRM_EMAIL = 'flask.mail.testtest@gmail.com'

@app.route('/')
def init():
    return redirect(url_for('fetch_projects'))

@app.route('/projects', methods=['GET'])
def fetch_projects():
    if session.get('user_id') is None:
        session['user_id'] = 1
    user = get_user_by_id(session['user_id'])
    projects_creatable_permission = get_user_by_id(session['user_id']).projects_creatable
    projects = get_projects_with_permission(session['user_id'])
    return render_template('projects.html', projects=projects, create_permission=projects_creatable_permission, user=user)
    
@app.route('/flows', methods=['GET'])
def fetch_flows():
    user = get_user_by_id(session['user_id'])
    # プロジェクトのパーミッション取得（フロー作成、削除権限の取得）
    project_permission = make_projects_dict_from_result([get_permissions_project(session['user_id'], request.args.get('project'))])
    project = db.session.query(Projects).filter_by(uuid=request.args.get('project')).first()
    flows = get_flows_with_permission(project.id, session['user_id'])
    return render_template('flows.html', flows=flows, flows_Edit_permission=project_permission, user=user)

@app.route('/projects', methods=['POST'])
def new_project():
    # 作成できるかチェック
    if not get_projects_creatable_by_user_id(session['user_id']):
        return redirect(url_for('fetch_projects'))

    # プロジェクト作成
    project_name = request.form['project_name']
    finished_create_projects = create_project(project_name, session['user_id'])

    return redirect(url_for('fetch_projects'))

@app.route('/flows', methods=['POST'])
def new_flow():
    # 作成できるかチェック

    # プロジェクト作成
    flow_name = request.form['flow_name']
    project = db.session.query(Projects).filter_by(uuid=request.form['project_uuid']).first()
    finished_create_projects = create_flow(flow_name, get_user_by_id(session['user_id']), project)

    return redirect(url_for('fetch_flows', project=request.form['project_uuid']))

@app.route('/project/<project_uuid>', methods=['POST'])
def delete_project(project_uuid):
    deleted_status = delete_project_and_permission(session['user_id'], project_uuid)
    return redirect(url_for('fetch_projects', deleted_status=deleted_status))

@app.route('/user/<user_id>', methods=['POST'])
def change_users(user_id):
    if user_id == TEST_USER1_ID:
        session['user_id'] = TEST_USER1_ID
    else:
        session['user_id'] = TEST_USER2_ID
    return redirect(url_for('fetch_projects'))

@app.route('/profile/<user_id>', methods=['GET'])
def detail_users(user_id):
    """
    自分のプロフィール情報を表示する
    """
    if session['user_id'] != user_id:
        # 自分以外のプロフィールへのアクセスは禁止する（URL直接たたくなど）
        return redirect(url_for('fetch_projects'))

    user = get_user_by_id(user_id)
    return render_template('profile.html', user=user)

@app.route('/profile/<user_id>', methods=['POST'])
def update_user_profile(user_id):
    """
    自分のプロフィール情報を変更する
    """
    if request.form.get('email'):
        # 新メールアドレスに確認のメールを送る
        email = request.form.get('email')
        user = get_user_by_id(user_id)
        old_email = user.email
        url = make_temporal_url_for_updating_email(email, user.email)

        with email_sender.connect() as conn:
            notify_change_of_email(conn, user, email, url)

        user = get_user_by_id(user_id)
        return render_template('profile.html', user=user)

    elif request.form.get('current_password') and request.form.get('new_password'):
        success = update_password(session['user_id'], request.form.get('current_password'), request.form.get('new_password'))
        if success:
            # 本来はどこに飛ばそう？ログイン画面かな。
            return redirect(url_for('detail_users', user_id=session['user_id']))
        else:
            return redirect(url_for('detail_users', user_id=session['user_id']))

    print(request.form.get('current_password'), request.form.get('new_password'))

@app.route('/profile/update/<mail_hash>')
def change_email(mail_hash):
    """
    メールの確認ができたので、アドレスを更新して画面をかえす
    """

    # ハッシュ値は不可逆なので、元々のアドレスを取得できない
    # なので、ハッシュ値をファイル名とした一時ファイルを作成し、そこに旧アドレス新アドレスを記載しておく
    path = make_path_of_auth_by_mail_hash(mail_hash)
    if not path.exists():
        redirect(url_for('fetch_projects'))

    with open(path.as_posix(), 'r') as f:
        profile = f.readlines()

    replace_user_email_with_old_email(profile[0], profile[1])
    path.unlink()

    return redirect(url_for('fetch_projects'))

def make_temporal_url_for_updating_email(new_email, old_email):
    """
    emailアドレス更新用のURLを作成する
    """
    hash_target = new_email + str(time.time())
    temp_path = hashlib.sha256(hash_target.encode()).hexdigest()
    url = f'{request.url_root}profile/update/{temp_path}'
    mail = [new_email, old_email]

    # 一時認証ファイルを作成する
    with open(make_path_of_auth_by_mail_hash(temp_path), 'a', encoding="utf-8") as f:
        f.write("\n".join(mail))

    return url

def make_path_of_auth_by_mail_hash(mail_hash):
    """
    一時認証ファイルのパスを作成する
    """
    path = pathlib.Path(app.root_path + '/profile/temp/' + mail_hash + '.activate')
    return path
