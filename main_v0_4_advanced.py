#!/usr/bin/env python3
"""
main.py — WiFi-DensePose fork advanced CSI anomaly head, v0.4

Purpose:
    Offline / replay-mode research detector for a "barrel-like long conductive-object
    anomaly" inside a bag using WiFi CSI.

Claim boundary:
    This program does NOT confirm weapons, rifles, or intent.
    It reports whether a target CSI scan is consistent with a long, rigid,
    conductive-object anomaly relative to an empty/safe-bag baseline.

Expected input:
    Two .npz files with a CSI array stored under key "csi".

Accepted CSI shapes:
    [time, rx, tx, subcarrier]
    [time, stream, subcarrier]
    [time, subcarrier]
    [..., 2] real/imag final channel is also accepted.

Examples:
    python main.py --make-demo --demo-dir demo_csi
    python main.py --empty demo_csi/empty_bag_csi.npz --scan demo_csi/target_bag_csi.npz --pretty
    python main.py --empty empty.npz --scan scan.npz --equations-out equations.md --concept-report report.md

Integration:
    Place this file at the root of a wifi-densepose fork. The GUI can import this
    module directly, and upstream CSI collectors can call detect_from_files().
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


CLAIM_BOUNDARY = (
    "Possible long conductive-object anomaly in bag; "
    "not weapon confirmation and not intent detection."
)

VERSION = "0.4.0"


# ---------------------------------------------------------------------------
# 50-equation concept registry patched from the requested research notes.
# These are used for: CLI report output, GUI display, model metadata, and
# linking formulas to implemented feature groups.
# ---------------------------------------------------------------------------

EQUATION_REGISTRY: List[Dict[str, str]] = [
    {"id": "E01", "group": "Signal and channel model", "name": "Received OFDM subcarrier model", "latex": r"y_k(t)=H_k(t)x_k(t)+n_k(t)", "implemented_as": "input CSI model"},
    {"id": "E02", "group": "Signal and channel model", "name": "Multipath CSI response", "latex": r"H_k(t)=\sum_{p=1}^{P} a_p(t)e^{-j2\pi f_k\tau_p(t)}", "implemented_as": "residual/multipath interpretation"},
    {"id": "E03", "group": "Signal and channel model", "name": "CSI amplitude", "latex": r"A_k(t)=|H_k(t)|", "implemented_as": "amplitude_distortion, amplitude_ratio"},
    {"id": "E04", "group": "Signal and channel model", "name": "CSI phase", "latex": r"\phi_k(t)=\arg(H_k(t))", "implemented_as": "phase_sanitize, phase_distortion"},
    {"id": "E05", "group": "Signal and channel model", "name": "Wavelength", "latex": r"\lambda=\frac{c}{f}", "implemented_as": "wavelength_m"},
    {"id": "E06", "group": "Signal and channel model", "name": "Path phase shift", "latex": r"\Delta \phi_k=-2\pi f_k\Delta\tau", "implemented_as": "phase residual features"},
    {"id": "E07", "group": "Signal and channel model", "name": "Propagation delay", "latex": r"\tau_p=\frac{d_p}{c}", "implemented_as": "delay profile interpretation"},
    {"id": "E08", "group": "Signal and channel model", "name": "Complex permittivity", "latex": r"\epsilon^*=\epsilon'-j\epsilon''", "implemented_as": "conductive prior metadata"},
    {"id": "E09", "group": "Signal and channel model", "name": "Skin depth", "latex": r"\delta=\sqrt{\frac{2}{\omega\mu\sigma}}", "implemented_as": "skin_depth_proxy"},
    {"id": "E10", "group": "Signal and channel model", "name": "Reflection coefficient", "latex": r"\Gamma=\frac{Z_2-Z_1}{Z_2+Z_1}", "implemented_as": "reflection_score_proxy"},

    {"id": "E11", "group": "CSI preprocessing", "name": "Baseline-normalized CSI", "latex": r"\tilde{H}_k(t)=\frac{H_k(t)}{H_{k,0}}", "implemented_as": "baseline_normalized_csi"},
    {"id": "E12", "group": "CSI preprocessing", "name": "CSI perturbation", "latex": r"\Delta H_k(t)=H_k(t)-H_{k,0}", "implemented_as": "baseline_residual"},
    {"id": "E13", "group": "CSI preprocessing", "name": "Amplitude residual", "latex": r"\Delta A_k(t)=|H_k(t)|-|H_{k,0}|", "implemented_as": "amplitude_residual_mean_z"},
    {"id": "E14", "group": "CSI preprocessing", "name": "Phase residual", "latex": r"\Delta \phi_k(t)=\operatorname{unwrap}(\phi_k(t))-\operatorname{unwrap}(\phi_{k,0})", "implemented_as": "phase_residual_mean_z"},
    {"id": "E15", "group": "CSI preprocessing", "name": "Antenna amplitude ratio", "latex": r"R^A_{i,j,k}(t)=\frac{|H_{i,k}(t)|}{|H_{j,k}(t)|+\epsilon}", "implemented_as": "amplitude_ratio_anomaly"},
    {"id": "E16", "group": "CSI preprocessing", "name": "Antenna phase difference", "latex": r"R^\phi_{i,j,k}(t)=\angle H_{i,k}(t)-\angle H_{j,k}(t)", "implemented_as": "phase_difference_anomaly"},
    {"id": "E17", "group": "CSI preprocessing", "name": "Phase sanitization", "latex": r"\phi'_k(t)=\phi_k(t)-(\alpha f_k+\beta)", "implemented_as": "phase_sanitize"},
    {"id": "E18", "group": "CSI preprocessing", "name": "MAD filter", "latex": r"z_k(t)=\frac{A_k(t)-\operatorname{median}(A_k)}{\operatorname{MAD}(A_k)}", "implemented_as": "robust_z"},
    {"id": "E19", "group": "CSI preprocessing", "name": "Smoothed CSI", "latex": r"\bar{H}_k(t)=\frac{1}{W}\sum_{u=t-W+1}^{t}H_k(u)", "implemented_as": "moving_average_csi"},
    {"id": "E20", "group": "CSI preprocessing", "name": "Kalman update", "latex": r"\hat{x}_{t|t}=\hat{x}_{t|t-1}+K_t(z_t-\hat{x}_{t|t-1})", "implemented_as": "kalman_smooth_1d"},

    {"id": "E21", "group": "Motion, Doppler, and temporal structure", "name": "STFT", "latex": r"S_k(t,\omega)=\sum_{\tau}H_k(\tau)w(\tau-t)e^{-j\omega\tau}", "implemented_as": "stft_peak_ratio"},
    {"id": "E22", "group": "Motion, Doppler, and temporal structure", "name": "Doppler estimate", "latex": r"f_D=\frac{1}{2\pi}\frac{d\phi(t)}{dt}", "implemented_as": "doppler_phase_rate_z"},
    {"id": "E23", "group": "Motion, Doppler, and temporal structure", "name": "Radial velocity estimate", "latex": r"v_r=\frac{\lambda f_D}{2}", "implemented_as": "radial_velocity_proxy"},
    {"id": "E24", "group": "Motion, Doppler, and temporal structure", "name": "Temporal energy", "latex": r"E(t)=\sum_k|\Delta H_k(t)|^2", "implemented_as": "energy_z"},
    {"id": "E25", "group": "Motion, Doppler, and temporal structure", "name": "Motion-normalized residual", "latex": r"M_k(t)=\frac{\Delta H_k(t)}{\sqrt{\sum_u|\Delta H_k(u)|^2+\epsilon}}", "implemented_as": "motion_normalized_residual"},
    {"id": "E26", "group": "Motion, Doppler, and temporal structure", "name": "Static-object persistence", "latex": r"P_s=\frac{1}{T}\sum_{t=1}^{T}\mathbb{1}(|\Delta H(t)|>\eta)", "implemented_as": "persistence"},
    {"id": "E27", "group": "Motion, Doppler, and temporal structure", "name": "Static/dynamic separation", "latex": r"H_k(t)=H^{static}_k+H^{dynamic}_k(t)+n_k(t)", "implemented_as": "baseline_residual"},
    {"id": "E28", "group": "Motion, Doppler, and temporal structure", "name": "Background-subtracted dynamic component", "latex": r"H^{dynamic}_k(t)=H_k(t)-\frac{1}{T_0}\sum_{u=1}^{T_0}H_k(u)", "implemented_as": "dynamic_component"},
    {"id": "E29", "group": "Motion, Doppler, and temporal structure", "name": "Temporal autocorrelation", "latex": r"\rho(\ell)=\frac{\sum_t x(t)x(t-\ell)}{\sum_t x(t)^2}", "implemented_as": "autocorr_lag1"},
    {"id": "E30", "group": "Motion, Doppler, and temporal structure", "name": "Cross-link coherence", "latex": r"C_{m,n}=\frac{|\sum_t \Delta H_m(t)\Delta H_n^*(t)|}{\sqrt{\sum_t|\Delta H_m(t)|^2\sum_t|\Delta H_n(t)|^2}}", "implemented_as": "cross_stream_coherence"},

    {"id": "E31", "group": "Spatial sensing and imaging abstractions", "name": "MIMO CSI matrix", "latex": r"\mathbf{H}_k(t)\in \mathbb{C}^{N_r\times N_t}", "implemented_as": "shape-aware CSI features"},
    {"id": "E32", "group": "Spatial sensing and imaging abstractions", "name": "Spatial covariance", "latex": r"\mathbf{R}_k=\mathbb{E}[\mathbf{h}_k\mathbf{h}_k^{H}]", "implemented_as": "spatial_covariance_score"},
    {"id": "E33", "group": "Spatial sensing and imaging abstractions", "name": "Beamforming response", "latex": r"B(\theta)=\mathbf{a}^{H}(\theta)\mathbf{R}\mathbf{a}(\theta)", "implemented_as": "beamforming_concentration_proxy"},
    {"id": "E34", "group": "Spatial sensing and imaging abstractions", "name": "MUSIC spectrum", "latex": r"P_{\text{MUSIC}}(\theta)=\frac{1}{\mathbf{a}^{H}(\theta)\mathbf{E}_n\mathbf{E}_n^{H}\mathbf{a}(\theta)}", "implemented_as": "music_sharpness_proxy"},
    {"id": "E35", "group": "Spatial sensing and imaging abstractions", "name": "Delay profile", "latex": r"P(\tau)=\left|\sum_k H_k e^{j2\pi f_k\tau}\right|^2", "implemented_as": "delay_profile_peakiness"},
    {"id": "E36", "group": "Spatial sensing and imaging abstractions", "name": "Range resolution limit", "latex": r"\Delta r=\frac{c}{2B}", "implemented_as": "range_resolution_m"},
    {"id": "E37", "group": "Spatial sensing and imaging abstractions", "name": "Fresnel-zone radius", "latex": r"r_F=\sqrt{\frac{\lambda d_1d_2}{d_1+d_2}}", "implemented_as": "fresnel_radius_m"},
    {"id": "E38", "group": "Spatial sensing and imaging abstractions", "name": "Tomographic projection", "latex": r"\mathbf{y}=\mathbf{A}\mathbf{x}+\mathbf{n}", "implemented_as": "tomographic_projection_proxy"},
    {"id": "E39", "group": "Spatial sensing and imaging abstractions", "name": "Regularized reconstruction", "latex": r"\hat{\mathbf{x}}=\arg\min_{\mathbf{x}}\|\mathbf{y}-\mathbf{A}\mathbf{x}\|_2^2+\lambda\|\mathbf{x}\|_1", "implemented_as": "sparse_reconstruction_proxy"},
    {"id": "E40", "group": "Spatial sensing and imaging abstractions", "name": "Spatial anomaly map", "latex": r"\mathcal{A}(x,y)=|\hat{x}(x,y)-\hat{x}_0(x,y)|", "implemented_as": "anomaly_map_proxy"},

    {"id": "E41", "group": "Metalness, elongation, and object-class features", "name": "Metalness vector", "latex": r"\mathbf{m}=[\Delta A,\Delta\phi,\sigma_A^2,\sigma_\phi^2,C_{m,n},P_s]", "implemented_as": "conductive_score_proxy"},
    {"id": "E42", "group": "Metalness, elongation, and object-class features", "name": "Inter-subcarrier variance", "latex": r"\sigma^2(t)=\frac{1}{K-1}\sum_{k=1}^{K}(A_k(t)-\bar{A}(t))^2", "implemented_as": "spectral_ripple_z"},
    {"id": "E43", "group": "Metalness, elongation, and object-class features", "name": "Phase curvature", "latex": r"\kappa_\phi=\frac{\partial^2 \phi(f)}{\partial f^2}", "implemented_as": "phase_curvature_z"},
    {"id": "E44", "group": "Metalness, elongation, and object-class features", "name": "Conductive reflection score", "latex": r"S_c=w_1|\Gamma|+w_2\sigma_A^2+w_3\sigma_\phi^2", "implemented_as": "conductive_score_proxy"},
    {"id": "E45", "group": "Metalness, elongation, and object-class features", "name": "Elongation from blob eigenvalues", "latex": r"E_{\text{long}}=\frac{\lambda_{\max}(\Sigma_{\text{blob}})}{\lambda_{\min}(\Sigma_{\text{blob}})+\epsilon}", "implemented_as": "elongation_proxy"},
    {"id": "E46", "group": "Metalness, elongation, and object-class features", "name": "Object orientation estimate", "latex": r"\theta_{\text{obj}}=\frac{1}{2}\tan^{-1}\left(\frac{2\Sigma_{xy}}{\Sigma_{xx}-\Sigma_{yy}}\right)", "implemented_as": "orientation_proxy_rad"},
    {"id": "E47", "group": "Metalness, elongation, and object-class features", "name": "Approximate object extent", "latex": r"L_{\text{est}}=\max_{i,j}\|p_i-p_j\|_2", "implemented_as": "extent_proxy"},
    {"id": "E48", "group": "Metalness, elongation, and object-class features", "name": "Bag/clutter compensation residual", "latex": r"\Delta H^{obj}=H^{bag+obj}-H^{bag}", "implemented_as": "bag residual"},
    {"id": "E49", "group": "Metalness, elongation, and object-class features", "name": "Class posterior", "latex": r"P(c|\mathbf{z})=\frac{e^{g_c(\mathbf{z})}}{\sum_{c'}e^{g_{c'}(\mathbf{z})}}", "implemented_as": "softmax_posteriors"},
    {"id": "E50", "group": "Metalness, elongation, and object-class features", "name": "Human-review alert score", "latex": r"S_{\text{alert}}=P(c=\text{elongated conductive object}|\mathbf{z})P(\text{restricted zone})C_{\text{sensor}}", "implemented_as": "score_features"},
]


@dataclass
class DetectionConfig:
    threshold: float = 0.85
    quality_threshold: float = 0.35
    zone: str = "bag_scan"
    min_frames: int = 8
    eps: float = 1e-9

    # Optional context priors. Keep bounded and explicit.
    restricted_zone_prior: float = 0.50
    bag_transition_prior: float = 0.50
    human_review_required: bool = True

    # RF metadata used for wavelength, range, Fresnel, Doppler proxies.
    carrier_hz: float = 5.8e9
    bandwidth_hz: float = 80e6
    link_distance_m: float = 3.0
    sample_rate_hz: float = 100.0
    assumed_conductivity_s_m: float = 1.0e7
    assumed_relative_permittivity: float = 1.0

    # Feature weights. These are research defaults; replace with calibrated
    # weights after collecting venue/device data.
    w_energy_z: float = 0.52
    w_spectral_ripple_z: float = 0.54
    w_phase_distortion_z: float = 0.26
    w_amplitude_distortion_z: float = 0.24
    w_phase_curvature_z: float = 0.32
    w_group_delay_z: float = 0.22
    w_amplitude_residual_z: float = 0.28
    w_phase_residual_z: float = 0.25
    w_amplitude_ratio_anomaly: float = 0.26
    w_phase_difference_anomaly: float = 0.26
    w_stft_peak_ratio: float = 0.16
    w_doppler_phase_rate_z: float = 0.18
    w_autocorr_lag1: float = 0.12
    w_cross_stream_coherence: float = 0.34
    w_coherence_rank: float = 0.22
    w_spatial_covariance_score: float = 0.18
    w_beamforming_concentration_proxy: float = 0.18
    w_music_sharpness_proxy: float = 0.16
    w_delay_profile_peakiness: float = 0.20
    w_elongation_proxy_log: float = 0.30
    w_orientation_stability: float = 0.18
    w_extent_proxy: float = 0.16
    w_rigidity_proxy: float = 0.30
    w_persistence: float = 0.36
    w_conductive_score_proxy: float = 0.32
    w_spectral_entropy_drop: float = 0.18
    w_spectral_flatness_drop: float = 0.20
    w_mahalanobis_proxy: float = 0.26
    w_quality: float = 0.24
    w_restricted_zone_prior: float = 0.26
    w_bag_transition_prior: float = 0.20
    bias: float = 4.40


@dataclass
class CSIFeatureVector:
    # Signal/channel and preprocessing concepts.
    wavelength_m: float
    skin_depth_proxy_m: float
    reflection_score_proxy: float
    baseline_norm_delta: float
    amplitude_residual_mean_z: float
    phase_residual_mean_z: float
    amplitude_ratio_anomaly: float
    phase_difference_anomaly: float
    smoothed_energy_z: float

    # Motion/Doppler/temporal concepts.
    energy_z: float
    spectral_ripple_z: float
    phase_distortion_z: float
    amplitude_distortion_z: float
    phase_curvature_z: float
    group_delay_z: float
    stft_peak_ratio: float
    doppler_phase_rate_z: float
    radial_velocity_proxy_m_s: float
    autocorr_lag1: float
    cross_stream_coherence: float

    # Spatial/imaging abstraction concepts.
    coherence_rank: float
    spatial_covariance_score: float
    beamforming_concentration_proxy: float
    music_sharpness_proxy: float
    delay_profile_peakiness: float
    range_resolution_m: float
    fresnel_radius_m: float
    tomographic_projection_proxy: float
    sparse_reconstruction_proxy: float
    anomaly_map_proxy: float

    # Metalness/elongation/object-class concepts.
    elongation_proxy: float
    orientation_proxy_rad: float
    orientation_stability: float
    extent_proxy: float
    rigidity_proxy: float
    persistence: float
    conductive_score_proxy: float
    spectral_entropy_delta: float
    spectral_flatness_delta: float
    residual_kurtosis_z: float
    mahalanobis_proxy: float
    posterior_normal: float
    posterior_long_conductive: float
    posterior_unknown: float

    # Governance/context.
    sensor_quality: float
    restricted_zone_prior: float
    bag_transition_prior: float


@dataclass
class DetectionResult:
    event: str
    zone: str
    timestamp_ms: int
    score: float
    threshold: float
    alert: bool
    severity: str
    claim_boundary: str
    features: Dict[str, float]
    contributions: Dict[str, float]
    equation_coverage: List[Dict[str, str]]
    model: Dict[str, Any]


class CSIInputError(ValueError):
    """Raised when CSI files are missing, malformed, or not comparable."""


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _softmax(logits: List[float]) -> List[float]:
    arr = np.asarray(logits, dtype=np.float64)
    arr -= np.max(arr)
    exp = np.exp(arr)
    return (exp / (np.sum(exp) + 1e-12)).tolist()


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        value = float(x)
        if not math.isfinite(value):
            return default
        return value
    except Exception:
        return default


def _clip01(x: float) -> float:
    return float(np.clip(_safe_float(x), 0.0, 1.0))


def _mad(x: np.ndarray, eps: float = 1e-9) -> float:
    x = np.asarray(x, dtype=np.float64).ravel()
    if x.size == 0:
        return eps
    med = np.median(x)
    return float(np.median(np.abs(x - med)) + eps)


def _robust_z(value: float, baseline_values: np.ndarray, eps: float = 1e-9) -> float:
    b = np.asarray(baseline_values, dtype=np.float64).ravel()
    if b.size == 0:
        return 0.0
    z = (float(value) - float(np.median(b))) / _mad(b, eps)
    return float(np.clip(z, -20.0, 20.0))


def _kurtosis(x: np.ndarray, eps: float = 1e-9) -> float:
    x = np.asarray(x, dtype=np.float64).ravel()
    if x.size < 4:
        return 0.0
    mu = float(np.mean(x))
    sd = float(np.std(x) + eps)
    return float(np.mean(((x - mu) / sd) ** 4))


def _entropy(p: np.ndarray, eps: float = 1e-12) -> float:
    p = np.asarray(p, dtype=np.float64).ravel()
    total = float(np.sum(p) + eps)
    p = np.clip(p / total, eps, 1.0)
    return float(-np.sum(p * np.log(p)))


def _spectral_flatness(power: np.ndarray, eps: float = 1e-12) -> float:
    p = np.asarray(power, dtype=np.float64).ravel() + eps
    return float(np.exp(np.mean(np.log(p))) / (np.mean(p) + eps))


def _ensure_complex_csi(x: np.ndarray) -> np.ndarray:
    arr = np.asarray(x)
    if np.iscomplexobj(arr):
        return arr.astype(np.complex64)
    if arr.ndim >= 2 and arr.shape[-1] == 2:
        return (arr[..., 0] + 1j * arr[..., 1]).astype(np.complex64)
    return arr.astype(np.float32).astype(np.complex64)


def load_csi_npz(path: Path, key: str = "csi") -> np.ndarray:
    path = Path(path)
    if not path.exists():
        raise CSIInputError(f"CSI file not found: {path}")

    try:
        payload = np.load(path, allow_pickle=False)
    except Exception as exc:
        raise CSIInputError(f"Could not read {path}: {exc}") from exc

    if key not in payload:
        keys = ", ".join(payload.files)
        raise CSIInputError(f"{path} does not contain key '{key}'. Available keys: {keys}")

    csi = _ensure_complex_csi(payload[key])
    if csi.ndim < 2:
        raise CSIInputError(f"CSI array must be at least [time, subcarrier]. Got shape {csi.shape}")
    if csi.shape[0] < 2:
        raise CSIInputError(f"CSI array needs at least 2 frames. Got shape {csi.shape}")

    csi = np.nan_to_num(csi, nan=0.0, posinf=0.0, neginf=0.0).astype(np.complex64)
    return csi


def align_csi(empty: np.ndarray, scan: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    if empty.shape[1:] != scan.shape[1:]:
        raise CSIInputError(
            f"CSI non-time dimensions must match. empty={empty.shape}, scan={scan.shape}"
        )
    t = min(empty.shape[0], scan.shape[0])
    if t < 2:
        raise CSIInputError("Need at least 2 aligned frames.")
    return empty[:t], scan[:t]


def flatten_streams(x: np.ndarray) -> np.ndarray:
    return x.reshape(x.shape[0], -1)


def stream_subcarrier_view(x: np.ndarray) -> np.ndarray:
    """
    Returns [time, streams, subcarrier].
    """
    if x.ndim == 2:
        return x[:, None, :]
    return x.reshape(x.shape[0], -1, x.shape[-1])


def wavelength_m(carrier_hz: float) -> float:
    return 299_792_458.0 / max(float(carrier_hz), 1.0)


def skin_depth_proxy(carrier_hz: float, conductivity_s_m: float) -> float:
    # δ = sqrt(2/(ω μ σ)), with μ≈μ0. This is a rough metadata proxy.
    mu0 = 4.0 * math.pi * 1e-7
    omega = 2.0 * math.pi * max(float(carrier_hz), 1.0)
    sigma = max(float(conductivity_s_m), 1e-9)
    return float(math.sqrt(2.0 / (omega * mu0 * sigma)))


def reflection_score_proxy_from_material(relative_permittivity: float, conductivity_s_m: float, carrier_hz: float) -> float:
    """
    Rough bounded material reflectivity proxy. It is not a calibrated EM solver.
    """
    eps0 = 8.8541878128e-12
    omega = 2.0 * math.pi * max(float(carrier_hz), 1.0)
    er = max(float(relative_permittivity), 1e-6)
    sigma_term = float(conductivity_s_m) / max(omega * eps0, 1e-12)
    complex_eps_mag = math.sqrt(er ** 2 + sigma_term ** 2)
    gamma = abs((math.sqrt(complex_eps_mag) - 1.0) / (math.sqrt(complex_eps_mag) + 1.0 + 1e-12))
    return float(np.clip(gamma, 0.0, 1.0))


def phase_sanitize(csi: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    """
    Unwrap phase along subcarrier dimension and remove a linear phase trend per
    time/stream slice. This implements the patched phase-sanitization equation:
        phi'_k(t)=phi_k(t)-(alpha f_k+beta)
    """
    phase = np.unwrap(np.angle(csi + eps), axis=-1).astype(np.float64)
    if csi.shape[-1] < 3:
        return phase

    k = np.arange(csi.shape[-1], dtype=np.float64)
    k_centered = k - k.mean()
    denom = float(np.sum(k_centered ** 2) + eps)

    flat = phase.reshape(-1, phase.shape[-1])
    sanitized = np.empty_like(flat)

    for i, row in enumerate(flat):
        slope = float(np.sum((row - row.mean()) * k_centered) / denom)
        intercept = float(row.mean() - slope * k.mean())
        sanitized[i] = row - (slope * k + intercept)

    return sanitized.reshape(phase.shape)


def moving_average_csi(csi: np.ndarray, window: int = 5) -> np.ndarray:
    if window <= 1 or csi.shape[0] < 3:
        return csi
    w = min(window, csi.shape[0])
    out = np.empty_like(csi)
    for t in range(csi.shape[0]):
        lo = max(0, t - w + 1)
        out[t] = np.mean(csi[lo:t + 1], axis=0)
    return out


def kalman_smooth_1d(values: np.ndarray, process_var: float = 1e-3, measurement_var: float = 1e-1) -> np.ndarray:
    vals = np.asarray(values, dtype=np.float64).ravel()
    if vals.size == 0:
        return vals
    x = vals[0]
    p = 1.0
    out = np.empty_like(vals)
    for i, z in enumerate(vals):
        p = p + process_var
        k = p / (p + measurement_var)
        x = x + k * (z - x)
        p = (1 - k) * p
        out[i] = x
    return out


def baseline_residual(empty: np.ndarray, scan: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    baseline = np.median(empty, axis=0, keepdims=True)
    return empty - baseline, scan - baseline


def baseline_normalized_csi(empty: np.ndarray, scan: np.ndarray, eps: float) -> Tuple[np.ndarray, np.ndarray]:
    baseline = np.median(empty, axis=0, keepdims=True)
    return empty / (baseline + eps), scan / (baseline + eps)


def dynamic_component(csi: np.ndarray) -> np.ndarray:
    return csi - np.mean(csi, axis=0, keepdims=True)


def motion_normalized_residual(delta: np.ndarray, eps: float) -> np.ndarray:
    denom = np.sqrt(np.sum(np.abs(delta) ** 2, axis=0, keepdims=True) + eps)
    return delta / denom


def temporal_energy(delta: np.ndarray) -> np.ndarray:
    f = flatten_streams(delta)
    return np.sum(np.abs(f) ** 2, axis=1).astype(np.float64)


def spectral_power_by_subcarrier(delta: np.ndarray) -> np.ndarray:
    power = np.abs(delta) ** 2
    if delta.ndim == 2:
        return power
    axes = tuple(range(1, delta.ndim - 1))
    return np.mean(power, axis=axes)


def spectral_ripple(delta: np.ndarray) -> np.ndarray:
    by_subcarrier = spectral_power_by_subcarrier(delta)
    return np.var(by_subcarrier, axis=-1).astype(np.float64)


def phase_distortion(csi: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    ph = phase_sanitize(csi, eps=eps)
    if ph.ndim == 2:
        return np.std(ph, axis=-1).astype(np.float64)
    axes = tuple(range(1, ph.ndim))
    return np.std(ph, axis=axes).astype(np.float64)


def amplitude_distortion(csi: np.ndarray) -> np.ndarray:
    amp = np.abs(csi)
    if amp.ndim == 2:
        return np.std(amp, axis=-1).astype(np.float64)
    axes = tuple(range(1, amp.ndim))
    return np.std(amp, axis=axes).astype(np.float64)


def amplitude_residual_series(empty: np.ndarray, scan: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    base = np.median(empty, axis=0, keepdims=True)
    d0 = np.abs(empty) - np.abs(base)
    d1 = np.abs(scan) - np.abs(base)
    axes = tuple(range(1, d0.ndim))
    return np.mean(d0, axis=axes), np.mean(d1, axis=axes)


def phase_residual_series(empty: np.ndarray, scan: np.ndarray, eps: float) -> Tuple[np.ndarray, np.ndarray]:
    base = np.median(empty, axis=0, keepdims=True)
    ph0 = phase_sanitize(empty, eps)
    ph1 = phase_sanitize(scan, eps)
    phb = phase_sanitize(base, eps)
    r0 = ph0 - phb
    r1 = ph1 - phb
    axes = tuple(range(1, r0.ndim))
    return np.mean(r0, axis=axes), np.mean(r1, axis=axes)


def phase_curvature(csi: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    ph = phase_sanitize(csi, eps=eps)
    if ph.shape[-1] < 3:
        return np.zeros(ph.shape[0], dtype=np.float64)
    curv = np.diff(ph, n=2, axis=-1)
    if curv.ndim == 2:
        return np.std(curv, axis=-1).astype(np.float64)
    axes = tuple(range(1, curv.ndim))
    return np.std(curv, axis=axes).astype(np.float64)


def group_delay_variance(csi: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    ph = phase_sanitize(csi, eps=eps)
    if ph.shape[-1] < 2:
        return np.zeros(ph.shape[0], dtype=np.float64)
    gd = -np.diff(ph, axis=-1)
    if gd.ndim == 2:
        return np.var(gd, axis=-1).astype(np.float64)
    axes = tuple(range(1, gd.ndim))
    return np.var(gd, axis=axes).astype(np.float64)


def amplitude_ratio_anomaly(empty: np.ndarray, scan: np.ndarray, eps: float) -> float:
    """
    Implements antenna amplitude ratio concept by comparing stream-pair ratios.
    """
    e = stream_subcarrier_view(empty)
    s = stream_subcarrier_view(scan)
    if e.shape[1] < 2:
        return 0.0

    def ratios(x: np.ndarray) -> np.ndarray:
        a = np.abs(x[:, :-1, :])
        b = np.abs(x[:, 1:, :])
        return a / (b + eps)

    r0 = ratios(e)
    r1 = ratios(s)
    return _robust_z(float(np.mean(np.abs(r1 - np.median(r0, axis=0, keepdims=True)))), np.mean(np.abs(r0 - np.median(r0, axis=0, keepdims=True)), axis=(1, 2)), eps)


def phase_difference_anomaly(empty: np.ndarray, scan: np.ndarray, eps: float) -> float:
    e = stream_subcarrier_view(empty)
    s = stream_subcarrier_view(scan)
    if e.shape[1] < 2:
        return 0.0

    def pdiff(x: np.ndarray) -> np.ndarray:
        ph = np.unwrap(np.angle(x + eps), axis=-1)
        return ph[:, :-1, :] - ph[:, 1:, :]

    p0 = pdiff(e)
    p1 = pdiff(s)
    return _robust_z(float(np.mean(np.abs(p1 - np.median(p0, axis=0, keepdims=True)))), np.mean(np.abs(p0 - np.median(p0, axis=0, keepdims=True)), axis=(1, 2)), eps)


def stft_peak_ratio(delta: np.ndarray, eps: float = 1e-9, window: int = 16) -> float:
    """
    STFT proxy over the dominant residual-energy trace.
    """
    x = temporal_energy(delta)
    if x.size < 8:
        return 0.0
    window = max(4, min(window, x.size))
    hop = max(1, window // 2)
    peaks = []
    totals = []
    win = np.hanning(window)
    for start in range(0, x.size - window + 1, hop):
        seg = (x[start:start + window] - np.mean(x[start:start + window])) * win
        spec = np.abs(np.fft.rfft(seg)) ** 2
        if spec.size > 1:
            spec[0] = 0.0
        peaks.append(float(np.max(spec)))
        totals.append(float(np.sum(spec) + eps))
    if not peaks:
        return 0.0
    return float(np.clip(np.median(np.asarray(peaks) / np.asarray(totals)), 0.0, 1.0))


def doppler_phase_rate_series(csi: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    ph = phase_sanitize(csi, eps=eps)
    # Average over streams/subcarriers into one phase trace, then differentiate.
    axes = tuple(range(1, ph.ndim))
    trace = np.mean(ph, axis=axes)
    if trace.size < 2:
        return np.zeros_like(trace)
    return np.diff(trace, prepend=trace[0]) / (2.0 * math.pi)


def autocorr_lag1(values: np.ndarray, eps: float = 1e-9) -> float:
    x = np.asarray(values, dtype=np.float64).ravel()
    if x.size < 3:
        return 0.0
    x = x - np.mean(x)
    denom = float(np.sum(x ** 2) + eps)
    return float(np.clip(np.sum(x[1:] * x[:-1]) / denom, -1.0, 1.0))


def cross_stream_coherence(delta: np.ndarray, eps: float = 1e-9) -> float:
    f = flatten_streams(delta)
    if f.shape[1] < 2:
        return 0.0
    a = f[:, 0]
    b = f[:, -1]
    denom = np.linalg.norm(a) * np.linalg.norm(b) + eps
    return float(np.clip(np.abs(np.vdot(a, b)) / denom, 0.0, 1.0))


def coherence_rank(delta: np.ndarray, eps: float = 1e-9) -> float:
    """
    Low effective rank can indicate a consistent scattering structure across time.
    Returns normalized inverse effective rank in [0,1].
    """
    f = flatten_streams(delta).astype(np.complex128)
    if f.shape[0] < 3 or f.shape[1] < 3:
        return 0.0
    max_cols = min(f.shape[1], 256)
    idx = np.linspace(0, f.shape[1] - 1, max_cols).astype(int)
    x = f[:, idx]
    x = x - np.mean(x, axis=0, keepdims=True)
    try:
        s = np.linalg.svd(x, compute_uv=False)
    except np.linalg.LinAlgError:
        return 0.0
    if s.size == 0:
        return 0.0
    p = (s ** 2) / (float(np.sum(s ** 2)) + eps)
    eff_rank = math.exp(_entropy(p, eps))
    normalized_inverse = 1.0 - ((eff_rank - 1.0) / max(float(len(p) - 1), 1.0))
    return float(np.clip(normalized_inverse, 0.0, 1.0))


def spatial_covariance_score(delta: np.ndarray, eps: float = 1e-9) -> float:
    x = stream_subcarrier_view(delta)
    if x.shape[1] < 2:
        return 0.0
    # Average over subcarriers, covariance across streams.
    h = np.mean(x, axis=-1)
    h = h - np.mean(h, axis=0, keepdims=True)
    cov = (h.conj().T @ h) / max(h.shape[0] - 1, 1)
    vals = np.linalg.eigvalsh(cov + eps * np.eye(cov.shape[0]))
    return float(np.clip(vals[-1].real / (np.sum(vals.real) + eps), 0.0, 1.0))


def beamforming_concentration_proxy(delta: np.ndarray, eps: float = 1e-9) -> float:
    x = stream_subcarrier_view(delta)
    n_stream = x.shape[1]
    if n_stream < 2:
        return 0.0
    h = np.mean(x, axis=(0, 2))
    angles = np.linspace(-math.pi / 2, math.pi / 2, 64)
    responses = []
    idx = np.arange(n_stream)
    for theta in angles:
        a = np.exp(1j * math.pi * idx * math.sin(theta))
        responses.append(float(np.abs(np.vdot(a, h)) ** 2))
    responses = np.asarray(responses)
    return float(np.clip(np.max(responses) / (np.mean(responses) * len(responses) + eps), 0.0, 1.0))


def music_sharpness_proxy(delta: np.ndarray, eps: float = 1e-9) -> float:
    x = stream_subcarrier_view(delta)
    if x.shape[1] < 3:
        return 0.0
    h = np.mean(x, axis=-1)
    h = h - np.mean(h, axis=0, keepdims=True)
    cov = (h.conj().T @ h) / max(h.shape[0] - 1, 1)
    vals = np.sort(np.linalg.eigvalsh(cov).real)
    if vals.size < 2:
        return 0.0
    return float(np.clip((vals[-1] - vals[-2]) / (np.sum(vals) + eps), 0.0, 1.0))


def delay_profile_peakiness(delta: np.ndarray, eps: float = 1e-9) -> float:
    by_sub = np.mean(stream_subcarrier_view(delta), axis=1)  # [time, subcarrier]
    profile = np.abs(np.fft.ifft(by_sub, axis=-1)) ** 2
    p = np.mean(profile, axis=0)
    return float(np.clip(np.max(p) / (np.mean(p) * p.size + eps), 0.0, 1.0))


def elongation_orientation_extent(delta: np.ndarray, eps: float = 1e-9) -> Tuple[float, float, float, float]:
    """
    Coarse pseudo-geometry from residual amplitude maps. This is not imaging;
    it gives stable scalar proxies for elongated, concentrated residual structure.
    """
    amp = np.abs(stream_subcarrier_view(delta))  # [time, stream, subcarrier]
    mean_map = np.mean(amp, axis=0)  # [stream, subcarrier]
    if mean_map.size < 4:
        return 1.0, 0.0, 0.0, 0.0

    threshold = np.percentile(mean_map, 75)
    points = np.argwhere(mean_map >= threshold)
    weights = mean_map[mean_map >= threshold].astype(np.float64)

    if points.shape[0] < 3 or np.sum(weights) <= eps:
        return 1.0, 0.0, 0.0, 0.0

    mu = np.average(points.astype(np.float64), axis=0, weights=weights)
    centered = points.astype(np.float64) - mu
    cov = (centered * weights[:, None]).T @ centered / (np.sum(weights) + eps)
    vals, vecs = np.linalg.eigh(cov + eps * np.eye(2))
    vals = np.maximum(vals, eps)
    elong = float(vals[-1] / vals[0])
    major_vec = vecs[:, -1]
    theta = float(math.atan2(major_vec[0], major_vec[1]))
    proj = centered @ major_vec
    extent = float((np.max(proj) - np.min(proj)) / max(mean_map.shape))
    # Orientation stability over time.
    thetas = []
    for t in range(amp.shape[0]):
        mm = amp[t]
        th = np.percentile(mm, 75)
        pts = np.argwhere(mm >= th)
        ws = mm[mm >= th].astype(np.float64)
        if pts.shape[0] >= 3 and np.sum(ws) > eps:
            m = np.average(pts.astype(np.float64), axis=0, weights=ws)
            cen = pts.astype(np.float64) - m
            cv = (cen * ws[:, None]).T @ cen / (np.sum(ws) + eps)
            _, vc = np.linalg.eigh(cv + eps * np.eye(2))
            mv = vc[:, -1]
            thetas.append(math.atan2(mv[0], mv[1]))
    if len(thetas) < 2:
        stability = 0.0
    else:
        stability = float(1.0 - np.clip(np.std(np.unwrap(thetas)) / math.pi, 0.0, 1.0))
    return float(elong), theta, stability, float(np.clip(extent, 0.0, 1.0))


def tomographic_projection_proxy(delta: np.ndarray, eps: float = 1e-9) -> float:
    # Treat stream-subcarrier power as a projection matrix; high anisotropy = stronger projection anomaly.
    m = np.mean(np.abs(stream_subcarrier_view(delta)) ** 2, axis=0)
    if min(m.shape) < 2:
        return 0.0
    row_var = np.var(np.sum(m, axis=1))
    col_var = np.var(np.sum(m, axis=0))
    total = np.var(m) + eps
    return float(np.clip((row_var + col_var) / (total * (m.shape[0] + m.shape[1]) + eps), 0.0, 5.0))


def sparse_reconstruction_proxy(delta: np.ndarray, eps: float = 1e-9) -> float:
    # L1/L2 concentration proxy: higher means residual can be explained by fewer coefficients.
    v = np.abs(np.mean(stream_subcarrier_view(delta), axis=0)).ravel()
    if v.size == 0:
        return 0.0
    l1 = float(np.sum(np.abs(v)))
    l2 = float(np.sqrt(np.sum(v ** 2)) + eps)
    concentration = l2 / (l1 + eps) * math.sqrt(v.size)
    return float(np.clip(concentration, 0.0, 1.0))


def anomaly_map_proxy(empty_delta: np.ndarray, scan_delta: np.ndarray, eps: float = 1e-9) -> float:
    m0 = np.mean(np.abs(stream_subcarrier_view(empty_delta)), axis=0)
    m1 = np.mean(np.abs(stream_subcarrier_view(scan_delta)), axis=0)
    diff = np.abs(m1 - m0)
    return float(np.clip(np.max(diff) / (np.mean(diff) + eps) / max(diff.size, 1), 0.0, 1.0))


def range_resolution_m(bandwidth_hz: float) -> float:
    return 299_792_458.0 / (2.0 * max(float(bandwidth_hz), 1.0))


def fresnel_radius_m(carrier_hz: float, link_distance_m: float) -> float:
    lam = wavelength_m(carrier_hz)
    d = max(float(link_distance_m), 1e-6)
    d1 = d / 2.0
    d2 = d / 2.0
    return float(math.sqrt(lam * d1 * d2 / (d1 + d2)))


def rigidity_proxy(delta: np.ndarray, eps: float = 1e-9) -> float:
    f = flatten_streams(delta)
    template = np.median(f, axis=0)
    template_norm = np.linalg.norm(template) + eps
    sims = [
        float(np.abs(np.vdot(row, template)) / ((np.linalg.norm(row) + eps) * template_norm))
        for row in f
    ]
    return float(np.clip(np.mean(sims), 0.0, 1.0))


def persistence(delta: np.ndarray, baseline_delta: np.ndarray, eps: float = 1e-9) -> float:
    e0 = temporal_energy(baseline_delta)
    e1 = temporal_energy(delta)
    threshold = float(np.median(e0) + 4.0 * _mad(e0, eps))
    return float(np.mean(e1 > threshold))


def spectral_entropy_and_flatness(delta: np.ndarray, eps: float = 1e-12) -> Tuple[float, float]:
    p = np.mean(spectral_power_by_subcarrier(delta), axis=0)
    return _entropy(p, eps), _spectral_flatness(p, eps)


def residual_kurtosis(delta: np.ndarray) -> np.ndarray:
    f = np.abs(flatten_streams(delta))
    return np.array([_kurtosis(row) for row in f], dtype=np.float64)


def mahalanobis_proxy(empty_delta: np.ndarray, scan_delta: np.ndarray, eps: float = 1e-9) -> float:
    def trace_features(d: np.ndarray) -> np.ndarray:
        return np.stack(
            [
                temporal_energy(d),
                spectral_ripple(d),
                phase_curvature(d),
                group_delay_variance(d),
                residual_kurtosis(d),
            ],
            axis=1,
        ).astype(np.float64)

    b = trace_features(empty_delta)
    s = trace_features(scan_delta)
    med = np.median(b, axis=0)
    scale = np.array([_mad(b[:, i], eps) for i in range(b.shape[1])], dtype=np.float64)
    z = (s - med) / (scale + eps)
    dist = np.sqrt(np.sum(z ** 2, axis=1))
    return float(np.clip(np.median(dist) / 10.0, 0.0, 5.0))


def sensor_quality(empty_delta: np.ndarray, scan_delta: np.ndarray, eps: float = 1e-9) -> float:
    e0 = temporal_energy(empty_delta)
    e1 = temporal_energy(scan_delta)
    separation = abs(float(np.mean(e1) - np.mean(e0))) / (float(np.std(e0) + np.std(e1)) + eps)
    nonzero = float(np.mean(np.abs(scan_delta) > eps))
    stable = float(1.0 / (1.0 + np.std(e1) / (abs(np.mean(e1)) + eps)))
    q = _sigmoid(0.60 * separation - 0.70) * nonzero * (0.65 + 0.35 * stable)
    return float(np.clip(q, 0.0, 1.0))


def conductive_score_proxy(f: Dict[str, float]) -> float:
    # E41/E44 combined metalness/reflective proxy, bounded.
    x = (
        0.18 * max(f["amplitude_residual_mean_z"], 0.0)
        + 0.16 * max(f["phase_residual_mean_z"], 0.0)
        + 0.13 * max(f["spectral_ripple_z"], 0.0)
        + 0.12 * max(f["phase_curvature_z"], 0.0)
        + 0.10 * f["cross_stream_coherence"]
        + 0.12 * f["persistence"]
        + 0.12 * f["reflection_score_proxy"]
        + 0.07 * f["amplitude_ratio_anomaly"]
    )
    return float(_sigmoid(x - 2.2))


def softmax_posteriors(features: Dict[str, float], score: float) -> Tuple[float, float, float]:
    # E49: class posterior toy model. Not trained; interpretable placeholder.
    normal_logit = 1.5 - 2.5 * score - 0.8 * features["persistence"]
    long_logit = 2.5 * score + 0.8 * features["elongation_proxy"] / (features["elongation_proxy"] + 10.0)
    unknown_logit = 0.8 * (1.0 - features["sensor_quality"]) + 0.3 * abs(features["mahalanobis_proxy"])
    p = _softmax([normal_logit, long_logit, unknown_logit])
    return float(p[0]), float(p[1]), float(p[2])


def extract_features(empty: np.ndarray, scan: np.ndarray, cfg: DetectionConfig) -> CSIFeatureVector:
    empty, scan = align_csi(empty, scan)
    if empty.shape[0] < cfg.min_frames or scan.shape[0] < cfg.min_frames:
        raise CSIInputError(
            f"Need at least {cfg.min_frames} frames for stable detection. "
            f"Got empty={empty.shape[0]}, scan={scan.shape[0]}"
        )

    d_empty, d_scan = baseline_residual(empty, scan)
    n_empty, n_scan = baseline_normalized_csi(empty, scan, cfg.eps)
    smooth_empty = moving_average_csi(empty, window=5)
    smooth_scan = moving_average_csi(scan, window=5)
    sd_empty, sd_scan = baseline_residual(smooth_empty, smooth_scan)

    e0, e1 = temporal_energy(d_empty), temporal_energy(d_scan)
    se0, se1 = temporal_energy(sd_empty), temporal_energy(sd_scan)
    r0, r1 = spectral_ripple(d_empty), spectral_ripple(d_scan)
    p0, p1 = phase_distortion(empty, eps=cfg.eps), phase_distortion(scan, eps=cfg.eps)
    a0, a1 = amplitude_distortion(empty), amplitude_distortion(scan)
    c0, c1 = phase_curvature(empty, eps=cfg.eps), phase_curvature(scan, eps=cfg.eps)
    g0, g1 = group_delay_variance(empty, eps=cfg.eps), group_delay_variance(scan, eps=cfg.eps)
    ar0, ar1 = amplitude_residual_series(empty, scan)
    pr0, pr1 = phase_residual_series(empty, scan, cfg.eps)
    k0, k1 = residual_kurtosis(d_empty), residual_kurtosis(d_scan)
    ent0, flat0 = spectral_entropy_and_flatness(d_empty)
    ent1, flat1 = spectral_entropy_and_flatness(d_scan)
    dop0 = doppler_phase_rate_series(empty, cfg.eps)
    dop1 = doppler_phase_rate_series(scan, cfg.eps)

    elong, theta, theta_stability, extent = elongation_orientation_extent(d_scan, cfg.eps)
    q = sensor_quality(d_empty, d_scan, cfg.eps)

    raw = {
        "wavelength_m": wavelength_m(cfg.carrier_hz),
        "skin_depth_proxy_m": skin_depth_proxy(cfg.carrier_hz, cfg.assumed_conductivity_s_m),
        "reflection_score_proxy": reflection_score_proxy_from_material(
            cfg.assumed_relative_permittivity, cfg.assumed_conductivity_s_m, cfg.carrier_hz
        ),
        "baseline_norm_delta": float(np.mean(np.abs(n_scan - n_empty))),
        "amplitude_residual_mean_z": _robust_z(float(np.mean(ar1)), ar0, cfg.eps),
        "phase_residual_mean_z": _robust_z(float(np.mean(pr1)), pr0, cfg.eps),
        "amplitude_ratio_anomaly": amplitude_ratio_anomaly(empty, scan, cfg.eps),
        "phase_difference_anomaly": phase_difference_anomaly(empty, scan, cfg.eps),
        "smoothed_energy_z": _robust_z(float(np.mean(se1)), se0, cfg.eps),

        "energy_z": _robust_z(float(np.mean(e1)), e0, cfg.eps),
        "spectral_ripple_z": _robust_z(float(np.mean(r1)), r0, cfg.eps),
        "phase_distortion_z": _robust_z(float(np.mean(p1)), p0, cfg.eps),
        "amplitude_distortion_z": _robust_z(float(np.mean(a1)), a0, cfg.eps),
        "phase_curvature_z": _robust_z(float(np.mean(c1)), c0, cfg.eps),
        "group_delay_z": _robust_z(float(np.mean(g1)), g0, cfg.eps),
        "stft_peak_ratio": stft_peak_ratio(d_scan, cfg.eps),
        "doppler_phase_rate_z": _robust_z(float(np.mean(np.abs(dop1))), np.abs(dop0), cfg.eps),
        "radial_velocity_proxy_m_s": float(wavelength_m(cfg.carrier_hz) * np.mean(np.abs(dop1)) * cfg.sample_rate_hz / 2.0),
        "autocorr_lag1": autocorr_lag1(kalman_smooth_1d(e1), cfg.eps),
        "cross_stream_coherence": cross_stream_coherence(d_scan, cfg.eps),

        "coherence_rank": coherence_rank(d_scan, cfg.eps),
        "spatial_covariance_score": spatial_covariance_score(d_scan, cfg.eps),
        "beamforming_concentration_proxy": beamforming_concentration_proxy(d_scan, cfg.eps),
        "music_sharpness_proxy": music_sharpness_proxy(d_scan, cfg.eps),
        "delay_profile_peakiness": delay_profile_peakiness(d_scan, cfg.eps),
        "range_resolution_m": range_resolution_m(cfg.bandwidth_hz),
        "fresnel_radius_m": fresnel_radius_m(cfg.carrier_hz, cfg.link_distance_m),
        "tomographic_projection_proxy": tomographic_projection_proxy(d_scan, cfg.eps),
        "sparse_reconstruction_proxy": sparse_reconstruction_proxy(d_scan, cfg.eps),
        "anomaly_map_proxy": anomaly_map_proxy(d_empty, d_scan, cfg.eps),

        "elongation_proxy": elong,
        "orientation_proxy_rad": theta,
        "orientation_stability": theta_stability,
        "extent_proxy": extent,
        "rigidity_proxy": rigidity_proxy(d_scan, cfg.eps),
        "persistence": persistence(d_scan, d_empty, cfg.eps),
        "spectral_entropy_delta": float(ent0 - ent1),
        "spectral_flatness_delta": float(flat0 - flat1),
        "residual_kurtosis_z": _robust_z(float(np.mean(k1)), k0, cfg.eps),
        "mahalanobis_proxy": mahalanobis_proxy(d_empty, d_scan, cfg.eps),
        "sensor_quality": q,
        "restricted_zone_prior": _clip01(cfg.restricted_zone_prior),
        "bag_transition_prior": _clip01(cfg.bag_transition_prior),
    }
    raw["conductive_score_proxy"] = conductive_score_proxy(raw)

    # Temporary posterior placeholder uses a pre-posterior score proxy.
    pre_score = _sigmoid(
        0.5 * raw["conductive_score_proxy"]
        + 0.3 * math.log1p(max(raw["elongation_proxy"], 0.0))
        + 0.3 * raw["persistence"]
        + 0.2 * raw["sensor_quality"]
        - 1.1
    )
    pn, pl, pu = softmax_posteriors(raw, pre_score)
    raw["posterior_normal"] = pn
    raw["posterior_long_conductive"] = pl
    raw["posterior_unknown"] = pu

    return CSIFeatureVector(**raw)


def feature_contributions(f: CSIFeatureVector, cfg: DetectionConfig) -> Dict[str, float]:
    d = asdict(f)
    return {
        "energy_z": cfg.w_energy_z * d["energy_z"],
        "spectral_ripple_z": cfg.w_spectral_ripple_z * d["spectral_ripple_z"],
        "phase_distortion_z": cfg.w_phase_distortion_z * d["phase_distortion_z"],
        "amplitude_distortion_z": cfg.w_amplitude_distortion_z * d["amplitude_distortion_z"],
        "phase_curvature_z": cfg.w_phase_curvature_z * d["phase_curvature_z"],
        "group_delay_z": cfg.w_group_delay_z * d["group_delay_z"],
        "amplitude_residual_mean_z": cfg.w_amplitude_residual_z * d["amplitude_residual_mean_z"],
        "phase_residual_mean_z": cfg.w_phase_residual_z * d["phase_residual_mean_z"],
        "amplitude_ratio_anomaly": cfg.w_amplitude_ratio_anomaly * d["amplitude_ratio_anomaly"],
        "phase_difference_anomaly": cfg.w_phase_difference_anomaly * d["phase_difference_anomaly"],
        "stft_peak_ratio": cfg.w_stft_peak_ratio * d["stft_peak_ratio"],
        "doppler_phase_rate_z": cfg.w_doppler_phase_rate_z * d["doppler_phase_rate_z"],
        "autocorr_lag1": cfg.w_autocorr_lag1 * max(d["autocorr_lag1"], 0.0),
        "cross_stream_coherence": cfg.w_cross_stream_coherence * d["cross_stream_coherence"],
        "coherence_rank": cfg.w_coherence_rank * d["coherence_rank"],
        "spatial_covariance_score": cfg.w_spatial_covariance_score * d["spatial_covariance_score"],
        "beamforming_concentration_proxy": cfg.w_beamforming_concentration_proxy * d["beamforming_concentration_proxy"],
        "music_sharpness_proxy": cfg.w_music_sharpness_proxy * d["music_sharpness_proxy"],
        "delay_profile_peakiness": cfg.w_delay_profile_peakiness * d["delay_profile_peakiness"],
        "elongation_proxy_log": cfg.w_elongation_proxy_log * math.log1p(max(d["elongation_proxy"], 0.0)),
        "orientation_stability": cfg.w_orientation_stability * d["orientation_stability"],
        "extent_proxy": cfg.w_extent_proxy * d["extent_proxy"],
        "rigidity_proxy": cfg.w_rigidity_proxy * d["rigidity_proxy"],
        "persistence": cfg.w_persistence * d["persistence"],
        "conductive_score_proxy": cfg.w_conductive_score_proxy * d["conductive_score_proxy"],
        "spectral_entropy_drop": cfg.w_spectral_entropy_drop * d["spectral_entropy_delta"],
        "spectral_flatness_drop": cfg.w_spectral_flatness_drop * d["spectral_flatness_delta"],
        "mahalanobis_proxy": cfg.w_mahalanobis_proxy * d["mahalanobis_proxy"],
        "sensor_quality": cfg.w_quality * d["sensor_quality"],
        "restricted_zone_prior": cfg.w_restricted_zone_prior * d["restricted_zone_prior"],
        "bag_transition_prior": cfg.w_bag_transition_prior * d["bag_transition_prior"],
        "bias": -cfg.bias,
    }


def score_features(f: CSIFeatureVector, cfg: DetectionConfig) -> float:
    logit = sum(feature_contributions(f, cfg).values())
    # E50: combine posterior, context, and sensor confidence while preserving
    # the logistic ensemble score.
    logistic_score = _sigmoid(logit)
    posterior_score = f.posterior_long_conductive * f.sensor_quality
    fused = 0.78 * logistic_score + 0.22 * posterior_score
    return float(np.clip(fused, 0.0, 1.0))


def severity_from_score(score: float, quality: float, cfg: DetectionConfig) -> str:
    if quality < cfg.quality_threshold:
        return "low_quality"
    if score >= 0.97:
        return "critical_human_review"
    if score >= 0.85:
        return "high_human_review"
    if score >= 0.65:
        return "medium_review"
    return "log_only"


SAFETY_LIMITATIONS: List[str] = [
    "Research/replay-mode anomaly scoring only; not weapon, rifle, identity, or intent detection.",
    "Do not use as the sole basis for enforcement, search, detention, or other adverse action.",
    "Requires local calibration with representative safe bags, device placement, venue layout, and RF environment.",
    "Scores can shift with multipath, wet objects, dense electronics, body motion, antenna placement, and firmware changes.",
]


def validate_config(cfg: DetectionConfig) -> None:
    checks = {
        "threshold": cfg.threshold,
        "quality_threshold": cfg.quality_threshold,
        "restricted_zone_prior": cfg.restricted_zone_prior,
        "bag_transition_prior": cfg.bag_transition_prior,
    }
    for name, value in checks.items():
        if not 0.0 <= float(value) <= 1.0:
            raise CSIInputError(f"{name} must be in [0, 1]. Got {value!r}.")
    if int(cfg.min_frames) < 2:
        raise CSIInputError(f"min_frames must be at least 2. Got {cfg.min_frames!r}.")
    if float(cfg.carrier_hz) <= 0 or float(cfg.bandwidth_hz) <= 0:
        raise CSIInputError("carrier_hz and bandwidth_hz must be positive.")
    if float(cfg.sample_rate_hz) <= 0:
        raise CSIInputError("sample_rate_hz must be positive.")
    if float(cfg.link_distance_m) <= 0:
        raise CSIInputError("link_distance_m must be positive.")


def decision_policy(score: float, quality: float, threshold: float, quality_threshold: float) -> str:
    if quality < quality_threshold:
        return "rescan_low_quality"
    if score >= threshold:
        return "human_review_anomaly"
    if score >= max(0.65, 0.75 * threshold):
        return "secondary_review_optional"
    return "log_only"


def top_contributions(contributions: Dict[str, float], k: int = 12) -> List[Dict[str, float]]:
    ranked = sorted(contributions.items(), key=lambda kv: abs(float(kv[1])), reverse=True)
    return [{"name": str(name), "value": float(value)} for name, value in ranked[:k]]


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def annotate_result(result: DetectionResult, cfg: DetectionConfig, audit: Optional[Dict[str, Any]] = None) -> DetectionResult:
    result.model["schema_version"] = "0.4"
    result.model["decision"] = decision_policy(result.score, result.features.get("sensor_quality", 0.0), cfg.threshold, cfg.quality_threshold)
    result.model["limitations"] = SAFETY_LIMITATIONS
    result.model["top_contributions"] = top_contributions(result.contributions)
    result.model["config"] = {
        "threshold": float(cfg.threshold),
        "quality_threshold": float(cfg.quality_threshold),
        "min_frames": int(cfg.min_frames),
        "carrier_hz": float(cfg.carrier_hz),
        "bandwidth_hz": float(cfg.bandwidth_hz),
        "link_distance_m": float(cfg.link_distance_m),
        "sample_rate_hz": float(cfg.sample_rate_hz),
        "restricted_zone_prior": float(cfg.restricted_zone_prior),
        "bag_transition_prior": float(cfg.bag_transition_prior),
    }
    if audit:
        result.model["audit"] = audit
    return result


def config_from_json(path: Path, base: Optional[DetectionConfig] = None) -> DetectionConfig:
    cfg = base or DetectionConfig()
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CSIInputError("Config JSON must contain an object.")
    allowed = set(DetectionConfig.__dataclass_fields__.keys())
    data = asdict(cfg)
    for key, value in payload.items():
        if key in allowed:
            data[key] = value
    out = DetectionConfig(**data)
    validate_config(out)
    return out


def write_config_json(path: Path, cfg: DetectionConfig) -> None:
    validate_config(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": VERSION,
        "claim_boundary": CLAIM_BOUNDARY,
        "config": asdict(cfg),
        "limitations": SAFETY_LIMITATIONS,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def calibration_summary(empty_path: Path, safe_scan_paths: List[Path], cfg: DetectionConfig, false_alarm_rate: float = 0.01) -> Dict[str, Any]:
    """
    Estimate a conservative threshold from safe/known-non-alert scans.
    This does not train a weapon classifier; it only sets a review threshold
    from local negative examples.
    """
    validate_config(cfg)
    if not safe_scan_paths:
        raise CSIInputError("Calibration requires at least one --safe-scan file.")
    if not 0.0 < float(false_alarm_rate) < 1.0:
        raise CSIInputError("false_alarm_rate must be between 0 and 1.")
    empty = load_csi_npz(empty_path)
    scores: List[float] = []
    qualities: List[float] = []
    for scan_path in safe_scan_paths:
        scan = load_csi_npz(scan_path)
        res = detect(empty, scan, cfg)
        scores.append(float(res.score))
        qualities.append(float(res.features.get("sensor_quality", 0.0)))
    q = 1.0 - float(false_alarm_rate)
    empirical = float(np.quantile(np.asarray(scores, dtype=np.float64), q, method="higher" if len(scores) > 1 else "linear"))
    # For very small safe sets, add a margin; with larger sets, the empirical quantile carries more weight.
    margin = 0.04 if len(scores) < 20 else 0.02
    recommended_threshold = float(np.clip(max(cfg.threshold, empirical + margin), 0.0, 0.995))
    recommended_quality = float(np.clip(max(cfg.quality_threshold, np.quantile(np.asarray(qualities), 0.10) * 0.8), 0.0, 0.95))
    return {
        "version": VERSION,
        "claim_boundary": CLAIM_BOUNDARY,
        "calibration_type": "safe_scan_threshold_estimate",
        "safe_scan_count": len(scores),
        "false_alarm_rate_target": float(false_alarm_rate),
        "score_min": float(np.min(scores)),
        "score_median": float(np.median(scores)),
        "score_max": float(np.max(scores)),
        "quality_median": float(np.median(qualities)),
        "recommended_threshold": recommended_threshold,
        "recommended_quality_threshold": recommended_quality,
        "limitations": SAFETY_LIMITATIONS,
    }


def write_calibration_json(path: Path, summary: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def detect(empty: np.ndarray, scan: np.ndarray, cfg: DetectionConfig) -> DetectionResult:
    validate_config(cfg)
    features = extract_features(empty, scan, cfg)
    score = score_features(features, cfg)

    # Final posterior update after true score.
    fdict = asdict(features)
    pn, pl, pu = softmax_posteriors(fdict, score)
    fdict["posterior_normal"] = pn
    fdict["posterior_long_conductive"] = pl
    fdict["posterior_unknown"] = pu
    features = CSIFeatureVector(**fdict)

    score = score_features(features, cfg)
    alert = bool(score >= cfg.threshold and features.sensor_quality >= cfg.quality_threshold)

    result = DetectionResult(
        event="long_conductive_object_anomaly",
        zone=cfg.zone,
        timestamp_ms=int(time.time() * 1000),
        score=score,
        threshold=cfg.threshold,
        alert=alert,
        severity=severity_from_score(score, features.sensor_quality, cfg),
        claim_boundary=CLAIM_BOUNDARY,
        features=asdict(features),
        contributions=feature_contributions(features, cfg),
        equation_coverage=EQUATION_REGISTRY,
        model={
            "name": "wifi_csi_long_conductive_object_advanced_research_head",
            "version": VERSION,
            "input": "empty/safe-bag CSI baseline vs target-bag CSI scan",
            "human_review_required": cfg.human_review_required,
            "output_boundary": "anomaly score only; not weapon confirmation",
            "implemented_equations": len(EQUATION_REGISTRY),
            "feature_groups": [
                "signal_channel",
                "preprocessing",
                "motion_doppler_temporal",
                "spatial_imaging_abstractions",
                "metalness_elongation_object_class",
                "context_governance",
            ],
        },
    )
    return annotate_result(result, cfg)


def detect_from_files(
    empty_path: Path,
    scan_path: Path,
    *,
    zone: str = "bag_scan",
    threshold: float = 0.85,
    quality_threshold: float = 0.35,
    min_frames: int = 8,
    restricted_zone_prior: float = 0.50,
    bag_transition_prior: float = 0.50,
    carrier_hz: float = 5.8e9,
    bandwidth_hz: float = 80e6,
    link_distance_m: float = 3.0,
    sample_rate_hz: float = 100.0,
) -> DetectionResult:
    cfg = DetectionConfig(
        threshold=threshold,
        quality_threshold=quality_threshold,
        zone=zone,
        min_frames=min_frames,
        restricted_zone_prior=restricted_zone_prior,
        bag_transition_prior=bag_transition_prior,
        carrier_hz=carrier_hz,
        bandwidth_hz=bandwidth_hz,
        link_distance_m=link_distance_m,
        sample_rate_hz=sample_rate_hz,
    )
    validate_config(cfg)
    empty_path = Path(empty_path)
    scan_path = Path(scan_path)
    empty = load_csi_npz(empty_path)
    scan = load_csi_npz(scan_path)
    result = detect(empty, scan, cfg)
    result.model["audit"] = {
        "empty_path": str(empty_path),
        "scan_path": str(scan_path),
        "empty_sha256": sha256_file(empty_path),
        "scan_sha256": sha256_file(scan_path),
        "empty_shape": list(empty.shape),
        "scan_shape": list(scan.shape),
    }
    return result


def write_json(path: Path, result: DetectionResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")


def write_feature_csv(path: Path, result: DetectionResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for key, value in result.features.items():
        rows.append({"kind": "feature", "name": key, "value": value})
    for key, value in result.contributions.items():
        rows.append({"kind": "contribution", "name": key, "value": value})
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["kind", "name", "value"])
        writer.writeheader()
        writer.writerows(rows)


def write_equations_markdown(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    groups: Dict[str, List[Dict[str, str]]] = {}
    for eq in EQUATION_REGISTRY:
        groups.setdefault(eq["group"], []).append(eq)

    lines = [
        "# WiFi CSI Long Conductive-Object Anomaly Equation Registry",
        "",
        f"Version: `{VERSION}`",
        "",
        f"Claim boundary: {CLAIM_BOUNDARY}",
        "",
    ]
    for group, items in groups.items():
        lines.append(f"## {group}")
        lines.append("")
        for eq in items:
            lines.append(f"### {eq['id']} — {eq['name']}")
            lines.append("")
            lines.append(f"`{eq['latex']}`")
            lines.append("")
            lines.append(f"Implemented as: `{eq['implemented_as']}`")
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_concept_report(path: Path, result: DetectionResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(result)
    lines = [
        "# CSI Concept Report",
        "",
        f"Event: `{data['event']}`",
        f"Zone: `{data['zone']}`",
        f"Score: `{data['score']:.6f}`",
        f"Alert: `{data['alert']}`",
        f"Severity: `{data['severity']}`",
        "",
        f"Claim boundary: {data['claim_boundary']}",
        "",
        "## Top Contributions",
        "",
    ]
    contrib = sorted(data["contributions"].items(), key=lambda kv: abs(float(kv[1])), reverse=True)
    for k, v in contrib[:20]:
        lines.append(f"- `{k}`: `{float(v):.6f}`")
    lines.extend(["", "## Features", ""])
    for k, v in sorted(data["features"].items()):
        lines.append(f"- `{k}`: `{float(v):.6f}`")
    lines.extend(["", "## Equation Coverage", ""])
    for eq in EQUATION_REGISTRY:
        lines.append(f"- **{eq['id']} {eq['name']}** — `{eq['implemented_as']}`")
    path.write_text("\n".join(lines), encoding="utf-8")


def generate_demo_pair(out_dir: Path, seed: int = 7) -> Tuple[Path, Path]:
    """
    Generates synthetic CSI-like data for UI/CLI smoke testing.
    This is not a physics simulator. It creates a stable baseline and a target
    scan with a persistent elongated spectral/phase perturbation.
    """
    rng = np.random.default_rng(seed)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    t, rx, tx, k = 96, 3, 2, 64
    base_amp = 1.0 + 0.03 * rng.normal(size=(t, rx, tx, k))
    base_phase = 0.05 * rng.normal(size=(t, rx, tx, k))
    empty = base_amp * np.exp(1j * base_phase)

    scan = empty.copy()
    sub = np.arange(k)
    elongated_ripple = 0.16 * np.cos(2 * np.pi * sub / 11.0)
    phase_curve = 0.12 * ((sub - sub.mean()) / sub.std()) ** 2
    persistent = (1.0 + 0.03 * rng.normal(size=(t, 1, 1, 1)))
    stream_pattern = np.zeros((1, rx, tx, k))
    stream_pattern[:, :, :, :] = elongated_ripple
    stream_pattern[:, 0:2, :, :] += 0.08
    scan_amp = np.abs(scan) + persistent * stream_pattern
    scan_phase = np.angle(scan) + persistent * phase_curve.reshape(1, 1, 1, k)
    scan = scan_amp * np.exp(1j * scan_phase)

    empty_path = out_dir / "empty_bag_csi.npz"
    scan_path = out_dir / "target_bag_csi.npz"
    np.savez_compressed(empty_path, csi=empty.astype(np.complex64))
    np.savez_compressed(scan_path, csi=scan.astype(np.complex64))
    return empty_path, scan_path



def generate_demo_safe_pair(out_dir: Path, seed: int = 17) -> Tuple[Path, Path]:
    """
    Generates a known-safe synthetic pair for smoke tests and calibration demos.
    The target scan has only small drift/noise, not a persistent elongated perturbation.
    """
    rng = np.random.default_rng(seed)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    t, rx, tx, k = 96, 3, 2, 64
    base_amp = 1.0 + 0.03 * rng.normal(size=(t, rx, tx, k))
    base_phase = 0.05 * rng.normal(size=(t, rx, tx, k))
    empty = base_amp * np.exp(1j * base_phase)

    drift_amp = 0.006 * rng.normal(size=(t, rx, tx, k))
    drift_phase = 0.006 * rng.normal(size=(t, rx, tx, k))
    scan = (np.abs(empty) + drift_amp) * np.exp(1j * (np.angle(empty) + drift_phase))

    empty_path = out_dir / "empty_bag_csi.npz"
    safe_path = out_dir / "safe_bag_csi.npz"
    np.savez_compressed(empty_path, csi=empty.astype(np.complex64))
    np.savez_compressed(safe_path, csi=scan.astype(np.complex64))
    return empty_path, safe_path


def run_self_test(out_dir: Path) -> Dict[str, Any]:
    out_dir = Path(out_dir)
    pos_empty, pos_scan = generate_demo_pair(out_dir / "positive", seed=7)
    safe_empty, safe_scan = generate_demo_safe_pair(out_dir / "safe", seed=17)

    cfg = DetectionConfig()
    positive = detect_from_files(pos_empty, pos_scan)
    safe = detect_from_files(safe_empty, safe_scan)
    passed = bool(
        positive.score > safe.score
        and positive.features.get("sensor_quality", 0.0) >= cfg.quality_threshold
        and positive.model.get("decision") in {"human_review_anomaly", "secondary_review_optional"}
        and safe.model.get("decision") in {"log_only", "secondary_review_optional", "rescan_low_quality"}
    )
    return {
        "version": VERSION,
        "passed": passed,
        "claim_boundary": CLAIM_BOUNDARY,
        "positive": {
            "score": positive.score,
            "alert": positive.alert,
            "severity": positive.severity,
            "decision": positive.model.get("decision"),
            "sensor_quality": positive.features.get("sensor_quality"),
        },
        "safe": {
            "score": safe.score,
            "alert": safe.alert,
            "severity": safe.severity,
            "decision": safe.model.get("decision"),
            "sensor_quality": safe.features.get("sensor_quality"),
        },
        "artifacts": {
            "positive_empty": str(pos_empty),
            "positive_scan": str(pos_scan),
            "safe_empty": str(safe_empty),
            "safe_scan": str(safe_scan),
        },
    }


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Advanced research detector for long conductive-object anomaly "
            "patterns inside bags using WiFi CSI. Does not confirm weapons."
        )
    )
    p.add_argument("--empty", type=Path, help="Path to empty/safe bag baseline .npz with key 'csi'.")
    p.add_argument("--scan", type=Path, help="Path to target bag scan .npz with key 'csi'.")
    p.add_argument("--zone", default="bag_scan", help="Zone or checkpoint label.")
    p.add_argument("--threshold", type=float, default=None, help="Alert threshold in [0, 1].")
    p.add_argument("--quality-threshold", type=float, default=None, help="Minimum sensor quality in [0, 1].")
    p.add_argument("--min-frames", type=int, default=None, help="Minimum frames required in each CSI file.")
    p.add_argument("--restricted-zone-prior", type=float, default=None, help="Context prior in [0,1].")
    p.add_argument("--bag-transition-prior", type=float, default=None, help="Context prior in [0,1].")
    p.add_argument("--carrier-hz", type=float, default=None, help="RF carrier frequency for wavelength/Doppler proxies.")
    p.add_argument("--bandwidth-hz", type=float, default=None, help="Bandwidth for range-resolution proxy.")
    p.add_argument("--link-distance-m", type=float, default=None, help="Link distance for Fresnel radius proxy.")
    p.add_argument("--sample-rate-hz", type=float, default=None, help="CSI frame/sample rate for Doppler proxy.")
    p.add_argument("--config-in", type=Path, default=None, help="Optional DetectionConfig JSON; CLI values override it.")
    p.add_argument("--config-out", type=Path, default=None, help="Optional path to write the resolved DetectionConfig JSON.")
    p.add_argument("--safe-scan", type=Path, action="append", default=[], help="Known-safe scan .npz for local threshold calibration. Repeatable.")
    p.add_argument("--calibration-out", type=Path, default=None, help="Optional path to write safe-scan calibration JSON.")
    p.add_argument("--false-alarm-rate", type=float, default=0.01, help="Target false-alarm rate for --safe-scan calibration.")
    p.add_argument("--json-out", type=Path, default=None, help="Optional path to write alert JSON.")
    p.add_argument("--csv-out", type=Path, default=None, help="Optional path to write features/contributions CSV.")
    p.add_argument("--equations-out", type=Path, default=None, help="Optional path to write equation registry Markdown.")
    p.add_argument("--concept-report", type=Path, default=None, help="Optional path to write full concept report Markdown.")
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON to stdout.")
    p.add_argument("--make-demo", action="store_true", help="Generate synthetic positive demo CSI files and exit.")
    p.add_argument("--make-demo-safe", action="store_true", help="Generate synthetic known-safe demo CSI files and exit.")
    p.add_argument("--self-test", action="store_true", help="Run a synthetic smoke test and exit.")
    p.add_argument("--demo-dir", type=Path, default=Path("demo_csi"), help="Directory for demo/self-test files.")
    p.add_argument("--demo-seed", type=int, default=7, help="Random seed for --make-demo.")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    try:
        cfg = config_from_json(args.config_in) if args.config_in is not None else DetectionConfig()
        override_map = {
            "threshold": args.threshold,
            "quality_threshold": args.quality_threshold,
            "min_frames": args.min_frames,
            "restricted_zone_prior": args.restricted_zone_prior,
            "bag_transition_prior": args.bag_transition_prior,
            "carrier_hz": args.carrier_hz,
            "bandwidth_hz": args.bandwidth_hz,
            "link_distance_m": args.link_distance_m,
            "sample_rate_hz": args.sample_rate_hz,
            "zone": args.zone,
        }
        cfg_data = asdict(cfg)
        for key, value in override_map.items():
            if value is not None:
                cfg_data[key] = value
        cfg = DetectionConfig(**cfg_data)
        validate_config(cfg)

        if args.equations_out is not None:
            write_equations_markdown(args.equations_out)

        if args.config_out is not None:
            write_config_json(args.config_out, cfg)

        if args.self_test:
            result = run_self_test(args.demo_dir)
            print(json.dumps(result, indent=2))
            return 0 if result.get("passed") else 3

        if args.make_demo:
            empty_path, scan_path = generate_demo_pair(args.demo_dir, seed=args.demo_seed)
            print(json.dumps({
                "created": {
                    "empty": str(empty_path),
                    "scan": str(scan_path),
                },
                "run": f"python main.py --empty {empty_path} --scan {scan_path} --pretty",
                "claim_boundary": CLAIM_BOUNDARY,
            }, indent=2))
            return 0

        if args.make_demo_safe:
            empty_path, safe_path = generate_demo_safe_pair(args.demo_dir, seed=args.demo_seed)
            print(json.dumps({
                "created": {
                    "empty": str(empty_path),
                    "safe_scan": str(safe_path),
                },
                "calibrate": f"python main.py --empty {empty_path} --safe-scan {safe_path} --calibration-out calibration.json --pretty",
                "claim_boundary": CLAIM_BOUNDARY,
            }, indent=2))
            return 0

        if args.safe_scan or args.calibration_out is not None:
            if args.empty is None:
                raise CSIInputError("Calibration requires --empty plus one or more --safe-scan files.")
            summary = calibration_summary(args.empty, list(args.safe_scan), cfg, false_alarm_rate=float(args.false_alarm_rate))
            if args.calibration_out is not None:
                write_calibration_json(args.calibration_out, summary)
            print(json.dumps(summary, indent=2 if args.pretty else None))
            if args.scan is None:
                return 0

        if args.empty is None or args.scan is None:
            if args.equations_out is not None or args.config_out is not None:
                print(json.dumps({
                    "equations_out": str(args.equations_out) if args.equations_out else None,
                    "config_out": str(args.config_out) if args.config_out else None,
                    "claim_boundary": CLAIM_BOUNDARY,
                }, indent=2))
                return 0
            raise CSIInputError("Provide --empty and --scan, use --make-demo, or run calibration with --safe-scan.")

        result = detect_from_files(
            args.empty,
            args.scan,
            zone=str(cfg.zone),
            threshold=float(cfg.threshold),
            quality_threshold=float(cfg.quality_threshold),
            min_frames=int(cfg.min_frames),
            restricted_zone_prior=float(cfg.restricted_zone_prior),
            bag_transition_prior=float(cfg.bag_transition_prior),
            carrier_hz=float(cfg.carrier_hz),
            bandwidth_hz=float(cfg.bandwidth_hz),
            link_distance_m=float(cfg.link_distance_m),
            sample_rate_hz=float(cfg.sample_rate_hz),
        )

        if args.json_out is not None:
            write_json(args.json_out, result)
        if args.csv_out is not None:
            write_feature_csv(args.csv_out, result)
        if args.concept_report is not None:
            write_concept_report(args.concept_report, result)

        print(json.dumps(asdict(result), indent=2 if args.pretty else None))
        return 0

    except CSIInputError as exc:
        print(json.dumps({"error": str(exc), "claim_boundary": CLAIM_BOUNDARY}, indent=2), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print(json.dumps({"error": "interrupted"}, indent=2), file=sys.stderr)
        return 130
    except Exception as exc:
        print(json.dumps({"error": f"unexpected failure: {exc}", "claim_boundary": CLAIM_BOUNDARY}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())