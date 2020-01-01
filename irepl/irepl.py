
from interactive import InteractiveMixin
from config import load_config_for
from wrappedrepl import WrappedRepl


class IRepl(InteractiveMixin, WrappedRepl):
    pass


if __name__ == "__main__":
    config = load_config_for("haskell")
    r = IRepl(config)
    #  print(dir(r))
    r.run()
