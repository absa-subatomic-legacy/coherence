from subatomic_coherence.testing.test import TestResult, ResultCode


def _expect_message(to_user_client,
                    from_user_id,
                    channel_id=None,
                    message_text=None,
                    ignore_case=True,
                    is_thread=False,
                    thread_ts=None):
    for event in to_user_client.events:
        if event["type"] == "message":
            message = event
            if "subtype" in event and "message" in event:
                message = event["message"]

            event_conditions_pass = (not is_thread or "thread_ts" in event) and \
                                    (thread_ts is None or event["thread_ts"] == thread_ts)
            if event_conditions_pass and "user" in message and message["user"] == from_user_id:
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
        channel_details = slack_user_workspace.find_group_or_channel_by_name(channel_name)
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
                         message,
                         thread_ts=None,
                         thread_ts_name=None):
    def send_message_to_user_function(slack_user_workspace, data_store):
        user_sender = slack_user_workspace.find_user_client_by_username(from_user_slack_name)
        user_receiver_details = slack_user_workspace.find_user_by_username(to_user_slack_name)
        actual_thread_ts = thread_ts
        if thread_ts_name in data_store:
            actual_thread_ts = data_store[thread_ts_name]
        user_sender.send_message(user_receiver_details["id"], message, thread_ts=actual_thread_ts)
        return TestResult(ResultCode.success)

    return send_message_to_user_function


def send_message_to_channel(from_user_slack_name,
                            channel_name,
                            message,
                            thread_ts=None,
                            thread_ts_name=None):
    def send_message_to_channel_function(slack_user_workspace, data_store):
        user_sender = slack_user_workspace.find_user_client_by_username(from_user_slack_name)
        channel_details = slack_user_workspace.find_channel_by_name(channel_name)
        actual_thread_ts = thread_ts
        if thread_ts_name in data_store:
            actual_thread_ts = data_store[thread_ts_name]
        user_sender.send_message(channel_details["id"], message, thread_ts=actual_thread_ts)
        return TestResult(ResultCode.success)

    return send_message_to_channel_function


def expect_message_from_user(from_user_slack_name,
                             to_user_slack_name,
                             channel_name=None,
                             thread_ts=None,
                             thread_ts_name=None,
                             message_text=None,
                             ignore_case=True,
                             validators=None):
    if validators is None:
        validators = []

    def expect_message_from_user_function(slack_user_workspace, data_store):
        user_receiver = slack_user_workspace.find_user_client_by_username(to_user_slack_name)
        user_sender_details = slack_user_workspace.find_user_by_username(from_user_slack_name)
        channel_id = _try_get_channel_id(slack_user_workspace, channel_name)
        actual_thread_ts = thread_ts
        is_thread = False
        if thread_ts_name in data_store:
            actual_thread_ts = data_store[thread_ts_name]
        if actual_thread_ts is not None:
            is_thread = True
        message = _expect_message(user_receiver, user_sender_details["id"], channel_id, message_text, ignore_case,
                                  is_thread, actual_thread_ts)
        if message is not None:
            validated = True
            for validator in validators:
                validated &= validator(message)
            if validated:
                if thread_ts_name is not None:
                    data_store[thread_ts_name] = message["thread_ts"]
                return TestResult(ResultCode.success)
        return TestResult(ResultCode.pending)

    return expect_message_from_user_function


def expect_and_store_action_message(from_user_slack_name,
                                    to_user_slack_name,
                                    event_storage_name,
                                    channel_name=None,
                                    message_text=None,
                                    ignore_case=True,
                                    validators=None):
    if validators is None:
        validators = []

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
                    if "attachments" in message and len(message["attachments"]) > 0:
                        attachments = message["attachments"]
                        for attachment in attachments:
                            if "actions" in attachment and len(attachment["actions"]) > 0:
                                if _try_compare_message_text(message["text"], message_text, ignore_case):
                                    validated = True
                                    for validator in validators:
                                        validated &= validator(event)
                                    if validated:
                                        data_store[event_storage_name] = event
                                        return TestResult(ResultCode.success)
        return TestResult(ResultCode.pending)

    return expect_and_store_action_message_function


