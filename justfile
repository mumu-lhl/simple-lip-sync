default: check

BLENDER := env_var_or_default("BLENDER", "blender")
DIST_DIR := "dist"
NATIVE_AUDIO_CRATE := "native/simple_lip_sync_audio"

check: lint test

lint:
    ruff check simple_lip_sync tests .github/scripts

test:
    python -m unittest discover -s tests

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
