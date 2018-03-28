# Coherence
Coherence is a python module designed to facilitate integration testing for ChatOps frameworks built using the
[Slack Api](https://api.slack.com/) and is built around the 
[python-slackclient](https://github.com/slackapi/python-slackclient). At it's core Coherence allows a developer to
control the actions of various Slack users via scripted commands and listen to events and responses in the Slack
workspace.

## Getting Started
Currently in this early development stage the only way to use the module is to use it directly via the source and 
importing this into your testing project. There are plans to put the module on 
[PyPi](https://github.com/absa-subatomic/coherence/issues/2) in the near future.

Coherence uses slack tokens for users to control their actions. It is usually a good idea to create an isolated
slack workspace for testing purposes specifically. This eliminates background event in the workspace which could make 
writing tests harder and conversely tests could contaminate important slack workspaces.

The main controller for the integration tests is the 
[SlackTestSuite](https://github.com/absa-subatomic/coherence/blob/master/coherence/SlackTestSuite.py). The constructor
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
    - `slack_user_workspace` - this will contain a reference to the `SlackUserWorkspace`(needs link) instance for the current test
    suite. It provides access to details such as existing users, groups, and channels metadata along with access to the
    slack users added to the test suite clients (used to send, receive, listen etc to messages for the associated user).
    - `data_store` - this is a simple python dictionary that persists any data stored in it for the duration of the test
     chain. It can be used to store data that will be used by later steps in the chain.  
- return - The function must return a `TestResult`(needs link) indicating whether the test is successful, unsuccessful, or pending.

Examples of these test actions can be found in the `SimpleActions`(needs link) python module.
