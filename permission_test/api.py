import uuid
from flask import Flask, render_template, url_for, redirect, request, session
from . import app
from .models import (
    Users,
    Projects,
    UserProjects,
    Flows,
    db,
    select_user_by_id,
    get_readable_projects_by_user_id,
    select_flows_by_project_uuid,
    check_can_create_projects,
    create_project,
    delete_project_by_uuid
    )

TEST_USER1_ID = 1
TEST_USER2_ID = 2

@app.route('/')
def init():
    return redirect(url_for('fetch_projects'))

@app.route('/flows')
def flows():
    project_uuid = request.args.get('project')
    flows = select_flows_by_project_uuid(project_uuid)
    return render_template('flows.html', flows=flows)

@app.route('/projects', methods=['GET'])
def fetch_projects():
    if session.get('user_id') is None:
        session['user_id'] = 1
    user = select_user_by_id(session['user_id'])
    projects_create_permission = select_user_by_id(session['user_id']).projects_create
    projects = get_readable_projects_by_user_id(session['user_id'])
    return render_template('projects.html', projects=projects, create_permission=projects_create_permission, user=user)

@app.route('/projects', methods=['POST'])
def new_project():
    # 作成できるかチェック
    if not check_can_create_projects(session['user_id']):
        return redirect(url_for('fetch_projects'))

    # プロジェクト作成
    project_name = request.form['project_name']
    finished_create_projects = create_project(project_name, session['user_id'])

    return redirect(url_for('fetch_projects'))

@app.route('/project/<project_uuid>', methods=['POST'])
def delete_project(project_uuid):
    delete_project_by_uuid(project_uuid)
    return redirect(url_for('fetch_projects'))

@app.route('/user/<user_id>', methods=['POST'])
def change_users(user_id):
    if user_id == '1':
        session['user_id'] = TEST_USER1_ID
    else:
        session['user_id'] = TEST_USER2_ID
    return redirect(url_for('fetch_projects'))

if __name__ == '__main__':
    app.run()
