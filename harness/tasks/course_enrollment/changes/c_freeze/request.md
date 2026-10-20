Add an enrollment freeze control.

- Add `set_freeze(frozen: bool)` and initialize the system in the unfrozen
  state.
- While frozen, every call to `enroll` raises `RuntimeError` before checking
  the student or course and changes no enrollment or waitlist state.
- Calling `set_freeze(False)` resumes normal enrollment behavior.
- Adding courses, registering students, and recording prerequisite completion
  remain allowed while frozen.

All existing behavior must keep working.
