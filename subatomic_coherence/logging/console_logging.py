import logging
import re

from colorama import Style, Fore


class ConsoleLogger(object):

    buffered_log = []
    interactive_mode = False

    @staticmethod
    def success(message):
        ConsoleLogger.buffer_message(message)
        logging.info(f"{message}\n")
        if not ConsoleLogger.interactive_mode:
            print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

    @staticmethod
    def error(message):
        ConsoleLogger.buffer_message(message)
        logging.error(f"{message}\n")
        if not ConsoleLogger.interactive_mode:
            print(f"{Fore.RED}{message}{Style.RESET_ALL}")

    @staticmethod
    def info(message):
        ConsoleLogger.buffer_message(message)
        logging.info(f"{message}\n")
        if not ConsoleLogger.interactive_mode:
            print(f"{Fore.MAGENTA}{message}{Style.RESET_ALL}")

    @staticmethod
    def log(message):
        ConsoleLogger.buffer_message(message)
        logging.info(f"{message}\n")
        if not ConsoleLogger.interactive_mode:
            print(message)

    @staticmethod
    def buffer_message(message):
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        message_filtered = ansi_escape.sub("", message)
        message_lines = message_filtered.split("\n")
        ConsoleLogger.buffered_log.extend(message_lines)

    @staticmethod
    def read_buffered_log():
        buffered_return = ConsoleLogger.buffered_log
        ConsoleLogger.buffered_log = []
        return buffered_return
