import unittest
import uuid
import distutils.util
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from permission_trial import app
import permission_trial.models as models
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = models.db

class ModelTestCase(unittest.TestCase):
    def setUp(self):
        db.create_all()
        db.session.commit()

    def tearDown(self):
        db.drop_all()
        db.session.commit()

    def test_create_user(self):
        """
        ユーザ作成のテスト
        """
        # ユーザ作成
        email = 'dev@kskp.io'
        models.create_user('ユーザ１', email, '')
        user = db.session.query(models.Users).filter_by(email=email).first()

        self.assertEqual(user.name, 'ユーザ１')
        self.assertEqual(user.email, email)
        self.assertEqual(user.group_id, None)
        self.assertEqual(user.creatable_projects, True)

    def test_get_readable_projects_by_user(self):
        """
        自分が見ることができるプロジェクトの取得テスト
        ユーザ単体
        """
        # 作成するプロジェクト情報
        project_name_1 = 'ユーザ１用プロジェクト'
        project_name_2 = 'ユーザ２用プロジェクト'
        project_name_3 = '共用プロジェクト'

        # ユーザ作成
        email1 = 'user1@kskp.io'
        models.create_user('ユーザ１', email1, '')
        user1 = db.session.query(models.Users).filter_by(email=email1).first()

        email2 = 'user2@kskp.io'
        models.create_user('ユーザ２', email2, '')
        user2 = db.session.query(models.Users).filter_by(email=email2).first()

        # ユーザ１がユーザ１用プロジェクトを作成
        models.create_project(project_name_1, user1.id)
        # ユーザ２がユーザ２用プロジェクトを作成
        models.create_project(project_name_2, user2.id)
        # 共用プロジェクトを作成
        models.create_project(project_name_3, user1.id)
        all_projects = models.get_all_projects()
        db.session.add(models.UserPermissionsProject(user2.id, all_projects[2].id))
        db.session.commit()

        # 自分が見れるプロジェクトが取得できているかテスト
        projects_for_user1 = models.get_readable_projects_by_user_id(user1.id)
        self.assertEqual(projects_for_user1.count(), 2)
        self.assertEqual(projects_for_user1[0].Projects.name, project_name_1)
        self.assertEqual(projects_for_user1[1].Projects.name, project_name_3)

        projects_for_user2 = models.get_readable_projects_by_user_id(user2.id)
        self.assertEqual(projects_for_user2.count(), 2)
        self.assertEqual(projects_for_user2[0].Projects.name, project_name_2)
        self.assertEqual(projects_for_user2[1].Projects.name, project_name_3)

    def test_creatable_projects_by_user(self):
        """
        ユーザがプロジェクト作成権限を持っているかどうかの判定のテスト（作成権限を持っている）
        """
        # ユーザ作成
        email1 = 'user1@kskp.io'
        models.create_user('ユーザ１', email1, '')
        user1 = db.session.query(models.Users).filter_by(email=email1).first()

        # テスト
        can_create_projects = models.get_creatable_projects_by_user_id(user1.id)
        self.assertEqual(can_create_projects, True)

    def test_not_creatable_projects(self):
        """
        ユーザがプロジェクト作成権限を持っているかどうかの判定のテスト（作成権限を持たない）
        """
        # ユーザ作成
        email1 = 'user1@kskp.io'
        models.create_user('ユーザ１', email1, '')
        user1 = db.session.query(models.Users).filter_by(email=email1).first()

        # ユーザのプロジェクト作成権限を変更する
        user1.creatable_projects = False
        db.session.add(user1)
        db.session.commit()

        # テスト
        can_create_projects = models.get_creatable_projects_by_user_id(user1.id)
        self.assertEqual(can_create_projects, False)

    def test_create_group(self):
        """
        グループを作成するテスト
        """
        # 作成するグループ
        group_name = "テストグループ"
        models.create_group(group_name)
        group = db.session.query(models.Groups).all()

        self.assertEqual(group[0].name, group_name)
        self.assertEqual(group[0].creatable_projects, True)

    def test_delete_group(self):
        """
        グループを削除するテスト
        """
        # グループの作成
        group_name = "テストグループ"
        models.create_group(group_name)

        before_group_count = db.session.query(models.Groups).count()
        self.assertEqual(before_group_count, 1)

        # グループの取得と削除
        group = models.get_group_by_id(1)
        models.delete_group_by_id(group.id)

        after_group_count = db.session.query(models.Groups).count()
        self.assertEqual(after_group_count, 0)

    def test_add_user_to_group(self):
        """
        グループにユーザを追加するテスト
        """
        # ユーザの作成
        email = 'dev@kskp.io'
        models.create_user('ユーザ１', email, '')
        before_user = db.session.query(models.Users).filter_by(email=email).first()

        # グループの作成
        group_name = "テストグループ"
        models.create_group(group_name)
        group = db.session.query(models.Groups).all()[0]

        # 所属させてもう一度ユーザを取得
        models.assign_user_to_group(before_user.id, group.id)
        after_user = db.session.query(models.Users).filter_by(email=email).first()

        self.assertEqual(after_user.group_id, group.id)

    def test_add_user_to_group(self):
        """
        ユーザの所属しているグループを取得するテスト
        """
        # ユーザの作成
        email = 'dev@kskp.io'
        models.create_user('ユーザ１', email, '')
        before_user = db.session.query(models.Users).filter_by(email=email).first()

        # グループの作成
        group_name = "テストグループ"
        models.create_group(group_name)
        group = db.session.query(models.Groups).all()[0]

        # グループに所属させる
        models.assign_user_to_group(before_user.id, group.id)

        assigned_group = models.get_group_from_user_id(before_user.id)

        self.assertEqual(assigned_group.id, group.id)
        self.assertEqual(assigned_group.name, group_name)

    def test_get_readable_projects_by_group(self):
        """
        グループが見ることができるプロジェクトの取得テスト
        グループ単体
        """
        # 作成するプロジェクト情報
        project_name_1 = 'ユーザ１用プロジェクト'
        project_name_2 = 'ユーザ２用プロジェクト'
        project_name_3 = '共用プロジェクト'

        # プロジェクト作成用ユーザ作成
        email = 'create@kskp.io'
        models.create_user('プロジェクト作成用', email, '')
        user = db.session.query(models.Users).filter_by(email=email).first()

        # プロジェクトの作成
        models.create_project(project_name_1, user.id)
        models.create_project(project_name_2, user.id)
        models.create_project(project_name_3, user.id)

        projects = models.get_all_projects()

        # グループの作成
        group_name1 = "テストグループ１"
        models.create_group(group_name1)
        group_name2 = "テストグループ２"
        models.create_group(group_name2)

        group1 = db.session.query(models.Groups).all()[0]
        group2 = db.session.query(models.Groups).all()[1]

        # グループ1にプロジェクト1,3を割り当てる
        models.commission_group_to_project(group1.id, projects[0].id)
        models.commission_group_to_project(group1.id, projects[2].id)

        # グループ2にプロジェクト2,3を割り当てる
        models.commission_group_to_project(group2.id, projects[1].id)
        models.commission_group_to_project(group2.id, projects[2].id)

        # それぞれのグループが見れるプロジェクトが取得できているかテスト
        projects_for_group1 = models.get_readable_projects_by_group_id(group1.id)
        self.assertEqual(projects_for_group1.count(), 2)
        self.assertEqual(projects_for_group1[0].Projects.name, project_name_1)
        self.assertEqual(projects_for_group1[1].Projects.name, project_name_3)

        projects_for_group2 = models.get_readable_projects_by_group_id(group2.id)
        self.assertEqual(projects_for_group2.count(), 2)
        self.assertEqual(projects_for_group2[0].Projects.name, project_name_2)
        self.assertEqual(projects_for_group2[1].Projects.name, project_name_3)

    def test_create_project_belong_to_group(self):
        """
        プロジェクトの作成のテスト（ユーザはグループに所属している）
        必要なデータが作成されているかに対するテスト
        ・プロジェクト
        ・ユーザ×プロジェクト
        ・グループ×プロジェクト
        """
        # 作成するプロジェクト情報
        project_name = '開発用'

        # ユーザ作成
        email = 'dev@kskp.io'
        models.create_user('ユーザ１', email, '')
        user = db.session.query(models.Users).filter_by(email=email).first()

        # グループの作成
        group_name = "テストグループ"
        models.create_group(group_name)
        group = db.session.query(models.Groups).all()[0]

        # ユーザをグループに所属させる
        models.assign_user_to_group(user.id, group.id)

        # プロジェクト作成
        models.create_project(project_name, user.id)

        # プロジェクトが作成されているかテスト
        projects = models.get_readable_projects_by_user_id(user.id)
        self.assertEqual(projects.count(), 1)
        self.assertEqual(projects[0].Projects.name, project_name)
        self.assertEqual(projects[0].Projects.creator_id, user.id)

        # ユーザ×プロジェクトが作成されているかテスト
        userpermission_projects = db.session.query(models.UserPermissionsProject).filter_by(project_id=projects[0].Projects.id, user_id=user.id)
        self.assertEqual(userpermission_projects.count(), 1)
        self.assertEqual(userpermission_projects[0].user_id, user.id)
        self.assertEqual(userpermission_projects[0].project_id, projects[0].Projects.id)

        # グループ×プロジェクトが作成されていることの確認テスト
        grouppermission_projects = db.session.query(models.GroupPermissionsProject).filter_by(project_id=projects[0].Projects.id, group_id=group.id)
        self.assertEqual(grouppermission_projects.count(), 1)
        self.assertEqual(grouppermission_projects[0].group_id, group.id)
        self.assertEqual(grouppermission_projects[0].project_id, projects[0].Projects.id)

    def test_delete_project_not_belong_to_group(self):
        """
        プロジェクト削除のテスト（ユーザはグループに所属している）
        必要なデータが削除されているかのテスト
        ・プロジェクト
        ・対象プロジェクトのユーザ×プロジェクト
        ・対象プロジェクトのグループ×プロジェクト
        """
        # 作成するプロジェクト情報
        project_name = '開発用'

        # ユーザ作成
        email = 'dev@kskp.io'
        models.create_user('ユーザ１', email, '')
        user = db.session.query(models.Users).filter_by(email=email).first()

        # グループの作成
        group_name = "テストグループ"
        models.create_group(group_name)
        group = db.session.query(models.Groups).all()[0]

        # ユーザをグループに所属させる
        models.assign_user_to_group(user.id, group.id)

        # プロジェクト作成
        models.create_project(project_name, user.id)

        # プロジェクトを削除
        before_projects = models.get_readable_projects_by_user_id(user.id)
        before_projects_id = before_projects[0].id
        models.delete_project_by_uuid(before_projects[0].uuid)

        # プロジェクトが削除されているか
        after_projects = models.get_readable_projects_by_user_id(user.id)
        self.assertEqual(after_projects.count(), 0)

        # ユーザ×プロジェクトにおいて、削除したプロジェクトのデータが削除されているか？
        userpermission_projects = db.session.query(models.UserPermissionsProject).filter_by(project_id=before_projects_id, user_id=user.id)
        self.assertEqual(userpermission_projects.count(), 0)

        # グループ×プロジェクトにおいて、削除したプロジェクトのデータが削除されているか？
        grouppermission_projects = db.session.query(models.GroupPermissionsProject).filter_by(project_id=before_projects_id, group_id=group.id)
        self.assertEqual(grouppermission_projects.count(), 0)

    def test_create_project_not_belong_to_group(self):
        """
        プロジェクトの作成のテスト（ユーザはグループに所属していない）
        必要なデータが作成されているかに対するテスト
        ・プロジェクト
        ・ユーザ×プロジェクト
        """
        # 作成するプロジェクト情報
        project_name = '開発用'

        # ユーザ作成
        email = 'dev@kskp.io'
        models.create_user('ユーザ１', email, '')
        user = db.session.query(models.Users).filter_by(email=email).first()

        # プロジェクト作成
        models.create_project(project_name, user.id)

        # プロジェクトが作成されているかテスト
        projects = models.get_readable_projects_by_user_id(user.id)
        self.assertEqual(projects.count(), 1)
        self.assertEqual(projects[0].Projects.name, project_name)
        self.assertEqual(projects[0].Projects.creator_id, user.id)

        # ユーザ×プロジェクトが作成されているかテスト
        userpermission_projects = db.session.query(models.UserPermissionsProject).filter_by(project_id=projects[0].Projects.id, user_id=user.id)
        self.assertEqual(userpermission_projects.count(), 1)
        self.assertEqual(userpermission_projects[0].user_id, user.id)
        self.assertEqual(userpermission_projects[0].project_id, 1)

        # グループ×プロジェクトが作成されていないことの確認テスト
        grouppermission_projects = db.session.query(models.GroupPermissionsProject).filter_by(project_id=projects[0].Projects.id)
        self.assertEqual(grouppermission_projects.count(), 0)

    def test_delete_project_not_belong_to_group(self):
        """
        プロジェクト削除のテスト（ユーザはグループに所属していない）
        必要なデータが削除されているかのテスト
        ・プロジェクト
        ・対象プロジェクトのユーザ×プロジェクト
        """
        # 作成するプロジェクト情報
        project_name = '開発用'

        # ユーザ作成
        email = 'dev@kskp.io'
        models.create_user('ユーザ１', email, '')
        user = db.session.query(models.Users).filter_by(email=email).first()

        # プロジェクト作成
        models.create_project(project_name, user.id)

        # プロジェクトを削除
        before_projects = models.get_readable_projects_by_user_id(user.id)
        before_projects_id = before_projects[0].Projects.id
        models.delete_project_by_uuid(before_projects[0].Projects.uuid)

        # プロジェクトが削除されているか
        after_projects = models.get_readable_projects_by_user_id(user.id)
        self.assertEqual(after_projects.count(), 0)

        # ユーザ×プロジェクトにおいて、削除したプロジェクトのデータが削除されているか？
        userpermission_projects = db.session.query(models.UserPermissionsProject).filter_by(project_id=before_projects_id, user_id=user.id)
        self.assertEqual(userpermission_projects.count(), 0)

    def test_delete_project_1(self):
        """
        プロジェクトを削除するテスト
        パーミッションを意識したもの

        ユーザ×プロジェクト・・・・存在しない
        グループ×プロジェクト・・・削除権限あり

        グループの権限が存在するため削除される
        """
        # プロジェクト作成用ユーザ作成
        email_1 = 'createproject@kskp.io'
        models.create_user('プロジェクト作成用ユーザ', email_1, '')
        create_project_user = db.session.query(models.Users).filter_by(email=email_1).first()

        # グループの作成
        group_name = "テストグループ"
        models.create_group(group_name)
        group = db.session.query(models.Groups).all()[0]

        # プロジェクト作成用ユーザをグループに所属させる
        models.assign_user_to_group(create_project_user.id, group.id)

        # 作成するプロジェクト情報
        project_name = '開発用'
        # プロジェクトの作成
        models.create_project(project_name, create_project_user.id)

        # グループ×プロジェクトの権限変更（削除できるように）
        projects = models.get_readable_projects_by_user_id(create_project_user.id)
        grouppermission_project = models.get_grouppermissions_project(group.id, projects[0].Projects.id)
        grouppermission_project.deletable_project = True
        db.session.add(grouppermission_project)
        db.session.commit()

        # ユーザの作成
        email = 'dev@kskp.io'
        models.create_user('ユーザ１', email, '')
        user = db.session.query(models.Users).filter_by(email=email).first()

        # ユーザを作成したグループに所属させる
        models.assign_user_to_group(user.id, group.id)

        # ユーザ×プロジェクトが存在しないことの確認
        userpermission_project = models.get_userpermissions_project(user.id, projects[0].Projects.id)
        self.assertIsNone(userpermission_project)

        # プロジェクトの削除
        delete_project_and_permission = models.delete_project_and_permission(user.id, projects[0].Projects.uuid)

        # テスト
        self.assertEqual(delete_project_and_permission, True)
        # プロジェクトが削除されていることの確認
        projects = models.get_readable_projects_by_user_id(create_project_user.id)
        self.assertEqual(projects.count(), 0)

    def test_delete_project_2(self):
        """
        プロジェクトを削除するテスト
        パーミッションを意識したもの

        ユーザ×プロジェクト・・・・削除権限あり
        グループ×プロジェクト・・・削除権限なし

        ユーザの権限が優先されるため削除される
        """
        # プロジェクト作成用ユーザ作成
        email = 'dev@kskp.io'
        models.create_user('ユーザ１', email, '')
        user = db.session.query(models.Users).filter_by(email=email).first()

        # グループの作成
        group_name = "テストグループ"
        models.create_group(group_name)
        group = db.session.query(models.Groups).all()[0]

        # プロジェクト作成用ユーザをグループに所属させる
        models.assign_user_to_group(user.id, group.id)

        # 作成するプロジェクト情報
        project_name = '開発用'
        # プロジェクトの作成
        # デフォルトがユーザ権限はプロジェクトを削除できる、グループ権限は削除できない
        models.create_project(project_name, user.id)
        projects = models.get_readable_projects_by_user_id(user.id)

        # プロジェクトの削除
        delete_project_and_permission = models.delete_project_and_permission(user.id, projects[0].Projects.uuid)

        # テスト
        self.assertEqual(delete_project_and_permission, True)
        # プロジェクトが削除されていることの確認
        projects = models.get_readable_projects_by_user_id(user.id)
        self.assertEqual(projects.count(), 0)

    def test_get_projects_1(self):
        """
        プロジェクト一覧を正しい権限をつけて返す

        グループ：プロジェクトの削除権限なし

        プロジェクト１：
            ユーザ×プロジェクト・・・・存在しない
            グループ×プロジェクト・・・削除権限なし

        プロジェクト２：
            ユーザ×プロジェクト・・・・削除権限あり
            グループ×プロジェクト・・・削除権限なし

        プロジェクト３：
            ユーザ×プロジェクト・・・・削除権限なし
            グループ×プロジェクト・・・削除権限なし

        プロジェクト１はグループが権限を持っているので一覧に取得できるが、削除はできない
        プロジェクト２はユーザ権限があるので、削除できる

        削除できるプロジェクトは２のみ
        """
        # プロジェクト作成用ユーザ作成
        email_p = 'createproject@kskp.io'
        models.create_user('プロジェクト作成用ユーザ', email_p, '')
        create_project_user = db.session.query(models.Users).filter_by(email=email_p).first()

        # グループの作成
        group_name = "テストグループ"
        models.create_group(group_name)
        group = db.session.query(models.Groups).all()[0]

        # 所属させる
        models.assign_user_to_group(create_project_user.id, group.id)

        # プロジェクトの作成
        project_name1 = '開発用1'
        project_name2 = '開発用2'
        project_name3 = '開発用3'

        models.create_project(project_name1, create_project_user.id)
        models.create_project(project_name2, create_project_user.id)
        models.create_project(project_name3, create_project_user.id)

        projects = models.get_readable_projects_by_user_id(create_project_user.id)

        # ユーザ１の作成
        email = 'dev@kskp.io'
        models.create_user('ユーザ１', email, '')
        user = db.session.query(models.Users).filter_by(email=email).first()
        # 所属させる
        models.assign_user_to_group(user.id, group.id)

        # パーミッションの設定
        # プロジェクト１は特になし

        # プロジェクト２
        # ユーザ１用のユーザ×プロジェクトを作成
        userpermission_project2 = models.UserPermissionsProject(user.id, projects[1].Projects.id)
        db.session.add(userpermission_project2)
        db.session.commit()

        # プロジェクト３
        # ユーザ１用のユーザ×プロジェクトを作成、プロジェクト削除権限をFalseにする（デフォルトがTrueなので）
        models.commission_user_to_project(user.id, projects[2].Projects.id, deletable_project=False)

        # 答え合わせ用のプロジェクトの取得
        result_projects = models.get_projects_add_permission(user.id)
        project1 = [project for project in result_projects if project['id'] == 1][0]
        project2 = [project for project in result_projects if project['id'] == 2][0]
        project3 = [project for project in result_projects if project['id'] == 3][0]

        # テスト
        self.assertEqual(len(result_projects), 3)
        self.assertEqual(project1['name'], project_name1)
        self.assertEqual(project1['deletable_project'], False)
        self.assertEqual(project2['name'], project_name2)
        self.assertEqual(project2['deletable_project'], True)
        self.assertEqual(project3['name'], project_name3)
        self.assertEqual(project3['deletable_project'], False)


        # 画面の制御を無視して、直接プロジェクトを削除してみる
        # 何かの間違いで、ユーザ１が削除できないはずのプロジェクト１を削除してみる（削除されないはず）
        delete_project_and_permission = models.delete_project_and_permission(user.id, project1['uuid'])
        self.assertEqual(delete_project_and_permission, False)

        # プロジェクト２を削除してみる（削除できる）
        delete_project_and_permission = models.delete_project_and_permission(user.id, project2['uuid'])
        self.assertEqual(delete_project_and_permission, True)

        # 何かの間違いで、ユーザ１が削除できないはずのプロジェクト３を削除してみる（削除されないはず）
        delete_project_and_permission = models.delete_project_and_permission(user.id, project3['uuid'])
        self.assertEqual(delete_project_and_permission, False)

        # 削除後のプロジェクト数を確認する（プロジェクト２が削除されているので、2つになるはず）
        after_readable_projects = models.get_projects_add_permission(user.id)
        self.assertEqual(len(after_readable_projects), 2)

    def test_get_projects_2(self):
        """
        プロジェクト一覧を正しい権限をつけて返す

        グループ：プロジェクトの削除権限あり

        プロジェクト１：
            ユーザ×プロジェクト・・・・存在しない
            グループ×プロジェクト・・・削除権限あり

        プロジェクト２：
            ユーザ×プロジェクト・・・・削除権限あり
            グループ×プロジェクト・・・削除権限あり

        プロジェクト３：
            ユーザ×プロジェクト・・・・削除権限なし
            グループ×プロジェクト・・・削除権限あり

        プロジェクト１はグループが権限を持っているので一覧に取得できる
        プロジェクト３はユーザ権限があるので、削除できない

        削除できるプロジェクトは１、２
        """
        # プロジェクト作成用ユーザ作成
        email_p = 'createproject@kskp.io'
        models.create_user('プロジェクト作成用ユーザ', email_p, '')
        create_project_user = db.session.query(models.Users).filter_by(email=email_p).first()

        # グループの作成
        group_name = "テストグループ"
        models.create_group(group_name)
        group = db.session.query(models.Groups).all()[0]

        # グループに所属させる
        models.assign_user_to_group(create_project_user.id, group.id)

        # プロジェクトの作成
        project_name1 = '開発用1'
        project_name2 = '開発用2'
        project_name3 = '開発用3'

        models.create_project(project_name1, create_project_user.id)
        models.create_project(project_name2, create_project_user.id)
        models.create_project(project_name3, create_project_user.id)

        projects = models.get_readable_projects_by_user_id(create_project_user.id)

        # ユーザ１の作成
        email = 'dev@kskp.io'
        models.create_user('ユーザ１', email, '')
        user = db.session.query(models.Users).filter_by(email=email).first()
        # グループに所属させる
        models.assign_user_to_group(user.id, group.id)

        # パーミッションの設定
        # プロジェクト１
        # グループ権限を変更する
        grouppermission_project1 = models.get_grouppermissions_project(group.id, projects[0].Projects.id)
        grouppermission_project1.deletable_project = True
        db.session.add(grouppermission_project1)

        # プロジェクト２
        # ユーザ１用のユーザ×プロジェクトを作成
        models.commission_user_to_project(user.id, projects[1].Projects.id)
        # グループのプロジェクト削除のパーミッションをTrueに設定する（デフォルトがFalseなので）
        grouppermission_project2 = models.get_grouppermissions_project(group.id, projects[1].Projects.id)
        grouppermission_project2.deletable_project = True
        db.session.add(grouppermission_project2)

        # プロジェクト３
        # ユーザ１用のユーザ×プロジェクトを作成、プロジェクト削除のパーミッションをFalseにする（デフォルトがTrueなので）
        models.commission_user_to_project(user.id, projects[2].Projects.id, deletable_project=False)
        # グループのプロジェクト削除のパーミッションをTrueに設定する（デフォルトがFalseなので）
        grouppermission_project3 = models.get_grouppermissions_project(group.id, projects[2].Projects.id)
        grouppermission_project3.deletable_project = True
        db.session.add(grouppermission_project3)
        # コミット
        db.session.commit()

        # プロジェクト一覧の取得
        result_projects = models.get_projects_add_permission(user.id)
        project1 = [project for project in result_projects if project['id'] == 1][0]
        project2 = [project for project in result_projects if project['id'] == 2][0]
        project3 = [project for project in result_projects if project['id'] == 3][0]

        # テスト
        self.assertEqual(len(result_projects), 3)
        self.assertEqual(project1['name'], project_name1)
        self.assertEqual(project1['deletable_project'], True)
        self.assertEqual(project2['name'], project_name2)
        self.assertEqual(project2['deletable_project'], True)
        self.assertEqual(project3['name'], project_name3)
        self.assertEqual(project3['deletable_project'], False)


        # 画面の制御を無視して、直接プロジェクトを削除してみる
        # プロジェクト１を削除してみる（削除できる）
        delete_project_and_permission = models.delete_project_and_permission(user.id, project1['uuid'])
        self.assertEqual(delete_project_and_permission, True)

        # プロジェクト２を削除してみる（削除できる）
        delete_project_and_permission = models.delete_project_and_permission(user.id, project2['uuid'])
        self.assertEqual(delete_project_and_permission, True)

        # 何かの間違いで、ユーザ１が削除できないはずのプロジェクト３を削除してみる（削除されないはず）
        delete_project_and_permission = models.delete_project_and_permission(user.id, project3['uuid'])
        self.assertEqual(delete_project_and_permission, False)

        # 削除後のプロジェクト数を確認する（プロジェクト１と２が削除されているので、１つになるはず）
        after_readable_projects = models.get_projects_add_permission(user.id)
        self.assertEqual(len(after_readable_projects), 1)
