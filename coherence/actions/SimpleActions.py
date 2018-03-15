import json
import logging

import requests

from coherence.testing.Test import TestResult


def _expect_dm_message(to_user_client,
                       from_user_id,
                       message_text=None,
                       ignore_case=True):
    for event in to_user_client.events:
        if event["type"] == "message":
            if "user" in event and event["user"] == from_user_id:
                if _try_compare_message_text(event["text"], message_text, ignore_case):
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


def send_message_to_user(from_user_slack_name,
                         to_user_slack_name,
                         message):
    def send_message_function(slack_user_workspace, data_store):
        user_sender = slack_user_workspace.find_user_client_by_username(from_user_slack_name)
        user_receiver_details = slack_user_workspace.find_user_by_username(to_user_slack_name)
        user_sender.send_message(user_receiver_details["id"], message)
        return TestResult(1)

    return send_message_function


def expect_message_from_user(from_user_slack_name,
                             to_user_slack_name,
                             message_text=None,
                             ignore_case=True):
    def expect_message_from_user_function(slack_user_workspace, data_store):
        user_sender_details = slack_user_workspace.find_user_by_username(from_user_slack_name)
        user_receiver = slack_user_workspace.find_user_client_by_username(to_user_slack_name)
        message = _expect_dm_message(user_receiver, user_sender_details["id"], message_text, ignore_case)
        if message is not None:
            return TestResult(1)
        return TestResult(0)

    return expect_message_from_user_function


def expect_and_store_action_message(from_user_slack_name,
                                    to_user_slack_name,
                                    event_storage_name,
                                    message_text=None,
                                    ignore_case=True):
    def expect_and_store_action_message_function(slack_user_workspace, data_store):
        user_sender_details = slack_user_workspace.find_user_by_username(from_user_slack_name)
        user_receiver = slack_user_workspace.find_user_client_by_username(to_user_slack_name)
        for event in user_receiver.events:
            if event["type"] == "message" and event["user"] == user_sender_details["id"]:
                if len(event["attachments"]) > 0:
                    attachments = event["attachments"]
                    for attachment in attachments:
                        if "actions" in attachment and len(attachment["actions"]) > 0:
                            if _try_compare_message_text(event["text"], message_text, ignore_case):
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
        response_body = {}
        service_id = button_event["bot_id"]
        bot_user_id = button_event["user"]
        token = user_sender.token
        found_action = False
        for attachment in button_event["attachments"]:
            if attachment["id"] == attachment_id:
                for action in attachment["actions"]:
                    if action["id"] == str(action_id):
                        response_body["actions"] = [action]
                        response_body["attachment_id"] = attachment_id
                        response_body["callback_id"] = attachment["callback_id"]
                        response_body["channel_id"] = button_event["channel"]
                        response_body["message_ts"] = button_event["ts"]
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
