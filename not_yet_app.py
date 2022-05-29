import jwt
import bcrypt
import requests

from flask import Flask, request, jsonify, current_app, Response, g
from flask.json import JSONEncoder
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from functools import wraps
from flask_cors import CORS


class CustomJsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return JSONEncoder.default(self, obj)


def get_user(user_id):
    user = current_app.database.execute(text("""
        SELECT
            id,
            name,
            email,
            follower,
            follow
        FROM users
        WHERE id = :user_id
    """), {
        'user_id': user_id
    }).fetchone()
    return {
        'id': user['id'],
        'name': user['name'],
        'email': user['email'],
        'follower': user['follower'],
        'follow': user['follow']
    } if user else None


def insert_user(user):
    return current_app.database.execute(text("""
        INSERT INTO USERS (
            name, 
            email, 
            hashed_password
        ) VALUES (
            :name,
            :email,
            :password
        )
    """), user).lastrowid

def get_user_id_and_password(email):
    row = current_app.database.execute(text("""
        SELECT
            id,
            hashed_password
        FROM USERS
        WHERE email = :email
    """), {'email': email}).fetchone()

    return {
        'id': row['id'],
        'hashed_password': row['hashed_password']
    } if row else None

def insert_community(user_posting):
    return current_app.database.execute(text("""
        INSERT INTO community (
            user_id,
            title,
            content
        ) VALUES (
            :id,
            :title,
            :content
        )
    """), user_posting).lastrowid

def insert_comment(user_comment):
    return current_app.database.execute(text("""
        INSERT INTO community_comments (
            user_id,
            community_id,
            comment
        ) VALUES (
            :user_id,
            :community_id,
            :comment
        )
    """), user_comment).rowcount

def get_comments(community_id):
    comments = current_app.database.execute(text("""
        SELECT users.name, cc.comment
        FROM community_comments as cc
        JOIN users ON cc.user_id = users.id
        WHERE cc.community_id = :id
    """), {'id': community_id}).fetch_all()
    return [{
        'user_name': c['name'],
        'comment': c['comment']
    } for c in comments]

def get_community():
    posting = current_app.database.execute(text("""
        SELECT id, user_id, title, content
        FROM community
        ORDER BY created_at DESC LIMIT 30
    """)).fetchall()
    return [{
        'id': p['id'],
        'user_id': p['user_id'],
        'title': p['title'],
        'content': p['content'],
        'comments': get_comments(p['id'])
    } for p in posting]

def insert_follow(user_follow):
    cnt = current_app.database.execute(text("""
        INSERT INTO users_follow_list (
            user_id,
            follow_user_id
        ) VALUES (
            :id,
            :follow
        )
    """), user_follow).rowcount
    current_app.database.execute(text("""
        UPDATE `users`
        SET `follow`=`follow`+1
        WHERE `id` = :id
    """), {'id': user_follow['id']})
    current_app.database.execute(text("""
        UPDATE `users`
        SET `follower`=`follower`+1
        WHERE `id` = :id
    """), {'id': user_follow['follow']})
    return cnt

def insert_unfollow(user_unfollow):
    cnt = current_app.database.execute(text("""
        DELETE FROM users_follow_list
        WHERE user_id = :id
        AND follow_user_id = :unfollow
    """), user_unfollow).rowcount
    current_app.database.execute(text("""
        UPDATE `users`
        SET `follow`=`follow`-1
        WHERE `id` = :id
    """), {'id': user_unfollow['id']})
    current_app.database.execute(text("""
        UPDATE `users`
        SET `follower`=`follower`-1
        WHERE `id` = :id
    """), {'id': user_unfollow['unfollow']})
    return cnt

def insert_like(user_like):
    cnt = current_app.database.execute(text("""
        INSERT INTO users_like_list (
            user_id,
            like_playlist_id
        ) VALUES (
            :id,
            :playlist_id
        )
    """), user_like).rowcount
    current_app.database.execute(text("""
        UPDATE `playlist`
        SET `like`=`like`+1
        WHERE `id` = :id
    """), {'id': user_like['playlist_id']})
    return cnt

