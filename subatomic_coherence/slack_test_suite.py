import json
import logging
import traceback

from colorama import Fore, Style

import subatomic_coherence.ui.ui as UI
from subatomic_coherence.logging.console_logging import ConsoleLogger
from subatomic_coherence.testing.test import ResultCode
from subatomic_coherence.ui.ui import TestStatus
from subatomic_coherence.ui.ui import TestingStage
from subatomic_coherence.user.slack_user import SlackUser
from subatomic_coherence.user.slack_user_workspace import SlackUserWorkspace


class SlackTestSuite(object):
    def __init__(self, description="Test Suite", log_file=None, log_level=logging.INFO, listen_after_tests=False,
                 interactive=False):
        self.description = description
        self.slack_user_workspace = SlackUserWorkspace()
        self.tests = []
        self._full_test_list = []
        self.total_tests = 0
        self.successful_tests = []
        self.failed_tests = []
        self.new_events = False
        self.log_file = log_file
        self._set_log_file(log_file, log_level)
        self.listen_after_tests = listen_after_tests
        self.is_listening = False
        self.recorded_events = []
        self.interactive = interactive
        self.test_status = TestStatus(self)
        ConsoleLogger.interactive_mode = self.interactive
        if not self.interactive:
            self.test_status.current_operation = TestingStage.run_tests
        self.current_recording = False
        self.screen = None

    def run_tests(self):
        ConsoleLogger.info(f"Running subatomic_coherence test suite: {self.description}")
        if not self._connect_clients():
            exit(1)
        run_tests = len(self.tests) > 0
        while run_tests:
            if len(self.tests) > 0 and self.test_status.break_at_test == self.tests[0].name:
                self.test_status.current_operation = TestingStage.idle

            self._read_slack_events(self.test_status.is_recording)

            if self.test_status.current_operation in [TestingStage.run_tests, TestingStage.run_one_test]:
                test_completed = self._process_current_test()
                if test_completed and self.test_status.current_operation == TestingStage.run_one_test:
                    self.test_status.current_operation = TestingStage.idle

            self._clear_event_stores()

            self._update_test_status()

            run_tests = not self.test_status.current_operation == TestingStage.quit
            if self.interactive:
                UI.update_screen(self._get_screen(), self.test_status)

        self._run_clean_up()
        self._log_recorded_events()

    def add_slack_user(self, username, token, connection_timeout=None):
        self.slack_user_workspace.add_slack_user_client(SlackUser(username, token, connection_timeout))

    def add_test(self, test_name, new_test):
        new_test.name = test_name
        self.tests.append(new_test)
        self._full_test_list.append(new_test)
        self.total_tests += 1

    def _connect_clients(self):
        for slack_user in self.slack_user_workspace.slack_user_clients:
            if not slack_user.connect():
                logging.error("{user} slack client failed to connect".format(user=slack_user.username))
                return False

        self._configure_workspace()

        for slack_user in self.slack_user_workspace.slack_user_clients:
            if not slack_user.link_user_details(self.slack_user_workspace.workspace_user_details):
                return False

            if slack_user.query_workspace_domain() is None:
                return False

        return True

    def _read_slack_events(self, record_events):
        self.new_events = False
        for slack_user in self.slack_user_workspace.slack_user_clients:
            events = slack_user.client.rtm_read()
            for event in events:
                if record_events:
                    self.recorded_events.append(RecordedEvent(slack_user.username, event))
                slack_user.load_events(event)
                logging.info("User {user} received event {event}"
                             .format(user=slack_user.username, event=json.dumps(event)))
                if event["type"] == "channel_created":
                    self.slack_user_workspace.workspace_channels.append(event["channel"])
                self.new_events = True

    def _update_test_status(self):
        if len(self.tests) == 0:
            self.test_status.next_test = "None"
            if self.interactive and self.test_status.current_operation == TestingStage.run_tests:
                self.test_status.current_operation = TestingStage.idle
            elif not self.interactive:
                self.test_status.current_operation = TestingStage.quit
        else:
            self.test_status.next_test = self.tests[0].name

    def _process_current_test(self):
        test_completed = False
        if len(self.tests) > 0:
            current_test = self.tests[0]
            if self.new_events:
                logging.info("Processing new events")
            result = current_test.test(self.slack_user_workspace)
            if not current_test.is_live:
                if result.result_code == ResultCode.success:
                    self.successful_tests += [current_test]
                    ConsoleLogger.success(f"Test passed: { current_test.name}")
                else:
                    self.failed_tests += [current_test]
                    message = f"{Fore.RED}Test failed: {Fore.LIGHTRED_EX}{current_test.name}" \
                              f"\n{Fore.RED}Action Stack: {Fore.YELLOW}{result.call_stack}" \
                              f"\n{Fore.RED}Result Message: {Fore.YELLOW}{result.message}{Style.RESET_ALL}"
                    ConsoleLogger.log(message)
                self.tests = self.tests[1:]
                test_completed = True

            if len(self.tests) == 0:
                total_tests = str(len(self.successful_tests) + len(self.failed_tests))

                summary = f"\n\n{Fore.MAGENTA}Test Summary:\n" \
                          f"{Fore.GREEN}{str(len(self.successful_tests))}/{total_tests} " \
                          f"tests passed\n{Style.RESET_ALL}"
                for test in self.successful_tests:
                    summary += f"{Fore.GREEN}Test passed: {test.name}{Style.RESET_ALL}\n"

                summary += f"\n{Fore.RED}{str(len(self.failed_tests))}/{total_tests} tests failed\n"
                for test in self.failed_tests:
                    summary += f"{Fore.RED}Test failed: {Fore.LIGHTRED_EX}{test.name}\n" \
                               f"{Fore.RED}Action Stack: {Fore.YELLOW}{test.call_stack_message}\n" \
                               f"{Fore.RED}Result Message: {Fore.YELLOW}{test.message}\n\n{Style.RESET_ALL}"

                ConsoleLogger.log(summary)
        return test_completed

    def _clear_event_stores(self):
        for slack_user in self.slack_user_workspace.slack_user_clients:
            slack_user.clear_event_store()

    def clear_recorded_events(self):
        self.recorded_events = []

    def _configure_workspace(self):
        self.slack_user_workspace.set_workspace_user_details(
            self.slack_user_workspace.slack_user_clients[0].query_workspace_user_details())
        self.slack_user_workspace.set_workspace_channels(
            self.slack_user_workspace.slack_user_clients[0].query_workspace_channels())
        self.slack_user_workspace.set_workspace_groups(
            self.slack_user_workspace.slack_user_clients[0].query_workspace_groups())

    def _set_log_file(self, log_file, log_level):
        if log_file is not None:
            logger = logging.getLogger()
            logger.setLevel(log_level)

            # create a file handler
            handler = logging.FileHandler(log_file)
            handler.setLevel(log_level)

            # create a logging format
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)

            # add the handlers to the logger
            logger.addHandler(handler)

    def _get_screen(self):
        if self.interactive and self.screen is None:
            self.screen = UI.initialise(self.test_status)
        return self.screen

    def _log_recorded_events(self):
        if len(self.recorded_events) > 0:
            ConsoleLogger.interactive_mode = False
            ConsoleLogger.success("The following events were successfully recorded (ordered by timestamp):")
            self.recorded_events = sorted(self.recorded_events, key=lambda entry: entry.time_stamp)
            ConsoleLogger.info("[")
            for event in self.recorded_events:
                comma = ","
                if event == self.recorded_events[-1]:
                    comma = ""
                ConsoleLogger.info(event.json() + comma)
            ConsoleLogger.info("]")

    def _run_clean_up(self):
        for test in self._full_test_list:
            ConsoleLogger.info(f"Running clean up for test: {test.name}")
            # noinspection PyBroadException
            try:
                test.tidy(self.slack_user_workspace)
            except:
                error_stack_trace = traceback.format_exc()
                ConsoleLogger.info("Clean up error ignored: " + error_stack_trace)


class RecordedEvent(object):
    def __init__(self, client_name, event):
        self.coherence_slack_client_name = client_name
        self.event = event
        self.time_stamp = ""
        if "event_ts" in event:
            self.time_stamp = event["event_ts"]
        elif "ts" in event:
            self.time_stamp = event["ts"]

    def json(self):
        return json.dumps({"CoherenceSlackClient": self.coherence_slack_client_name, "SlackEvent": self.event},
                          indent=4)
