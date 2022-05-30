import pytest
import bcrypt
import json
import config

from app import create_app
from sqlalchemy import create_engine, text

database = create_engine(config.test_config['DB_URL'],
                         encoding='utf-8',
                         max_overflow=0)

@pytest.fixture
def api():
    app = create_app(config.test_config)
    app.config['TEST'] = True
    api = app.test_client()
    return api

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

def test_ping(api):
    resp = api.get('/ping')
    assert b'pong' in resp.data

def test_login(api):
    resp = api.post(
        '/login',
        data = json.dumps({
            'email': 'kim@gmail.com',
            'password': 'test password'
        }),
        content_type='application/json'
    )
    assert b"access_token" in resp.data

def test_authorized(api):
    resp = api.post(
        '/community',
        data = json.dumps({
            'title': 'test title',
            'content': 'test content'
        }),
        content_type = 'application/json'
    )
    assert resp.status_code == 401

# def test_follow(api):
#     resp = api.post(
#         '/login',
#         data = json.dumps({
#             'email': 'kim@gmail.com',
#             'password': 'test password'
#         }),
#         content_type = 'application/json'
#     )
#     resp_json = json.loads(resp.data.decode('utf-8'))
#     access_token = resp_json['access_token']
#
#     resp = api.get()