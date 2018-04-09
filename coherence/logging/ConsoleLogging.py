import logging

from colorama import Style, Fore


class ConsoleLogger(object):
    @staticmethod
    def success(message):
        logging.info(f"{message}\n")
        print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")

    @staticmethod
    def error(message):
        logging.error(f"{message}\n")
        print(f"{Fore.RED}{message}{Style.RESET_ALL}")

    @staticmethod
    def info(message):
        logging.info(f"{message}\n")
        print(f"{Fore.MAGENTA}{message}{Style.RESET_ALL}")

    @staticmethod
    def log(message):
        logging.info(f"{message}\n")
        print(message)
