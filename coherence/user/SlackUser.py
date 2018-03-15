import logging

from slackclient import SlackClient


class SlackUser(object):
    def __init__(self, username, slack_token):
        self.username = username
        self.client = SlackClient(slack_token)
        self.token = slack_token
        self.slack_name = ""
        self.slack_id = ""
        self.events = []

    def connect(self):
        connection_result = self.client.rtm_connect()
        return connection_result

    def link_user_details(self, user_detail_list):
        self._get_user_identity(user_detail_list)

    def send_message(self, destination, message):
        self.client.api_call(
            "chat.postMessage",
            channel=destination,
            text=message,
            as_user=True
        )

    def clear_event_store(self):
        self.events = []

    def _get_user_identity(self, workspace_user_details):
        for user in workspace_user_details:
            if user["name"] == self.username:
                self.slack_id = user["id"]
                logging.info("Associated slack id {slack_id} to username {username}".format(
                    slack_id=self.slack_id, username=self.username))
                return
        logging.error("No associated slack user details found for user {username}."
                      " List of available users:\n{userlist}"
                      .format(username=self.username, userlist=workspace_user_details))
        exit(1)

    def query_workspace_domain(self):
        domain = None
        result = self.client.api_call("team.info")
        if result["ok"]:
            domain = result["team"]["domain"]
        # else throw error maybe?
        return domain

    def query_workspace_user_details(self, cursor=None):
        user_list = []
        if cursor is not None:
            result = self.client.api_call("users.list", cursor=cursor)
        else:
            result = self.client.api_call("users.list")
        logging.debug("Got user list {user_list}".format(user_list=result))
        if result["ok"]:
            user_list += result["members"]
        if "response_metadata" in result and "next_cursor" in result["response_metadata"]:
            return user_list + self.query_workspace_user_details(cursor=result["response_metadata"]["next_cursor"])
        else:
            return user_list

    def query_workspace_channels(self, cursor=None):
        channels_list = []
        if cursor is not None:
            result = self.client.api_call("channels.list", cursor=cursor)
        else:
            result = self.client.api_call("channels.list")
        logging.debug("Got user list {channels_list}".format(channels_list=result))
        if result["ok"]:
            channels_list += result["channels"]
        if "response_metadata" in result and "next_cursor" in result["response_metadata"]:
            return channels_list + self.query_workspace_user_details(cursor=result["response_metadata"]["next_cursor"])
        else:
            return channels_list

    def query_workspace_groups(self):
        groups_list = []
        result = self.client.api_call("groups.list")
        logging.debug("Got user list {groups_list}".format(groups_list=result))
        if result["ok"]:
            groups_list += result["groups"]

        return groups_list
