"""ctypes loader for the optional native audio analysis backend."""

import ctypes
import platform
from pathlib import Path


SAMPLE_WIDTH = 8
VISEMES = ("a", "i", "u", "e", "o", "n")


class NativeAnalysisResult(ctypes.Structure):
    """FFI result returned by the native analyzer."""

    _fields_ = [
        ("sample_count", ctypes.c_size_t),
        ("values", ctypes.POINTER(ctypes.c_float)),
        ("error_code", ctypes.c_int),
    ]


_LIBRARY = None
_LIBRARY_LOAD_ATTEMPTED = False


def analyze_samples(samples, sample_rate, db_threshold=-50.0, rms_threshold=0.01):
    """Analyze mono float samples with the native backend.

    Raises RuntimeError when the native backend is unavailable or reports an
    error. Callers should fall back to the pure Python analyzer.
    """
    library = _load_library()
    if library is None:
        raise RuntimeError("Native audio backend is unavailable")
    if not samples:
        return []

    array_type = ctypes.c_float * len(samples)
    sample_array = array_type(*samples)
    result = library.sls_analyze_mono_f32(
        sample_array,
        ctypes.c_size_t(len(samples)),
        ctypes.c_uint32(sample_rate),
        ctypes.c_float(db_threshold),
        ctypes.c_float(rms_threshold),
    )
    if result.error_code != 0:
        raise RuntimeError(f"Native audio backend failed: {result.error_code}")
    if not result.values:
        return []

    value_count = result.sample_count * SAMPLE_WIDTH
    try:
        raw_values = [result.values[index] for index in range(value_count)]
    finally:
        library.sls_free_analysis_result(result.values, ctypes.c_size_t(value_count))

    output = []
    for index in range(0, len(raw_values), SAMPLE_WIDTH):
        output.append({
            "time": round(float(raw_values[index]), 4),
            "openness": round(float(raw_values[index + 1]), 4),
            "weights": {
                viseme: float(raw_values[index + 2 + viseme_index])
                for viseme_index, viseme in enumerate(VISEMES)
            },
        })
    return output


def is_available():
    """Return whether the native backend can be loaded."""
    return _load_library() is not None


def _load_library():
    global _LIBRARY, _LIBRARY_LOAD_ATTEMPTED
    if _LIBRARY_LOAD_ATTEMPTED:
        return _LIBRARY
    _LIBRARY_LOAD_ATTEMPTED = True

    for library_path in _candidate_library_paths():
        if not library_path.is_file():
            continue
        try:
            library = ctypes.CDLL(str(library_path))
            library.sls_backend_version.restype = ctypes.c_uint32
            library.sls_analyze_mono_f32.argtypes = [
                ctypes.POINTER(ctypes.c_float),
                ctypes.c_size_t,
                ctypes.c_uint32,
                ctypes.c_float,
                ctypes.c_float,
            ]
            library.sls_analyze_mono_f32.restype = NativeAnalysisResult
            library.sls_free_analysis_result.argtypes = [
                ctypes.POINTER(ctypes.c_float),
                ctypes.c_size_t,
            ]
            library.sls_free_analysis_result.restype = None
            if library.sls_backend_version() != 1:
                continue
            _LIBRARY = library
            return _LIBRARY
        except OSError:
            continue
    return None


def _candidate_library_paths():
    base_dir = Path(__file__).resolve().parent / "native"
    system = platform.system()
    arch = _platform_arch()
    if system == "Windows":
        file_name = "simple_lip_sync_audio.dll"
        platform_dirs = (f"windows-{arch}", "windows")
    elif system == "Darwin":
        file_name = "libsimple_lip_sync_audio.dylib"
        platform_dirs = (f"macos-{arch}", "macos")
    else:
        file_name = "libsimple_lip_sync_audio.so"
        platform_dirs = (f"linux-{arch}", "linux")

    for platform_dir in platform_dirs:
        yield base_dir / platform_dir / file_name
    yield base_dir / file_name


def _platform_arch():
    machine = platform.machine().lower()
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    if machine in {"amd64", "x86_64", "x64"}:
        return "x64"
    return machine.replace("-", "_")
