from subatomic_coherence.testing.test import TestResult, ResultCode


def expect_event(user, event_template):
    def expect_event_function(slack_user_workspace, data_store):
        user_client = slack_user_workspace.find_user_client_by_username(user)
        event_verifier = EventVerifier(event_template)
        for event in user_client.events:
            if event_verifier.verify(event):
                for key in event_verifier.stored_values:
                    data_store[key] = event_verifier.stored_values[key]
                return TestResult(ResultCode.success)
        return TestResult(ResultCode.pending)

    return expect_event_function


class EventVerifier(object):
    """
    The EventVerifier class operates on some complicated logic and deserves a small write up to help future developers
    understand the functionality. The core idea is that we want to be able to define a template, and verify whether or
    not an event (or any data structure really) matches this template. We may also want to store some of the data from
    the matched event.

    For a basic example, start by defining a template. The template is only made of basic types: scalars, lists, and
    dictionaries, the root type is always a dictionary. Now given some data structure, begin by looping over the
    properties of the template. (verify_dict_property)
        - If the property maps to a scalar see if there is a value in the event in the current level
        (e.g. root property initially) that matches the scalar. (fall through condition in verify_property)
        - If the property maps to a list, see if there is a value in the event in the current level that is also a list
            - If yes: loop through the template list entries and perform this list of checks against the event list
            (verify_list_property)
        - If the property maps to a dict, see if there is a value in the event in the current level that in also a dict
            - Perform this same set of checks against the event dictionary (verify_dict_property)

    The implementation is done recursively, so essentially the algorithm keeps pulling out sub properties and from the
    template and comparing them to matching sub properties in the event.

    A more complicated example now comes in when we want to match/store values by groups in different sub properties.
    E.g. only store the value if a dict property with: a scalar child property matching the event, and a dict child
    property, which itself has a child list property with a scalar that matches the event. EventPattern groups are
    introduced to handle these cases. These store lists of pattern matchers in the template and overall the group will
    only be considered matched if all the pattern matchers in this group are matched successfully. In order to build
    these event groups, the template now needs to be initially parsed, during which, any EventPattern's with the
    same group_id will be added to an EventPatternGroup. Additionally, we need to ensure that we are not doing partial
    matching. I.e. The property matching template tree must only match properties for a single parent. If the recursive
    matching matches the parent and some sub properties, then, later in a different sub structure again matches the
    parent but now matches the other half od the sub properties, this could be marked as a successful group match even
    though no single property tree matched the template. In order to prevent this, the groups need to be reset to
    nothing within them being matched if the encapsulating property tree is exited. To handle this we introduce the
    EventPatternContext which manages all the group status's along with introducing a depth concept for a group. The
    depth concept is finding the recursive level of the common ancestor of all properties within a group. If the
    recursive level is ever smaller than the groups depth level, the EventPatternContext will mark all the
    EventPatternGroup EventPatterns as not matched. This will prevent the partial matching described earlier.

    This covers the basics of how the algorithm works. It still has edges cases that may not fit the spec of what is
    expected but that is really depends on what one would actually expected to happen in such cases which is logically
    ambiguous regardless. Such cases should be handled by fine grained conditional checks as was used before the
    event pattern matching was introduced.
    """

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
        verified = False
        if isinstance(event_property, list):
            self.event_pattern_context.reset_groups(depth)
            for event_entry in event_property:
                verified |= self.verify_property(base_property, event_entry, depth + 1)
        return verified

    def verify_property(self, base_property, event_property, depth=0):
        self.event_pattern_context.reset_groups(depth)
        # This early check allows for ComplexEventPattern to work
        if isinstance(base_property, EventPattern):
            if base_property.match(event_property):
                self.event_pattern_context.store_result(base_property, self.stored_values)
                return True
            return False

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
                event_pattern.reset()

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
                pattern.reset()


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

    def reset(self):
        self.matched = False


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


class ComplexEventPattern(EventPattern):
    def __init__(self, template, storage_name, group_id=None):
        super().__init__(storage_name, group_id)
        self.template = template
        self.event_verifier = EventVerifier(template)

    def match_implementation(self, value):
        matched = self.event_verifier.verify(value)
        if matched:
            self.matched_value = value

        return matched

    def store_value(self, value_store):
        if self.matched:
            value_store[self.storage_name] = self.matched_value
            for key in self.event_verifier.stored_values:
                value_store[key] = self.event_verifier.stored_values[key]

    def reset(self):
        self.matched = False
        self.event_verifier.stored_values = {}
