You are changing an existing Python program. Make the change requested below
while keeping all existing behavior working. Use Python 3.11 and only the
standard library.

Work within the program's existing design: build the change on what the
program already has (its helper methods, its data structures and the way
it keeps its state) rather than adding a parallel mechanism next to them,
and keep the change as small as that design allows.

## Change request

$request

## Current program

The program is shown as an outline: imports, constants and class
attributes in full, but each function and method only as its signature and
docstring, with its body hidden (`...  # body hidden`), unless you opened
it or changed it during this change.

$files

## Your latest turns

$history

## Result of your last action

$feedback

## How to reply

You may change only these files: $allowed_files
You have $turns_left turns left, including this one.

To see the full code of functions or methods, put a line like this on its
own:

SHOW Inventory.add, Inventory._check_quantity

To change the program, send complete definitions of only the functions,
methods and classes you change or add, in fenced code blocks whose info
string is `python file=<path>`. Put a method inside its class; the class's
other members stay as they are:

```python file=example.py
class Inventory:
    def add(self, item, quantity):
        # the complete new body
```

A function or method you send replaces the one with the same name, or is
added if there is none. You can replace only functions and methods you
opened with SHOW in an earlier turn (or changed already): one you have not
seen is not applied, so open first and change next turn. An opened function
stays open for the rest of this change. New functions, methods and classes can be added at any time.
Imports and assignments to a name (constants, class attributes) can be sent
the same way. Nothing can be deleted.

Then put one of these on a line by itself, outside any code block:

RUN_CHECKS
    Apply your code, run the public checks, and see the results next turn.
DONE
    Apply your code and finish. Do this once the change is complete.

A reply may contain SHOW, code and one command. If the checks failed,
change the code before running them again: running them on the same code
gives the same result.
