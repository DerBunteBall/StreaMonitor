from streamonitor.manager import Manager
from streamonitor.clean_exit import CleanExit
import streamonitor.log as log
import readline


class CLIManager(Manager):
    def __init__(self, streamers):
        super().__init__(streamers)
        self.logger = log.Logger("manager_cli")

    def run(self):
        while True:
            try:
                line = input("> ")
            except EOFError:
                print()
                continue
            reply = self.execCmd(line)
            if line == "quit":
                return
            self.logger.info(reply)

    def do_quit(self, _, __, ___):
        CleanExit(self.streamers).clean_exit(0, 0)
