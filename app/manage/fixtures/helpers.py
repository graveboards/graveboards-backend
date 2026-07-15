def get_categories_to_process(
    beatmaps: bool,
    beatmapsets: bool,
    users: bool,
    scores: bool,
    beatmap_scores: bool,
    beatmap_attributes: bool,
    queues: bool = False,
    requests: bool = False,
) -> list[str]:
    all_categories = not any([beatmaps, beatmapsets, users, scores, beatmap_scores, beatmap_attributes, queues, requests])

    categories_to_process = []
    if all_categories or beatmaps:
        categories_to_process.append("beatmaps")
    if all_categories or beatmapsets:
        categories_to_process.append("beatmapsets")
    if all_categories or beatmap_scores:
        categories_to_process.append("beatmap_scores")
    if all_categories or beatmap_attributes:
        categories_to_process.append("beatmap_attributes")
    if all_categories or users:
        categories_to_process.append("users")
    if all_categories or scores:
        categories_to_process.append("scores")
    if all_categories or queues:
        categories_to_process.append("queues")
    if all_categories or requests:
        categories_to_process.append("requests")

    return categories_to_process
