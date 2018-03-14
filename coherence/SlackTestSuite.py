import logging

from coherence.user.SlackUser import SlackUser
from coherence.user.SlackUserLedger import SlackUserLedger


class SlackTestSuite(object):
    def __init__(self, description="Test Suite"):
        self.description = description
        self.slack_user_ledger = SlackUserLedger()
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
        self.slack_user_ledger.add_slack_user_client(SlackUser(username, token))

    def add_test(self, new_test):
        self.tests.append(new_test)

    def _connect_clients(self):
        for slack_user in self.slack_user_ledger.slack_user_clients:
            if not slack_user.connect():
                logging.error("{user} slack client failed to connect".format(user=slack_user.name))
                exit(1)
        self.slack_user_ledger.set_slack_user_list(self.slack_user_ledger.slack_user_clients[0].query_user_list())
        for slack_user in self.slack_user_ledger.slack_user_clients:
            slack_user.link_user_details(self.slack_user_ledger.slack_user_list)

    def _read_slack_events(self):
        self.new_events = False
        for slack_user in self.slack_user_ledger.slack_user_clients:
            events = slack_user.client.rtm_read()
            for event in events:
                slack_user.events.append(event)
                logging.debug("User {user} received event {event}".format(user=slack_user.username, event=event))
                self.new_events = True

    def _process_current_test(self):
        if len(self.tests) > 0:
            current_test = self.tests[0]
            if self.new_events:
                logging.debug("Processing new events")
            result = current_test.test(self.slack_user_ledger)
            if not current_test.is_live:
                if result.result_code == 1:
                    self.successful_tests += [current_test]
                    logging.info(
                        "Test passed: {name}".format(name=current_test.name))
                else:
                    self.failed_tests += [current_test]
                    logging.info(
                        "Test failed: {name} - {message}".format(name=current_test.name, message=result.message))
                self.tests = self.tests[1:]

    def _clear_event_stores(self):
        for slack_user in self.slack_user_ledger.slack_user_clients:
            slack_user.events = []
