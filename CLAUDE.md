# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ossapi is a Python wrapper for the osu! API with complete coverage of both API v2 and API v1. It provides sync (`Ossapi`) and async (`OssapiAsync`) clients for API v2, and `OssapiV1` for the legacy API.

## Common Commands

**Run all tests:**
```bash
pytest
```

**Run a single test:**
```bash
pytest tests/test_endpoints.py::TestBeatmap::test_deserialize
```

**Build documentation:**
```bash
make docs
```

**Install for development:**
```bash
pip install -e ".[async]"
```

## Testing Setup

Tests require environment variables for API credentials:
- `OSU_API_KEY` - API v1 key
- `OSU_API_CLIENT_ID` - OAuth client ID
- `OSU_API_CLIENT_SECRET` - OAuth client secret
- `OSU_API_REDIRECT_URI` - OAuth redirect URI (for authorization code tests)

Set `OSSAPI_TEST_HEADLESS=1` to skip tests requiring browser interaction.

## Architecture

### Core Files

- `ossapi/ossapiv2.py` - Main sync client (`Ossapi`), OAuth handling, request/response processing, all API endpoint methods
- `ossapi/ossapiv2_async.py` - Async client (`OssapiAsync`), mirrors the sync API
- `ossapi/ossapi.py` - Legacy API v1 client (`OssapiV1`)
- `ossapi/models.py` - Dataclass models for API responses (User, Beatmap, Score, etc.)
- `ossapi/enums.py` - Enums used in API responses and requests (GameMode, RankStatus, etc.)
- `ossapi/utils.py` - Base model classes (`Model`, `BaseModel`, `_Model`) and deserialization utilities

### Model System

Models use a custom metaclass system (`ModelMeta` in `utils.py`) that enables automatic deserialization from API JSON responses. Key concepts:

- `Model` - Standard model base class with automatic field handling
- `BaseModel` - For models that handle their own member initialization
- `EnumModel` - Base for string-based enums with API value mapping
- `IntFlagModel` - Base for flag-based enums
- `Field` class - Used when the deserialization type differs from the runtime type

Models can override `preprocess_data()` to transform API data before instantiation, and `override_attributes()` to dynamically change attribute types based on field values.

### Type Hints for API Methods

The codebase uses Union types (e.g., `GameModeT = Union[GameMode, str]`) to allow passing either enum values or string literals to API methods. These are automatically converted to the base enum type during request processing.

### Sync/Async Parity

`OssapiAsync` mirrors `Ossapi` exactly. When adding new endpoints, implement in `ossapiv2.py` first, then mirror to `ossapiv2_async.py`.
