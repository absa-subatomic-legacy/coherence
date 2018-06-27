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

    def verify(self, event):
        self.stored_values = {}
        return self.verify_property(self.event_template, event)

    def verify_dict_property(self, base_property, event_property, property_name):
        if isinstance(event_property, dict) and property_name in event_property:
            return self.verify_property(base_property[property_name], event_property[property_name])
        return False

    def verify_list_property(self, base_property, event_property):
        verified = False
        if isinstance(event_property, list):
            for event_entry in event_property:
                verified |= self.verify_property(base_property, event_entry)
        return verified

    def verify_property(self, base_property, event_property):
        if isinstance(base_property, dict):
            verified = True
            for sub_property in base_property:
                verified &= self.verify_dict_property(base_property, event_property, sub_property)
            return verified
        elif isinstance(base_property, list):
            verified = True
            for base_entry in base_property:
                verified &= self.verify_list_property(base_entry, event_property)
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
