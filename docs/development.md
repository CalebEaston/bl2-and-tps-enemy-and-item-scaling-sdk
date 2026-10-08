# Development

Notes for anyone who wants to build on this mod. Players don't need any of this: the
[README](../README.md) covers installing the released `.sdkmod`.

## Layout

```
src/enemy_item_scaling/   the mod itself: __init__.py, pyproject.toml (mod metadata), Readme.md (changelog)
.willow2-mod-manager/     git submodule pinned to the SDK release the game ships, used for type-checking only
docs/                     these notes, the SDK reference (sdk-notes.md) and the in-game test plan (testing.md)
pyproject.toml            ruff and pyright configuration, copied from the bl-sdk repos
.github/workflows/        the release workflow
```

What players install is `enemy_item_scaling.sdkmod`, a zip of `src/enemy_item_scaling/`. Nothing
else in this repository goes into the game.

## Local checks

```sh
git submodule update --init .willow2-mod-manager
git -C .willow2-mod-manager submodule update --init src/mods_base src/keybinds src/console_mod_menu
python3 -m venv .venv && .venv/bin/pip install ruff        # once
.venv/bin/ruff check src && .venv/bin/ruff format --check src
npx --yes pyright src
```

The SDK embeds Python 3.14 and `mods_base` uses 3.14-only syntax, so use Python 3.14 locally.

## Running it from this checkout

Instead of re-zipping after every edit, point the game at `src/` as an extra mods folder. Create
`<game>/Binaries/Win32/Plugins/unrealsdk.user.toml`:

```toml
[mod_manager]
extra_folders = ['Z:\path\to\bl2-enemy-and-item-scaling-sdk\src']
```

(Windows path as the game sees it; under Proton `Z:` is `/`.) In the game console, tilde twice,
`rlm enemy_item_scaling` reloads the module after an edit. Errors land in
`<game>/Binaries/Win32/Plugins/unrealsdk.log`. The first-run checklist is in [testing.md](testing.md).

## Building the .sdkmod by hand

```sh
cd src && zip -r ../enemy_item_scaling.sdkmod enemy_item_scaling -x '*__pycache__*'
```

## Cutting a release

1. Bump `version` in `src/enemy_item_scaling/pyproject.toml` (dotted integers only, e.g. `0.2`) and
   add an entry to `src/enemy_item_scaling/Readme.md`.
2. Commit, then `git tag v0.2 && git push origin v0.2`.

The workflow in `.github/workflows/release.yml` checks that the tag matches the version, builds
the `.sdkmod` and publishes a GitHub Release with it attached and auto-generated notes.

## How it works

See [sdk-notes.md](sdk-notes.md) for the hook targets, the prior-art mods this borrows from, and
the open questions, and [.claude/CLAUDE.md](../.claude/CLAUDE.md) for the rules the code follows.
