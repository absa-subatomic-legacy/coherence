from unittest.mock import MagicMock

from subatomic_coherence.actions.event_actions import WildCardEventPattern, SimpleEventPattern, EventPatternGroup, \
    EventPatternContext, EventVerifier, expect_event
from subatomic_coherence.testing.test import ResultCode
from subatomic_coherence.user.slack_user import SlackUser
from subatomic_coherence.user.slack_user_workspace import SlackUserWorkspace


def test_wild_card_event_pattern_expect_match():
    event_pattern = WildCardEventPattern()

    event_pattern.match("Whatever")

    assert event_pattern.matched is True
    assert event_pattern.matched_value == "Whatever"


def test_wild_card_event_pattern_expect_matched_value_stored():
    event_pattern = WildCardEventPattern(storage_name="VAL")
    store = {}

    event_pattern.match("Whatever")
    event_pattern.store_value(store)

    assert event_pattern.matched is True
    assert store["VAL"] == "Whatever"


def test_simple_event_pattern_expect_match():
    event_pattern = SimpleEventPattern("Some value")
    event_pattern.match("Some value")

    assert event_pattern.matched is True
    assert event_pattern.matched_value == "Some value"


def test_simple_event_pattern_expect_not_matched():
    event_pattern = SimpleEventPattern("Some value")
    event_pattern.match("Some value 2")

    assert event_pattern.matched is False


def test_simple_event_pattern_expect_value_stored():
    event_pattern = SimpleEventPattern("Some value")
    store = {}
    event_pattern.match("Some value")
    event_pattern.store_value(store)

    assert event_pattern.matched is True
    assert event_pattern.matched_value == "Some value"


def test_event_group_expect_group_created():
    group = EventPatternGroup(1)
    pat1 = SimpleEventPattern("1", group_id=1)
    pat1.property_stack = ["base", "base{}", "1"]
    pat2 = SimpleEventPattern("2", group_id=1)
    pat2.property_stack = ["base", "base{}", "3", "something"]
    group.add_event_pattern(pat1)
    group.add_event_pattern(pat2)

    assert pat1 in group.event_patterns
    assert pat2 in group.event_patterns

    assert group.reset_depth == 1


def test_event_group_expect_group_matched():
    group = EventPatternGroup(1)
    pat1 = SimpleEventPattern("1", group_id=1)
    pat1.property_stack = ["base"]
    pat2 = SimpleEventPattern("2", group_id=1)
    pat2.property_stack = ["base"]
    group.add_event_pattern(pat1)
    group.add_event_pattern(pat2)
    pat1.match("1")
    pat2.match("2")

    assert group.is_fully_matched()


def test_event_group_expect_group_not_matched():
    group = EventPatternGroup(1)
    pat1 = SimpleEventPattern("1", group_id=1)
    pat1.property_stack = ["base"]
    pat2 = SimpleEventPattern("2", group_id=1)
    pat2.property_stack = ["base"]
    group.add_event_pattern(pat1)
    group.add_event_pattern(pat2)
    pat1.match("1")

    assert not group.is_fully_matched()


def test_event_group_expect_reset():
    group = EventPatternGroup(1)
    pat1 = SimpleEventPattern("1", group_id=1)
    pat1.property_stack = ["base", "base{}", "1"]
    pat2 = SimpleEventPattern("2", group_id=1)
    pat2.property_stack = ["base", "base{}", "3", "something"]
    group.add_event_pattern(pat1)
    group.add_event_pattern(pat2)
    pat1.match("1")

    group.reset_if_necessary(1)

    assert not pat1.matched


def test_event_group_expect_not_reset():
    group = EventPatternGroup(1)
    pat1 = SimpleEventPattern("1", group_id=1)
    pat1.property_stack = ["base", "base{}", "1"]
    pat2 = SimpleEventPattern("2", group_id=1)
    pat2.property_stack = ["base", "base{}", "3", "something"]
    group.add_event_pattern(pat1)
    group.add_event_pattern(pat2)
    pat1.match("1")

    group.reset_if_necessary(2)

    assert pat1.matched


def test_event_group_expect_stored_values():
    group = EventPatternGroup(1)
    pat1 = SimpleEventPattern("1", group_id=1, storage_name="VAL")
    pat1.property_stack = ["base"]
    pat2 = SimpleEventPattern("2", group_id=1)
    pat2.property_stack = ["base"]
    group.add_event_pattern(pat1)
    group.add_event_pattern(pat2)
    pat1.match("1")
    pat2.match("2")

    store = {}

    group.store_values(store)

    assert store["VAL"] == "1"


def test_event_group_expect_no_stored_values():
    group = EventPatternGroup(1)
    pat1 = SimpleEventPattern("1", group_id=1, storage_name="VAL")
    pat1.property_stack = ["base"]
    pat2 = SimpleEventPattern("2", group_id=1)
    pat2.property_stack = ["base"]
    group.add_event_pattern(pat1)
    group.add_event_pattern(pat2)
    pat1.match("1")

    store = {}

    group.store_values(store)

    assert "VAL" not in store


