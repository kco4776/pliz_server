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


@pytest.fixture
def community_dao():
    return CommunityDao(database)


@pytest.fixture
def playlist_dao():
    return PlaylistDao(database)


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
    database.execute(text("""
        INSERT INTO users_like_list (
            user_id,
            like_playlist_id
        ) VALUES (
            :user_id,
            :playlist_id
        )
    """), {
        'user_id': 2,
        'playlist_id': 1
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

def test_get_user(user_dao):
    info = user_dao.get_user(1)
    assert info == {
        'id': 1,
        'name': 'kim',
        'email': 'kim@gmail.com',
        'follower': 0,
        'follow': 0
    }


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


def test_insert_community(community_dao):
    title = "test2"
    content = "test2"
    posting_id = community_dao.insert_community(1, title, content)
    assert posting_id == 2
    posting = get_info_community(posting_id)
    assert posting == {
        'user_id': 1,
        'title': title,
        'content': content
    }


def test_insert_comment(community_dao):
    comment = {
        'user_id': 1,
        'community_id': 1,
        'comment': "test2"
    }
    community_dao.insert_comment(comment['user_id'], comment['community_id'], comment['comment'])
    assert get_comments(1) == [
        {
            'user_id': 1,
            'comment': 'test comment'
        },
        {
            'user_id': 1,
            'comment': 'test2'
        }
    ]


def test_get_comments(community_dao):
    assert community_dao.get_comments(1) == [{
        'user_id': 1,
        'user_name': 'kim',
        'comment': 'test comment'
    }]


def test_get_community(community_dao):
    assert community_dao.get_community() == [{
        'community_id': 1,
        'user_id': 1,
        'user_name': 'kim',
        'title': 'test title',
        'content': 'test content',
        'comments': [{
            'user_id': 1,
            'user_name': 'kim',
            'comment': 'test comment'
        }]
    }]

def test_get_community_by_id(community_dao):
    assert community_dao.get_community_by_id(1)['community_id'] == 1


def test_get_song(playlist_dao):
    assert playlist_dao.get_song(1) == [{
        'title': 'test song title',
        'singer': 'test singer'
    }]

def test_insert_playlist(playlist_dao):
    title = "test2"
    description = "test2"
    new_playlist_id = playlist_dao.insert_playlist(1, title, description)
    assert new_playlist_id == 2

    new_playlist = get_playlist_community(new_playlist_id)
    assert new_playlist['id'] == new_playlist_id
    assert new_playlist['title'] == title
    assert new_playlist['description'] == description

def test_get_playlist(playlist_dao):
    assert playlist_dao.get_playlist() == [{
        'playlist_id': 1,
        'user_id': 1,
        'user_name': 'kim',
        'like': 0,
        'title': "test playlist title",
        'description': 'test description',
        'song': [{'title': "test song title", 'singer': "test singer"}],
        'comments': [{
            'user_id': 1,
            'user_name': 'kim',
            'comment': "test playlist comment"}]
    }]

def test_get_playlist_by_id(playlist_dao):
    assert playlist_dao.get_playlist_by_id(1)['playlist_id'] == 1

def test_insert_like(playlist_dao):
    playlist_dao.insert_like(1, 1)
    playlist = playlist_dao.get_playlist()
    assert playlist[0]['like'] == 1

def test_insert_unlike(playlist_dao):
    playlist_dao.insert_like(1, 1)
    playlist_dao.insert_unlike(1, 1)
    playlist = playlist_dao.get_playlist()
    assert playlist[0]['like'] == 0

def test_playlist_ranking(playlist_dao):
    playlist_dao.insert_playlist(2, "test2", "test2")
    playlist_dao.insert_like(1, 1)
    assert playlist_dao.get_playlist_ranking() == [
        {
            'user_id': 1,
            'name': 'kim',
            'title': 'test playlist title',
            'like': 1
        },
        {
            'user_id': 2,
            'name': 'lee',
            'title': 'test2',
            'like': 0
        }
    ]

def test_playlist_comment(playlist_dao):
    playlist_dao.insert_comment(2, 1, "test2")
    playlist = playlist_dao.get_playlist()
    assert playlist[0]['comments'] == [
        {
            'user_id': 1,
            'user_name': 'kim',
            'comment': 'test playlist comment'
        },
        {
            'user_id': 2,
            'user_name': 'lee',
            'comment': "test2"
        }
    ]

def test_get_like_playlist(playlist_dao):
    assert playlist_dao.get_like_playlist(2) == [{
        'playlist_id': 1,
        'title': 'test playlist title'
    }]

