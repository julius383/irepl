
import os
import time
import signal
import sys
from interactive import InteractiveMixin
from remote import RemoteMixin
from config import load_config_for
from wrappedrepl import WrappedRepl


class IRepl(InteractiveMixin, WrappedRepl):
    pass


class RRepl(RemoteMixin, WrappedRepl):
    pass


class DRepl(InteractiveMixin, WrappedRepl):
    def run(self):
        while True:
            user_input = self.get_input()
            #  print(user_input, end='')
            os.write(self.master_in, str.encode(f"{user_input}\n", "utf-8"))
            # fixes problem of output appearing later than
            # expression that produces it
            time.sleep(0.1)
            output, err = self.get_repl_output()
            if output:
                print(output, end='')


def main():
    if sys.argv[1]:
        c = load_config_for(sys.argv[1])
    else:
        c = load_config_for("python")
    try:
        os.setpgrp()
        r = IRepl(config=c, echo=True)
        #  print(dir(r))
        r.run()
    except KeyboardInterrupt:
        os.killpg(os.getpgrp(), signal.SIGTERM)


if __name__ == "__main__":
    main()
