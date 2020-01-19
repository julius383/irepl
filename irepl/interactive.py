import re
import tempfile
import shutil
import subprocess
from queue import Queue
import time
from itertools import repeat, starmap
import operator

from prompt_toolkit.completion import WordCompleter
import prompt_toolkit as pt
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import merge_styles
from prompt_toolkit.styles.pygments import (
    style_from_pygments_cls,
)
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from pygments.formatters import TerminalTrueColorFormatter
from pygments.lexers import find_lexer_class_by_name
from pygments.styles import get_style_by_name
import pygments

PAGER_FILE = open(tempfile.mkstemp()[1], "w")
MULTILINE = False
BRACKETS_Q = Queue()

bindings = KeyBindings()


@bindings.add("c-o")
def _(event):
    "Toggle multiline input mode"
    global MULTILINE
    MULTILINE = not MULTILINE


def prompt_continuation(width, line_number, is_soft_wrap):
    return ('.' * (width - 1)) + ':'


def build_completion_list(lexer):
    completions = []
    if hasattr(lexer, "keywords"):
        completions.extend(list(lexer.keywords))
    if hasattr(lexer, "builtins"):
        completions.extend(list(lexer.builtins))
    return completions


class InteractiveMixin(object):
    def __init__(self, **kwargs):
        super(InteractiveMixin, self).__init__(**kwargs)
        self.config = kwargs["config"]
        self.initialize_pygments()
        self.initialize_prompttk()

    def initialize_pygments(self):
        prompt_style = {'prompt': "#85678f", 'extras': "#b294bb bold"}
        merged_style = merge_styles(
            [
                style_from_pygments_cls(get_style_by_name("monokai")),
                Style.from_dict(prompt_style),
            ]
        )
        self.style = merged_style

    def guess_lexer(self, lang=None):
        if lang is None:
            lang = self.config["lang"]
        try:
            return find_lexer_class_by_name(self.config["lexer"])
        except pygments.util.ClassNotFound:
            try:
                return find_lexer_class_by_name(str.lower(lang))
            except pygments.util.ClassNotFound:
                return None

    def initialize_prompttk(self):
        lexer = self.guess_lexer(self.config["lang"])
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
            "prompt_continuation": prompt_continuation,
            "include_default_pygments_style": False,
            "enable_open_in_editor": True,
            "key_bindings": None,
        }
        normalized_config = dict(
            filter(lambda x: x[1] is not None, prompt_config.items())
        )
        self.sess = pt.PromptSession(**normalized_config)

    def create_prompt(self):
        m = []
        if self.extras:
            ex = list(self.extras)
            ex = list(starmap(operator.add, zip(ex, repeat(' '))))  # pad each extra value with right space
            m.extend(list(zip(repeat('class:extras'), ex)))  # assign highlight class
            if MULTILINE:
                m.append(('class:prompt', 'ml> '))  # finally add prompt
            else:
                m.append(('class:prompt', '> '))
                return m
        else:
            return 'ml> ' if MULTILINE else '> '

    def get_input(self):
        def multiline_mode(text):
            """Add characters to enter multiline mode to input if
            they are available in config"""
            if self.config['multiline'] and not re.fullmatch(r'\s+', text):
                prefix, suffix = self.config['multiline']
                return f"{prefix}\n{text}\n{suffix}\n"
            else:
                return text
        if MULTILINE:
            pre_process = multiline_mode
        else:
            pre_process = lambda x: x
        return pre_process(
            self.sess.prompt(
                self.create_prompt(),
                key_bindings=bindings,
                multiline=MULTILINE
            ))

    def print_formatted(self, output):
        #  rx = re.compile(r"\[\?2004(h|l)")
        page = False
        if len(re.findall(r"\n", output)) > shutil.get_terminal_size().lines - 1:
            page = True
        formatted_output = pygments.highlight(
            code=output,
            lexer=self.lexer_instance,
            formatter=TerminalTrueColorFormatter(style=get_style_by_name("monokai")),
        )
        #  formatted_output = re.sub(rx, '', formatted_output)
        #  https://stackoverflow.com/questions/6728661/paging-output-from-python
        if page:
            print(formatted_output, file=PAGER_FILE)
            PAGER_FILE.flush()
            subprocess.call(["less", "-R", PAGER_FILE.name])
        else:
            print(formatted_output, end="")
