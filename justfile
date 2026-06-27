default: check

BLENDER := env_var_or_default("BLENDER", "blender")
DIST_DIR := "dist"
NATIVE_AUDIO_CRATE := "native/simple_lip_sync_audio"
UV_CACHE_DIR := env_var_or_default("UV_CACHE_DIR", "/tmp/simple_lip_sync_uv_cache")

check: lint test bandit

lint:
    ruff check simple_lip_sync tests .github/scripts

test:
    python -m unittest discover -s tests

bandit:
    UV_CACHE_DIR={{UV_CACHE_DIR}} uv run --with bandit bandit -r simple_lip_sync .github/scripts

build-native-audio:
    cargo build --manifest-path {{NATIVE_AUDIO_CRATE}}/Cargo.toml --release

copy-native-audio: build-native-audio
    python .github/scripts/copy_native_audio.py --crate {{NATIVE_AUDIO_CRATE}} --addon-dir simple_lip_sync

native-audio: copy-native-audio

validate-extension:
    {{BLENDER}} --factory-startup --background --command extension validate simple_lip_sync

build-extension:
    mkdir -p {{DIST_DIR}}
    {{BLENDER}} --factory-startup --background --command extension build --source-dir simple_lip_sync --output-dir {{DIST_DIR}}
