from flask import Flask
from sqlalchemy import create_engine
from flask_cors import CORS

from model import UserDao, CommunityDao, PlaylistDao
from service import UserService, CommunityService, PlaylistService
from view import create_endpoints

class Services:
    pass

def create_app(test_config=None):
    app = Flask(__name__)

    CORS(app)

    if test_config is None:
        app.config.from_pyfile("config.py")
    else:
        app.config.update(test_config)

    database = create_engine(app.config['DB_URL'], encoding='utf-8', max_overflow=0)

    user_dao = UserDao(database)
    community_dao = CommunityDao(database)
    playlist_dao = PlaylistDao(database)

    services = Services
    services.user_service = UserService(user_dao, playlist_dao, app.config)
    services.community_service = CommunityService(community_dao)
    services.playlist_service = PlaylistService(playlist_dao)

    create_endpoints(app, services, app.config)

    return app
