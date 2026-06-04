__all__ = ["BeatmapManager"]


def __getattr__(name):
    if name == "BeatmapManager":
        from .manager import BeatmapManager

        return BeatmapManager

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
