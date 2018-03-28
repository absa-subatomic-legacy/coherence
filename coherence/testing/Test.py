import time
from enum import Enum


class TestElement(object):
    def __init__(self, run_element, timeout=15000):
        self.test_stage = ResultCode.pending
        self.timeout = timeout
        self.next_action = lambda slack_users: TestResult(1, "SUCCESS")
        self.run_element = run_element
        self.has_child = False
        self.start_time = 0
        self.is_started = False

    def then(self, next_action, timeout=15000):
        found_leaf_then = False
        current_element = self
        while not found_leaf_then:
            if not current_element.has_child:
                current_element.next_action = TestElement(next_action, timeout)
                current_element.has_child = True
                found_leaf_then = True
            else:
                current_element = current_element.next_action

        return self


class TestEntry(TestElement):
    def __init__(self, name, timeout=15000):
        super().__init__(self.run, timeout)
        self.current_action = self
        self.is_live = True
        self.message = ResultCode.pending.name
        self.name = name
        self.data_store = {}

    def test(self, slack_users):
        if self.is_live:
            current_time = int(round(time.time() * 1000))
            if not self.current_action.is_started:
                self.current_action.is_started = True
                self.current_action.start_time = current_time
            if current_time - self.current_action.start_time > self.current_action.timeout:
                self.current_action.test_stage = ResultCode.failure
                result = TestResult(ResultCode.failure, "Time out occurred when calling {function_name}"
                                    .format(function_name=self.current_action.run_element.__name__))
            else:
                result = self.current_action.run_element(slack_users, self.data_store)
            if result.result_code is ResultCode.failure:
                self.test_stage = ResultCode.failure
                self.is_live = False
                self.message = result.message
            elif result.result_code is ResultCode.success and isinstance(self.current_action, TestElement) \
                    and self.current_action.has_child:
                self.current_action = self.current_action.next_action
            elif result.result_code is ResultCode.success:
                self.test_stage = ResultCode.success
                self.is_live = False
                self.message = result.message
        return TestResult(self.test_stage, self.message)

    def run(self, slack_user_workspace, data_store):
        return TestResult(self.test_stage)


class TestResult(object):
    def __init__(self, result_code, message=""):
        self.result = result_code.name
        self.result_code = result_code
        self.message = message


class ResultCode(Enum):
    pending = 0
    success = 1
    failure = 2
