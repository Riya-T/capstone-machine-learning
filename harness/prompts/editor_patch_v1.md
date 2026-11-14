You are changing an existing Python program. Make the change requested below
while keeping all existing behavior working. Use Python 3.11 and only the
standard library.

## Change request

$request

## Current program

$files

## Your latest turns

$history

## Result of your last action

$feedback

## How to reply

You may change only these files: $allowed_files
You have $turns_left turns left, including this one.

Change the code with search-and-replace edits, never by sending whole files.
Each edit names the file, quotes the lines to replace exactly as they are in
the current program, and gives the lines to put in their place:

example.py
<<<<<<< SEARCH
    def total(self):
        return sum(self.items)
=======
    def total(self):
        return sum(item.price for item in self.items)
>>>>>>> REPLACE

The SEARCH lines must match the current file exactly, including indentation,
and match only one place: quote a few more lines if they could match twice.
Keep each edit small: quote only the lines you change and enough around them
to place the edit, and leave out code you don't change. Don't put ``` lines
inside an edit.

SEARCH holds only code that is already in the file. To add new code, such as
a new method, quote the existing lines it should follow and repeat them in
REPLACE with the new code after them. This adds count() after total():

example.py
<<<<<<< SEARCH
    def total(self):
        return sum(item.price for item in self.items)
=======
    def total(self):
        return sum(item.price for item in self.items)

    def count(self):
        return len(self.items)
>>>>>>> REPLACE

Edits apply in order, each to the file as your earlier edits left it, so
make one edit per place: never quote lines that an earlier edit in the same
reply already changed. An edit that does not match is skipped and reported;
the others still apply.

Then put one of these on a line by itself, outside any edit:

RUN_CHECKS
    Apply your edits, run the public checks, and see the results next turn.
DONE
    Apply your edits and finish. Do this once the change is complete.

A reply may contain edits and one command. Code you don't edit stays as it
is. If the checks failed, change the code before running them again: running
them on the same code gives the same result.
