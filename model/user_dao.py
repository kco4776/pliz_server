from sqlalchemy import text


class UserDao:
    def __init__(self, database):
        self.db = database

    def get_user(self, user_id):
        user = self.db.execute(text("""
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

    def insert_user(self, user):
        return self.db.execute(text("""
            INSERT INTO users (
                name, 
                email, 
                hashed_password
            ) VALUES (
                :name,
                :email,
                :password
            )
        """), user).lastrowid

    def get_user_id_and_password(self, email):
        row = self.db.execute(text("""
            SELECT
                id,
                hashed_password
            FROM users
            WHERE email = :email
        """), {'email': email}).fetchone()

        return {
            'id': row['id'],
            'hashed_password': row['hashed_password']
        } if row else None

    def insert_follow(self, user_id, user_follow):
        cnt = self.db.execute(text("""
            INSERT INTO users_follow_list (
                user_id,
                follow_user_id
            ) VALUES (
                :id,
                :follow
            )
        """), {
            'id': user_id,
            'follow': user_follow
        }).rowcount
        self.db.execute(text("""
            UPDATE `users`
            SET `follow`=`follow`+1
            WHERE `id` = :id
        """), {'id': user_id})
        self.db.execute(text("""
            UPDATE `users`
            SET `follower`=`follower`+1
            WHERE `id` = :id
        """), {'id': user_follow})
        return cnt

    def insert_unfollow(self, user_id, user_unfollow):
        cnt = self.db.execute(text("""
            DELETE FROM users_follow_list
            WHERE user_id = :id
            AND follow_user_id = :unfollow
        """), {
            'id': user_id,
            'unfollow': user_unfollow
        }).rowcount
        self.db.execute(text("""
            UPDATE `users`
            SET `follow`=`follow`-1
            WHERE `id` = :id
        """), {'id': user_id})
        self.db.execute(text("""
            UPDATE `users`
            SET `follower`=`follower`-1
            WHERE `id` = :id
        """), {'id': user_unfollow})
        return cnt

    def get_follower_ranking(self):
        ranking = self.db.execute(text("""
            SELECT name, email, follower FROM users
            ORDER BY follower DESC LIMIT 10
        """)).fetchall()
        return [{
            'name': r['name'],
            'email': r['email'],
            'follower': r['follower']
        } for r in ranking]