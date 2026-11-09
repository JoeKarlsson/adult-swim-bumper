# Contributing

Thanks for your interest. Here's how to get set up and submit changes.

## Prerequisites

- Python 3.11+
- ffmpeg (`brew install ffmpeg` on Mac, `apt install ffmpeg` on Linux)
- [pipx](https://pipx.pypa.io/) or pip

## Local setup

```bash
git clone https://github.com/JoeKarlsson/adult-swim-bumper.git
cd adult-swim-bumper
pip install -e ".[dev]"   # installs package in editable mode
```

Verify it works:

```bash
bumper --version
bumper --help
```

## Project structure

```
adult_swim_bumper/
  __init__.py     version string
  cli.py          all CLI logic — commands, rendering, config loading
bumper            thin local entry point (calls cli.main)
bumpers.example.yaml  example config shipped with the repo
samples/
  videos/README.md  CC0 video sources
  music/README.md   CC0 music sources
pyproject.toml    package metadata and entry point
```

Everything lives in `adult_swim_bumper/cli.py`. It's intentionally a single file — keep it that way unless there's a strong reason to split.

## Making changes

1. Fork the repo and create a branch: `git checkout -b your-feature`
2. Make your changes
3. Smoke test manually — bumper is a rendering tool, so run it:
   ```bash
   mkdir /tmp/test-bumpers && cd /tmp/test-bumpers
   bumper init
   # add a music file to music/, then:
   bumper add
   bumper render
   ```
4. Make sure `bumper --version` and `bumper --help` still work
5. Open a PR against `main`

## What makes a good PR

- Bug fixes and clear improvements are always welcome
- New commands or config options: open an issue first to discuss
- Keep the single-file structure — resist splitting into modules unless it's unavoidable
- No new dependencies without a strong reason (Pillow + PyYAML + ffmpeg is the whole stack)

## CI

GitHub Actions runs on every push and PR. It installs the package and checks that imports, `--version`, and `--help` all work. If CI is red, fix it before requesting review.
