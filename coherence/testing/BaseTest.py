from coherence.testing.Test import TestEntry, TestResult


class BaseTest(TestEntry):
    def run(self, slack_user_ledger, data_store):
        return TestResult(1)
