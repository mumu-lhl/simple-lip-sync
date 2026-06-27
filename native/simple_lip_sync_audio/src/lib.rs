use std::f32::consts::PI;
use std::os::raw::{c_int, c_void};
use std::ptr;
use std::slice;

const VISEME_COUNT: usize = 6;
const SAMPLE_WIDTH: usize = 8;

const FORMANT_FREQUENCIES: [f32; 12] = [
    280.0, 320.0, 360.0, 500.0, 530.0, 850.0, 900.0, 980.0, 1350.0, 1450.0, 1850.0,
    2250.0,
];

#[repr(C)]
pub struct SlsAnalysisResult {
    pub sample_count: usize,
    pub values: *mut f32,
    pub error_code: c_int,
}

#[no_mangle]
pub extern "C" fn sls_analyze_mono_f32(
    samples: *const f32,
    sample_count: usize,
    sample_rate: u32,
    db_threshold: f32,
    rms_threshold: f32,
) -> SlsAnalysisResult {
    if samples.is_null() || sample_count == 0 || sample_rate == 0 {
        return SlsAnalysisResult {
            sample_count: 0,
            values: ptr::null_mut(),
            error_code: 1,
        };
    }

    let input = unsafe { slice::from_raw_parts(samples, sample_count) };
    let frame_length = ((sample_rate as f32 * 0.064) as usize).max(512);
    let hop_length = ((sample_rate as f32 * 0.010) as usize).max(80);

    let mut padded;
    let source = if input.len() < frame_length {
        padded = input.to_vec();
        padded.resize(frame_length, 0.0);
        padded.as_slice()
    } else {
        input
    };

    let window = hann_window(frame_length);
    let frame_count = ((source.len() - frame_length) / hop_length) + 1;
    let mut output = Vec::with_capacity(frame_count * SAMPLE_WIDTH);

    for frame_index in 0..frame_count {
        let start = frame_index * hop_length;
        let frame = &source[start..start + frame_length];
        let mut windowed = Vec::with_capacity(frame_length);
        let mut squared_sum = 0.0;
        for index in 0..frame_length {
            let value = frame[index] * window[index];
            squared_sum += value * value;
            windowed.push(value);
        }

        let frame_rms = (squared_sum / frame_length as f32).sqrt();
        let frame_db = 20.0 * (frame_rms + 1e-10).log10();
        let openness = compute_openness(frame_db, frame_rms, db_threshold, rms_threshold);
        let timestamp = ((start as f32) + (frame_length as f32 / 2.0)) / sample_rate as f32;

        let weights = if openness > 1e-3 {
            let mut energy = [0.0; 12];
            for (index, frequency) in FORMANT_FREQUENCIES.iter().enumerate() {
                energy[index] = goertzel_power(&windowed, sample_rate as f32, *frequency);
            }
            score_visemes_from_formant_energy(&energy)
        } else {
            [0.0; VISEME_COUNT]
        };

        output.push(timestamp);
        output.push((openness * 10000.0).round() / 10000.0);
        output.extend_from_slice(&weights);
    }

    let sample_count = output.len() / SAMPLE_WIDTH;
    let boxed = output.into_boxed_slice();
    let values = Box::into_raw(boxed) as *mut f32;
    SlsAnalysisResult {
        sample_count,
        values,
        error_code: 0,
    }
}

#[no_mangle]
pub extern "C" fn sls_free_analysis_result(values: *mut f32, value_count: usize) {
    if values.is_null() {
        return;
    }
    unsafe {
        let fat: *mut [f32] = ptr::slice_from_raw_parts_mut(values, value_count);
        drop(Box::from_raw(fat));
    }
}

#[no_mangle]
pub extern "C" fn sls_backend_version() -> u32 {
    1
}

fn clamp(value: f32, min_value: f32, max_value: f32) -> f32 {
    value.max(min_value).min(max_value)
}

fn compute_openness(frame_db: f32, frame_rms: f32, db_threshold: f32, rms_threshold: f32) -> f32 {
    let db_span = 12.0_f32.max(db_threshold.abs());
    let db_component = clamp((frame_db - db_threshold) / db_span, 0.0, 1.0);

    let rms_floor = rms_threshold.max(1e-4);
    let rms_span = (rms_floor * 6.0).max(0.05);
    let rms_component = clamp((frame_rms - rms_floor) / rms_span, 0.0, 1.0);

    clamp((db_component * 0.4) + (rms_component.sqrt() * 0.6), 0.0, 1.0)
}

fn hann_window(size: usize) -> Vec<f32> {
    if size <= 1 {
        return vec![1.0];
    }
    (0..size)
        .map(|index| 0.5 - (0.5 * ((2.0 * PI * index as f32) / (size - 1) as f32).cos()))
        .collect()
}

fn goertzel_power(samples: &[f32], sample_rate: f32, frequency: f32) -> f32 {
    let omega = (2.0 * PI * frequency) / sample_rate;
    let coefficient = 2.0 * omega.cos();
    let mut previous = 0.0;
    let mut previous2 = 0.0;
    for sample in samples {
        let current = sample + (coefficient * previous) - previous2;
        previous2 = previous;
        previous = current;
    }
    let power = (previous2 * previous2) + (previous * previous) - (coefficient * previous * previous2);
    power.max(0.0) / samples.len().max(1) as f32
}

fn score_visemes_from_formant_energy(energy: &[f32; 12]) -> [f32; VISEME_COUNT] {
    let mut weights = [
        (energy[5].max(0.0).sqrt() * energy[9].max(0.0).sqrt()) * 1.12,
        (energy[1].max(0.0).sqrt() * energy[11].max(0.0).sqrt()) * 1.05,
        energy[2].max(0.0).sqrt() * energy[6].max(0.0).sqrt(),
        energy[4].max(0.0).sqrt() * energy[10].max(0.0).sqrt(),
        energy[3].max(0.0).sqrt() * energy[7].max(0.0).sqrt(),
        (energy[0].max(0.0).sqrt() * energy[8].max(0.0).sqrt()) * 0.75,
    ];
    normalize_weights(&mut weights);
    weights
}

fn normalize_weights(weights: &mut [f32; VISEME_COUNT]) {
    let total: f32 = weights.iter().map(|value| value.max(0.0)).sum();
    if total <= 1e-8 {
        *weights = [0.0; VISEME_COUNT];
        return;
    }
    for value in weights.iter_mut() {
        *value = value.max(0.0) / total;
    }
}

#[no_mangle]
pub extern "C" fn sls_noop(_: *mut c_void) {}

