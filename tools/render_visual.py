"""Procedural raster artwork and ffmpeg media steps.

The painter is original and deterministic. It draws five answering arcs on a
walnut field. Brass arcs stand for keys and lead. A blue arc stands for the
counterline. Wide and square are different framings, not scales of each other.
It is an illustration, not a photograph of a session or of performers.

DejaVu Sans Bold is used only to rasterize the disclosure into the film and the
poster. The font file is not shipped.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ON_PICTURE = "preview, not master"


def _clamp(value: int) -> int:
    return 0 if value < 0 else 255 if value > 255 else value


def _plot(pixels: bytearray, width: int, height: int, x: int, y: int, color: tuple[int, int, int], radius: int) -> None:
    for yy in range(y - radius, y + radius + 1):
        if not 0 <= yy < height:
            continue
        row = yy * width * 3
        for xx in range(x - radius, x + radius + 1):
            if not 0 <= xx < width:
                continue
            if (xx - x) * (xx - x) + (yy - y) * (yy - y) > radius * radius:
                continue
            pixels[row + xx * 3] = color[0]
            pixels[row + xx * 3 + 1] = color[1]
            pixels[row + xx * 3 + 2] = color[2]


def _arc(pixels: bytearray, width: int, height: int, cx: int, cy: int, radius: int, color: tuple[int, int, int], thick: int, y_limit: int) -> None:
    for deg in range(180, 361):
        rad = deg * 3.141592653589793 / 180.0
        x = int(cx + radius * __import__("math").cos(rad))
        y = int(cy - radius * __import__("math").sin(rad) * 0.55)
        if y > y_limit:
            continue
        _plot(pixels, width, height, x, y, color, thick)


def paint(width: int, height: int, framing: str) -> bytes:
    """Walnut field and five arcs. Square and wide are different framings."""
    pixels = bytearray(width * height * 3)
    for y in range(height):
        shade = y / max(1, height - 1)
        row = y * width * 3
        red = int(42 + 28 * shade)
        green = int(26 + 16 * shade)
        blue = int(16 + 10 * shade)
        for x in range(width):
            pixels[row + x * 3] = red
            pixels[row + x * 3 + 1] = green
            pixels[row + x * 3 + 2] = blue
    horizon = int(height * (0.72 if framing == "wide" else 0.78))
    for y in range(horizon, height):
        row = y * width * 3
        for x in range(width):
            pixels[row + x * 3] = 28
            pixels[row + x * 3 + 1] = 18
            pixels[row + x * 3 + 2] = 12
    if framing == "wide":
        arcs = (
            (0.18, 0.70, 0.16, (110, 74, 42), 5),
            (0.34, 0.66, 0.22, (165, 112, 58), 6),
            (0.50, 0.62, 0.18, (226, 181, 106), 4),
            (0.66, 0.68, 0.20, (196, 140, 72), 5),
            (0.80, 0.60, 0.14, (62, 109, 134), 6),
        )
    else:
        arcs = (
            (0.22, 0.74, 0.20, (110, 74, 42), 7),
            (0.40, 0.66, 0.26, (165, 112, 58), 8),
            (0.55, 0.58, 0.16, (226, 181, 106), 6),
            (0.70, 0.70, 0.22, (196, 140, 72), 7),
            (0.84, 0.52, 0.15, (62, 109, 134), 8),
        )
    for xf, yf, rf, color, thick in arcs:
        _arc(
            pixels,
            width,
            height,
            int(width * xf),
            int(height * yf),
            int(width * rf),
            color,
            thick,
            horizon,
        )
    return bytes(pixels)

def write_ppm(path: Path, width: int, height: int, rgb: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"P6\n{width} {height}\n255\n".encode("ascii")
    path.write_bytes(header + rgb)


def run(command: list[str]) -> None:
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "command failed\n"
            + " ".join(command)
            + "\n"
            + completed.stderr[-2000:]
        )


def ppm_to_jpeg(ppm: Path, jpeg: Path, quality: int = 3) -> None:
    jpeg.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-i", str(ppm), "-frames:v", "1", "-q:v", str(quality), str(jpeg)])


def draw_disclosure(source: Path, dest: Path, textfile: Path) -> list[str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    textfile.write_text(ON_PICTURE + "\n", encoding="utf-8")
    command = [
        "ffmpeg", "-y", "-i", str(source),
        "-vf",
        (
            f"drawtext=textfile={textfile}:fontfile={FONT}:fontsize=48:"
            "fontcolor=white:x=(w-text_w)/2:y=h-100:box=1:boxcolor=black@0.68:boxborderw=22"
        ),
        "-frames:v", "1",
        "-q:v", "3",
        str(dest),
    ]
    run(command)
    return command


def encode_mp3(wav: Path, mp3: Path) -> list[str]:
    mp3.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-y", "-i", str(wav),
        "-codec:a", "libmp3lame", "-b:a", "192k",
        str(mp3),
    ]
    run(command)
    return command


def encode_film(plate: Path, mp3: Path, mp4: Path, textfile: Path, duration: str) -> list[str]:
    mp4.parent.mkdir(parents=True, exist_ok=True)
    textfile.write_text(ON_PICTURE + "\n", encoding="utf-8")
    command = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", "24", "-i", str(plate),
        "-i", str(mp3),
        "-t", duration,
        "-vf",
        (
            "scale=1280:720,"
            f"drawtext=textfile={textfile}:fontfile={FONT}:fontsize=48:"
            "fontcolor=white:x=(w-text_w)/2:y=h-100:box=1:boxcolor=black@0.68:boxborderw=22"
        ),
        "-r", "24",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest",
        "-movflags", "+faststart",
        str(mp4),
    ]
    run(command)
    return command


def derive_social(hero: Path, square: Path, portrait: Path, card: Path) -> dict[str, list[str]]:
    portrait.parent.mkdir(parents=True, exist_ok=True)
    card.parent.mkdir(parents=True, exist_ok=True)
    portrait_cmd = [
        "ffmpeg", "-y", "-i", str(square),
        "-vf", "crop=864:1080:108:0,scale=1080:1350",
        "-q:v", "3",
        str(portrait),
    ]
    card_cmd = [
        "ffmpeg", "-y", "-i", str(hero),
        "-vf", "scale=1600:900",
        "-q:v", "3",
        str(card),
    ]
    run(portrait_cmd)
    run(card_cmd)
    return {"portrait": portrait_cmd, "card": card_cmd}
