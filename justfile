default: check

BLENDER := env_var_or_default("BLENDER", "blender")
DIST_DIR := "dist"

check: lint test

lint:
    ruff check simple_lip_sync tests .github/scripts

test:
    python -m unittest discover -s tests

validate-extension:
    {{BLENDER}} --factory-startup --background --command extension validate simple_lip_sync

build-extension:
    mkdir -p {{DIST_DIR}}
    {{BLENDER}} --factory-startup --background --command extension build --source-dir simple_lip_sync --output-dir {{DIST_DIR}}
