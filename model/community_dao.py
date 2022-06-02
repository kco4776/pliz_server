from sqlalchemy import text


class CommunityDao:
    def __init__(self, database):
        self.db = database

    def insert_community(self, user_id, title, content):
        return self.db.execute(text("""
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
            'id': user_id,
            'title': title,
            'content': content
        }).lastrowid

    def insert_comment(self, user_id, community_id, comment):
        return self.db.execute(text("""
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
            'user_id': user_id,
            'community_id': community_id,
            'comment': comment
        }).rowcount

    def get_comments(self, community_id):
        comments = self.db.execute(text("""
            SELECT users.name, cc.comment
            FROM community_comments as cc
            JOIN users ON cc.user_id = users.id
            WHERE cc.community_id = :id
        """), {'id': community_id}).fetchall()
        return [{
            'user_name': c['name'],
            'comment': c['comment']
        } for c in comments]

    def get_community(self):
        posting = self.db.execute(text("""
            SELECT cc.id, users.name, cc.title, cc.content
            FROM community as cc
            JOIN users ON cc.user_id = users.id
            ORDER BY cc.created_at DESC LIMIT 30
        """)).fetchall()
        return [{
            'id': p['id'],
            'user_name': p['name'],
            'title': p['title'],
            'content': p['content'],
            'comments': self.get_comments(p['id'])
        } for p in posting]

    def get_community_by_id(self, community_id):
        community = self.db.execute(text("""
            SELECT cc.id, users.name, cc.title, cc.content
            FROM community as cc
            JOIN users ON cc.user_id = users.id
            WHERE cc.id = :id
        """), {'id': community_id}).fetchone()
        return {
            'id': community['id'],
            'user_name': community['name'],
            'title': community['title'],
            'content': community['content'],
            'comments': self.get_comments(community['id'])
        } if community else None
