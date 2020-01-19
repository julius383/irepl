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
import functools
import operator
from pprint import pprint
from select import select
import regex

#  https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
ANSI_ESCAPE = regex.compile(
    r"""
\x1B    # ESC
    [@-_]   # 7-bit C1 Fe
    [0-?]*  # Parameter bytes
    [ -/]*  # Intermediate bytes
    [@-~]   # Final byte
    """,
    regex.VERBOSE,
)


def remove_escapes(string):
    if (m := regex.search(ANSI_ESCAPE, string)) :  # noqa E203
        if (m.start == 0) or (m.end == len(string) - 1):
            return regex.sub(ANSI_ESCAPE, "", remove_escape)
    return string


def send(fd, text):
    os.write(fd, str.encode(f"{text}\n", "utf-8"))


class WrappedRepl(object):
    def __init__(self, *, config, **kwargs):
        self.config = config
        self.initialize_pty()
        self.start_process()
        self.extras = None
        #  self.prompt = self.create_prompt()

    def initialize_pty(self):
        self.master_out, self.slave_out = pty.openpty()
        self.master_in, self.slave_in = pty.openpty()
        self.master_err, self.slave_err = pty.openpty()
        # python termios module docs
        # remove standard input echo for slave pty
        new = termios.tcgetattr(self.slave_in)
        new[3] = new[3] & ~termios.ECHO
        termios.tcsetattr(self.slave_in, termios.TCSADRAIN, new)

    def start_process(self):
        exe = self.config["executable"]
        flags = self.config["flags"]
        self.proc = subprocess.Popen(
            [exe, *flags],
            stdout=self.slave_out,
            stdin=self.slave_in,
            stderr=self.slave_err,
        )
        time.sleep(0.5)
        send(self.master_in, '')
        self.get_repl_output()

    def create_prompt(self):
        if self.extras:
            ex = list(self.extras)
            ex.append("> ")
            return " ".join(ex)
        else:
            return "> "

    def clean_string(self, string):
        if string:
            #  without_repl = re.sub(self.config["prompt"], "", string)
            return remove_escapes(string)
        else:
            return string

    # TODO: Might need more complicated logic for removing continuation
    # TODO: Possibly merge this and clean_string function
    def strip_multiline_repl(self, string):
        if (cont := self.config["continuation"]) :  # noqa E203
            return regex.sub(cont, "", string)
        else:
            return string

    def remove_dummy_prompt(self, lines):
        if (self.config["prompt"].startswith('^')):
            rx = regex.compile(self.config["prompt"])
        else:
            rx = regex.compile('^' + self.config["prompt"])
        if lines:
            for i in [0, -1]:
                try:
                    t = lines[i]
                    if lines and t:
                        m = regex.search(rx, t)
                        if (m):
                            lines.pop(i)
                            if rx.groups > 0:
                                self.extras = functools.reduce(
                                    operator.add, [m.captures(i) for i in range(1, rx.groups + 1)]
                                )
                except IndexError:
                    continue
            return lines

    def get_input(self):
        return input(self.create_prompt())

    def print_formatted(self, text):
        print(text, end="")

    def process_stdout(self, text):
        if text:
            lines = str(text, "utf-8").splitlines()
            lines = self.remove_dummy_prompt(lines)
            without_continuation = map(self.strip_multiline_repl, lines)
            pre_processed = filter(
                lambda x: x, map(self.clean_string, without_continuation)
            )
            if (lst := list(pre_processed)) :  # noqa E203
                return str.join(os.linesep, lst)

    def get_repl_output(self):
        results = self.read_from_slave()
        stdout = self.process_stdout(results[self.master_out])
        stderr = remove_escapes(str(results[self.master_err], "utf-8"))
        return (stdout, stderr)

    def read_from_slave(self):
        fds = [self.master_out, self.master_err]
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
            send(self.master_in, user_input)
            # fixes problem of output appearing later than
            # expression that produces it
            time.sleep(0.1)
            output, err = self.get_repl_output()
            if output:
                self.print_formatted(output)
            if err:
                print(err, end="")
