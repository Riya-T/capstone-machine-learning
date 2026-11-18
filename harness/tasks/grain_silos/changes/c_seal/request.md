Let silos in `silos.py` be sealed, for example while the grain inside is
being fumigated. No grain may enter or leave a sealed silo.

- Add `Silos.seal(silo)` and `Silos.unseal(silo)`. Both raise `KeyError`
  for a silo that is not in use. New silos are not sealed. Sealing a
  sealed silo, or unsealing one that is not sealed, does nothing.
- Add `Silos.get_sealed() -> list[str]`, which returns the names of the
  sealed silos, in the order of `get_silos()`.
- Add `class SiloSealed(SiloError)` to `silos.py`.
- `load`, `unload`, `blend_into`, `demolish_silo`, and every other method
  that moves grain into or out of a silo, including methods added by other
  changes, raise `SiloSealed` and change nothing when any silo named in the
  call is sealed, whether grain would enter it or leave it. This holds
  even when no grain would actually move, for example `blend_into` from an
  empty silo, or demolishing an empty sealed silo.
- When a call would also raise another error, which error is raised is
  unspecified.
- The `get_` methods work as before on sealed silos, and `unseal` lifts the
  seal.
- `seal` and `unseal` are recorded like the other calls that change the
  silos, so `undo` reverses them too, and `undo` still restores the exact
  earlier state.

All existing behavior must keep working.
