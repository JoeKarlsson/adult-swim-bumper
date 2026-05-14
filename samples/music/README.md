# Sample Music

Drop background music files here (`.mp3`, `.flac`, `.wav`). These are picked up automatically by `bumper add` and `bumper assets`.

The main `music/` directory at the project root works the same way — `bumper` searches both locations.

## CC0 Music Sources (no attribution required)

| Source | Style | Notes |
|--------|-------|-------|
| [Internet Archive — Loyalty Freak Music](https://archive.org/search?query=loyalty+freak+music) | Lo-fi ambient, chillhop | Massive CC0 library, Adult Swim-adjacent sound |
| [Free Music Archive](https://freemusicarchive.org/) | All genres | Filter by CC0 license |
| [ccMixter](https://ccmixter.org/) | Electronic, ambient | Search for CC0 tracks |
| [Incompetech](https://incompetech.com/music/royalty-free/) | Instrumental | CC BY — free with credit |
| [Pixabay Music](https://pixabay.com/music/) | All genres | CC0, no attribution |

## What works well for bumpers

The Adult Swim bumper aesthetic is low-key, slightly melancholy, and atmospheric:

- **Lo-fi hip hop**: muted drums, jazzy chords, tape hiss
- **Ambient/downtempo**: Tycho, Boards of Canada, Nujabes-adjacent sounds
- **Jazz-inflected instrumentals**: quiet trumpet, Rhodes piano
- **Avoid**: songs with prominent vocals, fast tempos, or dramatic builds — bumpers are 10 seconds

## Audio notes

- `bumper` fades audio in (1s) and out (2s) automatically — no need to pre-edit tracks
- Volume is set to 35% of the original level to sit under the text without overpowering
- Longer tracks work fine; ffmpeg trims to `TOTAL_DURATION` automatically

## Naming convention

Use lowercase kebab-case: `lofi-jazz-01.mp3`, `ambient-rain.flac`, `chillhop-evening.mp3`