def insert_unlike(user_unlike):
    cnt = current_app.database.execute(text("""
        DELETE FROM users_like_list
        WHERE id = :id
        AND like_playlist_id = :playlist_id
    """), user_unlike).rowcount
    current_app.database.execute(text("""
        UPDATE `playlist`
        SET `like`=`like`-1
        WHERE `id` = :id
    """), {'id': user_unlike['playlist_id']})
    return cnt

def get_song(playlist_id):
    songs = current_app.database.execute(text("""
        SELECT song.title, song.singer FROM playlist as pl
        LEFT JOIN song
        ON pl.id = song.playlist_id
        WHERE pl.id = :id
    """), {'id': playlist_id}).fetchall()
    return [{
        'title': song['title'],
        'singer': song['singer']
    } for song in songs]

def get_playlist():
    playlist = current_app.database.execute(text("""
            SELECT pl.id, users.name, pl.title, pl.description, pl.like FROM playlist as pl
            LEFT JOIN users
            ON pl.user_id = users.id
            ORDER BY pl.created_at DESC limit 10
        """)).fetchall()
    return [{
        'id': p['id'],
        'user_name': p['name'],
        'like': p['like'],
        'title': p['title'],
        'description': p['description'],
        'song': get_song(p['id'])
    } for p in playlist]

def insert_playlist(user_playlist):
    return current_app.database.execute(text("""
        INSERT INTO playlist (
            user_id,
            title,
            description
        ) VALUES (
            :id,
            :title,
            :description
        )
    """), user_playlist).lastrowid

def insert_song(song):
    return current_app.database.execute(text("""
        INSERT INTO song (
            title,
            singer,
            playlist_id
        ) VALUES (
            :title,
            :singer,
            :id
        )
    """), song).rowcount

def get_follower_ranking():
    ranking = current_app.database.execute(text("""
        SELECT name, email, follower FROM users
        ORDER BY follower DESC LIMIT 10
    """)).fetchall()
    return [{
        'name': r['name'],
        'email': r['email'],
        'follower': r['follower']
    } for r in ranking]

def get_playlist_ranking():
    ranking = current_app.database.execute(text("""
        SELECT users.name, pl.title, pl.like
        FROM playlist as pl
        JOIN users ON pl.user_id = users.id
        ORDER BY pl.like DESC LIMIT 10
    """)).fetchall()
    return [{
        'name': r['name'],
        'title': r['title'],
        'like': r['like']
    } for r in ranking]

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = request.headers.get('Authorization')
        if access_token is not None:
            try:
                payload = jwt.decode(access_token, current_app.config['JWT_SECRET_KEY'], 'HS256')
            except jwt.InvalidTokenError:
                payload = None
            if payload is None:
                return Response(status=401)
            user_id = payload['user_id']
            g.user_id = user_id
            g.user = get_user(user_id) if user_id else None
        else:
            return Response(status=401)
        return f(*args, **kwargs)
    return decorated_function

