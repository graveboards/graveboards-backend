import struct
import re
from datetime import datetime
from typing import Union, Optional, Sequence, Any
from enum import IntFlag, auto, IntEnum

import numpy as np
from pydantic.main import BaseModel
from pydantic.fields import Field
from pydantic.functional_validators import model_validator, field_validator
from pydantic.config import ConfigDict

from app.security import safe_compile_regex

ConditionValue = Union[int, float, str, bool, datetime]
MAX_REGEX_LENGTH = 100
MAX_GROUPS = 10
DANGEROUS_PATTERNS = {
    r"\(\?<=.*?\)",     # Lookbehind
    r"\(\?<!.*?\)",     # Negative lookbehind
    r"\\\d+",           # Backreferences like \1
    r"\(\?P<.*?>",      # Named capture groups
    r"\(\?[^:=!#]"      # Other fancy constructs
}
SUSPICIOUS_PATTERNS = {
    r"\(\s*\.\*\s*\)\+",        # (.*)+ — classic ReDoS
    r"\(\s*\.\+\s*\)\+",        # (.+)+ — also dangerous
    r"\(\s*.+\*\s*\)\+",        # nested greedy quantifiers
    r"\(\s*\.\*\s*\)\{2,}",     # repeated (.*){2+}
    r"(\.\*){2,}",              # multiple chained .*
}
REGEX_TIMEOUT = 0.1


class ConditionValueId(IntEnum):
    SIGNED_CHAR = auto()
    SIGNED_VARINT = auto()
    UNSIGNED_CHAR = auto()
    UNSIGNED_VARINT = auto()
    HALF_FLOAT = auto()
    FLOAT = auto()
    DOUBLE = auto()
    STR = auto()
    BOOL = auto()
    DATETIME = auto()


class ConditionFieldFlag(IntFlag):
    EQ = auto()
    NEQ = auto()
    LT = auto()
    LTE = auto()
    GT = auto()
    GTE = auto()
    IN = auto()
    NOT_IN = auto()
    IS_NULL = auto()
    REGEX = auto()
    NOT_REGEX = auto()

    @property
    def field_name(self) -> str:
        return self.name.lower()


