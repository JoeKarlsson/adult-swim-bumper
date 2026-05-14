# joeflix-bumper

A CLI tool for generating [adult swim]-style pre-roll bumper videos for a personal Plex server. Define bumpers in a YAML config, drop in your own video and music assets, and render MP4s ready to use as Plex pre-rolls via [Tunarr](https://github.com/chrisbenincasa/tunarr) or similar tools.

![example bumper](docs/example.gif)

## What it makes

15–30 second MP4 videos with:
- A background video clip (or plain black)
- White text cards cycling one at a time
- Background music that fades in and out
- Your server name in brackets at the end — `[yourserver]` — Adult Swim style

## Requirements

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/download.html) (`brew install ffmpeg` on Mac)
- [Pillow](https://pillow.readthedocs.io/) (`pip install Pillow`)
- [PyYAML](https://pyyaml.org/) (`pip install pyyaml`)

Install Python dependencies:

```bash
pip install Pillow pyyaml
```

## Setup

1. Clone the repo:

```bash
git clone https://github.com/joekarlsson/joeflix-bumper.git
cd joeflix-bumper
```

2. Add your assets:

```
joeflix-bumper/
├── videos/          ← drop your background video clips here (.mp4)
├── music/           ← drop your background music here (.mp3 / .flac)
├── bumpers.yaml     ← define your bumpers here
└── joeflix-bumper   ← the CLI
```

3. Edit `bumpers.yaml` to customize the server name and bumper content (see below).

4. Render:

```bash
python3 joeflix-bumper render
```

Output lands in `output/`.

## Customizing the server name

Open `bumpers.yaml` and find the closing card in the CLI source (`joeflix-bumper`, line ~`all_cards = bumper["cards"] + ["[joeflix]"]`). Change `[joeflix]` to `[yourservername]` to match your setup.

## Usage

```bash
# list all bumpers and their render status
python3 joeflix-bumper list

# render all bumpers not yet rendered
python3 joeflix-bumper render

# force re-render everything
python3 joeflix-bumper render --all

# render one specific bumper by name
python3 joeflix-bumper render sit-back

# interactively add a new bumper
python3 joeflix-bumper add

# list available video and music assets
python3 joeflix-bumper assets

# open the output folder
python3 joeflix-bumper open
```

## Defining bumpers

Bumpers are defined in `bumpers.yaml`. Each entry has:

- `name` — unique slug used for the output filename
- `cards` — list of text cards shown one at a time (`[yourserver]` is always appended automatically as the final card)
- `video` — path to a background video relative to this directory, or `null` for plain black
- `music` — path to a music file relative to this directory

```yaml
- name: sit-back
  cards:
    - "sit back."
    - "breathe."
    - "it's just a movie."
  video: videos/ocean-waves.mp4
  music: music/tycho-adrift.mp3

- name: no-ads
  cards:
    - "no ads."
    - "no algorithm."
    - "no idea what you should watch."
  video: null
  music: music/nujabes-feather.mp3
```

Output filename for the above: `output/joeflix-bumper-sit-back.mp4`

## Finding free assets

**Videos** — royalty-free, no attribution required:
- [Pexels](https://www.pexels.com/videos/)
- [Mixkit](https://mixkit.co/free-stock-video/)
- [Pixabay](https://pixabay.com/videos/)

**Music** — CC0, no attribution required:
- [Internet Archive — Loyalty Freak Music](https://archive.org/search?query=loyalty+freak+music) (lo-fi ambient)
- [Free Music Archive](https://freemusicarchive.org/) (filter by CC0)

## Render settings

Defaults are set at the top of `joeflix-bumper`:

| Setting | Default | Description |
|---------|---------|-------------|
| `FONT` | Helvetica Neue | System font path |
| `FONT_SIZE` | 96 | Text size in pixels |
| `WIDTH, HEIGHT` | 1920, 1080 | Output resolution |
| `TOTAL_DURATION` | 10 | Bumper length in seconds |
| `FPS` | 30 | Frames per second |
| `CARD_GAP` | 0.2 | Blank gap between cards (seconds) |

## Adding to Plex via Tunarr

1. Render your bumpers: `python3 joeflix-bumper render`
2. Copy the `output/` folder to your media server
3. In Tunarr, add the bumper files as pre-roll content for your movie channel

## License

MIT — do whatever you want with it.
