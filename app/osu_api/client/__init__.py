__all__ = ["OsuAPIClient"]


def __getattr__(name):
    if name == "OsuAPIClient":
        from .osu_api_client import OsuAPIClient

        return OsuAPIClient

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
