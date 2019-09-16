#!/usr/bin/env python3

import re
import tempfile
import subprocess
import shutil
import sys
from os import path
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


class ReplWrap(object):
    def __init__(self, rname):
        self.rname = rname.upper()
        self.pkg_dir = path.dirname(__file__)
        self.lang_params = self.load_language_config()
        self.lexer_cls = find_lexer_class_by_name(self.lang_params["lexer"])
        self.prompt = self.lang_params["prompt"]
        self.exe = self.lang_params["executable"]
        self.completer = WordCompleter(self.build_completion_list())
        self.prompt_sess = PromptSession(
            style=STYLE,
            lexer=PygmentsLexer(self.lexer_cls),
            completer=self.completer,
            include_default_pygments_style=False,
            enable_open_in_editor=True,
        )
        self.repl = self.init_repl()
        self.pager_file = open(tempfile.mkstemp()[1], "w")
        self.lexer_ins = self.lexer_cls()

    def load_language_config(self):
        yaml = YAML(typ="safe")
        f = open(path.join(self.pkg_dir, "langs.yml"), "r")
        config = yaml.load(f)
        f.close()
        return config[self.rname]

    def build_completion_list(self):
        completions = []
        if hasattr(self.lexer_cls, "keywords"):
            completions.extend(list(self.lexer_cls.keywords))
        if hasattr(self.lexer_cls, "builtins"):
            completions.extend(list(self.lexer_cls.builtins))
        if hasattr(self.lexer_cls, "keywords"):
            completions.extend(list(self.lexer_cls.keywords))
        return completions

    def init_repl(self):
        repl = pexpect.spawn(self.exe, encoding="utf-8")
        repl.setecho(False)
        repl.waitnoecho()
        repl.expect(self.prompt)
        return repl

    def create_prompt(self):
        if self.repl.match.groups():
            info = " ".join([f"({m})" for m in self.repl.match.groups()])
            text = PygmentsTokens(
                [
                    (Token.Prompt, f"({self.rname}):"),
                    (Token.Info, info),
                    (Token.Text, " > "),
                ]
            )
        else:
            text = PygmentsTokens(
                [(Token.Prompt, f"({self.rname}):"), (Token.Text, " > ")]
            )
        return text

    def get_eval_results(self):
        user_in = self.prompt_sess.prompt(self.create_prompt())
        self.repl.sendline(user_in)
        self.repl.expect(self.prompt)
        if re.search(ANSI_ESCAPE, self.repl.before):
            output = re.sub(ANSI_ESCAPE, "", self.repl.before)[1:]
        else:
            output = self.repl.before
        return output

    def process_eval_results(self, output):
        page = False
        if (
            len(re.findall(r"\n", output))
            > shutil.get_terminal_size().lines - 1
        ):
            page = True

        formatted_output = pygments.highlight(
            output,
            self.lexer_ins,
            TerminalTrueColorFormatter(style=get_style_by_name("monokai")),
        )
        #  https://stackoverflow.com/questions/6728661/paging-output-from-python
        if page:
            print(formatted_output, file=self.pager_file)
            self.pager_file.flush()
            subprocess.call(["less", "-R", self.pager_file.name])
        else:
            print(formatted_output)

    def cleanup(self):
        self.pager_file.close()
        self.repl.close()


def main():
    try:
        LANGUAGE = sys.argv[1]
    except IndexError:
        LANGUAGE = "factor"
    wrapped = ReplWrap(LANGUAGE)
    while True:
        try:
            repl_output = wrapped.get_eval_results()
            wrapped.process_eval_results(repl_output)
        except KeyboardInterrupt:
            print("User interrupt")
            wrapped.cleanup()
            break


if __name__ == "__main__":
    main()
