from enum import Enum, IntEnum, auto
from typing import Union

from sqlalchemy.orm import InstrumentedAttribute

from app.database.ctes.hashable_cte import HashableCTE
from app.database.models import ModelClass, Profile, BeatmapSnapshot, BeatmapsetSnapshot, Request, Queue
from .field_category import SearchableFieldCategory


class ModelField(Enum):
    PROFILE__AVATAR_URL = "avatar_url", ModelClass.PROFILE, Profile.avatar_url
    PROFILE__USERNAME = "username", ModelClass.PROFILE, Profile.username
    PROFILE__COUNTRY_CODE = "country_code", ModelClass.PROFILE, Profile.country_code
    PROFILE__GRAVEYARD_BEATMAPSET_COUNT = "graveyard_beatmapset_count", ModelClass.PROFILE, Profile.graveyard_beatmapset_count
    PROFILE__LOVED_BEATMAPSET_COUNT = "loved_beatmapset_count", ModelClass.PROFILE, Profile.loved_beatmapset_count
    PROFILE__PENDING_BEATMAPSET_COUNT = "pending_beatmapset_count", ModelClass.PROFILE, Profile.pending_beatmapset_count
    PROFILE__RANKED_BEATMAPSET_COUNT = "ranked_beatmapset_count", ModelClass.PROFILE, Profile.ranked_beatmapset_count
    PROFILE__IS_RESTRICTED = "is_restricted", ModelClass.PROFILE, Profile.is_restricted
    PROFILE__TOTAL_MAPS = "total_maps", ModelClass.PROFILE, Profile.total_maps
    PROFILE__TOTAL_KUDOSU = "total_kudosu", ModelClass.PROFILE, Profile.total_kudosu

    BEATMAPSNAPSHOT__BEATMAP_ID = "beatmap_id", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.beatmap_id
    BEATMAPSNAPSHOT__USER_ID = "user_id", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.user_id
    BEATMAPSNAPSHOT__ACCURACY = "accuracy", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.accuracy
    BEATMAPSNAPSHOT__AR = "ar", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.ar
    BEATMAPSNAPSHOT__BPM = "bpm", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.bpm
    BEATMAPSNAPSHOT__CHECKSUM = "checksum", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.checksum
    BEATMAPSNAPSHOT__COUNT_CIRCLES = "count_circles", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.count_circles
    BEATMAPSNAPSHOT__COUNT_SLIDERS = "count_sliders", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.count_sliders
    BEATMAPSNAPSHOT__COUNT_SPINNERS = "count_spinners", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.count_spinners
    BEATMAPSNAPSHOT__CS = "cs", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.cs
    BEATMAPSNAPSHOT__DELETED_AT = "deleted_at", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.deleted_at
    BEATMAPSNAPSHOT__DIFFICULTY_RATING = "difficulty_rating", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.difficulty_rating
    BEATMAPSNAPSHOT__DRAIN = "drain", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.drain
    BEATMAPSNAPSHOT__HIT_LENGTH = "hit_length", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.hit_length
    BEATMAPSNAPSHOT__IS_SCOREABLE = "is_scoreable", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.is_scoreable
    BEATMAPSNAPSHOT__LAST_UPDATED = "last_updated", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.last_updated
    BEATMAPSNAPSHOT__MAX_COMBO = "max_combo", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.max_combo
    BEATMAPSNAPSHOT__MODE = "mode", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.mode
    BEATMAPSNAPSHOT__MODE_INT = "mode_int", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.mode_int
    BEATMAPSNAPSHOT__PASSCOUNT = "passcount", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.passcount
    BEATMAPSNAPSHOT__PLAYCOUNT = "playcount", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.playcount
    BEATMAPSNAPSHOT__RANKED = "ranked", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.ranked
    BEATMAPSNAPSHOT__STATUS = "status", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.status
    BEATMAPSNAPSHOT__TOTAL_LENGTH = "total_length", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.total_length
    BEATMAPSNAPSHOT__URL = "url", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.url
    BEATMAPSNAPSHOT__VERSION = "version", ModelClass.BEATMAP_SNAPSHOT, BeatmapSnapshot.version

    BEATMAPSETSNAPSHOT__BEATMAPSET_ID = "beatmapset_id", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.beatmapset_id
    BEATMAPSETSNAPSHOT__USER_ID = "user_id", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.user_id
    BEATMAPSETSNAPSHOT__ARTIST = "artist", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.artist
    BEATMAPSETSNAPSHOT__ARTIST_UNICODE = "artist_unicode", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.artist_unicode
    BEATMAPSETSNAPSHOT__BPM = "bpm", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.bpm
    BEATMAPSETSNAPSHOT__CAN_BE_HYPED = "can_be_hyped", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.can_be_hyped
    BEATMAPSETSNAPSHOT__CREATOR = "creator", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.creator
    BEATMAPSETSNAPSHOT__DELETED_AT = "deleted_at", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.deleted_at
    BEATMAPSETSNAPSHOT__DISCUSSION_ENABLED = "discussion_enabled", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.discussion_enabled
    BEATMAPSETSNAPSHOT__DISCUSSION_LOCKED = "discussion_locked", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.discussion_locked
    BEATMAPSETSNAPSHOT__FAVOURITE_COUNT = "favourite_count", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.favourite_count
    BEATMAPSETSNAPSHOT__IS_SCOREABLE = "is_scoreable", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.is_scoreable
    BEATMAPSETSNAPSHOT__LAST_UPDATED = "last_updated", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.last_updated
    BEATMAPSETSNAPSHOT__LEGACY_THREAD_URL = "legacy_thread_url", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.legacy_thread_url
    BEATMAPSETSNAPSHOT__NSFW = "nsfw", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.nsfw
    BEATMAPSETSNAPSHOT__OFFSET = "offset", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.offset
    BEATMAPSETSNAPSHOT__PLAY_COUNT = "play_count", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.play_count
    BEATMAPSETSNAPSHOT__PREVIEW_URL = "preview_url", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.preview_url
    BEATMAPSETSNAPSHOT__RANKED = "ranked", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.ranked
    BEATMAPSETSNAPSHOT__RATING = "rating", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.rating
    BEATMAPSETSNAPSHOT__SOURCE = "source", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.source
    BEATMAPSETSNAPSHOT__SPOTLIGHT = "spotlight", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.spotlight
    BEATMAPSETSNAPSHOT__STATUS = "status", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.status
    BEATMAPSETSNAPSHOT__SUBMITTED_DATE = "submitted_date", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.submitted_date
    BEATMAPSETSNAPSHOT__TAGS = "tags", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.tags
    BEATMAPSETSNAPSHOT__TITLE = "title", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.title
    BEATMAPSETSNAPSHOT__TITLE_UNICODE = "title_unicode", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.title_unicode
    BEATMAPSETSNAPSHOT__TRACK_ID = "track_id", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.track_id
    BEATMAPSETSNAPSHOT__VIDEO = "video", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.video
    BEATMAPSETSNAPSHOT__AVAILABILITY__DOWNLOAD_DISABLED = "availability_download_disabled", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.availability_download_disabled
    BEATMAPSETSNAPSHOT__AVAILABILITY__MORE_INFORMATION = "availability_more_information", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.availability_more_information
    BEATMAPSETSNAPSHOT__DESCRIPTION__DESCRIPTION = "description_description", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.description_description, "description"
    BEATMAPSETSNAPSHOT__GENRE__ID = "genre_id", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.genre_id
    BEATMAPSETSNAPSHOT__GENRE__NAME = "genre_name", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.genre_name
    BEATMAPSETSNAPSHOT__HYPE__CURRENT = "hype_current", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.hype_current
    BEATMAPSETSNAPSHOT__HYPE__REQUIRED = "hype_required", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.hype_required
    BEATMAPSETSNAPSHOT__LANGUAGE__ID = "language_id", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.language_id
    BEATMAPSETSNAPSHOT__LANGUAGE__NAME = "language_name", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.language_name
    # BEATMAPSETSNAPSHOT__TAGS = "tags", ModelClass.BEATMAPSET_SNAPSHOT, HashableCTE(beatmapset_tags_cte)
    BEATMAPSETSNAPSHOT__NOMINATIONS_SUMMARY_CURRENT = "nominations_summary_current", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.nominations_summary_current
    BEATMAPSETSNAPSHOT__NOMINATIONS_SUMMARY_REQUIRED_META_MAIN_RULESET = "nominations_summary_required_meta_main_ruleset", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.nominations_summary_required_meta_main_ruleset
    BEATMAPSETSNAPSHOT__NOMINATIONS_SUMMARY_REQUIRED_META_NON_MAIN_RULESET = "nominations_summary_required_meta_non_main_ruleset", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.nominations_summary_required_meta_non_main_ruleset
    BEATMAPSETSNAPSHOT__NUM_DIFFICULTIES = "num_difficulties", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.num_difficulties
    BEATMAPSETSNAPSHOT__SR_GAPS__MIN = "sr_gaps_min", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.sr_gaps_min
    BEATMAPSETSNAPSHOT__SR_GAPS__MAX = "sr_gaps_max", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.sr_gaps_max
    BEATMAPSETSNAPSHOT__SR_GAPS__AVG = "sr_gaps_avg", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.sr_gaps_avg
    BEATMAPSETSNAPSHOT__HIT_LENGTHS__MIN = "hit_lengths_min", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.hit_lengths_min
    BEATMAPSETSNAPSHOT__HIT_LENGTHS__MAX = "hit_lengths_max", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.hit_lengths_max
    BEATMAPSETSNAPSHOT__HIT_LENGTHS__AVG = "hit_lengths_avg", ModelClass.BEATMAPSET_SNAPSHOT, BeatmapsetSnapshot.hit_lengths_avg

    QUEUE__USER_ID = "user_id", ModelClass.QUEUE, Queue.user_id
    QUEUE__NAME = "name", ModelClass.QUEUE, Queue.name
    QUEUE__DESCRIPTION = "description", ModelClass.QUEUE, Queue.description
    QUEUE__CREATED_AT = "created_at", ModelClass.QUEUE, Queue.created_at
    QUEUE__UPDATED_AT = "updated_at", ModelClass.QUEUE, Queue.updated_at
    QUEUE__IS_OPEN = "is_open", ModelClass.QUEUE, Queue.is_open
    QUEUE__VISIBILITY = "visibility", ModelClass.QUEUE, Queue.visibility

    REQUEST__USER_ID = "user_id", ModelClass.REQUEST, Request.user_id
    REQUEST__BEATMAPSET_ID = "beatmapset_id", ModelClass.REQUEST, Request.beatmapset_id
    REQUEST__QUEUE_ID = "queue_id", ModelClass.REQUEST, Request.queue_id
    REQUEST__COMMENT = "comment", ModelClass.REQUEST, Request.comment
    REQUEST__MV_CHECKED = "mv_checked", ModelClass.REQUEST, Request.mv_checked
    REQUEST__CREATED_AT = "created_at", ModelClass.REQUEST, Request.created_at
    REQUEST__UPDATED_AT = "updated_at", ModelClass.REQUEST, Request.updated_at
    REQUEST__STATUS = "status", ModelClass.REQUEST, Request.status

    def __init__(self, field_name: str, model_class: ModelClass, target: Union[InstrumentedAttribute, HashableCTE], alias: str = None):
        self._value_ = f"{model_class.value.__name__}.{field_name}"
        self.field_name = field_name
        self.model_class = model_class
        self.target = target
        self.alias = alias

    @classmethod
    def from_category_field(cls, category_name: str, field_name: str) -> "ModelField":
        for category in SearchableFieldCategory.__members__.values():
            if category_name == category.value:
                for member in cls.__members__.values():
                    if (
                        category.model_class is member.model_class
                        and (
                            field_name == member.field_name
                            or (
                                member.is_aliased and field_name == member.alias
                            )
                        )
                    ):
                        return member

        raise ValueError(f"No ModelField exists with category '{category_name}' and field '{field_name}'")

    @property
    def is_aliased(self) -> bool:
        return self.alias is not None


ModelFieldId = IntEnum("ModelFieldId", {field.name: auto() for field in ModelField})
