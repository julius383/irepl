from os import path
import toml
import sys

DEFAULT_CONFIG = path.join(path.dirname(__file__), "languages.toml")


def load_config_for(lang, filename=DEFAULT_CONFIG):
    config_dict = toml.load(filename)
    try:
        lang_conf = config_dict[lang.lower()]
        lang_conf['lang'] = lang
        return lang_conf
    except KeyError:
        print(f"No config for {lang} found", file=sys.stderr)
        sys.exit(1)
