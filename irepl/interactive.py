import re
import tempfile
import shutil
import subprocess

from prompt_toolkit.completion import WordCompleter
import prompt_toolkit as pt
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import merge_styles
from prompt_toolkit.styles.pygments import (
    style_from_pygments_cls,
    style_from_pygments_dict,
)
from pygments.formatters import TerminalTrueColorFormatter
from pygments.lexers import find_lexer_class_by_name
from pygments.styles import get_style_by_name
from pygments.token import Token
import pygments

PAGER_FILE = open(tempfile.mkstemp()[1], "w")


def build_completion_list(lexer):
    completions = []
    if hasattr(lexer, "keywords"):
        completions.extend(list(lexer.keywords))
    if hasattr(lexer, "builtins"):
        completions.extend(list(lexer.builtins))
    return completions


class InteractiveMixin(object):
    def __init__(self, *args, **kwargs):
        super(InteractiveMixin, self).__init__(*args, **kwargs)
        self.config = args[0]
        self.initialize_pygments()
        self.initialize_prompt()

    def initialize_pygments(self):
        prompt_style = {Token.Prompt: "#85678f", Token.Info: "#b294bb bold"}
        merged_style = merge_styles(
            [
                style_from_pygments_cls(get_style_by_name("monokai")),
                style_from_pygments_dict(prompt_style),
            ]
        )
        self.style = merged_style

    def guess_lexer(self, lang=None):
        if lang is None:
            lang = self.config['lang']
        try:
            return find_lexer_class_by_name(self.config['lexer'])
        except pygments.util.ClassNotFound:
            try:
                return find_lexer_class_by_name(str.lower(lang))
            except pygments.util.ClassNotFound:
                return None

    def initialize_prompt(self):
        lexer = self.guess_lexer(self.config['lang'])
        if lexer is not None:
            completer = WordCompleter(build_completion_list(lexer))
            self.lexer = PygmentsLexer(lexer)
            self.lexer_instance = lexer()
        else:
            completer = None
            self.lexer = None
            self.lexer_instance = None
        prompt_config = {
            "style": self.style,
            "lexer": self.lexer,
            "completer": completer,
            "include_default_pygments_style": False,
            "enable_open_in_editor": True,
            "key_bindings": None,
        }
        normalized_config = dict(
            filter(lambda x: x[1] is not None, prompt_config.items())
        )

        self.sess = pt.PromptSession(**normalized_config)

    def get_input(self):
        return self.sess.prompt('> ')

    def print_formatted(self, output):
        rx = re.compile(r"\[\?2004(h|l)")
        page = False
        if (
            len(re.findall(r"\n", output))
            > shutil.get_terminal_size().lines - 1
        ):
            page = True

        formatted_output = pygments.highlight(
            code=output,
            lexer=self.lexer_instance,
            formatter=TerminalTrueColorFormatter(
                style=get_style_by_name("monokai")
            ),
        )
        #  formatted_output = re.sub(rx, '', formatted_output)
        #  https://stackoverflow.com/questions/6728661/paging-output-from-python
        if page:
            print(formatted_output, file=PAGER_FILE)
            PAGER_FILE.flush()
            subprocess.call(["less", "-R", PAGER_FILE.name])
        else:
            print(formatted_output, end="")
