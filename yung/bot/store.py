import json
from pathlib import Path

DATA = Path("data")
AUTOMATION_DATA = (
    Path(__file__).resolve().parent
    / "commands"
    / "automasi"
)


def _path(name, feature=None):
    if Path(name).name != name:
        raise ValueError("Nama file data harus berupa nama file, bukan path.")
    if feature and Path(feature).name != feature:
        raise ValueError("Nama fitur data harus berupa satu nama folder.")
    directory = (
        AUTOMATION_DATA / feature / "data"
        if feature
        else DATA
    )
    directory.mkdir(parents=True, exist_ok=True)
    return directory / name


def read(name, default, *, feature=None):
    path = _path(name, feature)
    if feature:
        legacy_paths = (DATA / feature / name, DATA / name)
        for legacy_path in legacy_paths:
            if path.exists() or not legacy_path.exists():
                continue
            try:
                data = json.loads(legacy_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            else:
                write(name, data, feature=feature)
                return data
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        path.write_text(
            json.dumps(default, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return default


def write(name, data, *, feature=None):
    path = _path(name, feature)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
