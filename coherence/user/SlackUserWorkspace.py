class SlackUserWorkspace(object):
    def __init__(self):
        self.slack_user_clients = []
        self.workspace_domain = ""
        self.workspace_user_details = []
        self.workspace_channels = []
        self.workspace_groups = []

    def set_workspace_user_details(self, workspace_user_details):
        self.workspace_user_details = workspace_user_details

    def set_workspace_channels(self, workspace_channels):
        self.workspace_channels = workspace_channels

    def set_workspace_groups(self, workspace_groups):
        self.workspace_groups = workspace_groups

    def set_workspace_domain(self, workspace_domain):
        self.workspace_domain = workspace_domain

    def find_user_by_username(self, username):
        for user in self.workspace_user_details:
            if user["name"] == username:
                return user
        return None

    def find_user_by_slack_id(self, slack_id):
        for user in self.workspace_user_details:
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
