"""Command line: python -m proads {validate|render|sample-assets} ..."""

from __future__ import annotations

import argparse
import logging
import os
import sys

from . import sample
from .config import FORMATS, ConfigError, load_config, validate
from .ffutil import FFmpegError
from .render import render

log = logging.getLogger("proads")
IN_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"


def _annotate(level: str, message: str) -> None:
    """Print a message; on GitHub Actions also surface it as an annotation."""
    if IN_ACTIONS:
        first, _, rest = message.partition("\n")
        print(f"::{level}::{first}", flush=True)
        if rest:
            print(rest, flush=True)
    else:
        print(f"{level.upper()}: {message}", file=sys.stderr, flush=True)


def _prepare(path: str) -> dict:
    raw = load_config(path)
    if raw.get("generate_sample_assets"):
        sample.generate()
    return raw


def cmd_validate(args) -> int:
    raw = _prepare(args.config)
    errors, warnings = validate(raw)
    for w in warnings:
        _annotate("warning", w)
    if errors:
        raise ConfigError(errors)
    print(f"OK: {args.config} is valid ({len(raw['scenes'])} scenes, {len(warnings)} warning(s))")
    return 0


def cmd_render(args) -> int:
    raw = _prepare(args.config)
    formats = None if args.format == "config" else (list(FORMATS)[:2] if args.format == "both" else [args.format])
    scale = 0.5 if args.draft else args.scale
    reports = render(raw, args.output, formats=formats, scale=scale, keep_work=args.keep_work)
    print("\nRendered files:")
    for r in reports:
        print(f"  {r['file']}  {r['width']}x{r['height']}  {r['duration_seconds']}s  {r['size_mb']} MB")
    return 0


def cmd_sample(args) -> int:
    print(f"Sample media ready in {sample.generate(force=args.force)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="proads", description="ProAds Cloud Studio video engine")
    parser.add_argument("-v", "--verbose", action="store_true", help="print every ffmpeg command")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="check a configuration and its media files")
    p.add_argument("config")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("render", help="render the advertisement")
    p.add_argument("config")
    p.add_argument("-o", "--output", default="output", help="output folder (default: output)")
    p.add_argument("--format", default="config", choices=["config", "both", *FORMATS],
                   help="which format(s) to render (default: the ones listed in the config)")
    p.add_argument("--draft", action="store_true", help="fast half-resolution preview")
    p.add_argument("--scale", type=float, default=1.0, help=argparse.SUPPRESS)
    p.add_argument("--keep-work", action="store_true", help="keep intermediate scene clips")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("sample-assets", help="generate the placeholder sample media")
    p.add_argument("--force", action="store_true", help="regenerate existing files")
    p.set_defaults(func=cmd_sample)

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S", stream=sys.stdout,
    )
    try:
        return args.func(args)
    except ConfigError as e:
        for err in e.errors:
            _annotate("error", f"Configuration: {err}")
        print(f"\n{len(e.errors)} configuration error(s). Fix them in the JSON file and run again.", file=sys.stderr)
        return 2
    except FFmpegError as e:
        _annotate("error", str(e))
        return 3
