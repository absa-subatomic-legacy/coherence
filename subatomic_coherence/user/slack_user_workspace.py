class SlackUserWorkspace(object):
    def __init__(self):
        self.slack_user_clients = []
        self.workspace_user_details = []
        self.workspace_channels = []
        self.workspace_groups = []

    def set_workspace_user_details(self, workspace_user_details):
        self.workspace_user_details = workspace_user_details

    def set_workspace_channels(self, workspace_channels):
        self.workspace_channels = workspace_channels

    def set_workspace_groups(self, workspace_groups):
        self.workspace_groups = workspace_groups

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

    def find_channel_by_name(self, channel_name):
        for channel in self.workspace_channels:
            if channel["name"] == channel_name:
                return channel
        return None

    def find_channel_by_slack_id(self, slack_id):
        for channel in self.workspace_channels:
            if channel["id"] == slack_id:
                return channel
        return None

    def find_group_by_name(self, group_name):
        for group in self.workspace_groups:
            if group["name"] == group_name:
                return group
        return None

    def find_group_by_slack_id(self, slack_id):
        for group in self.workspace_groups:
            if group["id"] == slack_id:
                return group
        return None

    def find_group_or_channel_by_name(self, name):
        result = self.find_channel_by_name(name)
        if result is None:
            result = self.find_group_by_name(name)
        return result

    def find_group_or_channel_by_slack_id(self, slack_id):
        result = self.find_channel_by_slack_id(slack_id)
        if result is None:
            result = self.find_group_by_slack_id(slack_id)
        return result

    def last_processed_event(self):
        for user in self.slack_user_clients:
            user_last_event = user.events.last_processed_event
            if user_last_event is not None:
                return user_last_event
        return None