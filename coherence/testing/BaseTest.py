from coherence.testing.Test import TestEntry, TestResult, ResultCode


class BaseTest(TestEntry):
    def run(self, slack_user_workspace, data_store):
        return TestResult(ResultCode.success)
