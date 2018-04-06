from unittest import mock
from unittest.mock import MagicMock

import coherence.actions.SimpleActions as SimpleActions
from coherence.testing.Test import ResultCode
from coherence.user.SlackUser import SlackUser
from coherence.user.SlackUserWorkspace import SlackUserWorkspace


def test_expect_message_with_simple_message_from_user_expect_event_returned():
    user = SlackUser("user", "token")
    expected_event = {
        "type": "message",
        "user": "U2222222",
        "text": "some text"
    }
    user.events = [
        expected_event,
        {
            "type": "not_a_message"
        }
    ]

    result = SimpleActions._expect_message(user, "U2222222")
    assert result["type"] == "message"
    assert result == expected_event


def test_expect_message_with_subtype_message_from_user_expect_event_returned():
    user = SlackUser("user", "token")
    expected_event = {
        "type": "message",
        "subtype": "some_sub_type",
        "message": {
            "user": "U2222222",
            "text": "some text"
        }
    }
    user.events = [
        expected_event,
        {
            "type": "not_a_message"
        }
    ]

    result = SimpleActions._expect_message(user, "U2222222")
    assert result == expected_event


def test_expect_message_threaded_message_from_user_expect_event_returned():
    user = SlackUser("user", "token")
    expected_event = {
        "type": "message",
        "user": "U2222222",
        "text": "some text",
        "thread_ts": "1000"
    }
    user.events = [
        expected_event,
        {
            "type": "not_a_message"
        }
    ]

    result = SimpleActions._expect_message(user, "U2222222", is_thread=True)
    assert result == expected_event


def test_expect_message_thread_message_with_ts_from_user_expect_event_returned():
    user = SlackUser("user", "token")
    expected_event = {
        "type": "message",
        "user": "U2222222",
        "text": "some text",
        "thread_ts": "1000"
    }
    user.events = [
        expected_event,
        {
            "type": "message",
            "user": "U2222222",
            "text": "some text",
            "thread_ts": "1002"
        }
    ]

    result = SimpleActions._expect_message(user, "U2222222", is_thread=True, thread_ts="1000")
    assert result["thread_ts"] == "1000"
    assert result == expected_event


def test_expect_message_with_simple_message_from_channel_expect_event_returned():
    user = SlackUser("user", "token")
    expected_event = {
        "type": "message",
        "user": "U2222222",
        "text": "some text",
        "channel": "G111111"
    }
    user.events = [
        expected_event,
        {
            "type": "message",
            "user": "U2222222",
            "text": "some text",
            "channel": "G111112"
        }
    ]

    result = SimpleActions._expect_message(user, "U2222222", channel_id="G111111")
    assert result["channel"] == "G111111"
    assert result == expected_event


def test_expect_message_with_matching_text_from_user_ignore_case_expect_event_returned():
    user = SlackUser("user", "token")
    expected_event = {
        "type": "message",
        "user": "U2222222",
        "text": "some text"
    }
    user.events = [
        expected_event,
        {
            "type": "message",
            "user": "U2222222",
            "text": "some text that is wrong"
        }
    ]

    result = SimpleActions._expect_message(user, "U2222222", message_text="SOME TEXT")
    assert result == expected_event


def test_expect_message_with_matching_text_from_user_case_sensitive_expect_event_returned():
    user = SlackUser("user", "token")
    expected_event = {
        "type": "message",
        "user": "U2222222",
        "text": "SOME TEXT"
    }
    user.events = [
        expected_event,
        {
            "type": "message",
            "user": "U2222222",
            "text": "some text"
        }
    ]

    result = SimpleActions._expect_message(user, "U2222222", message_text="SOME TEXT", ignore_case=False)
    assert result == expected_event


def test_try_compare_message_text_simple_comparison_expect_success():
    result = SimpleActions._try_compare_message_text("a message", "a message")
    assert result is True


def test_try_compare_message_text_ignore_case_expect_success():
    result = SimpleActions._try_compare_message_text("a message", "a Message")
    assert result is True


def test_try_compare_message_text_case_sensitive_expect_failure():
    result = SimpleActions._try_compare_message_text("a message", "a Message", ignore_case=False)
    assert result is False


def test_try_get_channel_id_expect_success():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.find_group_or_channel_by_name = MagicMock(return_value={"id": "G123456"})
    result = SimpleActions._try_get_channel_id(slack_user_workspace, "some_channel")
    assert result == "G123456"


def test_try_get_channel_id_expect_failure():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.find_group_or_channel_by_name = MagicMock(return_value=None)
    result = SimpleActions._try_get_channel_id(slack_user_workspace, "some_channel")
    assert result is None


def test_send_message_to_user_simple_expect_success():
    send_message_function = SimpleActions.send_message_to_user("user1", "user2", "hello")
    user1 = SlackUser("user1", "token")
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.find_user_client_by_username = MagicMock(return_value=user1)
    slack_user_workspace.find_user_by_username = MagicMock(return_value={"id": "U222222"})
    user1.send_message = MagicMock(return_value=True)
    result = send_message_function(slack_user_workspace, {})
    assert result.result_code == ResultCode.success


