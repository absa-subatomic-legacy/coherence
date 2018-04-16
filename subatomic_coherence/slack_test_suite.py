import logging
import json
from colorama import Fore, Style

from subatomic_coherence.logging.console_logging import ConsoleLogger
from subatomic_coherence.testing.test import ResultCode
from subatomic_coherence.user.slack_user import SlackUser
from subatomic_coherence.user.slack_user_workspace import SlackUserWorkspace


class SlackTestSuite(object):
    def __init__(self, description="Test Suite", log_file=None, log_level=logging.INFO, listen_after_tests=False):
        self.description = description
        self.slack_user_workspace = SlackUserWorkspace()
        self.tests = []
        self.successful_tests = []
        self.failed_tests = []
        self.new_events = False
        self.log_file = log_file
        self._set_log_file(log_file, log_level)
        self.listen_after_tests = listen_after_tests
        self.is_listening = False

    def run_tests(self):
        ConsoleLogger.info(f"Running subatomic_coherence test suite: {self.description}")
        if not self._connect_clients():
            exit(1)
        run_tests = len(self.tests) > 0
        while run_tests or self.listen_after_tests:
            self._read_slack_events()
            self._process_current_test()
            self._clear_event_stores()
            run_tests = len(self.tests) > 0
            if not run_tests and not self.is_listening and self.listen_after_tests:
                ConsoleLogger.info("Coherence is now listening and logging the event stream.")
                self.is_listening = True

    def add_slack_user(self, username, token, connection_timeout=None):
        self.slack_user_workspace.add_slack_user_client(SlackUser(username, token, connection_timeout))

    def add_test(self, test_name, new_test):
        new_test.name = test_name
        self.tests.append(new_test)

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

    def _read_slack_events(self):
        self.new_events = False
        for slack_user in self.slack_user_workspace.slack_user_clients:
            events = slack_user.client.rtm_read()
            for event in events:
                slack_user.load_events(event)
                logging.info("User {user} received event {event}"
                             .format(user=slack_user.username, event=json.dumps(event)))
                if event["type"] == "channel_created":
                    self.slack_user_workspace.workspace_channels.append(event["channel"])
                self.new_events = True

    def _process_current_test(self):
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

    def _clear_event_stores(self):
        for slack_user in self.slack_user_workspace.slack_user_clients:
            slack_user.clear_event_store()

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
