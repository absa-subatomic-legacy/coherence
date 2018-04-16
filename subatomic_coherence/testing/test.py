import json
import time
from enum import Enum
import traceback

from subatomic_coherence.logging.console_logging import ConsoleLogger


class TestElement(object):
    def __init__(self, run_element, timeout=15000):
        self.test_stage = ResultCode.pending
        self.timeout = timeout
        self.next_action = lambda slack_user_workspace, data_store: TestResult(ResultCode.success, "SUCCESS")
        self.run_element = run_element
        self.has_child = False
        self.start_time = 0
        self.is_started = False
        self.call_stack_message = ""

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


class TestPortal(TestElement):
    def __init__(self, timeout=15000):
        super().__init__(self.start_test, timeout)
        self.current_action = self
        self.is_live = True
        self.message = ResultCode.pending.name
        self.name = "Unnamed Test"
        self.data_store = {}
        self.simple_call_stack = []

    def test(self, slack_users):
        # noinspection PyBroadException
        try:
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
                    self.call_stack_message = self._build_simple_stack_message()
                elif result.result_code is ResultCode.success and isinstance(self.current_action, TestElement) \
                        and self.current_action.has_child:
                    last_processed_event = slack_users.last_processed_event()
                    if last_processed_event is not None and len(self.simple_call_stack) > 0:
                        self.simple_call_stack[-1].accepted_event = last_processed_event
                    self.current_action = self.current_action.next_action
                    self._push_action_onto_stack(self.current_action)
                elif result.result_code is ResultCode.success:
                    self.test_stage = ResultCode.success
                    self.is_live = False
                    self.message = result.message
                    self.call_stack_message = self._build_simple_stack_message()
            return TestResult(self.test_stage, self.message, self.call_stack_message)
        except:
            error_stack_trace = traceback.format_exc()
            self.is_live = False
            self.test_stage = ResultCode.failure
            self.message = f"{error_stack_trace}"
            self.call_stack_message = self._build_simple_stack_message()
            return TestResult(self.test_stage, self.message, self.call_stack_message)

    def start_test(self, slack_user_workspace, data_store):
        ConsoleLogger.success(f"Running Test: {self.name}")
        return TestResult(ResultCode.success)

    def _push_action_onto_stack(self, current_action):
        self.simple_call_stack += [CallStackAction(current_action.run_element.__name__)]

    def _build_simple_stack_message(self):
        message = self.name
        for call in self.simple_call_stack:
            message += "\n.then(" + call.name + ")"
            if call.accepted_event is not None:
                message += f" - {json.dumps(call.accepted_event)}"
        return message


class CallStackAction(object):
    def __init__(self, name):
        self.name = name
        self.accepted_event = None


class TestResult(object):
    def __init__(self, result_code, message="", call_stack=""):
        self.result = result_code.name
        self.result_code = result_code
        self.message = message
        self.call_stack = call_stack


class ResultCode(Enum):
    pending = 0
    success = 1
    failure = 2
