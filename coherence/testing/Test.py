import time

FAIL_RESULT = 2
SUCCESS_RESULT = 1
PENDING_RESULT = 0
RESULT_CODE_DESCRIPTIONS = ["PENDING", "SUCCESS", "FAILED"]

TESTING_STAGES = ["PENDING", "DO", "EXPECT", "CLEANUP"]


class TestElement(object):
    def __init__(self, run_element, timeout=5000):
        self.test_stage = 0
        self.timeout = timeout
        self.next_action = lambda slack_users: TestResult(1, "SUCCESS")
        self.run_element = run_element
        self.has_child = False
        self.start_time = 0
        self.is_started = False

    def then(self, next_action, timeout=5000):
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
    def __init__(self, name, timeout=5000):
        super().__init__(self.run, timeout)
        self.current_action = self
        self.is_live = True
        self.message = "PENDING"
        self.name = name
        self.data_store = {}

    def test(self, slack_users):
        if self.is_live:
            current_time = int(round(time.time() * 1000))
            if not self.current_action.is_started:
                self.current_action.is_started = True
                self.current_action.start_time = current_time
            if current_time - self.current_action.start_time > self.current_action.timeout:
                self.current_action.test_stage = FAIL_RESULT
                result = TestResult(FAIL_RESULT, "Time out occurred when calling {function_name}"
                                    .format(function_name=self.current_action.run_element.__name__))
            else:
                result = self.current_action.run_element(slack_users, self.data_store)
            if result.result_code is FAIL_RESULT:
                self.test_stage = FAIL_RESULT
                self.is_live = False
                self.message = result.message
            elif result.result_code is SUCCESS_RESULT and isinstance(self.current_action, TestElement) \
                    and self.current_action.has_child:
                self.current_action = self.current_action.next_action
            elif result.result_code is SUCCESS_RESULT:
                self.test_stage = SUCCESS_RESULT
                self.is_live = False
                self.message = result.message
        return TestResult(self.test_stage, self.message)

    def run(self, slack_user_ledger, data_store):
        return TestResult(self.test_stage)


class TestResult(object):
    def __init__(self, result_code, message=""):
        self.result = RESULT_CODE_DESCRIPTIONS[result_code]
        self.result_code = result_code
        self.message = message
