from unittest.mock import MagicMock

from coherence.SlackTestSuite import SlackTestSuite
from coherence.testing.Test import TestPortal, TestResult, ResultCode


def test_add_slack_test_expect_added_to_test_list():
    test_suite = SlackTestSuite()
    test = TestPortal()
    test_suite.add_test("a_test", test)
    assert test_suite.tests[-1] == test


def test_add_slack_user_expect_added_to_user_list():
    test_suite = SlackTestSuite()
    test_suite.add_slack_user("user", "token")
    assert test_suite.slack_user_workspace.find_user_client_by_username("user") is not None


def test_connect_clients_expect_clients_connected_successfully():
    test_suite = SlackTestSuite()
    test_suite.add_slack_user("user", "token")
    user = test_suite.slack_user_workspace.find_user_client_by_username("user")
    user.connect = MagicMock(return_value=True)
    user.link_user_details = MagicMock()
    user.query_workspace_domain = MagicMock()
    test_suite._configure_workspace = MagicMock()

    assert test_suite._connect_clients() is True


def test_connect_clients_expect_clients_connected_unsuccessfully():
    test_suite = SlackTestSuite()
    test_suite.add_slack_user("user", "token")
    user = test_suite.slack_user_workspace.find_user_client_by_username("user")
    user.connect = MagicMock(return_value=False)
    user.link_user_details = MagicMock(return_value=True)
    test_suite._configure_workspace = MagicMock()

    assert test_suite._connect_clients() is False


def test_client_read_event_expect_events_added_to_event_store_of_client():
    test_suite = SlackTestSuite()
    test_suite.add_slack_user("user", "token")
    user = test_suite.slack_user_workspace.find_user_client_by_username("user")
    user.slack_id = "U22GU28G2"
    event = {"type": "user_typing", "channel": "CF2HDSDC", "user": "U22GU28G2"}
    user.client.rtm_read = MagicMock(return_value=[event])
    test_suite._read_slack_events()
    assert test_suite.new_events is True
    assert user.events[-1] == event


def test_client_read_channel_created_event_expect_channel_details_added_to_slack_workspace():
    test_suite = SlackTestSuite()
    test_suite.add_slack_user("user", "token")
    user = test_suite.slack_user_workspace.find_user_client_by_username("user")
    event = {"type": "channel_created",
             "channel": {"id": "C024BE91L", "name": "fun", "created": 1360782804, "creator": "U024BE7LH"}}
    user.client.rtm_read = MagicMock(return_value=[event])
    test_suite._read_slack_events()
    assert test_suite.new_events is True
    assert test_suite.slack_user_workspace.find_channel_by_slack_id("C024BE91L")["name"] == "fun"


def test_process_current_test_expect_test_passes():
    test_suite = SlackTestSuite()
    test = TestPortal()
    test_suite.add_test("test", test)
    test_suite._process_current_test()
    assert len(test_suite.successful_tests) == 1
    assert test_suite.successful_tests[0] == test


def test_process_current_test_expect_test_fails():
    test_suite = SlackTestSuite()
    test = TestPortal()
    test.run_element = MagicMock(return_value=TestResult(ResultCode.failure))
    test_suite.add_test("test", test)
    test_suite._process_current_test()
    assert len(test_suite.failed_tests) == 1
    assert test_suite.failed_tests[0] == test


def test_process_test_with_child_expect_test_fails():
    test_suite = SlackTestSuite()
    test = TestPortal().then(lambda slack_user_workspace, data_store: TestResult(ResultCode.failure, "FAILURE"))
    test_suite.add_test("test", test)
    test_suite._process_current_test()
    assert len(test_suite.failed_tests) == 0
    assert len(test_suite.successful_tests) == 0
    # two iterations required to process the test fully
    test_suite._process_current_test()
    assert len(test_suite.failed_tests) == 1
    assert test_suite.failed_tests[0] == test