def test_event_context_expect_group_created():
    event_context = EventPatternContext()
    pat1 = SimpleEventPattern("1", group_id=1)
    pat1.property_stack = ["base"]
    pat2 = SimpleEventPattern("2", group_id=1)
    pat2.property_stack = ["base"]
    event_context.add_event_pattern(pat1)
    event_context.add_event_pattern(pat2)

    assert event_context.event_pattern_groups[1] is not None


def test_event_context_expect_group_not_created():
    event_context = EventPatternContext()
    pat1 = SimpleEventPattern("1", group_id=None)
    pat1.property_stack = ["base"]
    pat2 = SimpleEventPattern("2", group_id=None)
    pat2.property_stack = ["base"]
    event_context.add_event_pattern(pat1)
    event_context.add_event_pattern(pat2)

    assert len(event_context.event_pattern_groups.keys()) == 0


def test_event_context_expect_necessary_results_stored():
    event_context = EventPatternContext()
    pat1 = SimpleEventPattern("1", group_id=1, storage_name="VAL")
    pat1.property_stack = ["base"]
    pat2 = SimpleEventPattern("2", group_id=1)
    pat2.property_stack = ["base"]
    pat3 = SimpleEventPattern("3", group_id=2, storage_name="VAL2")
    pat3.property_stack = ["base"]
    pat4 = SimpleEventPattern("4", group_id=2)
    pat4.property_stack = ["base"]
    event_context.add_event_pattern(pat1)
    event_context.add_event_pattern(pat2)
    event_context.add_event_pattern(pat3)
    event_context.add_event_pattern(pat4)
    pat1.match("1")
    pat3.match("3")
    pat4.match("4")

    store = {}

    event_context.store_result(pat1, store)
    event_context.store_result(pat4, store)

    assert store["VAL2"] == "3"
    assert "VAL" not in store


def test_event_context_expect_group_reset():
    event_context = EventPatternContext()
    pat1 = SimpleEventPattern("1", group_id=1)
    pat1.property_stack = ["base"]
    pat2 = SimpleEventPattern("2", group_id=1)
    pat2.property_stack = ["base"]
    event_context.add_event_pattern(pat1)
    event_context.add_event_pattern(pat2)
    pat1.match("1")

    event_context.reset_groups(-1)

    assert not pat1.matched


def test_event_verifier_expect_double_slash_value_cleaned():
    verifier = EventVerifier({})
    result = verifier.clean_value("\\\\Something")
    assert result == "\\Something"


def test_event_verifier_expect_bracketed_value_cleaned():
    verifier = EventVerifier({})
    result = verifier.clean_value("{{name,value}}")
    assert result == "value"


def test_event_verifier_expect_normal_value_not_cleaned():
    verifier = EventVerifier({})
    result = verifier.clean_value("value")
    assert result == "value"


def test_event_verifier_expect_template_parsed():
    verifier = EventVerifier({
        "name": "Kieran",
        "store": "{{store,*}}",
        "list": [
            {
                "3": "*",
                "4": "{{FOUR,*}}",
                "5": SimpleEventPattern("This value", "Value2", 1),
                "6": SimpleEventPattern("2", "Value2", 1)
            },
            {
                "6": SimpleEventPattern("3", "Value5")
            }
        ],
        "event_pattern": WildCardEventPattern("Value", 1)
    })

    assert verifier.event_pattern_context.event_pattern_groups[1] is not None
    assert verifier.event_pattern_context.event_pattern_groups[1].reset_depth == 0
    assert len(verifier.event_pattern_context.event_patterns) == 4


def test_event_verifier_expect_built_in_match_and_store():
    verifier = EventVerifier({
        "name": "Kieran",
        "store": "{{store,*}}",
        "dont_store": "*"
    })

    result = verifier.verify({
        "name": "Kieran",
        "store": "1",
        "dont_store": "something"
    })

    assert result
    assert verifier.stored_values["store"] == "1"


def test_event_verifier_expect_event_pattern_match_and_store():
    verifier = EventVerifier({
        "name": SimpleEventPattern("Kieran"),
        "store": WildCardEventPattern("store"),
        "dont_store": WildCardEventPattern()
    })

    result = verifier.verify({
        "name": "Kieran",
        "store": "1",
        "dont_store": "something"
    })

    assert result
    assert verifier.stored_values["store"] == "1"


def test_event_verifier_expect_simple_match_failed():
    verifier = EventVerifier({
        "name": "Kieran",
        "store": "{{store,*}}",
        "dont_store": "*"
    })

    result = verifier.verify({
        "name": "Kieran",
        "store": "1",
    })

    assert not result


