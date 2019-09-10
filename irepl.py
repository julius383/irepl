#!/usr/bin/env python3

import re
import configparser
import pygments
from pygments.lexers import find_lexer_class_by_name
from pygments.styles import get_style_by_name
from pygments.formatters import TerminalTrueColorFormatter
from prompt_toolkit.styles.pygments import style_from_pygments_cls
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.formatted_text import PygmentsTokens
import pexpect
from ruamel.yaml import YAML
import sys
from io import StringIO


def build_completion_list(lexer):
    completions = []
    if hasattr(lexer, "keywords"):
        completions.extend(list(lexer.keywords))
    if hasattr(lexer, "builtins"):
        completions.extend(list(lexer.builtins))
    if hasattr(lexer, "keywords"):
        completions.extend(list(lexer.keywords))
    return completions


yaml = YAML(typ="safe")
f = open("langs.yml", "r")
CONFIG = yaml.load(f)
f.close()

try:
    LANGUAGE = sys.argv[1]
except IndexError:
    LANGUAGE = "factor"

PROMPT = CONFIG[LANGUAGE.upper()]["prompt"]
LEXER_CLS = find_lexer_class_by_name(CONFIG[LANGUAGE.upper()]["lexer"])
EXE = CONFIG[LANGUAGE.upper()]["executable"]

STYLE = get_style_by_name("monokai")
LEXER_INS = LEXER_CLS()

COMPLETER = WordCompleter(build_completion_list(LEXER_CLS))

sess = PromptSession(
    f"({LANGUAGE})> ",
    style=style_from_pygments_cls(STYLE),
    lexer=PygmentsLexer(LEXER_CLS),
    completer=COMPLETER,
)
#  https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
ansi_escape = re.compile(
    r"""
    \x1B    # ESC
    [@-_]   # 7-bit C1 Fe
    [0-?]*  # Parameter bytes
    [ -/]*  # Intermediate bytes
    [@-~]   # Final byte
""",
    re.VERBOSE,
)
repl = pexpect.spawn(EXE, encoding="utf-8")

repl.setecho(False)
repl.waitnoecho()
repl.expect(PROMPT)

while True:
    try:
        user_in = sess.prompt()
        repl.sendline(user_in)
        repl.expect(PROMPT)
        if re.search(ansi_escape, repl.before):
            output = re.sub(ansi_escape, "", repl.before)[1:]
        else:
            output = repl.before
        formatted_output = pygments.highlight(
            output, LEXER_INS, TerminalTrueColorFormatter(style=STYLE)
        )
        print(formatted_output)
    except KeyboardInterrupt:
        print("User interrupt")
        repl.close()
        break
