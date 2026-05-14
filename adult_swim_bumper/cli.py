#!/usr/bin/env python3
"""
bumper — Adult Swim-style pre-roll bumper video generator

Commands:
  init              First-time setup wizard
  list              Show all bumpers and render status
  render            Render all bumpers not yet rendered
  render --all      Force re-render everything
  render <name>     Render one specific bumper by name
  add               Interactive wizard to define a new bumper
  assets            List available videos and music files
  open              Open output folder in Finder
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont
from adult_swim_bumper import __version__

# BASE is the working directory — bumper operates on wherever you run it from
BASE = Path.cwd()
CONFIG = BASE / "bumpers.yaml"
BUMPER_CFG = BASE / "bumper.yaml"
OUTPUT = BASE / "output"

_FONT_SIZE_DEFAULT = 96
_WIDTH_DEFAULT, _HEIGHT_DEFAULT = 1920, 1080
TOTAL_DURATION = 10
FPS = 30
CARD_GAP = 0.2

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
DIM    = "\033[2m"

EXAMPLE_BUMPERS = """\
- name: sit-back
  cards:
    - "sit back."
    - "breathe."
    - "it's just a movie."
  video: videos/ocean.mp4
  music: music/ambient-01.mp3

- name: no-ads
  cards:
    - "no ads."
    - "no algorithm."
    - "no idea what you should watch."
  video: null
  music: music/lofi-01.mp3

- name: welcome
  cards:
    - "welcome."
    - "you made a good choice."
  video: videos/fire.mp4
  music: music/ambient-02.mp3

- name: friday-night
  cards:
    - "it's friday night."
    - "you're exactly where you should be."
  video: videos/rain.mp4
  music: music/lofi-02.mp3

- name: good-taste
  cards:
    - "you have good taste."
    - "probably."
  video: null
  music: music/ambient-01.mp3
