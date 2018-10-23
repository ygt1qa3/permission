import uuid
import time
import hashlib
import pathlib
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
    update_user_email_by_old_email,
    get_projects_with_permission,
    get_flows_by_project_uuid,
    get_projects_creatable_by_user_id,
    create_project,
    delete_project_and_permission
    )
from .profile import (
    send_email_of_address_modification,
    update_password
)

TEST_USER1_ID = '1'
TEST_USER2_ID = '2'

email_sender = Mail(app)
CONFIRM_EMAIL = 'flask.mail.testtest@gmail.com'

@app.route('/')
def init():
    return redirect(url_for('fetch_projects'))

@app.route('/flows')
def flows():
    project_uuid = request.args.get('project')
    flows = get_flows_by_project_uuid(project_uuid)
    return render_template('flows.html', flows=flows)

@app.route('/projects', methods=['GET'])
def fetch_projects():
    if session.get('user_id') is None:
        session['user_id'] = 1
    user = get_user_by_id(session['user_id'])
    projects_creatable_permission = get_user_by_id(session['user_id']).projects_creatable
    projects = get_projects_with_permission(session['user_id'])
    return render_template('projects.html', projects=projects, create_permission=projects_creatable_permission, user=user)

@app.route('/projects', methods=['POST'])
def new_project():
    # 作成できるかチェック
    if not get_projects_creatable_by_user_id(session['user_id']):
        return redirect(url_for('fetch_projects'))

    # プロジェクト作成
    project_name = request.form['project_name']
    finished_create_projects = create_project(project_name, session['user_id'])

    return redirect(url_for('fetch_projects'))

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
        url = make_temporal_url_for_update_email(email, user.email)

        with email_sender.connect() as conn:
            send_email_of_address_modification(conn, user, email, url)

        user = get_user_by_id(user_id)
        return render_template('profile.html', user=user)

    elif request.form.get('current_password') and request.form.get('new_password'):
        success = update_password(session['user_id'], request.form.get('current_password'), request.form.get('new_password'))
        print(success)
        if success:
            # 本来はどこに飛ばそう？ログイン画面かな。
            return redirect(url_for('detail_users', user_id=session['user_id']))
        else:
            return redirect(url_for('detail_users', user_id=session['user_id']))

    print(request.form.get('current_password'), request.form.get('new_password'))

@app.route('/profile/update/<mail_hash>')
def register_email(mail_hash):
    """
    メールの確認ができたので、アドレスを更新して画面をかえす
    """
    path = pathlib.Path(app.root_path + '/profile/temp/' + mail_hash + '.activate')
    if not path.exists():
        redirect(url_for('fetch_projects'))

    with open(path.as_posix(), 'r') as f:
        profile = f.readlines()

    update_user_email_by_old_email(profile[0], profile[1])
    path.unlink()

    return redirect(url_for('fetch_projects'))

def make_temporal_url_for_update_email(new_email, old_email):
    """
    emailアドレス更新用のURLを作成する
    """
    hash_target = new_email + str(time.time())
    temp_path = hashlib.sha256(hash_target.encode()).hexdigest()
    url = f'{request.url_root}profile/update/{temp_path}'
    mail = [new_email, old_email]

    # 一時認証ファイルを作成する
    with open(app.root_path + '/profile/temp/' + temp_path + '.activate', 'a', encoding="utf-8") as f:
        f.write("\n".join(mail))

    return url
