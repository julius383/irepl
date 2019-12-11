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


mo, so = pty.openpty()
me, se = pty.openpty()
mi, si = pty.openpty()

p = subprocess.Popen(
    shlex.split(LANG_CONFIG["executable"]),
    bufsize=1,
    stdout=so,
    stdin=si,
    stderr=se,
    close_fds=True,
)


def read_from(fds):
    ready, _, _ = select(fds, [], [], 0.04)
    result = dict(zip(fds, repeat(b'')))
    if ready:
        for fd in ready:
            data = os.read(fd, 512)
            if not data:
                break
            result[fd] += data
    return result


while True:
    result = read_from([mo, me])
    result = read_from([mo, me])
    if p.poll() is not None:  # select timed-out
        break
    if (out := result[mo]):
        print(f"{out=}")
        #  format_output(str(out))
    if (err := result[me]):
        print(f"{err=}")
        #  print(str(err), file=sys.stderr)
    user_in = PROMPT.prompt("> ")
    os.write(mi, str.encode(user_in + "\r\n"))
    print(f"{user_in=}")
