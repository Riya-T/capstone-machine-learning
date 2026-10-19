You are changing an existing Python program. Make the change requested below
while keeping all existing behavior working. Use Python 3.11 and only the
standard library.

## Change request

$request

## Current program

$files

## Result of your last action

$feedback

## How to reply

You may change only these files: $allowed_files
You have $turns_left turns left, including this one.

To replace a file, send its complete new contents (never a partial edit or a
diff) as a fenced code block whose info string is `python file=<path>`:

```python file=example.py
# complete file contents
```

Then put one of these on a line by itself, outside any code block:

RUN_CHECKS
    Apply your files, run the public checks, and see the results next turn.
DONE
    Apply your files and finish. Do this once the change is complete.

A reply may contain files and one command. Files you don't send stay as
they are.
