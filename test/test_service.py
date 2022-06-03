import jwt
import bcrypt
import pytest
import config

from model import UserDao, CommunityDao, PlaylistDao
from service import UserService, CommunityService, PlaylistService
from sqlalchemy import create_engine, text

database = create_engine(config.test_config['DB_URL'],
                         encoding='utf-8',
                         max_overflow=0)

@pytest.fixture
def user_service():
    return UserService(UserDao(database), PlaylistDao(database), config.test_config)

@pytest.fixture
def community_service():
    return CommunityService(CommunityDao(database))

@pytest.fixture
def playlist_service():
    return PlaylistService(PlaylistDao(database))

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

    database.execute(text("""
        INSERT INTO community (
            user_id,
            title,
            content
        ) VALUES (
            :id,
            :title,
            :content
        )
    """), {
        'id': 1,
        'title': 'test title',
        'content': 'test content'
    })
    database.execute(text("""
        INSERT INTO community_comments (
            user_id,
            community_id,
            comment
        ) VALUES (
            :user_id,
            :community_id,
            :comment
        )
    """), {
        'user_id': 1,
        'community_id': 1,
        'comment': "test comment"
    })
    database.execute(text("""
        INSERT INTO playlist (
            user_id,
            title,
            description
        ) VALUES (
            :id,
            :title,
            :description
        )
    """), {
        'id': 1,
        'title': "test playlist title",
        'description': 'test description'
    })
    database.execute(text("""
        INSERT INTO song (
            title,
            singer,
            playlist_id
        ) VALUES (
            :title,
            :singer,
            :playlist_id
        )
    """), {
        'title': 'test song title',
        'singer': 'test singer',
        'playlist_id': 1
    })
    database.execute(text("""
        INSERT INTO playlist_comments (
            user_id,
            playlist_id,
            comment
        ) VALUES (
            :user_id,
            :playlist_id,
            :comment
        )
    """), {
        'user_id': 1,
        'playlist_id': 1,
        'comment': "test playlist comment"
    })


def teardown_function():
    database.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    database.execute(text("TRUNCATE users"))
    database.execute(text("TRUNCATE users_follow_list"))
    database.execute(text("TRUNCATE community"))
    database.execute(text("TRUNCATE community_comments"))
    database.execute(text("TRUNCATE playlist"))
    database.execute(text("TRUNCATE song"))
    database.execute(text("TRUNCATE playlist_comments"))
    database.execute(text("TRUNCATE users_like_list"))
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


def get_info_community(community_id):
    r = database.execute(text("""
        SELECT `user_id`, `title`, `content`
        FROM `community`
        WHERE `id` = :community_id
    """), {'community_id': community_id}).fetchone()
    return {
        'user_id': r['user_id'],
        'title': r['title'],
        'content': r['content']
    }


def get_comments(community_id):
    rows = database.execute(text("""
        SELECT user_id, comment
        FROM community_comments
        WHERE community_id = :id
    """), {'id': community_id}).fetchall()
    return [{
        'user_id': row['user_id'],
        'comment': row['comment']
    } for row in rows]


def get_playlist_community(playlist_id):
    playlist = database.execute(text("""
        SELECT id, title, description, `like`
        FROM playlist
        WHERE id = :playlist_id
    """), {'playlist_id': playlist_id}).fetchone()
    return {
        'id': playlist['id'],
        'title': playlist['title'],
        'description': playlist['description'],
        'like': playlist['like']
    }

def get_song(playlist_id):
    songs = database.execute(text("""
        SELECT song.title, song.singer
        FROM playlist as pl
        JOIN song on pl.id = song.playlist_id
        WHERE pl.id = :playlist_id
    """), {'playlist_id': playlist_id}).fetchall()
    return [{
        'title': s['title'],
        'singer': s['singer']
    } for s in songs]

def test_create_new_user(user_service):
    new_user = {
        'name': 'park',
        'email': 'park@gmail.com',
        'password': 'test1234'
    }
    new_user_id = user_service.create_new_user(new_user)
    created_user = get_user(new_user_id)
    assert created_user == {
        'id': new_user_id,
        'name': new_user['name'],
        'email': new_user['email']
    }

