
from interactive import InteractiveMixin
from config import load_config_for
from wrappedrepl import WrappedRepl
import os
import signal


class IRepl(InteractiveMixin, WrappedRepl):
    pass


if __name__ == "__main__":
    config = load_config_for("haskell")
    try:
        os.setpgrp()
        r = IRepl(config)
        r.run()
    finally:
        os.killpg(os.getpgrp(), signal.SIGTERM)
