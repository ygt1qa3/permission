import unittest
import uuid
# from mock import Mock
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from permission_test import app
import permission_test.models as models
# sqliteに書き換え（ローカルでテストできるように sqliteが入っていることが必須だが）
# わざわざテストする度にpostgresのサーバ立てるのもあれだし
# データの置き場が変わるだけで、コードの記述方法は変わらないのでsqliteの代用でいいかな
# jsonbがpostgres限定なので、そこどうするか
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = models.db

class ModelTestCase(unittest.TestCase):
    def setUp(self):
        db.create_all()
        db.session.commit()

    def tearDown(self):
        db.drop_all()
        db.session.commit()

    def test_create_projects_by_user(self):
        """
        プロジェクトの作成のテスト
        ユーザ×プロジェクトに権限が作成されているかどうかのテストもする
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
        self.assertEqual(projects[0].name, project_name)
        self.assertEqual(projects[0].creator_id, user.id)

        # ユーザ×プロジェクトが作成されているかテスト
        userprojects = db.session.query(models.UserProjects).filter_by(project_id=1, user_id=user.id)
        self.assertEqual(userprojects[0].user_id, user.id)
        self.assertEqual(userprojects[0].project_id, 1)

    def test_delete_projects_by_user(self):
        """
        プロジェクトの削除のテスト
        ユーザ×プロジェクトの該当プロジェクトのidを持つものも削除されているかのテストも行う
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
        projects = models.get_readable_projects_by_user_id(user.id)
        models.delete_project_by_uuid(projects[0].uuid)

        # プロジェクトが削除されているか
        projects = models.get_readable_projects_by_user_id(user.id)
        self.assertEqual(projects.count(), 0)

        # ユーザ×プロジェクトにおいて、削除したプロジェクトのデータが削除されているか？
        userprojects = db.session.query(models.UserProjects).filter_by(project_id=1, user_id=user.id)
        self.assertEqual(userprojects.count(), 0)

    def test_get_readable_projects(self):
        """
        自分が見ることができるプロジェクトの取得テスト
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
        db.session.add(models.UserProjects(all_projects[2].id, user2.id))
        db.session.commit()

        # 自分が見れるプロジェクトが取得できているかテスト
        projects_for_user1 = models.get_readable_projects_by_user_id(user1.id)
        self.assertEqual(projects_for_user1.count(), 2)
        self.assertEqual(projects_for_user1[0].name, project_name_1)
        self.assertEqual(projects_for_user1[1].name, project_name_3)

        projects_for_user2 = models.get_readable_projects_by_user_id(user2.id)
        self.assertEqual(projects_for_user2.count(), 2)
        self.assertEqual(projects_for_user2[0].name, project_name_2)
        self.assertEqual(projects_for_user2[1].name, project_name_3)

    def test_cannot_create_projects(self):
        """
        プロジェクト作成権限のないユーザがプロジェクトを作成できないことを確認するテスト
        """
        # ユーザ作成
        email1 = 'user1@kskp.io'
        models.create_user('ユーザ１', email1, '')
        user1 = db.session.query(models.Users).filter_by(email=email1).first()

        # ユーザのプロジェクト作成権限を変更する
        user1.projects_create = False
        db.session.add(user1)
        db.session.commit()

        # テスト
        can_create_projects = models.check_can_create_projects(user1.id)
        self.assertEqual(can_create_projects, False)

    def test_can_delete_project(self):
        """
        プロジェクト削除権限を持つユーザがプロジェクトを削除できることを確認するテスト
        """
        # ユーザ作成
        email1 = 'user1@kskp.io'
        models.create_user('ユーザ１', email1, '')
        user = db.session.query(models.Users).filter_by(email=email1).first()

        # 作成するプロジェクト情報
        project_name = 'ユーザ１用プロジェクト'

        # プロジェクト作成
        models.create_project(project_name, user.id)
        # プロジェクトUUID,ID取得
        before_project = db.session.query(models.Projects).all()
        project_uuid = before_project[0].uuid
        project_id = before_project[0].id

        # 権限確認
        before_userproject = db.session.query(models.UserProjects).filter_by(project_id=project_id, user_id=user.id).all()
        self.assertEqual(before_userproject[0].project_delete, True)

        # 削除
        models.delete_project_by_uuid(project_uuid)

        # 削除後のプロジェクト数とユーザ×プロジェクト数を数える
        after_projects = db.session.query(models.Projects).count()
        after_userprojects = db.session.query(models.UserProjects).filter_by(project_id=project_id, user_id=user.id).count()

        self.assertEqual(after_projects, 0)
        self.assertEqual(after_userprojects, 0)

    def test_cannot_delete_project(self):
        """
        プロジェクト削除権限を持たないユーザがプロジェクトを削除できないことを確認するテスト
        """
        pass