def create_app(test_config=None):
    app = Flask(__name__)

    CORS(app)

    app.json_encoder = CustomJsonEncoder

    if test_config is None:
        app.config.from_pyfile("config.py")
    else:
        app.config.update(test_config)

    database = create_engine(app.config['DB_URL'], encoding='utf-8', max_overflow=0)
    app.database = database

    @app.route("/ping", methods=['GET'])
    def ping():
        return "pong"

    @app.route("/sign-up", methods=['POST'])
    def sign_up():
        new_user = request.json
        if 'name' not in new_user.keys() or 'email' not in new_user.keys() or 'password' not in new_user.keys():
            return "request data error", 400
        new_user['password'] = bcrypt.hashpw(
            new_user['password'].encode("UTF-8"), bcrypt.gensalt()
        )
        new_user_id = insert_user(new_user)
        new_user = get_user(new_user_id)
        return jsonify(new_user)

    @app.route("/login", methods=['POST'])
    def login():
        credential = request.json
        if 'email' not in credential.keys() or 'password' not in credential.keys():
            return "request data error", 400
        email = credential['email']
        password = credential['password']
        user_credential = get_user_id_and_password(email)

        if user_credential and bcrypt.checkpw(password.encode('UTF-8'),
                                              user_credential['hashed_password'].encode('UTF-8')):
            user_id = user_credential['id']
            payload = {
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(seconds=60*60*24)
            }
            token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], 'HS256')
            return jsonify({
                'access_token': token
            })
        else:
            return Response(status=401)

    @app.route("/follow", methods=['POST'])
    @login_required
    def follow():
        payload = request.json
        if 'follow' not in payload.keys():
            return "request data error", 400
        payload['id'] = g.user_id
        insert_follow(payload)
        return Response(status=200)

    @app.route("/unfollow", methods=['POST'])
    @login_required
    def unfollow():
        payload = request.json
        if 'unfollow' not in payload.keys():
            return "request data error", 400
        payload['id'] = g.user_id
        insert_unfollow(payload)
        return Response(status=200)

    @app.route("/like", methods=['POST'])
    @login_required
    def like():
        payload = request.json # playlist_id
        if 'playlist_id' not in payload.keys():
            return "request data error", 400
        payload['id'] = g.user_id
        insert_like(payload)
        return Response(status=200)

    @app.route("/unlike", methods=['POST'])
    @login_required
    def unlike():
        payload = request.json # playlist_id
        if 'playlist_id' not in payload.keys():
            return "request data error", 400
        payload['id'] = g.user_id
        insert_unlike(payload)
        return Response(status=200)

    @app.route("/info-community", methods=['GET'])
    def info_community():
        return jsonify({
            'info_community': get_community()
        })

    @app.route("/community", methods=['POST'])
    @login_required
    def community():
        user_posting = request.json # title, content
        if 'title' not in user_posting.keys() or 'content' not in user_posting.keys():
            return "request data error", 400
        user_posting['id'] = g.user_id
        if len(user_posting['title']) > 300:
            return 'title over letters 300!', 400
        if len(user_posting['content']) > 2000:
            return 'content over letters 2000!', 400
        new_community_id = insert_community(user_posting)
        return jsonify({
            'id': new_community_id
        })

    @app.route("/comment", methods=['POST'])
    @login_required
    def comment():
        payload = request.json # community_id, comment
        if 'community_id' not in payload.keys() or 'comment' not in payload.keys():
            return "request data error", 400
        if len(payload['comment'])>100:
            return "comment letters over 100", 400
        payload['user_id'] = g.user_id
        insert_comment(payload)
        return Response(status=200)

    @app.route("/search-song", methods=['GET'])
    def search_song():
        payload = request.json
        if 'title' not in payload.keys():
            return "request data error", 400
        title = payload['title']
        last_fm = requests.get(f"https://ws.audioscrobbler.com/2.0/?method=track.search&track={title}&api_key={app.config['LAST_FM_API_KEY']}&format=json&limit=5")
        if last_fm.status_code != 200:
            return Response(status=400)
        last_fm = last_fm.json()
        matches = last_fm['results']['trackmatches']['track']
        return jsonify({
            'matches': [{
                'title': m['name'],
                'singer': m['artist']
            } for m in matches]
        })

    @app.route("/song", methods=['POST'])
    @login_required
    def song():
        payload = request.json # title, singer, id
        if 'title' not in payload.keys() or 'singer' not in payload.keys() or 'id' not in payload.keys():
            return "request data error", 400
        insert_song(payload)
        return Response(status=200)

    @app.route("/playlist-community", methods=['GET'])
    def playlist_community():
        return jsonify({
            'playlist-community': get_playlist()
        })

    @app.route("/playlist", methods=['POST'])
    @login_required
    def playlist():
        payload = request.json # title, description
        if 'title' not in payload.keys() or 'description' not in payload.keys():
            return "request data error", 400
        payload['id'] = g.user_id
        if len(payload['title'])>100:
            return "title letters over 100!", 400
        if len(payload['description'])>2000:
            return "description letters over 2000!", 400
        new_playlist_id = insert_playlist(payload)
        return jsonify({
            'id': new_playlist_id
        })

    @app.route("/follower-ranking", methods=['GET'])
    def follower_ranking():
        return jsonify({
            'ranking': get_follower_ranking()
        })

    @app.route("/playlist-ranking", methods=['GET'])
    def playlist_ranking():
        return jsonify({
            'ranking': get_playlist_ranking()
        })

    return app


if __name__ == '__main__':
    app = create_app()
    app.run()

