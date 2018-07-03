from enum import Enum

from subatomic_coherence.testing.test import TestResult, ResultCode


def expect_event(user, event_template):
    def expect_event_function(slack_user_workspace, data_store):
        user_client = slack_user_workspace.find_user_client_by_username(user)
        event_verifier = EventVerifier(event_template)
        for event in user_client.events:
            if event_verifier.verify(event):
                return TestResult(ResultCode.success)
        return TestResult(ResultCode.pending)

    return expect_event_function


class EventVerifier(object):
    def __init__(self, event_template):
        self.event_template = event_template
        self.stored_values = {}
        self.event_pattern_context = EventPatternContext()
        self.parse_template(self.event_template)

    def verify(self, event):
        self.stored_values = {}
        return self.verify_property(self.event_template, event)

    def verify_dict_property(self, base_property, event_property, property_name, depth):
        self.event_pattern_context.reset_groups(depth)
        if isinstance(event_property, dict) and property_name in event_property:
            return self.verify_property(base_property[property_name], event_property[property_name], depth + 1)
        return False

    def verify_list_property(self, base_property, event_property, depth):
        self.event_pattern_context.reset_groups(depth)
        verified = False
        if isinstance(event_property, list):
            for event_entry in event_property:
                verified |= self.verify_property(base_property, event_entry, depth + 1)
        return verified

    def verify_property(self, base_property, event_property, depth=0):
        self.event_pattern_context.reset_groups(depth)
        if isinstance(base_property, dict):
            verified = True
            for sub_property in base_property:
                verified &= self.verify_dict_property(base_property, event_property, sub_property, depth + 1)
            return verified
        elif isinstance(base_property, list):
            verified = True
            for base_entry in base_property:
                verified &= self.verify_list_property(base_entry, event_property, depth + 1)
            return verified
        elif isinstance(base_property, EventPattern):
            if base_property.match(event_property):
                self.event_pattern_context.store_result(base_property, self.stored_values)
                return True
            return False
        else:
            cleaned_base_property = self.clean_value(base_property)
            if cleaned_base_property == "*":
                result = True
            else:
                result = cleaned_base_property == event_property
            if result:
                self.try_store_requested_value(base_property, event_property)
            return result

    def try_store_requested_value(self, base_property, event_value):
        if base_property.startswith("{{") and base_property.endswith("}}"):
            name = base_property[2: base_property.index(",")]
            self.stored_values[name] = event_value

    def clean_value(self, value):
        if value.startswith("\\"):
            return value[1:]
        if value.startswith("{{") and value.endswith("}}"):
            return value[value.index(",") + 1:-2]

        return value

    def parse_template(self, next_property, property_stack=None):
        if property_stack is None:
            property_stack = ["base"]
        if isinstance(next_property, dict):
            for sub_property in next_property:
                self.parse_template(next_property[sub_property], property_stack + [sub_property])
        elif isinstance(next_property, list):
            for entry in next_property:
                self.parse_template(entry, property_stack + [property_stack[-1] + "[]"])
        elif isinstance(next_property, EventPattern):
            next_property.property_stack = property_stack
            self.event_pattern_context.add_event_pattern(next_property)


class EventPatternContext(object):
    def __init__(self):
        self.event_pattern_groups = {}
        self.event_patterns = []

    def add_event_pattern(self, event_pattern):
        self.event_patterns += [event_pattern]
        if event_pattern.group_id is not None:
            if event_pattern.group_id not in self.event_pattern_groups:
                self.event_pattern_groups[event_pattern.group_id] = EventPatternGroup(event_pattern.group_id)

            self.event_pattern_groups[event_pattern.group_id].add_event_pattern(event_pattern)

    def reset_groups(self, depth):
        for key in self.event_pattern_groups:
            self.event_pattern_groups[key].reset_if_necessary(depth)

    def store_result(self, event_pattern, value_store):
        if event_pattern.group_id in self.event_pattern_groups:
            self.event_pattern_groups[event_pattern.group_id].store_values(value_store)
        else:
            event_pattern.store_value(value_store)


class EventPatternGroup(object):
    def __init__(self, group_id):
        self.group_id = group_id
        self.event_patterns = []
        self.reset_depth = 0

    def add_event_pattern(self, event_pattern):
        self.event_patterns += [event_pattern]
        self.calculate_depth()

    def calculate_depth(self):
        reference_property_stack = self.event_patterns[0].property_stack
        for property_index in range(0, len(reference_property_stack)):
            for pattern in self.event_patterns:
                if len(pattern.property_stack) <= property_index or not pattern.property_stack[property_index] == \
                        reference_property_stack[property_index]:
                    self.reset_depth = property_index - 1
                    return

        self.reset_depth = -1

    def reset_if_necessary(self, depth):
        if depth == self.reset_depth:
            for event_pattern in self.event_patterns:
                event_pattern.matched = False

    def is_fully_matched(self):
        fully_matched = True
        for pattern in self.event_patterns:
            if not pattern.matched:
                fully_matched = False
                break
        return fully_matched

    def store_values(self, value_store):
        if self.is_fully_matched():
            for pattern in self.event_patterns:
                pattern.store_value(value_store)


class EventPattern(object):
    def __init__(self, storage_name=None, group_id=None):
        self.group_id = group_id
        self.matched = False
        self.matched_value = None
        self.storage_name = storage_name
        self.property_stack = []

    def match(self, value):
        matched_value = self.match_implementation(value)
        if matched_value:
            self.matched = True
            self.matched_value = value
        elif self.group_id is None:
            self.matched = False
        # dont set matched to false for groups unless reset is called
        return self.matched

    def match_implementation(self, value):
        return NotImplementedError()

    def store_value(self, value_store):
        if self.storage_name is not None and self.matched:
            value_store[self.storage_name] = self.matched_value


class WildCardEventPattern(EventPattern):
    def __init__(self, storage_name=None, group_id=None):
        super().__init__(storage_name, group_id)

    def match_implementation(self, value):
        return True


class SimpleEventPattern(EventPattern):
    def __init__(self, expected_value, storage_name=None, group_id=None):
        super().__init__(storage_name, group_id)
        self.expected_value = expected_value

    def match_implementation(self, value):
        return self.expected_value == value
