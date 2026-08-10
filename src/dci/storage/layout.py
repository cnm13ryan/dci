"""Durable-storage resolution without Colab assumptions.

Reproduces the notebook's semantics exactly, with Google Drive demoted to one
optional adapter:

  * colab + Drive mounted      -> DURABLE_BASE = CFG.drive_root (on Drive)
  * mirror on, no Drive, local
    fallback allowed           -> DURABLE_BASE = CFG.local_root/drive_fallback
                                  (the validated headless-dry-run path)
  * mirror on, no fallback     -> hard error, as before
  * mirror off                 -> DURABLE_BASE = CFG.local_root

On a workstation or Lambda instance, point --data-root at a durable location
(local project disk, or /lambda/nfs/<name> for a Lambda persistent filesystem).
The instance root disk is erased on termination, so on Lambda the durable root
belongs on the persistent filesystem or must be exported before terminate.
"""
from __future__ import annotations

from pathlib import Path

# The notebook's shipped roots both live under Colab's ephemeral /content. A
# root that is NOT under /content was configured deliberately and is therefore
# the durable root; one that is under it is the unconfigured default.
COLAB_EPHEMERAL_ROOT = Path("/content")


def is_colab_default_root(path) -> bool:
    """Whether `path` is inside Colab's ephemeral tree.

    Decided with path semantics, not with a text prefix: "/content-data/dci" is
    a perfectly good durable root on a workstation and startswith("/content")
    misclassified it as the notebook default, silently diverting the run into
    the local fallback.
    """
    return Path(path).is_relative_to(COLAB_EPHEMERAL_ROOT)


def resolve_durable_base(cfg) -> tuple[bool, str, Path]:
    """Return (DRIVE_AVAILABLE, DRIVE_NOTE, DURABLE_BASE) — notebook contract."""
    drive_available, note = False, ""
    if cfg.use_google_drive:
        try:  # pragma: no cover - only on Colab
            from google.colab import drive as _gdrive  # type: ignore
            _gdrive.mount("/content/drive")
            drive_available = Path("/content/drive/MyDrive").exists()
            note = "mounted"
        except Exception as exc:
            # Off Colab the decision must be DETERMINISTIC: concurrent shard
            # workers probing "does the parent exist yet" raced each other into
            # different branches. An explicitly configured root (anything that
            # is not under the notebook's /content default) IS the durable
            # root; the fallback branch remains only for the unconfigured
            # default.
            drive_available = not is_colab_default_root(cfg.drive_root)
            note = f"not mounted ({type(exc).__name__})"
    if cfg.use_google_drive and drive_available:
        base = Path(cfg.drive_root)
        base.mkdir(parents=True, exist_ok=True)
        return True, note or "local durable root", base
    if cfg.use_google_drive and cfg.allow_local_fallback:
        base = Path(cfg.local_root) / "drive_fallback"
        print(f"""
WARNING: the configured durable root is not available ({note}).
Falling back to {base}, which is LOCAL and disappears with this machine.
Persistence guarantees do not hold. This is permitted because
allow_local_fallback is set; unset it to make the durable mirror mandatory.
""")
        return False, note, base
    if cfg.use_google_drive:
        raise RuntimeError(
            "A durable mirror was requested, is unavailable, and local "
            "fallback is disabled. Point --data-root at a real disk or set "
            "allow_local_fallback.")
    return False, "mirror disabled", Path(cfg.local_root)
