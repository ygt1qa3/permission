import uuid
from flask import Flask, render_template, url_for, redirect, request, session
from . import app
from .models import (
    Users,
    Projects,
    UserPermissionsProject,
    Flows,
    db,
    get_user_by_id,
    get_projects_add_permission,
    get_flows_by_project_uuid,
    get_creatable_projects_by_user_id,
    create_project,
    delete_project_and_permission
    )

TEST_USER1_ID = '1'
TEST_USER2_ID = '2'

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
    creatable_projects_permission = get_user_by_id(session['user_id']).creatable_projects
    projects = get_projects_add_permission(session['user_id'])
    return render_template('projects.html', projects=projects, create_permission=creatable_projects_permission, user=user)

@app.route('/projects', methods=['POST'])
def new_project():
    # 作成できるかチェック
    if not get_creatable_projects_by_user_id(session['user_id']):
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
