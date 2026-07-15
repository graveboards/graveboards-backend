"""Known IDs for hard-to-find coverage gaps.

These are IDs of beatmapsets/users that are difficult to find via random search
due to API limitations (NSFW content, restricted users, rare statuses).

Update this file when discovering new IDs.
"""

# Beatmapset IDs with restricted/deleted user references
# These beatmapsets have empty user objects due to:
# - Type 1: User account restricted (banned) but beatmapset still exists
# - Type 2: User account deleted from osu! database
# Example: beatmapset 744593 (SOOOO - Happppy song) has restricted user
# Example: beatmapset 117 (Billy Joel - Uptown Girl) has deleted user
RESTRICTED_BEATMAPSET_IDS = [
    744593,  # SOOOO - Happppy song (restricted user)
    117,  # Billy Joel - Uptown Girl (deleted user)
]

# NSFW beatmapset IDs
# These are beatmapsets marked as NSFW (not returned by search API by default)
# Corresponds to the "Explicit" tag on the osu! website
# Organized by mode: taiko, fruits, mania, osu (5 each + 1 existing = 6 taiko, 5 others)
NSFW_BEATMAPSET_IDS = [
    # Taiko
    2526004,  # May These Noises Startle You In Your Sleep Tonight / Hell Above
    2268255,
    2336948,
    2550405,
    2532269,
    # Fruits
    2520794,
    2525818,
    1016325,
    2559576,
    2542546,
    # Mania
    2443377,
    2515013,
    2559592,
    1502865,
    2484635,
    # Osu
    2555391,
    2548848,
    2278182,
    2113239,
    2513658,
]
