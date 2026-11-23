from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile


def main():
    repository = Path(__file__).resolve().parents[1]
    output = repository / "Sublime Atari 6502.sublime-package"
    resource_suffixes = {
        ".sublime-build",
        ".sublime-commands",
        ".sublime-completions",
        ".sublime-menu",
        ".sublime-settings",
        ".sublime-syntax",
        ".tmPreferences",
    }
    files = [repository / name for name in ("asm6502.py", "LICENSE", "README.md")]
    files.extend(
        path for path in repository.iterdir()
        if path.is_file() and path.suffix in resource_suffixes
    )

    with NamedTemporaryFile(dir=repository, suffix=".tmp", delete=False) as temporary:
        staged = Path(temporary.name)
    try:
        with ZipFile(staged, "w", compression=ZIP_DEFLATED) as archive:
            for path in sorted(files):
                archive.write(path, arcname=path.name)
        staged.replace(output)
    finally:
        staged.unlink(missing_ok=True)

    print(f"Built {output}")


if __name__ == "__main__":
    main()
