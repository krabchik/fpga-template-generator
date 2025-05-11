import pathlib
import shutil


def clear_dir(directory: pathlib.Path):
    if not directory.is_dir():
        return

    for path in directory.iterdir():
        if path.is_file() or path.is_symlink():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
