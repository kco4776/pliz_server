from sqlalchemy import text


class PlaylistDao:
    def __init__(self, database):
        self.db = database

    def get_song(self, playlist_id):
        songs = self.db.execute(text("""
            SELECT song.title, song.singer FROM playlist as pl
            LEFT JOIN song
            ON pl.id = song.playlist_id
            WHERE pl.id = :id
        """), {'id': playlist_id}).fetchall()
        return [{
            'title': song['title'],
            'singer': song['singer']
        } for song in songs]

    def insert_playlist(self, user_id, title, description):
        return self.db.execute(text("""
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
            'id': user_id,
            'title': title,
            'description': description
        }).lastrowid

    def insert_song(self, song):
        return self.db.execute(text("""
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

    def get_playlist(self):
        playlist = self.execute(text("""
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
            'song': self.get_song(p['id'])
        } for p in playlist]

    def insert_like(self, user_id, playlist_id):
        cnt = self.db.execute(text("""
            INSERT INTO users_like_list (
                user_id,
                like_playlist_id
            ) VALUES (
                :id,
                :playlist_id
            )
        """), {
            'id': user_id,
            'playlist_id': playlist_id
        }).rowcount
        self.db.execute(text("""
            UPDATE `playlist`
            SET `like`=`like`+1
            WHERE `id` = :id
        """), {'id': playlist_id})
        return cnt

    def insert_unlike(self, user_id, playlist_id):
        cnt = self.db.execute(text("""
            DELETE FROM users_like_list
            WHERE id = :id
            AND like_playlist_id = :playlist_id
        """), {
            'id': user_id,
            'playlist_id': playlist_id
        }).rowcount
        self.db.execute(text("""
            UPDATE `playlist`
            SET `like`=`like`-1
            WHERE `id` = :id
        """), {'id': playlist_id})
        return cnt

    def get_playlist_ranking(self):
        ranking = self.db.execute(text("""
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