def test_send_message_to_user_thread_with_ts_name_expect_success():
    send_message_function = SimpleActions.send_message_to_user("user1", "user2", "hello", thread_ts_name="my_thread")
    user1 = SlackUser("user1", "token")
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.find_user_client_by_username = MagicMock(return_value=user1)
    slack_user_workspace.find_user_by_username = MagicMock(return_value={"id": "U222222"})
    user1.send_message = MagicMock(return_value=True)
    result = send_message_function(slack_user_workspace, {"my_thread": "1000"})
    assert result.result_code == ResultCode.success


def test_send_message_to_channel_simple_expect_success():
    send_message_function = SimpleActions.send_message_to_channel("user1", "channel1", "hello")
    user1 = SlackUser("user1", "token")
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.find_user_client_by_username = MagicMock(return_value=user1)
    slack_user_workspace.find_channel_by_name = MagicMock(return_value={"id": "G123456"})
    user1.send_message = MagicMock(return_value=True)
    result = send_message_function(slack_user_workspace, {})
    assert result.result_code == ResultCode.success


def test_expect_message_from_user_simple_message_expect_success():
    import coherence.actions.SimpleActions as MockableSimpleActions
    expect_message_function = MockableSimpleActions.expect_message_from_user("user1", "user2")
    slack_user_workspace = SlackUserWorkspace()
    user1 = SlackUser("user1", "token")
    slack_user_workspace.find_user_client_by_username = MagicMock(return_value=user1)
    slack_user_workspace.find_user_by_username = MagicMock(return_value={"id": "U222222"})
    MockableSimpleActions._expect_message = MagicMock(return_value={
        "type": "message",
        "user": "U2222222",
        "text": "some text"
    })
    MockableSimpleActions._try_get_channel_id = MagicMock(return_value=None)

    result = expect_message_function(slack_user_workspace, {})
    assert result.result_code == ResultCode.success


def test_expect_message_from_user_store_thread_ts_expect_success():
    import coherence.actions.SimpleActions as MockableSimpleActions
    expect_message_function = MockableSimpleActions.expect_message_from_user("user1", "user2",
                                                                             thread_ts_name="my_thread")
    slack_user_workspace = SlackUserWorkspace()
    user1 = SlackUser("user1", "token")
    slack_user_workspace.find_user_client_by_username = MagicMock(return_value=user1)
    slack_user_workspace.find_user_by_username = MagicMock(return_value={"id": "U222222"})
    MockableSimpleActions._expect_message = MagicMock(return_value={
        "type": "message",
        "user": "U2222222",
        "text": "some text",
        "thread_ts": "1000"
    })
    MockableSimpleActions._try_get_channel_id = MagicMock(return_value=None)
    data_store = {}
    result = expect_message_function(slack_user_workspace, data_store)
    assert result.result_code == ResultCode.success
    assert data_store["my_thread"] == "1000"


def test_expect_message_from_user_with_validator_expect_pending():
    import coherence.actions.SimpleActions as MockableSimpleActions

    def validator(message):
        return False

    expect_message_function = MockableSimpleActions.expect_message_from_user("user1", "user2", validators=[validator])
    slack_user_workspace = SlackUserWorkspace()
    user1 = SlackUser("user1", "token")
    slack_user_workspace.find_user_client_by_username = MagicMock(return_value=user1)
    slack_user_workspace.find_user_by_username = MagicMock(return_value={"id": "U222222"})
    MockableSimpleActions._expect_message = MagicMock(return_value={
        "type": "message",
        "user": "U2222222",
        "text": "some text"
    })
    MockableSimpleActions._try_get_channel_id = MagicMock(return_value=None)
    data_store = {}
    result = expect_message_function(slack_user_workspace, data_store)
    assert result.result_code == ResultCode.pending


def test_expect_and_store_action_message_with_validator_expect_failure():
    import coherence.actions.SimpleActions as MockableSimpleActions

    def validator(message):
        return False

    expect_action_function = MockableSimpleActions.expect_and_store_action_message("user1", "user2", "my_action",
                                                                                   validators=[validator])
    slack_user_workspace = SlackUserWorkspace()
    user2 = SlackUser("user2", "token")
    slack_user_workspace.find_user_client_by_username = MagicMock(return_value=user2)
    slack_user_workspace.find_user_by_username = MagicMock(return_value={"id": "U111111"})
    expected_event = {
        "type": "message",
        "user": "U111111",
        "text": "some text",
        "attachments": [
            {
                "actions": [
                    {"id": "action1"}
                ]
            }
        ]
    }
    MockableSimpleActions._try_get_channel_id = MagicMock(return_value=None)
    user2.events = [expected_event]
    data_store = {}
    result = expect_action_function(slack_user_workspace, data_store)
    assert result.result_code == ResultCode.pending