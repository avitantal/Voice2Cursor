import sys
from pathlib import Path


def app_base_dir() -> Path:
    return Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent


def resource_path(*parts: str) -> Path:
    candidates = []
    bundled_root = getattr(sys, "_MEIPASS", None)
    if bundled_root:
        candidates.append(Path(bundled_root))
    candidates.append(app_base_dir())
    candidates.append(Path(__file__).parent)

    for root in candidates:
        path = root.joinpath(*parts)
        if path.exists():
            return path
    return candidates[0].joinpath(*parts)


def app_icon_png() -> Path:
    return resource_path("assets", "voice2cursor-icon.png")


def app_icon_ico() -> Path:
    return resource_path("assets", "voice2cursor-icon.ico")
