# bumper

![A jellyfish drifting in dark blue water with white text reading "no idea what you should watch."](.github/readme/2026-11-recording.gif)

Adult Swim's bumpers were a black screen and plain white text, one card at a
time, then [adult swim] and you were back in the show, and it was the first TV I
watched that seemed like weirdos made it for other weirdos. bumper makes those
for your own media server, so every movie opens with a few lines from you and
ends on your server's name in brackets.

[Read the full statement](https://www.joekarlsson.com/work/adult-swim-bumper/)

## Quick start

Python 3.9+ and [ffmpeg](https://ffmpeg.org/download.html) (`brew install ffmpeg`
on Mac, `apt install ffmpeg` on Linux).

```bash
pipx install git+https://github.com/joekarlsson/adult-swim-bumper.git
mkdir my-bumpers && cd my-bumpers
bumper init       # creates bumper.yaml and bumpers.yaml
bumper render     # MP4s land in output/
```

Or run it from a clone:

```bash
git clone https://github.com/joekarlsson/adult-swim-bumper.git
cd adult-swim-bumper
pip install -r requirements.txt
python3 bumper init
```

Put clips in `videos/` and music in `music/` (`samples/videos/README.md` and
`samples/music/README.md` list CC0 sources), then edit `bumpers.yaml`. Those
files and folders are gitignored.

## Usage

```bash
bumper list                       # all bumpers and whether they're rendered
bumper render                     # render the ones not rendered yet
bumper render --all               # re-render everything
bumper render sit-back            # one bumper by name
bumper render --duration 15       # override the length for this run
bumper add                        # add a bumper interactively
bumper assets                     # list video and music files
bumper open                       # open the output folder
```

### Defining bumpers

```yaml
- name: sit-back
  cards:
    - "sit back."
    - "breathe."
    - "it's just a movie."
  video: videos/ocean.mp4
  music: music/lofi-jazz.mp3
```

- `name`: unique slug, used in the output filename `output/{servername}-bumper-{name}.mp4`
- `cards`: 2 to 4 lines, shown one at a time; `[yourserver]` is always added as the last card
- `video`: background clip relative to this directory, or `null` for plain black
- `music`: music file relative to this directory
- `duration`: optional, overrides the project default for this bumper

### Configuration

`bumper.yaml`, written by `bumper init`. Every field is optional; these are the defaults:

```yaml
server_name: yourserver
duration: 10              # default bumper length in seconds
font_size: 96             # text size in pixels
resolution: [1920, 1080]  # output width x height
font_path: /path/to/font.ttf  # optional: any .ttf or .ttc
```

Without `font_path` it picks Helvetica Neue (macOS), DejaVu Sans (Linux) or
Arial (Windows). Duration priority: `--duration` flag, then the bumper's
`duration:`, then `bumper.yaml`, then 10 seconds. `FPS` (30) and `CARD_GAP`
(0.2 seconds) are constants at the top of `adult_swim_bumper/cli.py`.

To use them in Plex, copy `output/` to your media server and add the files as
pre-roll content for your movie channel in Tunarr.

## Development

```bash
pip install -e . pytest
python3 -m pytest
```

Everything lives in `adult_swim_bumper/cli.py`. See
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
