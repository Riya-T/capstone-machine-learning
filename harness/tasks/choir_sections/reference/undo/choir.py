"""Choir sections with undo.

Correct solution for choir_sections after c_undo.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from choir import Choir
    choir = Choir()
    choir.add_section("alto")
    choir.add_singer("alto", "Ada")
    choir.remove_singer("Ada")
    choir.undo()  # Ada is back
"""


class ChoirError(Exception):
    pass


class Choir:
    def __init__(self):
        # section name -> list of singers in standing order; the dict keeps
        # the sections in the order they were added.
        self._sections = {}
        self._section_of = {}  # singer -> name of their section
        self._undo_stack = []  # copies of the sections as they were before each call

    def add_section(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("section name must be a non-empty str")
        if name in self._sections:
            raise ChoirError(f"section name {name!r} is already used")
        self._save()
        self._sections[name] = []

    def add_singer(self, section, singer):
        self._require_section(section)
        if not isinstance(singer, str) or not singer:
            raise ValueError("singer name must be a non-empty str")
        if singer in self._section_of:
            raise ChoirError(f"singer {singer!r} is already in the choir")
        self._save()
        self._sections[section].append(singer)
        self._section_of[singer] = section

    def remove_singer(self, singer):
        section = self._require_singer(singer)
        self._save()
        self._sections[section].remove(singer)
        del self._section_of[singer]

    def move_singer(self, singer, to_section):
        section = self._require_singer(singer)
        self._require_section(to_section)
        self._save()
        self._sections[section].remove(singer)
        self._sections[to_section].append(singer)
        self._section_of[singer] = to_section

    def merge_sections(self, source, into):
        self._require_section(source)
        self._require_section(into)
        if source == into:
            raise ValueError("cannot merge a section into itself")
        self._save()
        singers = self._sections.pop(source)
        self._sections[into].extend(singers)
        for singer in singers:
            self._section_of[singer] = into
        return len(singers)

    def move_all(self, source, into):
        self._require_section(source)
        self._require_section(into)
        if source == into:
            raise ValueError("cannot move singers into the section they are in")
        self._save()
        singers = self._sections[source]
        self._sections[source] = []
        self._sections[into].extend(singers)
        for singer in singers:
            self._section_of[singer] = into
        return len(singers)

    def undo(self):
        if not self._undo_stack:
            raise ChoirError("nothing to undo")
        self._sections = self._undo_stack.pop()
        self._section_of = {
            singer: section for section, singers in self._sections.items() for singer in singers
        }

    def get_singers(self, section):
        self._require_section(section)
        return list(self._sections[section])

    def get_sections(self):
        return list(self._sections)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._undo_stack.append({name: list(singers) for name, singers in self._sections.items()})

    def _require_section(self, section):
        if not isinstance(section, str) or section not in self._sections:
            raise KeyError(section)

    def _require_singer(self, singer):
        if not isinstance(singer, str) or singer not in self._section_of:
            raise KeyError(singer)
        return self._section_of[singer]
