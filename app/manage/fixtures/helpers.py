def get_categories_to_process(
    beatmaps: bool,
    beatmapsets: bool,
    users: bool,
    scores: bool,
    beatmap_scores: bool,
    beatmap_attributes: bool,
    all_categories: bool | None = None,
) -> list[tuple[str, str, str]]:
    if all_categories is None:
        all_categories = not any([beatmaps, beatmapsets, users, scores, beatmap_scores, beatmap_attributes])

    categories_to_process = []
    if all_categories or beatmaps:
        categories_to_process.append(("beatmaps", "beatmaps", "beatmaps"))
    if all_categories or beatmapsets:
        categories_to_process.append(("beatmapsets", "beatmapsets", "beatmapsets"))
    if all_categories or beatmap_scores:
        categories_to_process.append(("beatmap_scores", "beatmap_scores", "beatmap_scores"))
    if all_categories or beatmap_attributes:
        categories_to_process.append(("beatmap_attributes", "beatmap_attributes", "beatmap_attributes"))
    if all_categories or users:
        categories_to_process.append(("users", "users", "users"))
    if all_categories or scores:
        categories_to_process.append(("scores", "scores", "scores"))
    
    return categories_to_process
