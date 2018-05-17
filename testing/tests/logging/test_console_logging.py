from subatomic_coherence.logging.console_logging import ConsoleLogger


def test_success_log_expect_added_to_buffer():
    ConsoleLogger.interactive_mode = True
    ConsoleLogger.success("Test")
    assert ConsoleLogger.read_buffered_log()[-1] == "Test"


def test_error_log_expect_added_to_buffer():
    ConsoleLogger.interactive_mode = True
    ConsoleLogger.error("Test")
    assert ConsoleLogger.read_buffered_log()[-1] == "Test"


def test_info_log_expect_added_to_buffer():
    ConsoleLogger.interactive_mode = True
    ConsoleLogger.info("Test")
    assert ConsoleLogger.read_buffered_log()[-1] == "Test"


def test_log_expect_added_to_buffer():
    ConsoleLogger.interactive_mode = True
    ConsoleLogger.log("Test")
    assert ConsoleLogger.read_buffered_log()[-1] == "Test"


def test_buffer_message_multi_line_expect_added_to_buffer():
    ConsoleLogger.interactive_mode = True
    ConsoleLogger.success("Test1\nTest2")
    assert ConsoleLogger.buffered_log[-2] == "Test1" and ConsoleLogger.buffered_log[-1] == "Test2"


def test_read_buffered_log_expect_emptied_buffer():
    ConsoleLogger.interactive_mode = True
    ConsoleLogger.success("Test1\nTest2")
    ConsoleLogger.read_buffered_log()
    assert len(ConsoleLogger.buffered_log) == 0