class Conditions(BaseModel):
    eq: Optional[ConditionValue] = None
    neq: Optional[ConditionValue] = None
    lt: Optional[ConditionValue] = None
    lte: Optional[ConditionValue] = None
    gt: Optional[ConditionValue] = None
    gte: Optional[ConditionValue] = None
    in_: Optional[Sequence[ConditionValue]] = Field(default=None, alias="in")
    not_in: Optional[Sequence[ConditionValue]] = Field(default=None)
    is_null: Optional[bool] = None
    regex: Optional[str] = None
    not_regex: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid"
    )

    def __repr__(self):
        non_null_fields = self.model_dump(exclude_none=True)
        fields_repr = ", ".join(f"{k}={v!r}" for k, v in non_null_fields.items())
        return f"{self.__class__.__name__}({fields_repr})"

    @model_validator(mode="before")
    @classmethod
    def normalize_shorthand(cls, value: Any):
        if isinstance(value, (cls, dict)):
            return value
        elif isinstance(value, ConditionValue):
            return {"eq": value}
        elif value is None:
            return {"is_null": True}
        else:
            raise TypeError(f"Shorthand value to normalize must be {Optional[ConditionValue]}, got {type(value).__name__}")

    @model_validator(mode="before")
    @classmethod
    def validate_condition_keys(cls, value: Any):
        if isinstance(value, dict):
            valid_keys = {
                field.alias if field.alias is not None else name
                for name, field in cls.model_fields.items()
            }

            if extras := set(value) - valid_keys:
                raise ValueError(f"Unsupported condition keys: {", ".join(extras)}")

        return value

    @field_validator("eq", "neq", "lt", "lte", "gt", "gte", "in_", "not_in", mode="before")
    @classmethod
    def parse_datetime(cls, value: Any):
        def parse_datetime_value(value_: Any):
            if isinstance(value_, str):
                try:
                    return datetime.fromisoformat(value_)
                except ValueError:
                    pass

            return value_

        if isinstance(value, list):
            return [parse_datetime_value(item) for item in value]

        return parse_datetime_value(value)

    @field_validator("regex", "not_regex", mode="after")
    @classmethod
    def validate_regex(cls, value: str):
        if value is None:
            return None

        if len(value) > MAX_REGEX_LENGTH:
            raise ValueError("Regex pattern too long or complex")

        if not value.strip():
            raise ValueError("Empty pattern")

        if re.search(r"\.\*\.\*", value) or (".+" in value and len(value) < 10):
            raise ValueError("Regex pattern may be unsafe or overly greedy")

        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, value):
                raise ValueError(f"Regex contains disallowed feature: {pattern}")

        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, value):
                raise ValueError(f"Regex contains a pattern that may lead to catastrophic backtracking: {pattern}")

        compiled = safe_compile_regex(value, timeout=REGEX_TIMEOUT)

        if compiled is None:
            # Bypassing compilation safety check (running on non-UNIX system)
            try:
                compiled = re.compile(value)
            except re.error as e:
                raise ValueError(f"Invalid regex: {e}")

        if compiled.groups > MAX_GROUPS:
            raise ValueError(f"Too many capture groups (>{MAX_GROUPS})")

        return value

    @model_validator(mode="after")
    def validate_logic(self):
        conditions = self.model_dump(exclude_unset=True)

        if not conditions or not any(v is not None for v in conditions.values()):
            raise ValueError("At least one condition must be specified")

        if self.is_null is True and len(conditions) > 1:
            raise ValueError("If 'is_null' is True, no other conditions can be specified")

        if self.eq is not None:
            if self.neq is not None and self.neq == self.eq:
                raise ValueError("'eq' and 'neq' cannot be the same value")

            if self.in_ and self.eq not in self.in_:
                raise ValueError("'eq' value must be included in 'in' if both are specified")

            if self.not_in and self.eq in self.not_in:
                raise ValueError("'eq' value must not be included in 'not_in'")

        if self.gt is not None and self.gte is not None:
            raise ValueError("Specify only one of 'gt' or 'gte'")

        if self.lt is not None and self.lte is not None:
            raise ValueError("Specify only one of 'lt' or 'lte'")

        lower_bound = self.gt if self.gt is not None else self.gte
        upper_bound = self.lt if self.lt is not None else self.lte

        if lower_bound is not None and upper_bound is not None:
            if self.gt is not None and self.lt is not None and self.gt >= self.lt:
                raise ValueError(f"Invalid range: gt ({self.gt}) >= lt ({self.lt})")

            if self.gt is not None and self.lte is not None and self.gt >= self.lte:
                raise ValueError(f"Invalid range: gt ({self.gt}) >= lte ({self.lte})")

            if self.gte is not None and self.lt is not None and self.gte >= self.lt:
                raise ValueError(f"Invalid range: gte ({self.gte}) >= lt ({self.lt})")

            if self.gte is not None and self.lte is not None and self.gte > self.lte:
                raise ValueError(f"Invalid range: gte ({self.gte}) > lte ({self.lte})")

        return self

    def values_for_validation(self) -> list[Any]:
        values = [self.eq, self.neq, self.lt, self.lte, self.gt, self.gte]
        values += (self.in_ or []) + (self.not_in or [])
        return [value for value in values if value is not None]

    def serialize(self) -> bytes:
        presence = 0
        chunks = []

        for flag in ConditionFieldFlag:
            field_name = flag.field_name
            attr_name = next(
                name for name, field in Conditions.model_fields.items()
                if field.alias == field_name or name == field_name
            )
            value = getattr(self, attr_name)

            if value is None:
                continue

            presence |= flag

            if flag in {
                ConditionFieldFlag.EQ, ConditionFieldFlag.NEQ, ConditionFieldFlag.LT,
                ConditionFieldFlag.LTE, ConditionFieldFlag.GT, ConditionFieldFlag.GTE,
                ConditionFieldFlag.REGEX, ConditionFieldFlag.NOT_REGEX
            }:
                chunks.append(self.serialize_condition_value(value))
            elif flag in {ConditionFieldFlag.IN, ConditionFieldFlag.NOT_IN}:
                chunks.append(struct.pack("!B", len(value)))

                for item in value:
                    chunks.append(self.serialize_condition_value(item))
            elif flag is ConditionFieldFlag.IS_NULL:
                chunks.append(struct.pack("!?", value))
            else:
                raise TypeError(f"Unsupported type for serialization. Expected {Union[ConditionValue, Sequence[ConditionValue]]}, got {type(value).__name__}")

        presence_byte = struct.pack("!H", presence)

        return presence_byte + b"".join(chunks)

    @classmethod
    def deserialize(cls, data: bytes, offset: int = 0) -> tuple["Conditions", int]:
        presence = struct.unpack_from("!H", data, offset=offset)[0]
        offset += 2
        values = {}

        for flag in ConditionFieldFlag:
            if not presence & flag:
                continue

            field_name = flag.field_name

            if flag in {
                ConditionFieldFlag.EQ, ConditionFieldFlag.NEQ, ConditionFieldFlag.LT,
                ConditionFieldFlag.LTE, ConditionFieldFlag.GT, ConditionFieldFlag.GTE,
                ConditionFieldFlag.REGEX, ConditionFieldFlag.NOT_REGEX
            }:
                value, offset = Conditions.deserialize_condition_value(data, offset=offset)
                values[field_name] = value
            elif flag in {ConditionFieldFlag.IN, ConditionFieldFlag.NOT_IN}:
                length = struct.unpack_from("!B", data, offset)[0]
                offset += 1
                sequence = []

                for _ in range(length):
                    item, offset = Conditions.deserialize_condition_value(data, offset=offset)
                    sequence.append(item)

                values[field_name] = sequence
            elif flag is ConditionFieldFlag.IS_NULL:
                values[field_name] = struct.unpack_from("!?", data, offset=offset)[0]
                offset += 1
            else:
                raise ValueError(f"Unsupported ConditionField for deserialization: {flag}")

        return cls.model_validate(values), offset

    @staticmethod
    def serialize_condition_value(value: ConditionValue) -> bytes:
        if isinstance(value, int) and not isinstance(value, bool):
            if 0 <= value <= 255:
                return struct.pack("!BB", ConditionValueId.UNSIGNED_CHAR, value)
            elif -128 <= value <= 127:
                return struct.pack("!Bb", ConditionValueId.SIGNED_CHAR, value)
            elif value >= 0:
                return struct.pack("!B", ConditionValueId.UNSIGNED_VARINT) + Conditions.encode_varint(value)
            else:
                zz = Conditions.encode_zigzag(value)
                return struct.pack("!B", ConditionValueId.SIGNED_VARINT) + Conditions.encode_varint(zz)
        elif isinstance(value, float):
            half = np.float16(value)

            if float(half) == value:
                return struct.pack("!B", ConditionValueId.HALF_FLOAT) + half.tobytes()
            elif -3.4e38 <= value <= 3.4e38:
                return struct.pack("!Bf", ConditionValueId.FLOAT, value)

            return struct.pack("!Bd", ConditionValueId.DOUBLE, value)
        elif isinstance(value, str):
            encoded = value.encode()
            return struct.pack("!B", ConditionValueId.STR) + Conditions.encode_varint(len(encoded)) + encoded
        elif isinstance(value, bool):
            return struct.pack("!B?", ConditionValueId.BOOL, value)
        elif isinstance(value, datetime):
            timestamp = int(value.timestamp() * 1000)
            return struct.pack("!B", ConditionValueId.DATETIME) + Conditions.encode_varint(timestamp)
        else:
            raise TypeError(f"Unsupported value type. Expected {ConditionValue}, got {type(value).__name__}")

    @staticmethod
    def deserialize_condition_value(data: bytes, offset: int = 0) -> tuple[ConditionValue, int]:
        type_id = struct.unpack_from("!B", data, offset)[0]
        offset += 1

        if type_id == ConditionValueId.SIGNED_CHAR:
            return struct.unpack_from("!b", data, offset)[0], offset + 1
        elif type_id == ConditionValueId.SIGNED_VARINT:
            zz, offset = Conditions.decode_varint(data, offset)
            return Conditions.decode_zigzag(zz), offset
        elif type_id == ConditionValueId.UNSIGNED_CHAR:
            return struct.unpack_from("!B", data, offset)[0], offset + 1
        elif type_id == ConditionValueId.UNSIGNED_VARINT:
            value, offset = Conditions.decode_varint(data, offset)
            return value, offset
        elif type_id == ConditionValueId.HALF_FLOAT:
            value = np.frombuffer(data[offset:offset + 2], dtype=np.float16)[0]
            return float(value), offset + 2
        elif type_id == ConditionValueId.FLOAT:
            return struct.unpack_from("!f", data, offset)[0], offset + 4
        elif type_id == ConditionValueId.DOUBLE:
            return struct.unpack_from("!d", data, offset)[0], offset + 8
        elif type_id == ConditionValueId.STR:
            length, offset = Conditions.decode_varint(data, offset)
            return data[offset:offset + length].decode(), offset + length
        elif type_id == ConditionValueId.BOOL:
            return struct.unpack_from("!?", data, offset)[0], offset + 1
        elif type_id == ConditionValueId.DATETIME:
            millis, offset = Conditions.decode_varint(data, offset)
            return datetime.fromtimestamp(millis / 1000), offset
        else:
            raise ValueError(f"Unsupported type ID: {type_id}")

    @staticmethod
    def encode_varint(value: int) -> bytes:
        result = bytearray()

        while value > 0x7F:
            result.append((value & 0x7F) | 0x80)
            value >>= 7

        result.append(value)
        return bytes(result)

    @staticmethod
    def decode_varint(data: bytes, offset: int = 0) -> tuple[int, int]:
        shift = 0
        result = 0

        while True:
            byte = data[offset]
            result |= (byte & 0x7F) << shift
            offset += 1

            if not (byte & 0x80):
                break

            shift += 7

        return result, offset

    @staticmethod
    def encode_zigzag(n: int) -> int:
        return (n << 1) ^ (n >> 63)

    @staticmethod
    def decode_zigzag(n: int) -> int:
        return (n >> 1) ^ -(n & 1)