def test_login(user_service):
    credential = {
        'email': 'kim@gmail.com',
        'password': 'test password'
    }
    assert user_service.login(credential) == True

    false_credential = {
        'email': 'kim@gmail.com',
        'password': 'false password'
    }
    assert user_service.login(false_credential) == False

def test_generate_access_token(user_service):
    token = user_service.generate_access_token(1)
    payload = jwt.decode(token, config.JWT_SECRET_KEY, 'HS256')

    assert payload['user_id'] == 1

def test_user_info(user_service):
    user_id = 2
    info = user_service.user_info(user_id)
    assert info['id'] == user_id

def test_follow(user_service):
    user_service.follow(1, 2)
    follow_list = get_follow_list(1)
    assert follow_list == [2]

def test_unfollow(user_service):
    user_service.follow(1, 2)
    user_service.unfollow(1, 2)
    follow_list = get_follow_list(1)
    assert follow_list == []

def test_follower_ranking(user_service):
    user_service.follow(1, 2)
    ranking = user_service.follower_ranking()
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

def test_info_community(community_service):
    assert community_service.info_community() == [{
        'community_id': 1,
        'user_id': 1,
        'user_name': 'kim',
        'title': 'test title',
        'content': 'test content',
        'comments': [{
            'user_id': 1,
            'user_name': 'kim',
            'comment': 'test comment'}]
    }]

def test_info_community_by_id(community_service):
    info = community_service.info_community_by_id(1)
    assert info['community_id'] == 1

def test_community(community_service):
    title = "test2"
    content = "test2"
    new_community_id = community_service.community(2, title, content)
    assert new_community_id == 2
    assert get_info_community(new_community_id) == {
        'user_id': 2,
        'title': title,
        'content': content
    }

def test_community_comment(community_service):
    comment = "test2"
    community_service.comment(1, 1, comment)
    assert get_comments(1) == [
        {
            'user_id': 1,
            'comment': 'test comment'
        },
        {
            'user_id': 1,
            'comment': comment
        }
    ]

def test_playlist_community(playlist_service):
    assert playlist_service.playlist_community() == [{
        'playlist_id': 1,
        'user_id': 1,
        'user_name': 'kim',
        'like': 0,
        'title': 'test playlist title',
        'description': 'test description',
        'song': [{'title': 'test song title', 'singer': 'test singer'}],
        'comments': [{
            'user_id': 1,
            'user_name': 'kim',
            'comment': 'test playlist comment'}]
    }]

def test_playlist_community_by_id(playlist_service):
    assert playlist_service.playlist_community_by_id(1)['playlist_id'] == 1

def test_playlist(playlist_service):
    title = "test2"
    description = "test2"
    new_playlist_id = playlist_service.playlist(1, title, description)
    assert new_playlist_id == 2
    assert get_playlist_community(new_playlist_id) == {
        'id': new_playlist_id,
        'title': title,
        'description': description,
        'like': 0
    }

def test_song(playlist_service):
    title = "test2"
    singer = "test2"
    playlist_service.song(title, singer, 1)
    assert get_song(1) == [
        {
            'title': 'test song title',
            'singer': 'test singer'
        },
        {
            'title': 'test2',
            'singer': 'test2'
        }
    ]

def test_like(playlist_service):
    playlist_service.like(1, 1)
    playlist = get_playlist_community(1)
    assert playlist['like'] == 1

def test_unlike(playlist_service):
    playlist_service.like(1, 1)
    playlist_service.unlike(1, 1)
    playlist = get_playlist_community(1)
    assert playlist['like'] == 0

def test_ranking(playlist_service):
    title = 'test2'
    description = 'test2'
    new_playlist_id = playlist_service.playlist(2, title, description)
    playlist_service.like(1, 1)
    assert playlist_service.ranking() == [
        {
            'user_id': 1,
            'name': 'kim',
            'title': 'test playlist title',
            'like': 1
        },
        {
            'user_id': 2,
            'name': 'lee',
            'title': title,
            'like': 0
        }
    ]