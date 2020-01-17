
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

To add a new language edit the `languages.toml` file and add

* prompt - the prompt of the repl you want to Wrap
* continuation - which is the prompt during multi-line input prompt if any
* lexer - which is the pygments lexer for the language(this has the same name
  as the language)
* executable - which is command to execute to start the underlying REPL
* multiline - which is a pair of strings that single the start and end of 
  multi-line mode in some REPLs
* files - which consist of `history` and `init` which are the history and 
  initialization files for the language

Afterwards run `pip install -U -e .`