"""


# ── config ───────────────────────────────────────────────────────────────────

def load_cfg():
    if BUMPER_CFG.exists():
        with open(BUMPER_CFG) as f:
            return yaml.safe_load(f) or {}
    return {}

_cfg = load_cfg()
SERVER_NAME = _cfg.get("server_name", "myserver")
DEFAULT_DURATION = _cfg.get("duration", TOTAL_DURATION)
FONT_SIZE = _cfg.get("font_size", _FONT_SIZE_DEFAULT)
_res = _cfg.get("resolution", [_WIDTH_DEFAULT, _HEIGHT_DEFAULT])
WIDTH, HEIGHT = _res[0], _res[1]

ASSET_DIRS = {
    "videos": [BASE / "videos", BASE / "samples" / "videos"],
    "music":  [BASE / "music",  BASE / "samples" / "music"],
}


# ── helpers ──────────────────────────────────────────────────────────────────

def get_font(size=FONT_SIZE):
    candidates = [
        "/System/Library/Fonts/HelveticaNeue.ttc",          # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "C:/Windows/Fonts/arial.ttf",                        # Windows
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()

def load_bumpers():
    if not CONFIG.exists():
        print(f"{YELLOW}bumpers.yaml not found.{RESET} Run `bumper init` to get started.")
        sys.exit(1)
    with open(CONFIG) as f:
        return yaml.safe_load(f) or []

def save_bumpers(bumpers):
    with open(CONFIG, "w") as f:
        yaml.dump(bumpers, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return text[:50]

def out_path(name):
    return OUTPUT / f"{SERVER_NAME}-bumper-{name}.mp4"

def is_rendered(name):
    return out_path(name).exists()

def get_timings(n_cards, total, gap=CARD_GAP):
    dur = total / n_cards
    return [
        (round(i * dur, 2), round((i + 1) * dur - gap, 2))
        for i in range(n_cards)
    ]

def make_card_image(text, path, font):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (WIDTH - w) / 2
    y = (HEIGHT - h) / 2
    draw.text((x + 2, y + 2), text, fill=(0, 0, 0, 160), font=font)
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    img.save(path)

def check_ffmpeg():
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    if result.returncode != 0:
        print(f"{BOLD}error:{RESET} ffmpeg not found.\n")
        print(f"  install it:")
        print(f"    Mac:    brew install ffmpeg")
        print(f"    Linux:  apt install ffmpeg")
        print(f"    Other:  https://ffmpeg.org/download.html")
        sys.exit(1)

def list_assets(kind):
    files = []
    seen = set()
    for d in ASSET_DIRS.get(kind, []):
        if d.exists():
            for f in sorted(d.glob("*")):
                if f.is_file() and not f.name.startswith(".") and f.name != "README.md":
                    if f.name not in seen:
                        files.append(f)
                        seen.add(f.name)
    return files

def render_one(bumper, verbose=True, duration_override=None):
    name = bumper["name"]
    duration = duration_override or bumper.get("duration", DEFAULT_DURATION)
    all_cards = bumper["cards"] + [f"[{SERVER_NAME}]"]
    timings = get_timings(len(all_cards), total=duration)
    music_path = BASE / bumper["music"]
    dest = out_path(name)

    if not music_path.exists():
        print(f"  {YELLOW}skip{RESET} {name} — music not found: {bumper['music']}")
        return False

    if bumper.get("video") and not (BASE / bumper["video"]).exists():
        print(f"  {YELLOW}skip{RESET} {name} — video not found: {bumper['video']}")
        return False

    if verbose:
        print(f"  {CYAN}rendering{RESET} {name}")

    font = get_font()

    with tempfile.TemporaryDirectory() as tmpdir:
        card_paths = []
        for i, card in enumerate(all_cards):
            p = os.path.join(tmpdir, f"card_{i:02d}.png")
            make_card_image(card, p, font)
            card_paths.append(p)

        cmd = ["ffmpeg", "-y"]

        if bumper.get("video"):
            cmd += ["-stream_loop", "-1", "-i", str(BASE / bumper["video"])]
        else:
            cmd += ["-f", "lavfi", "-i",
                    f"color=c=black:size={WIDTH}x{HEIGHT}:rate={FPS}"]

        for p in card_paths:
            cmd += ["-i", p]
        cmd += ["-i", str(music_path)]

        n = len(all_cards)
        music_idx = n + 1

        filter_parts = [
            f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},setsar=1[bg]"
        ]
        prev = "bg"
        for i, (start, end) in enumerate(timings):
            curr = f"s{i}"
            filter_parts.append(
                f"[{prev}][{i+1}:v]overlay=0:0:enable='between(t,{start},{end})'[{curr}]"
            )
            prev = curr

        fade_out_start = max(duration - 2, duration / 2)
        filter_parts.append(
            f"[{music_idx}:a]volume=0.35,"
            f"afade=t=in:st=0:d=1,"
            f"afade=t=out:st={fade_out_start}:d=2[a]"
        )

        fc = ";\n    ".join(filter_parts)
        cmd += ["-filter_complex", fc,
                "-map", f"[{prev}]", "-map", "[a]",
                "-t", str(duration), "-r", str(FPS),
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "aac", "-b:a", "192k",
                str(dest)]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  {YELLOW}error:{RESET} {result.stderr[-300:]}")
            return False

        size = dest.stat().st_size / 1024 / 1024
        print(f"  {GREEN}✓{RESET} {SERVER_NAME}-bumper-{name}.mp4 ({size:.1f}MB)")
        return True


# ── commands ─────────────────────────────────────────────────────────────────

def cmd_init(args):
    print(f"\n{BOLD}bumper setup{RESET}\n")

    current = SERVER_NAME if SERVER_NAME != "myserver" else ""
    prompt = f"  server name [{current}]: " if current else "  server name (e.g. netflix, myserver): "
    name = input(prompt).strip() or current or "myserver"

    current_dur = DEFAULT_DURATION if DEFAULT_DURATION != TOTAL_DURATION else 10
    dur_input = input(f"  default duration in seconds [{current_dur}]: ").strip()
    duration = int(dur_input) if dur_input.isdigit() else current_dur

    cfg = {"server_name": name, "duration": duration}
    with open(BUMPER_CFG, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)
    print(f"  saved → bumper.yaml  (server: [{name}], duration: {duration}s)")

    if not CONFIG.exists():
        CONFIG.write_text(EXAMPLE_BUMPERS)
        print(f"  created bumpers.yaml from built-in example")
    else:
        print(f"  bumpers.yaml already exists, skipping")

    for d in ["videos", "music", "output"]:
        (BASE / d).mkdir(exist_ok=True)
    print(f"  created directories: videos/  music/  output/")

    print(f"\n{BOLD}next steps:{RESET}")
    print(f"  1. add video clips (.mp4) to {BASE}/videos/")
    print(f"  2. add music (.mp3/.flac) to {BASE}/music/")
    print(f"  3. edit bumpers.yaml to define your bumpers")
    print(f"  4. bumper render\n")


def missing_assets(bumper):
    missing = []
    if bumper.get("video") and not (BASE / bumper["video"]).exists():
        missing.append(bumper["video"])
    if not (BASE / bumper["music"]).exists():
        missing.append(bumper["music"])
    return missing

def cmd_list(args):
    bumpers = load_bumpers()
    rendered = sum(1 for b in bumpers if is_rendered(b["name"]))
    broken = sum(1 for b in bumpers if missing_assets(b))
    summary = f"({rendered}/{len(bumpers)} rendered"
    if broken:
        summary += f", {YELLOW}{broken} missing assets{RESET}"
    summary += ")"
    print(f"\n{BOLD}bumpers{RESET}  {DIM}[{SERVER_NAME}]{RESET}  {DIM}{summary}{RESET}\n")
    for b in bumpers:
        name = b["name"]
        absent = missing_assets(b)
        if absent:
            status = f"{YELLOW}⚠{RESET}"
        elif is_rendered(name):
            status = f"{GREEN}✓{RESET}"
        else:
            status = f"{YELLOW}○{RESET}"
        cards_preview = " → ".join(b["cards"][:2])
        if len(b["cards"]) > 2:
            cards_preview += " → ..."
        video = Path(b["video"]).stem if b.get("video") else "black"
        print(f"  {status} {BOLD}{name}{RESET}")
        print(f"     {DIM}{cards_preview} → [{SERVER_NAME}]{RESET}")
        print(f"     {DIM}video: {video}  music: {Path(b['music']).stem}{RESET}")
        for path in absent:
            print(f"     {YELLOW}missing: {path}{RESET}")
        print()


def cmd_render(args):
    check_ffmpeg()
    bumpers = load_bumpers()
    OUTPUT.mkdir(exist_ok=True)

    duration_override = args.duration if args.duration else None

    if args.name:
        matches = [b for b in bumpers if b["name"] == args.name]
        if not matches:
            print(f"no bumper named '{args.name}'")
            sys.exit(1)
        targets = matches
    elif args.all:
        targets = bumpers
    else:
        targets = [b for b in bumpers if not is_rendered(b["name"])]

    if not targets:
        print("nothing to render — all bumpers already exist. use --all to force.")
        return

    print(f"\nrendering {len(targets)} bumper(s)...\n")
    ok = 0
    for b in targets:
        if render_one(b, duration_override=duration_override):
            ok += 1

    print(f"\n{ok}/{len(targets)} rendered successfully → {OUTPUT}")


def cmd_add(args):
    bumpers = load_bumpers()
    existing_names = {b["name"] for b in bumpers}

    print(f"\n{BOLD}add a new bumper{RESET}\n")

    print("enter cards one at a time. blank line when done.")
    print(f"{DIM}([{SERVER_NAME}] is always appended automatically){RESET}\n")
    cards = []
    while True:
        card = input(f"  card {len(cards)+1}: ").strip()
        if not card:
            if len(cards) < 2:
                print("  need at least 2 cards.")
                continue
            break
        cards.append(card)

    default_name = slugify(cards[0])
    if default_name in existing_names:
        default_name += "-2"
    name = input(f"\n  name [{default_name}]: ").strip() or default_name

    print(f"\n  available videos:")
    videos = list_assets("videos")
    for i, v in enumerate(videos):
        print(f"    {i+1}. {v.stem}  {DIM}({v.parent.name}/){RESET}")
    print(f"    0. black (no video)")
    choice = input("  choose [0]: ").strip()
    if choice and choice != "0":
        try:
            chosen = videos[int(choice) - 1]
            video = str(chosen.relative_to(BASE))
        except (ValueError, IndexError):
            video = None
    else:
        video = None

    print(f"\n  available music:")
    tracks = list_assets("music")
    if not tracks:
        print(f"  {YELLOW}no music found{RESET} — add files to music/ or samples/music/")
        sys.exit(1)
    for i, t in enumerate(tracks):
        print(f"    {i+1}. {t.stem}  {DIM}({t.parent.name}/){RESET}")
    choice = input("  choose [1]: ").strip() or "1"
    try:
        chosen = tracks[int(choice) - 1]
        music = str(chosen.relative_to(BASE))
    except (ValueError, IndexError):
        music = str(tracks[0].relative_to(BASE))

    print(f"\n{BOLD}preview:{RESET}")
    for card in cards:
        print(f"  \"{card}\"")
    print(f"  [{SERVER_NAME}]")
    print(f"  video: {Path(video).stem if video else 'black'}")
    print(f"  music: {Path(music).stem}")

    confirm = input("\n  save and render? [y/n]: ").strip().lower()
    if confirm != "y":
        print("  cancelled.")
        return

    new_bumper = {"name": name, "cards": cards, "video": video, "music": music}
    bumpers.append(new_bumper)
    save_bumpers(bumpers)
    print(f"\n  saved to bumpers.yaml")

    OUTPUT.mkdir(exist_ok=True)
    render_one(new_bumper)


def cmd_assets(args):
    print(f"\n{BOLD}videos{RESET}\n")
    videos = list_assets("videos")
    if videos:
        for v in videos:
            size = v.stat().st_size / 1024 / 1024
            print(f"  {v.stem:<30} {size:.1f}MB  {DIM}({v.parent.name}/){RESET}")
    else:
        print(f"  {DIM}none — add .mp4 files to videos/ or samples/videos/{RESET}")

    print(f"\n{BOLD}music{RESET}\n")
    tracks = list_assets("music")
    if tracks:
        for m in tracks:
            size = m.stat().st_size / 1024 / 1024
            print(f"  {m.stem:<40} {size:.1f}MB  {DIM}({m.parent.name}/){RESET}")
    else:
        print(f"  {DIM}none — add .mp3/.flac files to music/ or samples/music/{RESET}")
    print()


def cmd_open(args):
    if not OUTPUT.exists():
        print(f"output folder doesn't exist yet — render something first.")
        return
    if sys.platform == "darwin":
        subprocess.run(["open", str(OUTPUT)])
    elif sys.platform == "win32":
        subprocess.run(["explorer", str(OUTPUT)])
    else:
        subprocess.run(["xdg-open", str(OUTPUT)])


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="bumper",
        description="Adult Swim-style pre-roll bumper video generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"bumper {__version__}")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="first-time setup: set server name, scaffold dirs")
    sub.add_parser("list", help="show all bumpers and render status")

    p_render = sub.add_parser("render", help="render bumpers")
    p_render.add_argument("name", nargs="?", help="render a specific bumper by name")
    p_render.add_argument("--all", action="store_true", help="force re-render everything")
    p_render.add_argument("--duration", type=int, metavar="SECONDS",
                          help="override duration for this render (ignores bumper.yaml and per-bumper settings)")

    sub.add_parser("add", help="interactive wizard to add a new bumper")
    sub.add_parser("assets", help="list available videos and music")
    sub.add_parser("open", help="open output folder in Finder")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "render":
        cmd_render(args)
    elif args.command == "add":
        cmd_add(args)
    elif args.command == "assets":
        cmd_assets(args)
    elif args.command == "open":
        cmd_open(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
