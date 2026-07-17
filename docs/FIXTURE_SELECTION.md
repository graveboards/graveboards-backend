# Fixture Selection Strategy Guide

This document explains when to use each fixture loading method in the Graveboards test suite.

## Overview

The test suite provides multiple ways to load osu! API fixture data:

1. **`load_*()` functions** - Simple JSON file loading
2. **`FixtureReader`** - Programmatic fixture reading by directory/entity
3. **Factory functions** - Programmatic test data generation

## When to Use Each Method

### Use `load_beatmap()`, `load_user()`, etc. when:

- You need **exact, real osu! API response data**
- Testing **parsing logic** that depends on specific API field values
- You need to verify **specific edge cases** from real data
- Testing **CSV export** or **JSON serialization** against real data

**Example:**
```python
def test_beatmap_parsing(load_beatmap):
    beatmap_data = load_beatmap("beatmap_12345")
    beatmap = parse_beatmap(beatmap_data)
    assert beatmap.id == 12345
```

**Files:**
- `tests/fixtures/osu/__init__.py` - Contains `load_beatmap()`, `load_user()`, etc.
- Fixture files: `tests/fixtures/osu/beatmaps/`, `tests/fixtures/osu/users/`, etc.

---

### Use `FixtureReader` when:

- You need to work with **multiple related fixtures**
- Testing **relationships between entities** (e.g., user + beatmap + score)
- You need to **load fixtures by entity type** programmatically
- Testing **batch operations** on multiple fixtures

**Example:**
```python
from app.fixtures.reader import FixtureReader

def test_user_score_relationship():
    reader = FixtureReader()
    user_data = reader.load("users", "osu/user_12345_osu")
    beatmap_data = reader.load("beatmaps", "beatmap_100")
    score_data = reader.load("scores", "best", "user_12345_best")
    
    # Test relationship between all three
    assert score_data[0]["user_id"] == user_data["id"]
    assert score_data[0]["beatmap_id"] == beatmap_data["id"]
```

**Files:**
- `app/fixtures/reader.py` - FixtureReader class
- `tests/fixtures/osu/__init__.py` - Convenience `load_*()` helpers

---

### Use Factory Functions when:

- You need to **generate test data programmatically**
- You need to **customize specific fields** while keeping others default
- Testing **validation logic** with varying inputs
- You want **deterministic, reproducible data** (for debugging)
- You need to **generate large datasets** without JSON file overhead

**Example:**
```python
from tests.fixtures.factories import generate_user_data, generate_score_data

def test_user_validation(user_factory):
    users = generate_user_data(count=5, is_active=True)
    for user in users:
        validate_user(user)  # Should not raise
```

**Files:**
- `tests/fixtures/factories.py` - Factory functions

---

## Decision Tree

```
Need exact osu! API data?
  ├─ YES → load_*() functions
  └─ NO → Need related fixtures?
      ├─ YES → FixtureReader
      └─ NO → Need programmatic generation?
          ├─ YES → Factory functions
          └─ NO → Use load_*() anyway
```

## Best Practices

1. **Prefer factories for unit tests** - More flexible and faster
2. **Use load_*() for integration tests** - Verify real API parsing
3. **Use FixtureReader for complex relationships** - Tests with multiple entities
4. **Document which method each test uses** in the docstring
5. **Keep fixture JSON files minimal** - Only include essential edge cases

## Migration Guide

### From load_*() to Factory

**Before:**
```python
def test_user_profile(load_user):
    user_data = load_user("osu/user_12345_osu")
    profile = create_profile(user_data)
```

**After:**
```python
def test_user_profile(user_factory):
    user_data = generate_user_data(count=1, id=12345)[0]
    profile = create_profile(user_data)
```

### From load_*() to FixtureReader

**Before:**
```python
def test_user_beatmap_relationship(load_user, load_beatmap):
    user = load_user("osu/user_12345_osu")
    beatmap = load_beatmap("beatmap_100")
```

**After:**
```python
from app.fixtures.reader import FixtureReader

def test_user_beatmap_relationship():
    reader = FixtureReader()
    user = reader.load("users", "osu/user_12345_osu")
    beatmap = reader.load("beatmaps", "beatmap_100")
```

## Related Documentation

- `TESTING.md` - Overall testing guidelines
- `tests/fixtures/osu/__init__.py` - load_*() function definitions
- `app/fixtures/reader.py` - FixtureReader class
- `tests/fixtures/factories.py` - Factory function definitions