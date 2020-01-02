import io
import os
import pty
import re
import shlex
import subprocess
import termios
import time
import tty
from itertools import repeat
from pprint import pprint
from select import select

from interactive import InteractiveMixin
from config import load_config_for

#  https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
ANSI_ESCAPE = re.compile(
    r"""
\x1B    # ESC
    [@-_]   # 7-bit C1 Fe
    [0-?]*  # Parameter bytes
    [ -/]*  # Intermediate bytes
    [@-~]   # Final byte
    """,
    re.VERBOSE,
)


def remove_escapes(string):
    if (m := re.search(ANSI_ESCAPE, string)) :
        if (m.start == 0) or (m.end == len(string) - 1):
            return re.sub(ANSI_ESCAPE, "", remove_escape)
    return string


class WrappedRepl(object):
    def __init__(self, *, config):
        self.config = config
        self.initialize_pty()
        self.start_process()

    def initialize_pty(self):
        self.master_out, self.slave_out = pty.openpty()
        self.master_in, self.slave_in = pty.openpty()
        # python termios module docs
        # remove standard input echo for slave pty
        new = termios.tcgetattr(self.slave_in)
        new[3] = new[3] & ~termios.ECHO
        termios.tcsetattr(self.slave_in, termios.TCSADRAIN, new)

    def start_process(self):
        exe = shlex.split(self.config["executable"])
        self.proc = subprocess.Popen(
            exe,
            stdout=self.slave_out,
            stdin=self.slave_in,
            stderr=subprocess.PIPE,
        )
        time.sleep(0.5)
        self.get_repl_output()

    def clean_string(self, string):
        without_repl = re.sub(self.config["prompt"], "", string)
        return remove_escapes(without_repl)

    def get_input(self):
        return input("> ")

    def print_formatted(self, text):
        print(text, end='')

    def get_repl_output(self):
        results = self.read_from_slave()
        output = results[self.master_out]
        #  return str(output, "utf-8")
        lines = str(output, "utf-8").splitlines()
        pre_processed = filter(lambda x: x, map(self.clean_string, lines))
        if (lst := list(pre_processed)):
            return str.join(os.linesep, lst)

    def read_from_slave(self):
        fds = [self.master_out]
        ready, _, _ = select(fds, [], [], 0.04)
        result = dict(zip(fds, repeat(b"")))
        if ready:
            for fd in ready:
                data = os.read(fd, 8192)
                result[fd] = data
        return result

    def run(self):
        while True:
            user_input = self.get_input()
            os.write(self.master_in, str.encode(f"{user_input}\n", "utf-8"))
            # fixes problem of output appearing later than
            # expression that produces it
            time.sleep(0.1)
            output = self.get_repl_output()
            #  print(output, end='')
            self.print_formatted(output)
