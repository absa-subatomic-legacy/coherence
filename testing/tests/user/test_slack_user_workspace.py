from subatomic_coherence.user.slack_user import SlackUser
from subatomic_coherence.user.slack_user_workspace import SlackUserWorkspace


def test_find_user_by_username_expect_success():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.set_workspace_user_details([{"name": "user1"}, {"name": "user2"}])
    user = slack_user_workspace.find_user_by_username("user2")
    assert user["name"] == "user2"


def test_find_user_by_username_expect_failure():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.set_workspace_user_details([{"name": "user1"}, {"name": "user2"}])
    user = slack_user_workspace.find_user_by_username("user3")
    assert user is None


def test_find_user_client_by_username_expect_success():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.add_slack_user_client(SlackUser("user", "token"))
    slack_user_workspace.add_slack_user_client(SlackUser("user2", "token"))
    user = slack_user_workspace.find_user_client_by_username("user")
    assert user is not None
    assert user.username is "user"


def test_find_user_client_by_username_expect_failure():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.add_slack_user_client(SlackUser("user", "token"))
    slack_user_workspace.add_slack_user_client(SlackUser("user2", "token"))
    user = slack_user_workspace.find_user_client_by_username("user3")
    assert user is None


def test_find_channel_by_name_expect_success():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.set_workspace_channels([{"name": "channel1"}, {"name": "channel2"}])
    channel = slack_user_workspace.find_channel_by_name("channel2")
    assert channel["name"] == "channel2"


def test_find_channel_by_name_expect_failure():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.set_workspace_channels([{"name": "channel1"}, {"name": "channel2"}])
    channel = slack_user_workspace.find_channel_by_name("channel3")
    assert channel is None


def test_find_channel_by_id_expect_success():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.set_workspace_channels([{"id": "channel1"}, {"id": "channel2"}])
    channel = slack_user_workspace.find_channel_by_slack_id("channel2")
    assert channel["id"] == "channel2"


def test_find_channel_by_id_expect_failure():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.set_workspace_channels([{"id": "channel1"}, {"id": "channel2"}])
    channel = slack_user_workspace.find_channel_by_slack_id("channel3")
    assert channel is None

def test_find_group_by_name_expect_success():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.set_workspace_groups([{"name": "group1"}, {"name": "group2"}])
    group = slack_user_workspace.find_group_by_name("group2")
    assert group["name"] == "group2"


def test_find_group_by_name_expect_failure():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.set_workspace_groups([{"name": "group1"}, {"name": "group2"}])
    group = slack_user_workspace.find_group_by_name("group3")
    assert group is None


def test_find_group_by_id_expect_success():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.set_workspace_groups([{"id": "group1"}, {"id": "group2"}])
    group = slack_user_workspace.find_group_by_slack_id("group2")
    assert group["id"] == "group2"


def test_find_group_by_id_expect_failure():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.set_workspace_groups([{"id": "group1"}, {"id": "group2"}])
    group = slack_user_workspace.find_group_by_slack_id("group3")
    assert group is None


def test_find_group_or_channel_by_name_expect_find_group():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.set_workspace_channels([{"name": "channel1"}, {"name": "channel2"}])
    slack_user_workspace.set_workspace_groups([{"name": "group1"}, {"name": "group2"}])
    result = slack_user_workspace.find_group_or_channel_by_name("group1")
    assert result["name"] == "group1"


def test_find_group_or_channel_by_name_expect_find_channel():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.set_workspace_channels([{"name": "channel1"}, {"name": "channel2"}])
    slack_user_workspace.set_workspace_groups([{"name": "group1"}, {"name": "group2"}])
    result = slack_user_workspace.find_group_or_channel_by_name("channel2")
    assert result["name"] == "channel2"


def test_find_group_or_channel_by_name_expect_failure():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.set_workspace_channels([{"name": "channel1"}, {"name": "channel2"}])
    slack_user_workspace.set_workspace_groups([{"name": "group1"}, {"name": "group2"}])
    result = slack_user_workspace.find_group_or_channel_by_name("channel3")
    assert result is None


def test_find_group_or_channel_by_id_expect_find_group():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.set_workspace_channels([{"id": "channel1"}, {"id": "channel2"}])
    slack_user_workspace.set_workspace_groups([{"id": "group1"}, {"id": "group2"}])
    result = slack_user_workspace.find_group_or_channel_by_slack_id("group1")
    assert result["id"] == "group1"


def test_find_group_or_channel_by_id_expect_find_channel():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.set_workspace_channels([{"id": "channel1"}, {"id": "channel2"}])
    slack_user_workspace.set_workspace_groups([{"id": "group1"}, {"id": "group2"}])
    result = slack_user_workspace.find_group_or_channel_by_slack_id("channel2")
    assert result["id"] == "channel2"


def test_find_group_or_channel_by_id_expect_failure():
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.set_workspace_channels([{"id": "channel1"}, {"id": "channel2"}])
    slack_user_workspace.set_workspace_groups([{"id": "group1"}, {"id": "group2"}])
    result = slack_user_workspace.find_channel_by_slack_id("channel3")
    assert result is None