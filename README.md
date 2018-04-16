
# Coherence [![Build Status](https://travis-ci.org/absa-subatomic/coherence.svg?branch=master)](https://travis-ci.org/absa-subatomic/coherence) [![codecov](https://codecov.io/gh/absa-subatomic/coherence/branch/master/graph/badge.svg)](https://codecov.io/gh/absa-subatomic/coherence) [![PyPI version](https://badge.fury.io/py/subatomic-coherence.svg)](https://badge.fury.io/py/subatomic-coherence)
Coherence is a python module designed to facilitate integration testing for ChatOps frameworks built using the
[Slack Api](https://api.slack.com/) and is built around the 
[python-slackclient](https://github.com/slackapi/python-slackclient). At it's core Coherence allows a developer to
control the actions of various Slack users via scripted commands and listen to events and responses in the Slack
workspace.

## Getting Started
Start by installing coherence:
```
pip install subatomic_coherence
```

Coherence can then be imported using
```python
import subatomic_coherence
```

Coherence uses slack tokens for users to control their actions. It is usually a good idea to create an isolated
slack workspace for testing purposes specifically. This eliminates background event in the workspace which could make 
writing tests harder and conversely tests could contaminate important slack workspaces.

The main controller for the integration tests is the 
[SlackTestSuite](subatomic_coherence/slack_test_suite.py). The constructor
can be called as such:
```python
test_suite = SlackTestSuite(description="Test suite description", log_file="log_file.log", log_level=logging.INFO,
    listen_after_tests=False)
```
All arguments are optional. 
- `description` - A descriptive string for the test suite.
- `log_file` - Path to a file where the detailed logs will be written. If not specified, logging will be turned off.
- `log_level` - Level at which to log output. This uses the default python `logging` module levels.
- `listen_after_tests` - If True, continues to listen to events after the test suite is run. This can be useful to run
and watch the events that occur when performing certain actions in the workspace when trying to map out the events 
expected when writing a test.

The test suite cannot run without a user to issue commands with. All built in commands require a user to be specified
in order to access the workspace. Any user can be used but a slack user token must be created in order to do so. This
can be done [here](https://api.slack.com/custom-integrations/legacy-tokens). Users can then added to the 
`SlackTestSuite` as follows:

```python
test_suite.add_slack_user("slack_user_name", "slack_token")
```

A slack user token is usually of the form `xoxp-...`.

Multiple users can be added to the `SlackTestSuite` and each can be used to issue slack commands as shown later in the
read me.

Tests should then be added to the test suite. Tests added are run synchronously in the order they are added. Adding a 
test can be done as follows:

```python
test_suite.add_test(test_function)
```

Finally the tests are running by invoking the `run_tests` command.

```python
test_suite.run_tests()
```

## Creating Tests
All tests are defined as a series of steps added to a testing chain. The chain starts with a TestEntry instance and new
elements are added to the chain by invoking the `then` command. `TestElement.then(next_action)` takes a parameter 
`next_action` which is a function of the form
- arguments
    - `slack_user_workspace` - this will contain a reference to the [`SlackUserWorkspace`](subatomic_coherence/user/slack_user_workspace.py) instance for the current test
    suite. It provides access to details such as existing users, groups, and channels metadata along with access to the
    slack users added to the test suite clients (used to send, receive, listen etc to messages for the associated user).
    - `data_store` - this is a simple python dictionary that persists any data stored in it for the duration of the test
     chain. It can be used to store data that will be used by later steps in the chain.  
- return - The function must return a [`TestResult`](subatomic_coherence/testing/test.py) indicating whether the test is successful, unsuccessful, or pending.

Examples of these test actions can be found in the [`simple_actions`](subatomic_coherence/actions/simple_actions.py) python module. The `simple_actions` module
additionally provides a number of re-usable testing steps. A few simple examples are shown here.

### Send Message To User
A send message action can be defined as follows:
```python
def send_message_to_user(from_user_slack_name,
                         to_user_slack_name,
                         message):
    def send_message_function(slack_user_workspace, data_store):
        user_sender = slack_user_workspace.find_user_client_by_username(from_user_slack_name)
        user_receiver_details = slack_user_workspace.find_user_by_username(to_user_slack_name)
        user_sender.send_message(user_receiver_details["id"], message)
        return TestResult(ResultCode.success)

    return send_message_function
```

As described previously, this returns a function which takes `slack_user_workspace` and `data_store` parameters, and 
returns a `TestResult` which in this case is always marked with Success. It starts by finding the slack client for the
user that wishes to send the message and getting the slack metadata details for the user that the message will be sent
to. The slack id for the receiver is pulled from the metadata and the sender client is instructed to send the message 
to the receiver. It is assumed this is done successfully and a successful result is returned. This could be added to 
a slack test suite as follows:

```python
test_suite.add_test("test_send_message_to_user", TestPortal() \
                    .then(send_message_to_user("sender_name", "receiver_name", "Hello")))
``` 

### Listen for an event
It is also possible to wait for an event to continue. The entire test suite runs on an event loop with the following
structure:

- Read slack events for each user client
- Try to process the current test/current step in the current test
- Clear the event stores

Test actions can be designed to wait for a certain events to occur before succeeding/failing. The key to this is
returning a `TestResult` with a pending result. Below is an example where the action will wait for a channel to be
created.

```python
def expect_channel_created(user, channel_name):
    def expect_channel_created_function(slack_user_workspace, data_store):
        user_client = slack_user_workspace.find_user_client_by_username(user)
        for event in user_client.events:
            if event["type"] == "channel_created" and event["channel"]["name"] == channel_name:
                return TestResult(ResultCode.success)
        return TestResult(ResultCode.pending)

    return expect_channel_created_function
```

This defines an action that waits for the channel with `channel_name` to be created that is visible to the event feed
for the slack client associated to the slack user with the name `user`. If the channel is not detected as having been 
created, a pending result is returned and the action will run in the next event loop again. All action steps by default
have a 15 second timeout, so if this action does not succeed within 15 seconds, the test will fail and exit.

### Storing data
It is sometimes useful to have access to previous events or data created in earlier actions. This is made possible using
the `data_store` passed into all test actions. The `data_store` is persisted for the duration of the test and all actions
can access data stored in it by earlier actions. The `data_store` is not shared between Tests, only the steps/actions
within each test. It is a simple python dictionary and store key/value pairs. An example of its use is below.

```python
def expect_any_channel_created_and_store_name(user):
    def expect_any_channel_created_and_store_name_function(slack_user_workspace, data_store):
        user_client = slack_user_workspace.find_user_client_by_username(user)
        for event in user_client.events:
            if event["type"] == "channel_created":
                data_store["channel-created"] = event["channel"]["name"]
                return TestResult(ResultCode.success)
        return TestResult(ResultCode.pending)

    return expect_any_channel_created_and_store_name
    
def send_message_to_channel(from_user_slack_name,
                            message):
    def send_message_to_channel_function(slack_user_workspace, data_store):
        user_sender = slack_user_workspace.find_user_client_by_username(from_user_slack_name)
        channel_details = slack_user_workspace.find_channel_by_name(data_store["channel-created"])
        user_sender.send_message(channel_details["id"], message)
        return TestResult(ResultCode.success)

    return send_message_to_channel_function
```

The `expect_any_channel_created_and_store_name` functions creates an action that will store the name of any channel that
is created in the `data_store`. This is then called on by the `send_message_to_channel_function` to send a message to 
the channel that was created. These can be used as follows:

```python
test_suite.add_test("test_send_message_to_channel", TestPortal() \
                    .then(expect_any_channel_created_and_store_name("user_to_listen_as"))
                    .then(send_message_to_channel("user_to_send_as", "Hello")))
``` 
