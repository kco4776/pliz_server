

class CommunityService:
    def __init__(self, community_dao):
        self.community_dao = community_dao

    def info_community(self):
        return self.community_dao.get_community()

    def info_community_by_id(self, community_id):
        return self.community_dao.get_community_by_id(community_id)

    def community(self, user_id, title, content):
        if len(title)>30:
            return None
        if len(content)>500:
            return None
        new_community_id = self.community_dao.insert_community(user_id, title, content)
        return new_community_id

    def comment(self, user_id, community_id, comment):
        if len(comment)>100:
            return None
        return self.community_dao.insert_comment(user_id, community_id, comment)