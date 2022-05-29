import bcrypt
import pytest
import config

from model import UserDao, CommunityDao, PlaylistDao
from sqlalchemy import create_engine, text

database = create_engine(config.test_config['DB_URL'],
                         encoding='utf-8',
                         max_overflow=0)


@pytest.fixture
def user_dao():
    return UserDao(database)


def setup_function():
    hashed_password = bcrypt.hashpw(
        b"test password",
        bcrypt.gensalt()
    )
    new_users = [
        {
            'id': 1,
            'name': 'kim',
            'email': 'kim@gmail.com',
            'hashed_password': hashed_password
        }, {
            'id': 2,
            'name': 'lee',
            'email': 'lee@gmail.com',
            'hashed_password': hashed_password
        }
    ]
    database.execute(text("""
        INSERT INTO users (
            id,
            name,
            email,
            hashed_password
        ) VALUES (
            :id,
            :name,
            :email,
            :hashed_password
        )
    """), new_users)



def teardown_function():
    database.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    database.execute(text("TRUNCATE users"))
    database.execute(text("TRUNCATE users_follow_list"))
    database.execute(text("SET FOREIGN_KEY_CHECKS=1"))


def get_user(user_id):
    row = database.execute(text("""
        SELECT id, name, email
        FROM users
        WHERE id = :user_id
    """), {'user_id': user_id}).fetchone()

    return {
        'id': row['id'],
        'name': row['name'],
        'email': row['email']
    } if row else None

def get_follow_list(user_id):
    rows = database.execute(text("""
        SELECT follow_user_id as id
        FROM users_follow_list
        WHERE user_id = :user_id
    """), {'user_id': user_id}).fetchall()
    return [int(row['id']) for row in rows]

def test_insert_user(user_dao):
    new_user = {
        'name': 'park',
        'email': 'park@gmail.com',
        'password': 'test1234'
    }

    new_user_id = user_dao.insert_user(new_user)
    user = get_user(new_user_id)

    assert user == {
        'id': new_user_id,
        'name': new_user['name'],
        'email': new_user['email']
    }

def test_get_user_id_and_password(user_dao):
    user_credential = user_dao.get_user_id_and_password(
        'kim@gmail.com'
    )
    assert user_credential['id'] == 1

    assert bcrypt.checkpw('test password'.encode('UTF-8'),
                          user_credential['hashed_password'].encode('UTF-8'))

def test_insert_follow(user_dao):
    user_dao.insert_follow(1, 2)
    follow_list = get_follow_list(1)
    assert follow_list == [2]

def test_insert_unfollow(user_dao):
    user_dao.insert_follow(1, 2)
    user_dao.insert_unfollow(1, 2)
    follow_list = get_follow_list(1)
    assert follow_list == []

def test_get_follower_ranking(user_dao):
    user_dao.insert_follow(1, 2)
    ranking = user_dao.get_follower_ranking()
    assert ranking == [
        {
            'name': 'lee',
            'email': 'lee@gmail.com',
            'follower': 1
        },
        {
            'name': 'kim',
            'email': 'kim@gmail.com',
            'follower': 0
        }
    ]
