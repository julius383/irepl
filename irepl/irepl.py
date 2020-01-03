
import os
import signal
from interactive import InteractiveMixin
from remote import RemoteMixin
from config import load_config_for
from wrappedrepl import WrappedRepl


class IRepl(InteractiveMixin, WrappedRepl):
    pass


class RRepl(RemoteMixin, WrappedRepl):
    pass


if __name__ == "__main__":
    c = load_config_for("haskell")
    try:
        os.setpgrp()
        r = RRepl(config=c)
        #  r.get_input()
        r.run()
    except KeyboardInterrupt:
        os.killpg(os.getpgrp(), signal.SIGTERM)
