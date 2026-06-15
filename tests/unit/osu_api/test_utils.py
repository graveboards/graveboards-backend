


def _create_mock_beatmap(**overrides):
    mock_data = {
        "id": 100001,
        "beatmapset_id": 10000,
        "status": "ranked",
        "ruleset_id": 0,
        "difficulty_rating": 4.5,
        "version": "Hard",
        "accuracy": 95.0,
        "ar": 9.0,
        "bpm": 120.0,
        "cs": 4.0,
        "drain": 5.0,
        "hit_length": 180,
        "mode": 0,
        "passcount": 100,
        "playcount": 1000,
        "max_combo": 500,
        "checksum": "a1b2c3d4e5f6",
        "count_circles": 100,
        "count_sliders": 50,
        "count_spinners": 10,
        "deleted_at": None,
        "failtimes": {},
        "is_scoreable": True,
        "last_updated": "2024-01-01T00:00:00Z",
        "mode_int": 0,
        "ranked": 1,
        "total_length": 180,
        "url": "https://osu.ppy.sh/b/100001",
        "user_id": 1000,
    }
    mock_data.update(overrides)
    return mock_data


def _create_mock_beatmapset(**overrides):
    mock_data = {
        "id": 10000,
        "status": "ranked",
        "user_id": 1000,
        "title": "Test Song",
        "creator": "Test Creator",
        "artist": "Test Artist",
        "artist_unicode": "Test Artist",
        "bpm": 120.0,
        "cover": "https://assets.ppy.sh/beatmaps/10000/covers/cover.jpg",
        "covers": {
            "list": "https://assets.ppy.sh/beatmaps/10000/covers/list.jpg",
            "card": "https://assets.ppy.sh/beatmaps/10000/covers/card.jpg",
            "cover": "https://assets.ppy.sh/beatmaps/10000/covers/cover.jpg",
            "cover@2x": "https://assets.ppy.sh/beatmaps/10000/covers/cover@2x.jpg",
            "channel": "https://assets.ppy.sh/beatmaps/10000/covers/channel.jpg",
            "channel@2x": "https://assets.ppy.sh/beatmaps/10000/covers/channel@2x.jpg",
            "storyboard": "https://assets.ppy.sh/beatmaps/10000/covers/storyboard.jpg",
            "storyboard@2x": "https://assets.ppy.sh/beatmaps/10000/covers/storyboard@2x.jpg",
            "beatmapset": "https://assets.ppy.sh/beatmaps/10000/covers/beatmapset.jpg",
            "beatmapset@2x": "https://assets.ppy.sh/beatmaps/10000/covers/beatmapset@2x.jpg",
        },
        "description": "Test description",
        "favourite_count": 10,
        "genre": {"id": 1, "name": "Unspecified"},
        "hype": {"current": 5, "maximum": 10},
        "language": {"id": 1, "name": "Any"},
        "nominations_summary": {"current": 2, "required": 2},
        "play_count": 100,
        "preview_url": "//b.ppy.sh/preview/10000.mp3",
        "ranked": 1,
        "ranked_date": "2024-01-01T00:00:00Z",
        "ratings": [5, 5, 5, 5, 5],
        "source": "Test Source",
        "tags": "test osu",
        "title": "Test Song",
        "title_unicode": "Test Song",
        "video": False,
        "availability": {"download_disabled": False, "more_info": ""},
        "current_nominations": [],
        "discussion_enabled": True,
        "discussion_locked": False,
        "is_scoreable": True,
        "last_updated": "2024-01-01T00:00:00Z",
        "legacy_thread_url": "",
        "offset": 0,
        "pack_tags": [],
        "storyboard": False,
        "submitted_date": "2023-12-01T00:00:00Z",
        "spotlight": False,
    }
    mock_data.update(overrides)
    return mock_data


def _create_mock_user(ruleset="osu", **overrides):
    mock_data = {
        "id": 200001,
        "username": "test_user",
        "country": "US",
        "country_code": "US",
        "avatar_url": "https://example.com/avatar.png",
        "cover_url": "https://example.com/cover.png",
        "custom_url": "test_user",
        "is_active": True,
        "is_bot": False,
        "is_deleted": False,
        "is_supporter": False,
        "last_visit": "2024-01-01T00:00:00Z",
        "pm_friends_only": False,
        "profile_order": [],
        "title_id": None,
        "user_color": None,
        "ruleset": ruleset,
        "statistics": {
            "level": {
                "current": 50,
                "progress": 50,
            },
            "play_count": 10000,
            "rank": {
                "country": 100,
            },
            "pp": 1000.0,
            "accuracy": 95.0,
            "total_score": 10000000,
            "total_hits": 1000000,
            "maximum_combo": 5000,
            "replays_watched_by_others": 100,
            "grade_counts": {
                "ss": 10,
                "s": 50,
                "a": 100,
            },
            "rank": {
                "country": 100,
            },
        },
        "rank_highest": {
            "rank": 100,
            "updated_at": "2024-01-01T00:00:00Z",
        },
        "created_at": "2020-01-01T00:00:00Z",
        "friends": [],
        "interests": [],
        "occupation": "",
        "location": "",
        "total_seconds_used": 100000,
        "pending_marketplace_placements": False,
        "signature": "",
        "avatar_lock_status": None,
        "avatar_lock_reason": None,
        "github": "",
        "discord": "",
        "website": "",
        "donation_level": 0,
        "change_name_history": [],
    }
    mock_data.update(overrides)
    return mock_data


