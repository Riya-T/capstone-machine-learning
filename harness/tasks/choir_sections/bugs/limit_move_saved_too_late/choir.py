"""Choir sections with undo and a limit per section.

Planted bug (after c_undo and c_limit): limits were added correctly, but
move_singer, rewritten to check the limit, saves the state for undo only
after taking the singer out of their old section, so an undone move loses
the singer instead of putting them back.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from choir import Choir
    choir = Choir()
    choir.add_section("alto")
    choir.set_limit("alto", 1)
    choir.add_singer("alto", "Ada")
    choir.undo()  # Ada is gone again; the limit stays
"""


class ChoirError(Exception):
    pass


class SectionFull(ChoirError):
    pass


class Choir:
    def __init__(self):
        # section name -> list of singers in standing order; the dict keeps
        # the sections in the order they were added.
        self._sections = {}
        self._section_of = {}  # singer -> name of their section
        self._limits = {}  # section name -> limit; missing = no limit
        self._undo_stack = []  # (sections, limits) as they were before each call

    def add_section(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("section name must be a non-empty str")
        if name in self._sections:
            raise ChoirError(f"section name {name!r} is already used")
        self._save()
        self._sections[name] = []
        self._limits.pop(name, None)

    def add_singer(self, section, singer):
        self._require_section(section)
        if not isinstance(singer, str) or not singer:
            raise ValueError("singer name must be a non-empty str")
        if singer in self._section_of:
            raise ChoirError(f"singer {singer!r} is already in the choir")
        self._require_room(section, 1)
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
        self._require_room(to_section, 1)
        self._sections[section].remove(singer)
        self._save()
        self._sections[to_section].append(singer)
        self._section_of[singer] = to_section

    def merge_sections(self, source, into):
        self._require_section(source)
        self._require_section(into)
        if source == into:
            raise ValueError("cannot merge a section into itself")
        self._require_room(into, len(self._sections[source]))
        self._save()
        singers = self._sections.pop(source)
        self._limits.pop(source, None)
        self._sections[into].extend(singers)
        for singer in singers:
            self._section_of[singer] = into
        return len(singers)

    def move_all(self, source, into):
        self._require_section(source)
        self._require_section(into)
        if source == into:
            raise ValueError("cannot move singers into the section they are in")
        self._require_room(into, len(self._sections[source]))
        self._save()
        singers = self._sections[source]
        self._sections[source] = []
        self._sections[into].extend(singers)
        for singer in singers:
            self._section_of[singer] = into
        return len(singers)

    def set_limit(self, section, limit):
        self._require_section(section)
        if limit is not None and (
            isinstance(limit, bool) or not isinstance(limit, int) or limit < 1
        ):
            raise ValueError(f"limit must be None or an int of at least 1, got {limit!r}")
        self._save()
        if limit is None:
            self._limits.pop(section, None)
        else:
            self._limits[section] = limit

    def get_limit(self, section):
        self._require_section(section)
        return self._limits.get(section)

    def undo(self):
        if not self._undo_stack:
            raise ChoirError("nothing to undo")
        self._sections, self._limits = self._undo_stack.pop()
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
        sections = {name: list(singers) for name, singers in self._sections.items()}
        self._undo_stack.append((sections, dict(self._limits)))

    def _require_section(self, section):
        if not isinstance(section, str) or section not in self._sections:
            raise KeyError(section)

    def _require_singer(self, singer):
        if not isinstance(singer, str) or singer not in self._section_of:
            raise KeyError(singer)
        return self._section_of[singer]

    def _require_room(self, section, joining):
        limit = self._limits.get(section)
        if limit is not None and len(self._sections[section]) + joining > limit:
            raise SectionFull(f"section {section!r} has room for at most {limit} singers")
