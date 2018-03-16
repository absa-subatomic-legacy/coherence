import logging
import json
from colorama import Fore, Style

from coherence.user.SlackUser import SlackUser
from coherence.user.SlackUserWorkspace import SlackUserWorkspace


class SlackTestSuite(object):
    def __init__(self, description="Test Suite"):
        self.description = description
        self.slack_user_workspace = SlackUserWorkspace()
        self.tests = []
        self.successful_tests = []
        self.failed_tests = []
        self.new_events = False

    def run_tests(self):
        self._connect_clients()
        run_tests = len(self.tests) > 0
        listening = True
        while run_tests or listening:
            self._read_slack_events()
            self._process_current_test()
            self._clear_event_stores()
            run_tests = len(self.tests) > 0

    def add_slack_user(self, username, token):
        self.slack_user_workspace.add_slack_user_client(SlackUser(username, token))

    def add_test(self, new_test):
        self.tests.append(new_test)

    def _connect_clients(self):
        for slack_user in self.slack_user_workspace.slack_user_clients:
            if not slack_user.connect():
                logging.error("{user} slack client failed to connect".format(user=slack_user.name))
                exit(1)

        self._configure_workspace()

        for slack_user in self.slack_user_workspace.slack_user_clients:
            slack_user.link_user_details(self.slack_user_workspace.workspace_user_details)

    def _read_slack_events(self):
        self.new_events = False
        for slack_user in self.slack_user_workspace.slack_user_clients:
            events = slack_user.client.rtm_read()
            for event in events:
                slack_user.events.append(event)
                logging.debug("User {user} received event {event}"
                              .format(user=slack_user.username, event=json.dumps(event)))
                if event["type"] == "channel_created":
                    self.slack_user_workspace.workspace_channels.append(event["channel"])
                self.new_events = True

    def _process_current_test(self):
        if len(self.tests) > 0:
            current_test = self.tests[0]
            if self.new_events:
                logging.debug("Processing new events")
            result = current_test.test(self.slack_user_workspace)
            if not current_test.is_live:
                if result.result_code == 1:
                    self.successful_tests += [current_test]
                    print(f"{Fore.GREEN}Test passed: { current_test.name}{Style.RESET_ALL}")
                else:
                    self.failed_tests += [current_test]

                    print(f"{Fore.LIGHTRED_EX}Test failed: {current_test.name} - {result.message}{Style.RESET_ALL}")
                self.tests = self.tests[1:]

            if len(self.tests) == 0:
                total_tests = str(len(self.successful_tests) + len(self.failed_tests))

                summary = f"\n\n{Fore.GREEN}{str(len(self.successful_tests))}/{total_tests} " \
                          f"tests passed\n{Style.RESET_ALL}"
                for test in self.successful_tests:
                    summary += f"{Fore.GREEN}Test passed: {test.name}{Style.RESET_ALL}\n"

                summary += f"\n{Fore.LIGHTRED_EX}{str(len(self.failed_tests))}/{total_tests} tests failed"
                for test in self.failed_tests:
                    summary += f"{Fore.LIGHTRED_EX}Test failed: {test.name} - {result.message}{Style.RESET_ALL}\n"

                print(summary)

    def _clear_event_stores(self):
        for slack_user in self.slack_user_workspace.slack_user_clients:
            slack_user.events = []

    def _configure_workspace(self):
        self.slack_user_workspace.set_workspace_domain(
            self.slack_user_workspace.slack_user_clients[0].query_workspace_domain())
        self.slack_user_workspace.set_workspace_user_details(
            self.slack_user_workspace.slack_user_clients[0].query_workspace_user_details())
        self.slack_user_workspace.set_workspace_channels(
            self.slack_user_workspace.slack_user_clients[0].query_workspace_channels())
        self.slack_user_workspace.set_workspace_groups(
            self.slack_user_workspace.slack_user_clients[0].query_workspace_groups())
