#!/usr/bin/env python3

import re
import tempfile
import shutil
import sys
import os
from os import path
import subprocess
import pty
from select import select
import tty
import errno
import shlex
from itertools import repeat
from pprint import pprint
import termios
import time

import pygments
from pygments.lexers import find_lexer_class_by_name
from pygments.styles import get_style_by_name
from pygments.formatters import TerminalTrueColorFormatter
from pygments.token import Token
from prompt_toolkit.styles import merge_styles
from prompt_toolkit.styles.pygments import style_from_pygments_cls
from prompt_toolkit.styles.pygments import style_from_pygments_dict
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.formatted_text import PygmentsTokens
import pexpect
from ruamel.yaml import YAML

#  from keys import BINDINGS, MULTILINE
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.filters import Condition

BINDINGS = KeyBindings()
MULTILINE = False


@BINDINGS.add("escape", "enter")
def _(event):
    global MULTILINE
    MULTILINE = not MULTILINE


@BINDINGS.add("c-x")
def _(event):
    " Exit when `c-x` is pressed. "
    event.app.exit()


STYLE_DICT = {Token.Prompt: "#85678f", Token.Info: "#b294bb bold"}

STYLE = merge_styles(
    [
        style_from_pygments_cls(get_style_by_name("monokai")),
        style_from_pygments_dict(STYLE_DICT),
    ]
)

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

LANGUAGE = "PYTHON"


def load_config():
    yaml = YAML(typ="safe")
    config_file = path.join(path.dirname(__file__), "langs.yml")
    with open(config_file, "r") as f:
        config_dict = yaml.load(f)
    return config_dict


def build_completion_list(lexer):
    completions = []
    if hasattr(lexer, "keywords"):
        completions.extend(list(lexer.keywords))
    if hasattr(lexer, "builtins"):
        completions.extend(list(lexer.builtins))
    if hasattr(lexer, "keywords"):
        completions.extend(list(lexer.keywords))
    return completions


CONFIG = load_config()
LANG_CONFIG = CONFIG[LANGUAGE]
LEXER = find_lexer_class_by_name(LANG_CONFIG["lexer"])
COMPLETER = WordCompleter(build_completion_list(LEXER))
PAGER_FILE = open(tempfile.mkstemp()[1], "w")
LEXER_INS = LEXER()

PROMPT = PromptSession(
    style=STYLE,
    lexer=PygmentsLexer(LEXER),
    completer=COMPLETER,
    include_default_pygments_style=False,
    enable_open_in_editor=True,
    key_bindings=BINDINGS,
)


def format_output(output):
    page = False
    if len(re.findall(r"\n", output)) > shutil.get_terminal_size().lines - 1:
        page = True

    formatted_output = pygments.highlight(
        output,
        LEXER_INS,
        TerminalTrueColorFormatter(style=get_style_by_name("monokai")),
    )
    #  https://stackoverflow.com/questions/6728661/paging-output-from-python
    if page:
        print(formatted_output, file=PAGER_FILE)
        PAGER_FILE.flush()
        subprocess.call(["less", "-R", PAGER_FILE.name])
    else:
        print(formatted_output)


#  https://stackoverflow.com/questions/52954248/capture-output-as-a-tty-in-python
mo, so = pty.openpty()
#  me, se = pty.openpty()
mi, si = pty.openpty()

p = subprocess.Popen(
    shlex.split(LANG_CONFIG["executable"]),
    stdout=so,
    stdin=si,
    stderr=subprocess.PIPE,
)

def read_from(fds):
    ready, _, _ = select(fds, [], [], 0.04)
    result = dict(zip(fds, repeat(b"")))
    if ready:
        for fd in ready:
            data = os.read(fd, 8192)
            result[fd] = data
    return result


def clean_string(string):
    without_repl = re.sub(LANG_CONFIG["prompt"], "", string)
    without_escapes = re.sub(ANSI_ESCAPE, "", without_repl)
    return without_escapes


def get_real_output(fds):
    maybe_output = read_from(fds)
    text = maybe_output[mo]
    lines = str(text, "utf-8").splitlines()
    if (lst := list(filter(lambda x: x, map(clean_string, lines)))) :
        return str.join(os.linesep, lst)


print(f"stdin: {mi} {si}, stdout: {mo} {so}")
# TODO: Figure out how to fix dir and help functions

# python termios module docs
new = termios.tcgetattr(si)
new[3] = new[3] & ~termios.ECHO
termios.tcsetattr(si, termios.TCSADRAIN, new)
while True:
    user_in = PROMPT.prompt("> ")
    os.write(mi, str.encode(f"{user_in}\n", 'utf-8'))
    # fixes problem of output appearing later than
    # expression that produces it
    time.sleep(0.1)
    ready, _, _ = select([mo], [], [], 0.04)
    if ready:
        r = get_real_output([mo])
        print(f"got {r}")
