
## Enhanced Repl

Wrap an existing REPL to add ipython like features

## Installation
Clone the repo and then in a virtual environment run(optional)

```sh
pip install -U -r requirements.txt
pip install -U -e .
```

To run enter:
```sh
irepl <language-name>
```

To add a new language edit the `langs.yml` file and add
* prompt - the prompt of the repl you want to Wrap
* lexer - which is the pygments lexer for the language(this usually
  corresponding
* the executable path
then run `pip install -U -e .`
