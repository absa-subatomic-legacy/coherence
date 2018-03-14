class SlackUserLedger(object):
    def __init__(self):
        self.slack_user_clients = []
        self.slack_user_list = []

    def set_slack_user_list(self, slack_user_list):
        self.slack_user_list = slack_user_list

    def find_user_by_username(self, username):
        for user in self.slack_user_list:
            if user["name"] == username:
                return user
        return None

    def find_user_by_slack_id(self, slack_id):
        for user in self.slack_user_list:
            if user["id"] == slack_id:
                return user
        return None

    def find_user_client_by_username(self, username):
        for user in self.slack_user_clients:
            if user.username == username:
                return user
        return None

    def find_user_client_by_slack_id(self, slack_id):
        for user in self.slack_user_clients:
            if user.slack_id == slack_id:
                return user
        return None

    def add_slack_user_client(self, new_user):
        self.slack_user_clients.append(new_user)
