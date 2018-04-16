from unittest import mock
from unittest.mock import MagicMock

from subatomic_coherence.user.slack_user import SlackUser, RateLimiter, EventStore
from testing.mocking.mocking import MockRequestsResponse


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


def _mock_attachment_action_post(*args, **kwargs):
    return MockRequestsResponse({"files": kwargs["files"], "url": args[0]}, 200)


@mock.patch('subatomic_coherence.user.slack_user.requests.post', side_effect=_mock_attachment_action_post)
def test_attachment_action_expect_body_and_url_correctly_formed(mock_post):
    user = SlackUser("user", "token")
    user.domain = "adomain"
    result, response = user.attachment_action("service_id", "bot_user_id", [{"id": "action_id"}], "attachment_id",
                                              "callback_id", "channel_id", "message_ts")
    print(response)
    assert response.json_data["files"][
               "payload"][1] == '{"actions": [{"id": "action_id"}], "attachment_id": "attachment_id",' \
                                ' "callback_id": "callback_id", "channel_id": "channel_id", "message_ts": "message_ts"}'
    assert response.json_data["files"]["service_id"][1] == "service_id"
    assert response.json_data["files"]["bot_user_id"][1] == "bot_user_id"
    assert response.json_data["files"]["token"][1] == "token"
    assert response.status_code == 200
    assert result is True


def test_rate_limiter_log_call_expect_call_logged():
    limiter = RateLimiter(2, 100000)
    limiter.current_milli_time = lambda: 0
    limiter.log_call()
    assert limiter.calls[0] == 0
    limiter.current_milli_time = lambda: 5
    limiter.log_call()
    assert limiter.calls[1] == 5


def test_rate_limiter_prune_expect_non_expired_calls_pruned():
    limiter = RateLimiter(2, 10)
    limiter.current_milli_time = lambda: 0
    limiter.log_call()
    limiter.current_milli_time = lambda: 8
    limiter.log_call()
    limiter.current_milli_time = lambda: 15
    limiter.prune()
    assert limiter.calls[0] == 8
    assert len(limiter.calls) == 1


def test_rate_limiter_where_not_exceeding_count_expect_success():
    limiter = RateLimiter(2, 100000)
    limiter.log_call()
    assert limiter.can_call() is True


def test_rate_limiter_where_exceeding_count_expect_cannot_call():
    limiter = RateLimiter(1, 100000)
    limiter.log_call()
    assert limiter.can_call() is False


def test_rate_limiter_where_exceeding_count_expect_wait_time_correct():
    limiter = RateLimiter(1, 10)
    limiter.current_milli_time = lambda: 0
    limiter.log_call()
    # pretend 5 milliseconds have passed
    limiter.current_milli_time = lambda: 5
    assert limiter.can_call() is False
    assert limiter.wait_time() == 5


def test_event_store_load_event_expect_success():
    event_store = EventStore()
    event_store.load_event({"id": 5})
    assert event_store.events[0]["id"] == 5


def test_event_store_clear_event_store_expect_success():
    event_store = EventStore()
    event_store.load_event({"id": 5})
    event_store.__next__()
    event_store.clear_event_store()
    assert len(event_store.events) == 0
    assert event_store.next_event_index == 0
    assert event_store.last_processed_event is None


def test_event_store_iter_expect_success():
    event_store = EventStore()
    event_store.load_event({"id": 5})
    for event in event_store:
        assert event["id"] == 5

    assert event_store.last_processed_event is None
    assert event_store.next_event_index == 1