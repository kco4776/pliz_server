import jwt
import requests

from flask import request, jsonify, current_app, Response, g
from flask.json import JSONEncoder
from functools import wraps


class CustomJsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return JSONEncoder.default(self, obj)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = request.headers.get('Authorization')
        if access_token is not None:
            try:
                payload = jwt.decode(access_token, current_app.config['JWT_SECRET_KEY'], 'HS256')
            except jwt.InvalidTokenError:
                payload = None
            if payload is None: return Response(status=401)

            user_id = payload['user_id']
            g.user_id = user_id
        else:
            return Response(status=401)
        return f(*args, **kwargs)

    return decorated_function


def create_endpoints(app, services, config):
    app.json_encoder = CustomJsonEncoder

    user_service = services.user_service
    community_service = services.community_service
    playlist_service = services.playlist_service

    @app.route("/ping", methods=['GET'])
    def ping():
        return "pong"

    @app.route("/sign-up", methods=['POST'])
    def sign_up():
        new_user = request.json
        if 'name' not in new_user.keys() or 'email' not in new_user.keys() or 'password' not in new_user.keys():
            return "request data error", 400
        new_user = user_service.create_new_user(new_user)
        return jsonify(new_user)

    @app.route("/login", methods=['POST'])
    def login():
        credential = request.json
        authorized = user_service.login(credential)

        if authorized:
            user_credential = user_service.user_dao.get_user_id_and_password(
                credential['email']
            )
            user_id = user_credential['id']
            token = user_service.generate_access_token(user_id)

            return jsonify({
                'user_id': user_id,
                'access_token': token
            })
        else:
            return Response(status=401)

    @app.route("/user-info/<int:user_id>", methods=['GET'])
    def user_info(user_id):
        info = user_service.user_info(user_id)
        return jsonify(info) if info else Response(status=404)

    @app.route("/my-info", methods=['GET'])
    @login_required
    def my_info():
        user_id = g.user_id
        info = user_service.user_info(user_id)
        return jsonify(info) if info else Response(status=404)

    @app.route("/unfollow", methods=['POST'])
    @login_required
    def unfollow():
        payload = request.json
        if 'unfollow' not in payload:
            return Response(status=400)
        user_id = g.user_id
        unfollow_id = payload['unfollow']

        user_service.unfolow(user_id, unfollow_id)
        return Response(status=200)

    @app.route("/follower-ranking", methods=['GET'])
    def follower_ranking():
        return jsonify({
            'ranking': user_service.follower_ranking()
        })

    @app.route("/info-community", methods=['GET'])
    def info_community():
        return jsonify({
            'info_community': community_service.info_community()
        })

    @app.route("/info-community-id/<int:community_id>", methods=['GET'])
    def info_community_id(community_id):
        info = community_service.info_community_by_id(community_id)
        return jsonify(info) if info else Response(status=404)

    @app.route("/community", methods=['POST'])
    @login_required
    def community():
        user_posting = request.json
        if 'title' not in user_posting.keys() or 'content' not in user_posting.keys():
            return Response(status=400)
        user_id = g.user_id
        title = user_posting['title']
        content = user_posting['content']
        return jsonify({
            'id': community_service.community(user_id, title, content)
        })

    @app.route("/info-comment", methods=['POST'])
    @login_required
    def info_comment():
        user_comment = request.json
        if 'community_id' not in user_comment.keys() or 'comment' not in user_comment.keys():
            return Response(status=400)
        user_id = g.user_id
        community_id = user_comment['community_id']
        _comment = user_comment['comment']
        community_service.comment(user_id, community_id, _comment)
        return Response(status=200)

    @app.route("/search-song", methods=['POST'])
    def search_song():
        payload = request.json
        if 'title' not in payload.keys():
            return "request data error", 400
        title = payload['title']
        last_fm = requests.get(
            f"https://ws.audioscrobbler.com/2.0/?method=track.search&track={title}&api_key={config['LAST_FM_API_KEY']}&format=json&limit=10")
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

    @app.route("/playlist-community", methods=['GET'])
    def playlist_community():
        return jsonify({
            'playlist_community': playlist_service.playlist_community()
        })

    @app.route("/playlist-community-id/<int:playlist_id>", methods=['GET'])
    def playlist_community_id(playlist_id):
        info = playlist_service.playlist_community_by_id(playlist_id)
        return jsonify(info) if info else Response(status=404)

    @app.route("/playlist", methods=['POST'])
    @login_required
    def playlist():
        payload = request.json
        if 'title' not in payload.keys() or 'description' not in payload.keys():
            return Response(status=400)
        user_id = g.user_id
        title = payload['title']
        description = payload['description']
        return jsonify({
            'id': playlist_service.playlist(user_id, title, description)
        })

    @app.route("/song", methods=['POST'])
    def song():
        payload = request.json
        if 'title' not in payload.keys() or 'singer' not in payload.keys() or 'id' not in payload.keys():
            return Response(status=400)
        title = payload['title']
        singer = payload['singer']
        playlist_id = payload['id']
        playlist_service.song(title, singer, playlist_id)
        return Response(status=200)

    @app.route("/like", methods=['POST'])
    @login_required
    def like():
        payload = request.json
        if 'playlist_id' not in payload.keys():
            return Response(status=400)
        user_id = g.user_id
        playlist_id = payload['playlist_id']
        playlist_service.like(user_id, playlist_id)
        return Response(status=200)

    @app.route("/unlike", methods=['POST'])
    @login_required
    def unlike():
        payload = request.json
        if 'playlist_id' not in payload.keys():
            return Response(status=400)
        user_id = g.user_id
        playlist_id = payload['playlist_id']
        playlist_service.unlike(user_id, playlist_id)
        return Response(status=200)

    @app.route("/playlist-comment", methods=['POST'])
    @login_required
    def playlist_comment():
        user_comment = request.json
        if 'playlist_id' not in user_comment.keys() or 'comment' not in user_comment.keys():
            return Response(status=400)
        user_id = g.user_id
        playlist_id = user_comment['playlist_id']
        _comment = user_comment['comment']
        playlist_service.comment(user_id, playlist_id, _comment)
        return Response(status=200)

    @app.route("/playlist-ranking", methods=['GET'])
    def playlist_ranking():
        return jsonify({
            'ranking': playlist_service.ranking()
        })