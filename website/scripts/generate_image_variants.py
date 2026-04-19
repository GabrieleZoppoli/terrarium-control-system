#!/usr/bin/env python3
"""Generate responsive srcset variants (480w, 960w) next to every JPEG
in static/img/collection/ and static/img/highland/.

For foo.jpg we emit foo-480.jpg and foo-960.jpg. If a variant already
exists and its mtime is newer than the source, we skip. Runs on macOS
(uses `sips`, no PIL dependency).

Usage:
    python3 scripts/generate_image_variants.py
    python3 scripts/generate_image_variants.py --force   # regenerate all
"""
import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
STATIC_DIR = REPO_ROOT / "static" / "img"
WIDTHS = [480, 960]
EXTS = {".jpg", ".jpeg", ".JPG", ".JPEG"}


def is_variant(path: Path) -> bool:
    """Return True if the filename looks like a variant (ends with -NNNN)."""
    stem = path.stem
    for w in WIDTHS:
        if stem.endswith(f"-{w}"):
            return True
    return False


def needs_regen(src: Path, dst: Path, force: bool) -> bool:
    if force or not dst.exists():
        return True
    return src.stat().st_mtime > dst.stat().st_mtime


def resize_to(src: Path, dst: Path, width: int) -> None:
    """Shell out to macOS `sips` — keeps aspect ratio, high-quality."""
    subprocess.run(
        [
            "sips",
            "--resampleWidth", str(width),
            "-s", "format", "jpeg",
            "-s", "formatOptions", "85",
            str(src),
            "--out", str(dst),
        ],
        check=True,
        capture_output=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force", action="store_true",
        help="Regenerate variants even if they look up-to-date",
    )
    parser.add_argument(
        "--subdir", default=None,
        help="Limit to a subdirectory under static/img (e.g. collection/heliamphora)",
    )
    args = parser.parse_args()

    root = STATIC_DIR if args.subdir is None else STATIC_DIR / args.subdir
    if not root.exists():
        print(f"error: {root} not found", file=sys.stderr)
        return 1

    generated = 0
    skipped = 0
    for src in root.rglob("*"):
        if src.suffix not in EXTS:
            continue
        if is_variant(src):
            continue
        for w in WIDTHS:
            dst = src.with_name(f"{src.stem}-{w}{src.suffix.lower()}")
            if needs_regen(src, dst, args.force):
                try:
                    resize_to(src, dst, w)
                    generated += 1
                    print(f"  [{w:>4}w] {dst.relative_to(REPO_ROOT)}")
                except subprocess.CalledProcessError as e:
                    print(
                        f"  FAIL {src.name} @ {w}w: {e.stderr.decode().strip()}",
                        file=sys.stderr,
                    )
            else:
                skipped += 1

    print(f"\n{generated} generated, {skipped} up-to-date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