def _create_mock_score(**overrides):
    mock_data = {
        "id": 300001,
        "user_id": 200001,
        "beatmap_id": 100001,
        "rank": "S",
        "mods": [4, 16],
        "score": 950000,
        "max_combo": 500,
        "perfect": True,
        "type": "best",
        "statistics": {
            "count_50": 0,
            "count_100": 10,
            "count_300": 300,
            "count_geki": 10,
            "count_katsu": 5,
            "count_miss": 0,
        },
        "total_score": 950000,
        "pp": 200.0,
        "weight": {
            "percentage": 100.0,
            "pp": 200.0,
        },
        "start_time": "2024-01-01T00:00:00Z",
        "ended_at": "2024-01-01T00:03:00Z",
        "comment": "",
        "mod": ["HR", "HD"],
    }
    mock_data.update(overrides)
    return mock_data


def _create_mock_beatmap_scores(beatmap_id=None, **overrides):
    if beatmap_id is None:
        beatmap_id = 100001
    mock_data = {
        "beatmap_id": beatmap_id,
        "scores": [
            {
                "id": 300001,
                "user_id": 200001,
                "beatmap_id": beatmap_id,
                "rank": "S",
                "mods": [4, 16],
                "score": 950000,
                "max_combo": 500,
                "perfect": True,
                "statistics": {
                    "count_50": 0,
                    "count_100": 10,
                    "count_300": 300,
                    "count_geki": 10,
                    "count_katsu": 5,
                    "count_miss": 0,
                },
                "total_score": 950000,
                "pp": 200.0,
                "weight": {
                    "percentage": 100.0,
                    "pp": 200.0,
                },
                "start_time": "2024-01-01T00:00:00Z",
                "ended_at": "2024-01-01T00:03:00Z",
                "comment": "",
                "mod": ["HR", "HD"],
            }
        ],
    }
    mock_data.update(overrides)
    return mock_data


def _create_mock_beatmap_attributes(beatmap_id=None, **overrides):
    if beatmap_id is None:
        beatmap_id = 100001
    mock_data = {
        "attributes": {
            "beatmap_id": beatmap_id,
            "difficulty_rating": 4.5,
            "total_length": 180,
            "user_id": 1000,
            "version": "Hard",
            "accuracy": 95.0,
            "ar": 9.0,
            "bpm": 120.0,
            "cs": 4.0,
            "drain": 5.0,
            "count_circles": 100,
            "count_sliders": 50,
            "count_spinners": 10,
            "max_combo": 500,
            "mode": 0,
            "tags": ["test", "easy"],
            "favourite_count": 100,
            "playcount": 1000,
            "passcount": 100,
            "allow_custom_difficulty": True,
            "allow UserModel": True,
            "allow UserModel_scores": True,
            "allow UserModel_mods": True,
            "allow UserModel_leaderboard": True,
            "allow UserModel_chat": True,
            "allow UserModel_report": True,
            "allow UserModel_moderation": True,
            "allow UserModel_admin": True,
            "allow UserModel_system": True,
            "allow UserModel_donation": True,
            "allow UserModel_supporter": True,
            "allow UserModel_patron": True,
            "allow UserModel_veteran": True,
            "allow UserModel_contributor": True,
            "allow UserModel_developer": True,
            "allow UserModel_maintainer": True,
            "allow UserModel_mod": True,
            "allow UserModel_editor": True,
            "allow UserModel_beta": True,
            "allow UserModel_alpha": True,
            "allow UserModel_dev": True,
            "allow UserModel_admin": True,
            "allow UserModel_sys": True,
            "allow UserModel_don": True,
            "allow UserModel_sup": True,
            "allow UserModel_pat": True,
            "allow UserModel_vet": True,
            "allow UserModel_con": True,
            "allow UserModel_dev": True,
            "allow UserModel_mod": True,
            "allow UserModel_ed": True,
            "allow UserModel_bet": True,
            "allow UserModel_alp": True,
        },
        "mods": [16],
        "remaining_beatmapset_locks": 0,
        "remaining_beatmap_locks": 0,
        "remaining_user_locks": 0,
    }
    mock_data.update(overrides)
    return mock_data


def _create_mock_tags(**overrides):
    mock_data = {
        "tags": ["test", "osu", "easy", "mapped"],
    }
    mock_data.update(overrides)
    return mock_data


def _create_mock_rankings_user(**overrides):
    mock_data = {
        "user_id": 200001,
        "username": "test_user",
        "country": "US",
        "country_code": "US",
        "avatar_url": "https://example.com/avatar.png",
        "cover_url": "https://example.com/cover.png",
        "custom_url": "test_user",
        "is_active": True,
        "is_bot": False,
        "is_deleted": False,
        "is_supporter": False,
        "last_visit": "2024-01-01T00:00:00Z",
        "pm_friends_only": False,
        "profile_order": [],
        "title_id": None,
        "user_color": None,
        "statistics": {
            "play_count": 10000,
            "rank": {
                "country": 100,
            },
            "pp": 1000.0,
            "accuracy": 95.0,
            "total_score": 10000000,
            "total_hits": 1000000,
            "maximum_combo": 5000,
            "replays_watched_by_others": 100,
            "grade_counts": {
                "ss": 10,
                "s": 50,
                "a": 100,
            },
        },
        "rank_highest": {
            "rank": 100,
            "updated_at": "2024-01-01T00:00:00Z",
        },
        "created_at": "2020-01-01T00:00:00Z",
        "friends": [],
        "interests": [],
        "occupation": "",
        "location": "",
        "total_seconds_used": 100000,
        "pending_marketplace_placements": False,
        "signature": "",
        "avatar_lock_status": None,
        "avatar_lock_reason": None,
        "github": "",
        "discord": "",
        "website": "",
        "donation_level": 0,
        "change_name_history": [],
    }
    mock_data.update(overrides)
    return mock_data