def test_event_verifier_expect_event_pattern_match_list():
    verifier = EventVerifier({
        "name": SimpleEventPattern("Kieran"),
        "list": [
            SimpleEventPattern("1")
        ],
    })

    result = verifier.verify({
        "name": "Kieran",
        "list": [
            "1",
            "2"
        ]
    })

    assert result


def test_event_verifier_expect_event_pattern_match_list_failed():
    verifier = EventVerifier({
        "name": SimpleEventPattern("Kieran"),
        "list": [
            SimpleEventPattern("1")
        ],
    })

    result = verifier.verify({
        "name": "Kieran",
        "list": [
            "2"
        ]
    })

    assert not result


def test_event_verifier_expect_event_pattern_match_dict():
    verifier = EventVerifier({
        "name": SimpleEventPattern("Kieran"),
        "dict": {
            "child": SimpleEventPattern("1")
        },
    })

    result = verifier.verify({
        "name": "Kieran",
        "dict": {
            "child": "1"
        }
    })

    assert result


def test_event_verifier_expect_event_pattern_match_dict_failed():
    verifier = EventVerifier({
        "name": SimpleEventPattern("Kieran"),
        "dict": {
            "child": SimpleEventPattern("1")
        },
    })

    result = verifier.verify({
        "name": "Kieran",
        "dict": {
            "child": "2"
        }
    })

    assert not result


def test_event_verifier_expect_event_pattern_group_match():
    verifier = EventVerifier({
        "name": SimpleEventPattern("Kieran", 1),
        "list": [
            {
                "child": SimpleEventPattern("1", 1)
            }
        ]
    })

    result = verifier.verify({
        "name": "Kieran",
        "list": [
            {
                "child": "1"
            },
            {
                "child": "2"
            }
        ]
    })

    assert result


def test_event_verifier_expect_event_pattern_group_match_failed():
    verifier = EventVerifier({
        "name": SimpleEventPattern("Kieran", 1),
        "list": [
            {
                "child": SimpleEventPattern("1", 1)
            }
        ]
    })

    result = verifier.verify({
        "name": "Kieran",
        "list": [
            {
                "child": "2"
            },
            {
                "child": "3"
            }
        ]
    })

    assert not result


def test_event_verifier_expect_event_pattern_group_match_complex():
    verifier = EventVerifier({
        "name": "Kieran",
        "store": "{{store1,*}}",
        "list": [
            {
                "3": "*",
                "4": "{{store2,*}}",
                "5": SimpleEventPattern("V3", "store3", 1),
                "6": SimpleEventPattern("V4", "store4", 1)
            },
            {
                "6": SimpleEventPattern("V5", "store5")
            }
        ],
        "event_pattern": WildCardEventPattern("V6", 1)
    })

    result = verifier.verify({
        "name": "Kieran",
        "store": "V1",
        "list": [
            "1",
            "2",
            {
                "6": "V5"
            },
            {
                "3": {},
                "4": "V2",
                "5": 'V3',
                "6": "V4"
            }
        ],
        "event_pattern": "V6"
    })

    assert result
    assert verifier.stored_values["store1"] == "V1"
    assert verifier.stored_values["store2"] == "V2"
    assert verifier.stored_values["store3"] == "V3"
    assert verifier.stored_values["store4"] == "V4"
    assert verifier.stored_values["store5"] == "V5"


def test_event_verifier_expect_event_pattern_group_match_complex_failed():
    verifier = EventVerifier({
        "name": "Kieran",
        "store": "{{store1,*}}",
        "list": [
            {
                "3": "*",
                "4": "{{store2,*}}",
                "5": SimpleEventPattern("V3", "store3", 1),
                "6": SimpleEventPattern("V4", "store4", 1)
            },
            {
                "6": SimpleEventPattern("V5", "store5")
            }
        ],
        "event_pattern": WildCardEventPattern("V6", 1)
    })

    result = verifier.verify({
        "name": "Kieran",
        "store": "V1",
        "list": [
            "1",
            "2",
            {
                "6": "V5"
            },
            {
                "3": {},
                "4": "V2",
                "5": 'VWRONG',
                "6": "V4"
            }
        ],
        "event_pattern": "V6"
    })

    assert not result


def test_expect_event_with_simple_event_expect_values_success_and_values_stored():
    user = SlackUser("user", "token")
    slack_user_workspace = SlackUserWorkspace()
    slack_user_workspace.find_user_client_by_username = MagicMock(return_value=user)
    event_template = {
        "name": "user",
        "id": "U2222222",
        "text": "{{store,some text}}"
    }
    user.load_events([
        {
            "name": "user",
            "id": "U2222222",
            "text": "some text"
        },
        {
            "type": "not_a_message"
        }
    ])

    expect_event_function = expect_event(user, event_template)
    store = {}
    result = expect_event_function(slack_user_workspace, store)
    assert result.result_code == ResultCode.success
    assert store["store"] == "some text"
