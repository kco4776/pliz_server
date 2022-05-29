

class PlaylistService:
    def __init__(self, playlist_dao):
        self.playlist_dao = playlist_dao

    def playlist_community(self):
        return self.playlist_dao.get_playlist()

    def playlist(self, user_id, title, description):
        if len(title)>30:
            return None
        if len(description)>500:
            return None
        return self.playlist_dao.insert_playlist(user_id, title, description)

    def song(self, title, singer, playlist_id):
        if len(title)>50:
            return None
        if len(singer)>50:
            return None
        return self.playlist_dao.insert_song(title, singer, playlist_id)

    def like(self, user_id, playlist_id):
        return self.playlist_dao.insert_like(user_id, playlist_id)

    def unlike(self, user_id, playlist_id):
        return self.playlist_dao.insert_unlike(user_id, playlist_id)

    def ranking(self):
        return self.playlist_dao.get_playlist_ranking()