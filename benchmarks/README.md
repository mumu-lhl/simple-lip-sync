# Benchmarks

Performance benchmarks for `simple_lip_sync` audio analysis backends.

## `bench_audio_analysis.py`

Compares the **pure-Python** audio analysis implementation
(`simple_lip_sync/audio/analysis.py`) against the **Rust native** backend
(`native/simple_lip_sync_audio/`) which is loaded at runtime via `ctypes`.

### Prerequisites

The native backend `.so` / `.dll` / `.dylib` must be built and placed under
`simple_lip_sync/audio/native/` before the Rust numbers are meaningful.  
Build it with:

```bash
# using just (recommended)
just native-audio

# or directly with cargo
cargo build --release --manifest-path native/simple_lip_sync_audio/Cargo.toml
python .github/scripts/copy_native_audio.py \
    --crate native/simple_lip_sync_audio \
    --addon-dir simple_lip_sync
```

### Running

```bash
# Run all scenarios (short / medium / long) with 5 repetitions each
python benchmarks/bench_audio_analysis.py

# Faster smoke-test (1 repetition, short scenario only)
python benchmarks/bench_audio_analysis.py --repeat 1 --scenario short

# Only the 5-second scenario
python benchmarks/bench_audio_analysis.py --scenario medium

# Save results to CSV
python benchmarks/bench_audio_analysis.py --csv results.csv
```

### CLI options

| Option | Default | Description |
|--------|---------|-------------|
| `--repeat N` | `5` | Number of timed repetitions per scenario |
| `--scenario NAME` | `all` | `short` \| `medium` \| `long` \| `all` |
| `--no-warmup` | off | Skip the one-shot warmup iteration |
| `--csv FILE` | — | Write raw results to a CSV file |

### What is measured

| Metric | Meaning |
|--------|---------|
| **Best** | Fastest single run |
| **Mean** | Arithmetic mean across all repetitions |
| **Worst** | Slowest single run |
| **Std** | Population standard deviation |
| **×-realtime** | Audio duration ÷ mean wall-clock time (higher = faster) |
| **Frames** | Number of viseme frames returned by the analyser |

### Scenarios

| Name | Audio duration | Approx. samples |
|------|---------------|-----------------|
| `short` | 0.5 s | ~22 050 |
| `medium` | 5.0 s | ~220 500 |
| `long` | 30.0 s | ~1 323 000 |

All scenarios use a synthetic multi-frequency sine-wave signal (44 100 Hz,
mono) that exercises all internal branches of both analysers:
- Hann windowing
- Goertzel filter bank (12 formant frequencies)
- Viseme scoring & weight normalisation

### Example output

```
==========================================================================
  simple_lip_sync  —  Audio Analysis Benchmark
  Pure Python  vs  Rust native backend (cdylib via ctypes)
==========================================================================

  ✓ Native (Rust) backend loaded successfully.

  Generating 0.5s of synthetic audio …
  22,050 samples @ 44100 Hz

  Scenario: short  (0.5 s  (~22 050 samples))
  Backend              Best       Mean      Worst        Std   ×-realtime   Frames
  --------------------------------------------------------------------
  Python (pure)      82.50 ms    83.68 ms    84.43 ms    845.1 µs          6.0×       44
  Rust (native)       8.53 ms     8.82 ms     9.35 ms    374.5 µs         56.7×       44

  Speedup (Python ÷ Rust, mean): 9.5×  → Rust native is faster
```
