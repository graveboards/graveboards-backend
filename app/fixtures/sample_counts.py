"""Sample count calculation for fixture fetching."""

from .constants import BASE_SAMPLE_COUNTS, MINIMAL_PROFILE


def calculate_sample_counts(
    scale: float = 1.0,
    beatmaps: int | None = None,
    beatmapsets: int | None = None,
    users_osu: int | None = None,
    users_taiko: int | None = None,
    users_fruits: int | None = None,
    users_mania: int | None = None,
    scores_best: int | None = None,
    scores_firsts: int | None = None,
    scores_recent: int | None = None,
    beatmap_scores: int | None = None,
    beatmap_attributes: int | None = None,
    use_minimal: bool = False,
) -> dict:
    """Calculate sample counts for fixture fetching.

    Args:
        scale: Scale factor for base counts (1.0 = base, 0.5 = half, 2.0 = double)
        beatmaps: Override count for beatmaps
        beatmapsets: Override count for beatmapsets
        users_osu: Override count for osu users
        users_taiko: Override count for taiko users
        users_fruits: Override count for fruits users
        users_mania: Override count for mania users
        scores_best: Override count for best scores
        scores_firsts: Override count for first scores
        scores_recent: Override count for recent scores
        beatmap_scores: Override count for beatmap scores
        beatmap_attributes: Override count for beatmap attributes
        use_minimal: Use minimal profile instead of base counts

    Returns:
        Dictionary with calculated counts for each category
    """
    has_explicit_categories = any(
        [
            beatmaps is not None,
            beatmapsets is not None,
            users_osu is not None,
            users_taiko is not None,
            users_fruits is not None,
            users_mania is not None,
            scores_best is not None,
            scores_firsts is not None,
            scores_recent is not None,
            beatmap_scores is not None,
            beatmap_attributes is not None,
        ]
    )

    if use_minimal:
        base = MINIMAL_PROFILE.copy()
    else:
        base = BASE_SAMPLE_COUNTS.copy()

    if scale != 1.0:
        if isinstance(base, dict):
            for key, value in base.items():
                if isinstance(value, int):
                    base[key] = max(1, int(value * scale))
                elif isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        base[key][subkey] = max(1, int(subvalue * scale))

    if has_explicit_categories:
        result = {}
    else:
        result = base.copy()

    overrides = {
        "beatmaps": beatmaps,
        "beatmapsets": beatmapsets,
        "users": {
            "osu": users_osu,
            "taiko": users_taiko,
            "fruits": users_fruits,
            "mania": users_mania,
        },
        "scores": {
            "best": scores_best,
            "firsts": scores_firsts,
            "recent": scores_recent,
        },
        "beatmap_scores": beatmap_scores,
        "beatmap_attributes": beatmap_attributes,
    }

    for key, override_value in overrides.items():
        if override_value is not None:
            if isinstance(override_value, dict):
                if key not in result:
                    result[key] = {}
                for subkey, subvalue in override_value.items():
                    if subvalue is not None:
                        result[key][subkey] = subvalue
            else:
                result[key] = override_value

    return result
