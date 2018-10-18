from permission_test.api import app
from permission_test.models import db, create_user

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    email1 = 'user1@kskp.io'
    create_user('ユーザ１', email1, '')
    email2 = 'user2@kskp.io'
    create_user('ユーザ2', email2, '')
    app.run()
