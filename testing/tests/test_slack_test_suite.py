from unittest.mock import MagicMock

from subatomic_coherence.logging.console_logging import ConsoleLogger
from subatomic_coherence.slack_test_suite import SlackTestSuite, RecordedEvent
from subatomic_coherence.testing.test import TestPortal, TestResult, ResultCode
from subatomic_coherence.ui.ui import TestingStage


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
    test_suite._read_slack_events(False)
    assert test_suite.new_events is True
    assert user.events.events[-1] == event


def test_client_read_channel_created_event_expect_channel_details_added_to_slack_workspace():
    test_suite = SlackTestSuite()
    test_suite.add_slack_user("user", "token")
    user = test_suite.slack_user_workspace.find_user_client_by_username("user")
    event = {"type": "channel_created",
             "channel": {"id": "C024BE91L", "name": "fun", "created": 1360782804, "creator": "U024BE7LH"}}
    user.client.rtm_read = MagicMock(return_value=[event])
    test_suite._read_slack_events(False)
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


def test_log_recorded_events_expect_printed_log_buffer():
    # clear the buffer
    ConsoleLogger.read_buffered_log()
    test_suite = SlackTestSuite()
    event = RecordedEvent("client", {"name": "test", "ts": "1"})
    test_suite.recorded_events.append(event)
    test_suite._log_recorded_events()

    log_buffer = ConsoleLogger.read_buffered_log()
    assert '"name": "test"' in log_buffer[-5]
    assert '"ts": "1"' in log_buffer[-4]


def test_log_recorded_multiple_events_expect_sorted_by_time_stamp():
    # clear the buffer
    ConsoleLogger.read_buffered_log()
    test_suite = SlackTestSuite()
    event1 = RecordedEvent("client", {"name": "test", "ts": "1"})
    event2 = RecordedEvent("client", {"name": "test", "event_ts": "2"})
    test_suite.recorded_events.append(event2)
    test_suite.recorded_events.append(event1)
    test_suite._log_recorded_events()
    assert test_suite.recorded_events[0] == event1
    assert test_suite.recorded_events[1] == event2


def test_update_test_status_with_no_tests_interactive_mode_expect_test_status_idle():
    test_suite = SlackTestSuite()
    test_suite.interactive = True
    test_suite.test_status.current_operation = TestingStage.run_tests
    test_suite._update_test_status()
    assert test_suite.test_status.current_operation == TestingStage.idle


def test_update_test_status_with_no_tests_normal_mode_expect_test_status_quit():
    test_suite = SlackTestSuite()
    test_suite.test_status.current_operation = TestingStage.run_tests
    test_suite._update_test_status()
    assert test_suite.test_status.current_operation == TestingStage.quit


def test_process_current_test_expect_test_passes():
    test_suite = SlackTestSuite()
    some_var = 0

    def clean_up(workspace):
        nonlocal some_var
        some_var = 2

    test = TestPortal().set_clean_up(clean_up)
    test_suite.add_test("test", test)
    test_suite._run_clean_up()
    assert some_var == 2
