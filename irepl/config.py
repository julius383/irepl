from os import path
from ruamel.yaml import YAML
import sys

DEFAULT_CONFIG = path.join(path.dirname(__file__), "langs.yml")


def load_config_for(lang, filename=DEFAULT_CONFIG):
    yaml = YAML(typ="safe")
    #  config_file = path.join(path.dirname(__file__), "langs.yml")
    with open(filename, "r") as f:
        config_dict = yaml.load(f)
        try:
            lang_conf = config_dict[lang.upper()]
            lang_conf['lang'] = lang
            return lang_conf
        except KeyError:
            print(f"No config for {lang} found", file=sys.stderr)
            sys.exit(1)
