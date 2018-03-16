import json
import logging

import requests

from coherence.testing.Test import TestResult


def _expect_message(to_user_client,
                    from_user_id,
                    channel_id=None,
                    message_text=None,
                    ignore_case=True):
    for event in to_user_client.events:
        if event["type"] == "message":
            message = event
            if "subtype" in event and "message" in event:
                message = event["message"]
            if "user" in message and message["user"] == from_user_id:
                if channel_id is None or ("channel" in message and message["channel"]):
                    if _try_compare_message_text(message["text"], message_text, ignore_case):
                        return event
    return None


def _try_compare_message_text(real_message,
                              comparison_text,
                              ignore_case=True):
    result = False
    if comparison_text is not None:
        actual_text = real_message
        if ignore_case:
            comparison_text = comparison_text.lower()
            actual_text = actual_text.lower()
        if comparison_text == actual_text:
            result = True
    else:
        # Response is true if there is no text to compare to. Probably bad but allows use a more general way.
        # Maybe should rename this function
        result = True
    return result


def _try_get_channel_id(slack_user_workspace, channel_name):
    channel_id = None
    if channel_name is not None:
        channel_details = slack_user_workspace.find_channel_by_name(channel_name)
        if channel_details is not None:
            channel_id = channel_details["id"]
        else:
            # Throw error maybe?
            pass
    return channel_id


def _get_main_message_body(event):
    message = event
    if "subtype" in event and "message" in event:
        message = event["message"]
    return message


def send_message_to_user(from_user_slack_name,
                         to_user_slack_name,
                         message):
    def send_message_function(slack_user_workspace, data_store):
        logging.debug("Sending message {message}".format(message=message))
        user_sender = slack_user_workspace.find_user_client_by_username(from_user_slack_name)
        user_receiver_details = slack_user_workspace.find_user_by_username(to_user_slack_name)
        user_sender.send_message(user_receiver_details["id"], message)
        return TestResult(1)

    return send_message_function


def expect_message_from_user(from_user_slack_name,
                             to_user_slack_name,
                             channel_name=None,
                             message_text=None,
                             ignore_case=True,
                             validators=[]):
    def expect_message_from_user_function(slack_user_workspace, data_store):
        user_sender_details = slack_user_workspace.find_user_by_username(from_user_slack_name)
        user_receiver = slack_user_workspace.find_user_client_by_username(to_user_slack_name)
        channel_id = _try_get_channel_id(slack_user_workspace, channel_name)
        message = _expect_message(user_receiver, user_sender_details["id"], channel_id, message_text, ignore_case)
        if message is not None:
            validated = True
            for validator in validators:
                validated &= validator(message)
            if validated:
                return TestResult(1)
        return TestResult(0)

    return expect_message_from_user_function


def expect_and_store_action_message(from_user_slack_name,
                                    to_user_slack_name,
                                    event_storage_name,
                                    channel_name=None,
                                    message_text=None,
                                    ignore_case=True,
                                    validators=[]):
    def expect_and_store_action_message_function(slack_user_workspace, data_store):
        user_sender_details = slack_user_workspace.find_user_by_username(from_user_slack_name)
        user_receiver = slack_user_workspace.find_user_client_by_username(to_user_slack_name)
        channel_id = _try_get_channel_id(slack_user_workspace, channel_name)
        for event in user_receiver.events:
            message = event
            if event["type"] == "message" and "subtype" in event and "message" in event:
                message = event["message"]
            if message["type"] == "message" and message["user"] == user_sender_details["id"]:
                if channel_id is None or ("channel" in message and message["channel"]):
                    if len(message["attachments"]) > 0:
                        attachments = message["attachments"]
                        for attachment in attachments:
                            if "actions" in attachment and len(attachment["actions"]) > 0:
                                if _try_compare_message_text(message["text"], message_text, ignore_case):
                                    validated = True
                                    for validator in validators:
                                        validated &= validator(event)
                                    if validated:
                                        data_store[event_storage_name] = event
                                        return TestResult(1)
        return TestResult(0)

    return expect_and_store_action_message_function


def respond_to_stored_action_message(from_user_slack_name,
                                     event_storage_name,
                                     attachment_id,
                                     action_id):
    def respond_to_stored_action_message_function(slack_user_workspace, data_store):
        user_sender = slack_user_workspace.find_user_client_by_username(from_user_slack_name)
        button_event = data_store[event_storage_name]
        button_event_main_message = _get_main_message_body(button_event)
        response_body = {}
        service_id = button_event_main_message["bot_id"]
        bot_user_id = button_event_main_message["user"]
        token = user_sender.token
        found_action = False
        for attachment in button_event_main_message["attachments"]:
            if attachment["id"] == attachment_id and "actions" in attachment:
                for action in attachment["actions"]:
                    if action["id"] == str(action_id):
                        response_body["actions"] = [action]
                        response_body["attachment_id"] = attachment_id
                        response_body["callback_id"] = attachment["callback_id"]
                        response_body["channel_id"] = button_event["channel"]
                        response_body["message_ts"] = button_event_main_message["ts"]
                        found_action = True
                        break
            if found_action:
                break

        request_url = "https://{domain}.slack.com/api/chat.attachmentAction" \
            .format(domain=slack_user_workspace.workspace_domain)
        response = requests.post(request_url,
                                 files={
                                     'payload': (None, json.dumps(response_body)),
                                     "service_id": (None, service_id),
                                     "bot_user_id": (None, bot_user_id),
                                     "token": (None, token)
                                 }
                                 )

        if response.status_code == 200:
            return TestResult(1)
        else:
            return TestResult(2, response.content)

    return respond_to_stored_action_message_function


def expect_channel_created(user, channel_name):
    def expect_channel_created_function(slack_user_workspace, data_store):
        user_client = slack_user_workspace.find_user_client_by_username(user)
        for event in user_client.events:
            if event["type"] == "channel_created" and event["channel"]["name"] == channel_name:
                return TestResult(1)
        return TestResult(0)

    return expect_channel_created_function


def delete_channel(as_user, channel_name):
    def delete_channel_function(slack_user_workspace, data_store):
        as_user_client = slack_user_workspace.find_user_client_by_username(as_user)
        as_user_client.delete_channel(slack_user_workspace.find_channel_by_name(channel_name)["id"])
        return TestResult(1)

    return delete_channel_function
