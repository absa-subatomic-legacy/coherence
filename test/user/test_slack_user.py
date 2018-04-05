from unittest.mock import MagicMock

from coherence.user.SlackUser import SlackUser


def test_user_connect_expect_success():
    user = SlackUser("user", "token")
    user.client.rtm_connect = MagicMock(return_value=True)
    assert user.connect() is True


def test_user_connect_expect_failure():
    user = SlackUser("user", "token")
    user.client.rtm_connect = MagicMock(return_value=False)
    assert user.connect() is False


def test_link_user_details_expect_correct_slack_id_found():
    user = SlackUser("user", "token")
    assert user.link_user_details([{"name": "user", "id": "U2203024"}]) is True
    assert user.slack_id == "U2203024"


def test_link_user_details_expect_no_id_found():
    user = SlackUser("user", "token")
    assert user.link_user_details([{"name": "user2", "id": "U2203024"}]) is False
    assert user.slack_id == ""


def test_invite_to_channel_expect_success():
    user = SlackUser("user", "token")
    user.client.api_call = MagicMock(return_value={"ok": True})
    assert user.invite_to_channel("some_user", "some_channel") is True


def test_invite_to_channel_expect_failure():
    user = SlackUser("user", "token")
    user.client.api_call = MagicMock(return_value={"ok": False})
    assert user.invite_to_channel("some_user", "some_channel") is False


def test_invite_to_group_expect_success():
    user = SlackUser("user", "token")
    user.client.api_call = MagicMock(return_value={"ok": True})
    result, response = user.invite_to_group("some_user", "some_group")
    assert result is True


def test_invite_to_group_expect_failure():
    user = SlackUser("user", "token")
    user.client.api_call = MagicMock(return_value={"ok": False})
    result, response = user.invite_to_group("some_user", "some_group")
    assert result is False


def test_kick_from_channel_expect_success():
    user = SlackUser("user", "token")
    user.client.api_call = MagicMock(return_value={"ok": True})
    result, response = user.kick_from_channel("some_user", "some_channel")
    assert result is True


def test_kick_from_channel_expect_failure():
    user = SlackUser("user", "token")
    user.client.api_call = MagicMock(return_value={"ok": False})
    result, response = user.kick_from_channel("some_user", "some_channel")
    assert result is False


def test_kick_from_group_expect_success():
    user = SlackUser("user", "token")
    user.client.api_call = MagicMock(return_value={"ok": True})
    result, response = user.kick_from_group("some_user", "some_group")
    assert result is True


def test_kick_from_group_expect_failure():
    user = SlackUser("user", "token")
    user.client.api_call = MagicMock(return_value={"ok": False})
    result, response = user.kick_from_group("some_user", "some_group")
    assert result is False


def test_delete_channel_expect_success():
    user = SlackUser("user", "token")
    user.client.api_call = MagicMock(return_value={"ok": True})
    result, response = user.delete_channel("some_channel")
    assert result is True


def test_delete_channel_expect_failure():
    user = SlackUser("user", "token")
    user.client.api_call = MagicMock(return_value={"ok": False})
    result, response = user.delete_channel("some_channel")
    assert result is False


def test_query_workspace_domain_expect_domain_name():
    user = SlackUser("user", "token")
    user.client.api_call = MagicMock(return_value={"ok": True, "team": {"domain": "mydomain"}})
    domain = user.query_workspace_domain()
    assert domain == "mydomain"


def test_query_workspace_user_details_expect_all_user_details():
    user = SlackUser("user", "token")
    call_count = 0

    def mocked_user_list_function(method, **kwargs):
        nonlocal call_count
        if call_count == 0:
            call_count += 1
            return {
                "ok": True,
                "members": [{"id": 1}, {"id": 2}],
                "response_metadata": {
                    "next_cursor": 3
                }
            }
        else:
            return {
                "ok": True,
                "members": [{"id": 3}, {"id": 4}]
            }

    user.client.api_call = mocked_user_list_function
    user_list = user.query_workspace_user_details()
    assert len(user_list) == 4
    assert user_list[-1]["id"] == 4


def test_query_workspace_channels_expect_all_channels():
    user = SlackUser("user", "token")
    call_count = 0

    def mocked_channel_list_function(method, **kwargs):
        nonlocal call_count
        if call_count == 0:
            call_count += 1
            return {
                "ok": True,
                "channels": [{"id": 1}, {"id": 2}],
                "response_metadata": {
                    "next_cursor": 3
                }
            }
        else:
            return {
                "ok": True,
                "channels": [{"id": 3}, {"id": 4}]
            }

    user.client.api_call = mocked_channel_list_function
    channel_list = user.query_workspace_channels()
    assert len(channel_list) == 4
    assert channel_list[-1]["id"] == 4


def test_query_workspace_groups_expect_all_groups():
    user = SlackUser("user", "token")
    user.client.api_call = MagicMock(return_value={
        "ok": True,
        "groups": [{"id": 1}, {"id": 2}]
    })
    group_list = user.query_workspace_groups()
    assert len(group_list) == 2
    assert group_list[-1]["id"] == 2
