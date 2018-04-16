import json
import logging
from time import sleep, time

import requests
from slackclient import SlackClient

from subatomic_coherence.logging.console_logging import ConsoleLogger


class SlackUser(object):
    def __init__(self, username, slack_token, connect_timeout=None):
        self.username = username
        self.client = SlackClient(slack_token)
        self.token = slack_token
        if connect_timeout is not None:
            connect_timeout = connect_timeout / 1000.0
        self.connect_timeout = connect_timeout
        self.slack_name = ""
        self.slack_id = ""
        self.events = EventStore()
        self.domain = ""
        self.rate_limiters = {
            self.delete_channel.__name__: RateLimiter(1, 10000)
        }

    def connect(self):
        connection_result = self.client.rtm_connect(timeout=self.connect_timeout)
        return connection_result

    def link_user_details(self, user_detail_list):
        return self._get_user_identity(user_detail_list)

    def send_message(self, destination, message, **kwargs):
        keyword_args = {k: v for k, v in kwargs.items() if v is not None}
        keyword_args["channel"] = destination
        keyword_args["text"] = message
        keyword_args["as_user"] = True
        keyword_args["link_names"] = 1
        self.client.api_call(
            "chat.postMessage",
            None,
            **keyword_args
        )
        logging.info(f"User {self.username} sent message to {destination}. Content: {message}")

    def invite_to_channel(self, user_id, channel_id):
        response = self.client.api_call(
            "channels.invite",
            user=user_id,
            channel=channel_id
        )
        result = response["ok"]
        if result is False:
            ConsoleLogger.error(
                f"Failed to invite user {user_id} to channel {channel_id} as user {self.username}:{self.slack_id}")
        else:
            logging.info(f"User {user_id} invited to channel {channel_id}")
        return result

    def invite_to_group(self, user_id, group_id):
        response = self.client.api_call(
            "groups.invite",
            user=user_id,
            channel=group_id
        )
        result = response["ok"]
        if result is False:
            ConsoleLogger.error(
                f"Failed to invite user {user_id} to group {group_id} as user {self.username}:{self.slack_id}")
        else:
            logging.info(f"User {user_id} invited to group {group_id}")
        return result, response

    def kick_from_channel(self, user_id, channel_id):
        response = self.client.api_call(
            "channels.kick",
            user=user_id,
            channel=channel_id
        )
        result = response["ok"]
        if result is False:
            ConsoleLogger.error(
                f"Failed to kick user {user_id} from channel {channel_id} as user {self.username}:{self.slack_id}")
        else:
            logging.info(f"User {user_id} kicked from channel {channel_id}")
        return result, response

    def kick_from_group(self, user_id, group_id):
        response = self.client.api_call(
            "groups.kick",
            user=user_id,
            channel=group_id
        )
        result = response["ok"]
        if result is False:
            ConsoleLogger.error(
                f"Failed to kick user {user_id} from group {group_id} as user {self.username}:{self.slack_id}")
        else:
            logging.info(f"User {user_id} kicked from group {group_id}")
        return result, response

    def delete_channel(self, channel_id):
        rate_limiter = self.rate_limiters[self.delete_channel.__name__]

        wait_time = rate_limiter.wait_time() / 1000
        if wait_time > 0:
            sleep(wait_time)

        response = self.client.api_call(
            "channels.delete",
            channel=channel_id
        )

        rate_limiter.log_call()

        result = response["ok"]
        if result is True:
            logging.info(f"Channel {channel_id} deleted successfully.")
        else:
            ConsoleLogger.error(f"Channel {channel_id} delete command failed as user {self.username}:{self.slack_id}")
        return result, response

    def attachment_action(self, service_id, bot_user_id, actions, attachment_id, callback_id, channel_id, message_ts):
        payload = {
            "actions": actions,
            "attachment_id": attachment_id,
            "callback_id": callback_id,
            "channel_id": channel_id,
            "message_ts": message_ts
        }
        files = {
            "payload": (None, json.dumps(payload)),
            "service_id": (None, service_id),
            "bot_user_id": (None, bot_user_id),
            "token": (None, self.token)
        }

        request_url = f"https://{self.domain}.slack.com/api/chat.attachmentAction"
        response = requests.post(request_url, files=files)
        if response.status_code == 200:
            return True, response
        else:
            return False, response

    def load_events(self, events):
        if type(events) in [list, tuple]:
            for event in events:
                self.events.load_event(event)
        else:
            self.events.load_event(events)

    def clear_event_store(self):
        self.events.clear_event_store()

    def query_workspace_domain(self):
        domain = None
        result = self.client.api_call("team.info")
        if result["ok"]:
            domain = result["team"]["domain"]
            self.domain = domain
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
        logging.debug("Got channel list {channels_list}".format(channels_list=result))
        if result["ok"]:
            channels_list += result["channels"]
        if "response_metadata" in result and "next_cursor" in result["response_metadata"]:
            return channels_list + self.query_workspace_channels(cursor=result["response_metadata"]["next_cursor"])
        else:
            return channels_list

    def query_workspace_groups(self):
        groups_list = []
        result = self.client.api_call("groups.list")
        logging.debug("Got group list {groups_list}".format(groups_list=result))
        if result["ok"]:
            groups_list += result["groups"]

        return groups_list

    def _get_user_identity(self, workspace_user_details):
        for user in workspace_user_details:
            if user["name"] == self.username:
                self.slack_id = user["id"]
                logging.info("Associated slack id {slack_id} to username {username}".format(
                    slack_id=self.slack_id, username=self.username))
                return True
        logging.error("No associated slack user details found for user {username}."
                      " List of available users:\n{userlist}"
                      .format(username=self.username, userlist=workspace_user_details))
        return False


class RateLimiter(object):
    def __init__(self, count, time_period):
        self.count = count
        self.time_period = time_period
        self.calls = []
        self.current_milli_time = lambda: int(round(time() * 1000))

    def can_call(self):
        self.prune()
        return len(self.calls) < self.count

    def wait_time(self):
        self.prune()
        if len(self.calls) > 0:
            return self.time_period - (self.current_milli_time() - self.calls[0])
        return 0

    def prune(self):
        valid_calls = []
        for call in self.calls:
            if self.current_milli_time() - call < self.time_period:
                valid_calls += [call]
        self.calls = valid_calls

    def log_call(self):
        self.calls += [self.current_milli_time()]


class EventStore:
    def __init__(self):
        self.events = []
        self.last_processed_event = None
        self.next_event_index = 0

    def load_event(self, event):
        self.events.append(event)

    def clear_event_store(self):
        self.events = []
        self.next_event_index = 0
        self.last_processed_event = None

    def __iter__(self):
        return self

    def __next__(self):
        self.last_processed_event = None
        if self.next_event_index < len(self.events):
            self.last_processed_event = self.events[self.next_event_index]
            self.next_event_index += 1
            return self.last_processed_event

        raise StopIteration
