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

    def insert_song(self, title, singer, playlist_id):
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
        """), {
            'title': title,
            'singer': singer,
            'id': playlist_id
        }).rowcount

    def get_playlist(self):
        playlist = self.db.execute(text("""
                SELECT pl.id as playlist_id, users.id as user_id, users.name, pl.title, pl.description, pl.like FROM playlist as pl
                LEFT JOIN users
                ON pl.user_id = users.id
                ORDER BY pl.created_at DESC limit 10
            """)).fetchall()
        return [{
            'playlist_id': p['playlist_id'],
            'user_id': p['user_id'],
            'user_name': p['name'],
            'like': p['like'],
            'title': p['title'],
            'description': p['description'],
            'song': self.get_song(p['playlist_id']),
            'comments': self.get_comments(p['playlist_id'])
        } for p in playlist]

    def get_playlist_by_id(self, playlist_id):
        playlist = self.db.execute(text("""
            SELECT pl.id as playlist_id, users.id as user_id, users.name, pl.title, pl.description, pl.like
            FROM playlist as pl
            JOIN users ON pl.user_id = users.id
            WHERE pl.id = :id
        """), {'id': playlist_id}).fetchone()
        return {
            'playlist_id': playlist['playlist_id'],
            'user_id': playlist['user_id'],
            'user_name': playlist['name'],
            'like': playlist['like'],
            'title': playlist['title'],
            'description': playlist['description'],
            'song': self.get_song(playlist['playlist_id']),
            'comments': self.get_comments(playlist['playlist_id'])
        } if playlist else None

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
            WHERE user_id = :id
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
            SELECT users.id as user_id, users.name, pl.title, pl.like
            FROM playlist as pl
            JOIN users ON pl.user_id = users.id
            ORDER BY pl.like DESC LIMIT 10
        """)).fetchall()
        return [{
            'user_id': r['user_id'],
            'name': r['name'],
            'title': r['title'],
            'like': r['like']
        } for r in ranking]

    def insert_comment(self, user_id, playlist_id, comment):
        return self.db.execute(text("""
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
            'user_id': user_id,
            'playlist_id': playlist_id,
            'comment': comment
        }).rowcount

    def get_comments(self, playlist_id):
        playlist = self.db.execute(text("""
            SELECT users.id as user_id, users.name, pc.comment
            FROM playlist_comments as pc
            JOIN users ON pc.user_id = users.id
            WHERE pc.playlist_id = :id
        """), {'id': playlist_id}).fetchall()
        return [{
            'user_id': p['user_id'],
            'user_name': p['name'],
            'comment': p['comment']
        } for p in playlist]

    def get_like_playlist(self, user_id):
        like_playlist = self.db.execute(text("""
            SELECT pl.id, pl.title
            FROM users_like_list as ul
            JOIN playlist as pl ON ul.like_playlist_id = pl.id
            WHERE ul.user_id = :id
        """), {'id': user_id}).fetchall()
        return [{
            'playlist_id': p['id'],
            'title': p['title']
        } for p in like_playlist]