def respond_to_stored_action_message(from_user_slack_name,
                                     event_storage_name,
                                     attachment_ids=None,
                                     action_ids=None,
                                     attachment_action_validators=None):
    if type(attachment_ids) is int:
        attachment_ids = [attachment_ids]
    elif attachment_ids is None:
        attachment_ids = []

    attachment_ids = [int(attachment_id) for attachment_id in attachment_ids]

    if type(action_ids) is int:
        action_ids = [action_ids]
    elif action_ids is None:
        action_ids = []

    action_ids = [int(action_id) for action_id in action_ids]

    if attachment_action_validators is None:
        attachment_action_validators = []

    def respond_to_stored_action_message_function(slack_user_workspace, data_store):
        user_sender = slack_user_workspace.find_user_client_by_username(from_user_slack_name)
        button_event = data_store[event_storage_name]
        button_event_main_message = _get_main_message_body(button_event)
        service_id = button_event_main_message["bot_id"]
        bot_user_id = button_event_main_message["user"]
        for attachment in button_event_main_message["attachments"]:
            if "actions" in attachment and (len(attachment_ids) == 0 or int(attachment["id"]) in attachment_ids):
                for action in attachment["actions"]:
                    if len(action_ids) == 0 or int(action["id"]) in action_ids:
                        validated = True
                        for validator in attachment_action_validators:
                            validated &= validator(attachment, action)
                        if validated:
                            result, response = user_sender.attachment_action(service_id, bot_user_id, [action],
                                                                             attachment_ids,
                                                                             attachment["callback_id"],
                                                                             button_event["channel"],
                                                                             button_event_main_message["ts"])
                            if result:
                                return TestResult(ResultCode.success)
                            else:
                                return TestResult(ResultCode.failure, response.content)

        return TestResult(ResultCode.failure, "Action or attachment not found.")

    return respond_to_stored_action_message_function


def expect_channel_created(user, channel_name):
    def expect_channel_created_function(slack_user_workspace, data_store):
        user_client = slack_user_workspace.find_user_client_by_username(user)
        for event in user_client.events:
            if event["type"] == "channel_created" and event["channel"]["name"] == channel_name:
                return TestResult(ResultCode.success)
        return TestResult(ResultCode.pending)

    return expect_channel_created_function


def delete_channel(as_user, channel_name):
    def delete_channel_function(slack_user_workspace, data_store):
        as_user_client = slack_user_workspace.find_user_client_by_username(as_user)
        result, response = as_user_client.delete_channel(slack_user_workspace.find_channel_by_name(channel_name)["id"])
        test_result = TestResult(ResultCode.success)
        if result is False:
            test_result = TestResult(ResultCode.failure, response["error"])
        return test_result

    return delete_channel_function


def invite_user_to_channel(inviting_user, invited_user, channel_name, is_private=False):
    def invite_user_to_channel_function(slack_user_workspace, data_store):
        inviting_user_client = slack_user_workspace.find_user_client_by_username(inviting_user)
        invited_user_details = slack_user_workspace.find_user_by_username(invited_user)
        channel_id = _try_get_channel_id(slack_user_workspace, channel_name)
        if is_private:
            result, response = inviting_user_client.invite_to_group(invited_user_details["id"], channel_id)
        else:
            result, response = inviting_user_client.invite_to_channel(invited_user_details["id"], channel_id)

        test_result = TestResult(ResultCode.success)
        if result is False:
            test_result = TestResult(ResultCode.failure, response["error"])
        return test_result

    return invite_user_to_channel_function


def kick_user_from_channel(kicking_user, kicked_user, channel_name, is_private=False):
    def kick_user_from_channel_function(slack_user_workspace, data_store):
        kicker_user_client = slack_user_workspace.find_user_client_by_username(kicking_user)
        kicked_user_details = slack_user_workspace.find_user_by_username(kicked_user)
        channel_id = _try_get_channel_id(slack_user_workspace, channel_name)
        if is_private:
            result, response = kicker_user_client.kick_from_group(kicked_user_details["id"], channel_id)
        else:
            result, response = kicker_user_client.kick_from_channel(kicked_user_details["id"], channel_id)

        test_result = TestResult(ResultCode.success)
        if result is False:
            test_result = TestResult(ResultCode.failure, response["error"])
        return test_result

    return kick_user_from_channel_function
