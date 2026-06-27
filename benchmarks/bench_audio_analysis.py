"""Benchmark: Rust native backend vs pure Python audio analysis.

Usage
-----
Run from the project root::

    python benchmarks/bench_audio_analysis.py

    # Custom repeat count (default 5):
    python benchmarks/bench_audio_analysis.py --repeat 10

    # Only a specific scenario:
    python benchmarks/bench_audio_analysis.py --scenario medium

    # Write CSV output:
    python benchmarks/bench_audio_analysis.py --csv results.csv

Options
-------
--repeat N        Number of timed repetitions per scenario (default: 5)
--scenario NAME   Run only: short | medium | long | all  (default: all)
--no-warmup       Skip the warmup iteration
--csv FILE        Write results to a CSV file
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Make sure the project root is on sys.path so the package is importable when
# the script is executed directly:  python benchmarks/bench_audio_analysis.py
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from simple_lip_sync.audio import native_backend  # noqa: E402
from simple_lip_sync.audio.analysis import analyze_samples_python  # noqa: E402

# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

SAMPLE_RATE = 44100  # Hz – matches typical audio files

# (name, duration_seconds, human-readable description)
SCENARIOS: list[tuple[str, float, str]] = [
    ("short",  0.5,  "0.5 s  (~22 050 samples)"),
    ("medium", 5.0,  "5.0 s  (~220 500 samples)"),
    ("long",   30.0, "30.0 s (~1 323 000 samples)"),
]

# ---------------------------------------------------------------------------
# Synthetic audio generator
# ---------------------------------------------------------------------------

def _make_samples(duration: float, sample_rate: int = SAMPLE_RATE) -> list[float]:
    """Return a synthetic mono signal (multi-frequency sine mixture).

    The mix exercises all internal analysis branches (windowing, Goertzel
    filter bank, viseme scoring) without requiring an actual audio file.
    Frequencies match vowel formant prototypes used by the analysers:
      - 850 Hz  / 1450 Hz  → viseme 'a'
      - 320 Hz  / 2250 Hz  → viseme 'i'
    """
    n = int(sample_rate * duration)
    two_pi = 2.0 * math.pi
    out: list[float] = []
    for i in range(n):
        t = i / sample_rate
        v = (
            0.35 * math.sin(two_pi * 850.0  * t)
            + 0.25 * math.sin(two_pi * 1450.0 * t)
            + 0.15 * math.sin(two_pi * 320.0  * t)
            + 0.10 * math.sin(two_pi * 2250.0 * t)
            # slow AM so RMS varies frame-to-frame
            + 0.05 * math.sin(two_pi * 3.5 * t) * math.sin(two_pi * 850.0 * t)
        )
        out.append(max(-1.0, min(1.0, v)))
    return out

# ---------------------------------------------------------------------------
# Timing helpers
# ---------------------------------------------------------------------------

class BenchmarkResult:
    """Holds raw timing data and computed statistics for one backend run."""

    def __init__(
        self,
        scenario: str,
        backend: str,
        duration_s: float,
        repeat: int,
        times: list[float],
        output_frames: int,
    ) -> None:
        self.scenario = scenario
        self.backend = backend
        self.duration_s = duration_s
        self.repeat = repeat
        self.times = times
        self.output_frames = output_frames

    @property
    def mean(self) -> float:
        return sum(self.times) / len(self.times)

    @property
    def best(self) -> float:
        return min(self.times)

    @property
    def worst(self) -> float:
        return max(self.times)

    @property
    def stddev(self) -> float:
        m = self.mean
        return math.sqrt(sum((t - m) ** 2 for t in self.times) / len(self.times))

    def throughput_xrt(self) -> float:
        """Multiples of real-time that this backend can process (higher = faster)."""
        return self.duration_s / self.mean if self.mean > 0 else float("inf")


def _run_timed(fn: Callable[[], object]) -> tuple[float, object]:
    """Invoke *fn* once; return (wall-clock seconds, return value)."""
    t0 = time.perf_counter()
    result = fn()
    return time.perf_counter() - t0, result


def run_benchmark(
    *,
    scenario: str,
    duration_s: float,
    backend: str,
    repeat: int,
    warmup: bool,
    fn: Callable[[], object],
) -> BenchmarkResult:
    if warmup:
        _run_timed(fn)

    times: list[float] = []
    output_frames = 0
    for _ in range(repeat):
        elapsed, result = _run_timed(fn)
        times.append(elapsed)
        if result:
            output_frames = len(result)  # type: ignore[arg-type]

    return BenchmarkResult(
        scenario=scenario,
        backend=backend,
        duration_s=duration_s,
        repeat=repeat,
        times=times,
        output_frames=output_frames,
    )

# ---------------------------------------------------------------------------
# Terminal formatting
# ---------------------------------------------------------------------------

_RST    = "\033[0m"
_BOLD   = "\033[1m"
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_CYAN   = "\033[36m"
_RED    = "\033[31m"


def _c(text: str, code: str) -> str:
    return f"{code}{text}{_RST}" if sys.stdout.isatty() else text


def _fmt(seconds: float) -> str:
    if seconds < 1e-3:
        return f"{seconds * 1e6:8.1f} µs"
    if seconds < 1.0:
        return f"{seconds * 1e3:8.2f} ms"
    return f"{seconds:8.3f}  s"


def _print_header() -> None:
    print()
    print(_c("=" * 74, _BOLD))
    print(_c("  simple_lip_sync  —  Audio Analysis Benchmark", _BOLD))
    print(_c("  Pure Python  vs  Rust native backend (cdylib via ctypes)", _CYAN))
    print(_c("=" * 74, _BOLD))
    print()


def _print_scenario(
    scenario_name: str,
    description: str,
    py: BenchmarkResult,
    nat: BenchmarkResult | None,
) -> None:
    print(_c(f"  Scenario: {scenario_name}  ({description})", _BOLD))
    header = (
        f"  {'Backend':<14}"
        f" {'Best':>10}"
        f" {'Mean':>10}"
        f" {'Worst':>10}"
        f" {'Std':>10}"
        f" {'×-realtime':>12}"
        f" {'Frames':>8}"
    )
    print(header)
    print("  " + "-" * 68)

    def _row(res: BenchmarkResult, *, highlight: bool = False) -> None:
        line = (
            f"  {res.backend:<14}"
            f" {_fmt(res.best)}"
            f" {_fmt(res.mean)}"
            f" {_fmt(res.worst)}"
            f" {_fmt(res.stddev)}"
            f" {res.throughput_xrt():>12.1f}×"
            f" {res.output_frames:>8}"
        )
        if highlight and sys.stdout.isatty():
            print(f"\033[32m{line}{_RST}")
        else:
            print(line)

    if nat is not None:
        speedup = py.mean / nat.mean if nat.mean > 0 else float("inf")
        rust_faster = speedup >= 1.0
        _row(py, highlight=not rust_faster)
        _row(nat, highlight=rust_faster)
        speedup_str = _c(f"{speedup:.1f}×", _GREEN if rust_faster else _RED)
        winner = _c("Rust native", _GREEN) if rust_faster else _c("Python", _YELLOW)
        print(f"\n  Speedup (Python ÷ Rust, mean): {speedup_str}  → {winner} is faster\n")
    else:
        _row(py)
        print()


def _print_summary(pairs: list[tuple[BenchmarkResult, BenchmarkResult | None]]) -> None:
    print(_c("=" * 74, _BOLD))
    print(_c("  Summary", _BOLD))
    print(_c("=" * 74, _BOLD))
    print(f"  {'Scenario':<10} {'Python mean':>14} {'Native mean':>14} {'Speedup':>10}")
    print("  " + "-" * 50)
    for py, nat in pairs:
        nat_str = _fmt(nat.mean) if nat else "   N/A"
        spd_str = f"{py.mean / nat.mean:.1f}×" if nat else "—"
        print(f"  {py.scenario:<10} {_fmt(py.mean)} {nat_str} {spd_str:>10}")
    print()

# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def _write_csv(path: str, results: list[BenchmarkResult]) -> None:
    fields = [
        "scenario", "backend", "audio_duration_s", "repeat",
        "best_s", "mean_s", "worst_s", "stddev_s",
        "throughput_x_realtime", "output_frames",
    ]
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "scenario":             r.scenario,
                "backend":              r.backend,
                "audio_duration_s":     r.duration_s,
                "repeat":               r.repeat,
                "best_s":               f"{r.best:.6f}",
                "mean_s":               f"{r.mean:.6f}",
                "worst_s":              f"{r.worst:.6f}",
                "stddev_s":             f"{r.stddev:.6f}",
                "throughput_x_realtime": f"{r.throughput_xrt():.2f}",
                "output_frames":        r.output_frames,
            })
    print(f"  CSV written to: {path}\n")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark the pure-Python vs Rust native audio analysis backends.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--repeat", type=int, default=5, metavar="N",
        help="Timed repetitions per scenario (default: 5)",
    )
    parser.add_argument(
        "--scenario", default="all",
        choices=["short", "medium", "long", "all"],
        help="Scenario to run (default: all)",
    )
    parser.add_argument(
        "--no-warmup", dest="no_warmup", action="store_true",
        help="Skip the warmup iteration",
    )
    parser.add_argument(
        "--csv", metavar="FILE", default=None,
        help="Write results to this CSV file",
    )
    args = parser.parse_args(argv)

    warmup = not args.no_warmup
    native_ok = native_backend.is_available()

    _print_header()

    if native_ok:
        print(_c("  ✓ Native (Rust) backend loaded successfully.", _GREEN))
    else:
        print(_c("  ✗ Native backend not available — only Python will be benchmarked.", _YELLOW))
        print(_c("    Build it with:  just native-audio", _YELLOW))
        print(_c("    (or: cargo build --release --manifest-path native/simple_lip_sync_audio/Cargo.toml)", _YELLOW))
    print()

    active = [s for s in SCENARIOS if args.scenario in ("all", s[0])]

    all_results: list[BenchmarkResult] = []
    pairs: list[tuple[BenchmarkResult, BenchmarkResult | None]] = []

    for name, dur, desc in active:
        print(_c(f"  Generating {dur:.1f}s of synthetic audio …", _CYAN))
        samples = _make_samples(dur, SAMPLE_RATE)
        print(f"  {len(samples):,} samples @ {SAMPLE_RATE} Hz\n")

        # --- pure-Python ---
        py_res = run_benchmark(
            scenario=name,
            duration_s=dur,
            backend="Python (pure)",
            repeat=args.repeat,
            warmup=warmup,
            fn=lambda s=samples: analyze_samples_python(
                s, SAMPLE_RATE, db_threshold=-50.0, rms_threshold=0.01
            ),
        )
        all_results.append(py_res)

        # --- Rust native ---
        nat_res: BenchmarkResult | None = None
        if native_ok:
            nat_res = run_benchmark(
                scenario=name,
                duration_s=dur,
                backend="Rust (native)",
                repeat=args.repeat,
                warmup=warmup,
                fn=lambda s=samples: native_backend.analyze_samples(
                    s, SAMPLE_RATE, db_threshold=-50.0, rms_threshold=0.01
                ),
            )
            all_results.append(nat_res)

        _print_scenario(name, desc, py_res, nat_res)
        pairs.append((py_res, nat_res))

    if len(active) > 1:
        _print_summary(pairs)

    if args.csv:
        _write_csv(args.csv, all_results)


if __name__ == "__main__":
    main()
