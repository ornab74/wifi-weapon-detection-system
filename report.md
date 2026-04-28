# CSI Concept Report

Event: `long_conductive_object_anomaly`
Zone: `bag_scan`
Score: `0.959107`
Alert: `True`
Severity: `high_human_review`

Claim boundary: Possible long conductive-object anomaly in bag; not weapon confirmation and not intent detection.

## Top Contributions

- `spectral_ripple_z`: `10.800000`
- `energy_z`: `10.400000`
- `amplitude_residual_mean_z`: `5.600000`
- `phase_distortion_z`: `5.200000`
- `amplitude_distortion_z`: `4.800000`
- `bias`: `-4.400000`
- `amplitude_ratio_anomaly`: `1.864329`
- `elongation_proxy_log`: `1.661547`
- `mahalanobis_proxy`: `1.300000`
- `persistence`: `0.360000`
- `cross_stream_coherence`: `0.332180`
- `conductive_score_proxy`: `0.317528`
- `rigidity_proxy`: `0.284983`
- `sensor_quality`: `0.235451`
- `orientation_stability`: `0.179843`
- `extent_proxy`: `0.157539`
- `restricted_zone_prior`: `0.130000`
- `group_delay_z`: `0.122713`
- `bag_transition_prior`: `0.100000`
- `autocorr_lag1`: `0.084807`

## Features

- `amplitude_distortion_z`: `20.000000`
- `amplitude_ratio_anomaly`: `7.170495`
- `amplitude_residual_mean_z`: `20.000000`
- `anomaly_map_proxy`: `0.008037`
- `autocorr_lag1`: `0.706721`
- `bag_transition_prior`: `0.500000`
- `baseline_norm_delta`: `0.185488`
- `beamforming_concentration_proxy`: `0.137811`
- `coherence_rank`: `0.183366`
- `conductive_score_proxy`: `0.992274`
- `cross_stream_coherence`: `0.977000`
- `delay_profile_peakiness`: `0.384800`
- `doppler_phase_rate_z`: `0.000000`
- `elongation_proxy`: `253.294029`
- `energy_z`: `20.000000`
- `extent_proxy`: `0.984618`
- `fresnel_radius_m`: `0.196892`
- `group_delay_z`: `0.557788`
- `mahalanobis_proxy`: `5.000000`
- `music_sharpness_proxy`: `0.147682`
- `orientation_proxy_rad`: `-0.003173`
- `orientation_stability`: `0.999130`
- `persistence`: `1.000000`
- `phase_curvature_z`: `0.131893`
- `phase_difference_anomaly`: `0.251525`
- `phase_distortion_z`: `20.000000`
- `phase_residual_mean_z`: `-0.000000`
- `posterior_long_conductive`: `0.829855`
- `posterior_normal`: `0.006755`
- `posterior_unknown`: `0.163389`
- `radial_velocity_proxy_m_s`: `0.000000`
- `range_resolution_m`: `1.873703`
- `reflection_score_proxy`: `0.999641`
- `residual_kurtosis_z`: `-2.926431`
- `restricted_zone_prior`: `0.500000`
- `rigidity_proxy`: `0.949942`
- `sensor_quality`: `0.981044`
- `skin_depth_proxy_m`: `0.000002`
- `smoothed_energy_z`: `20.000000`
- `sparse_reconstruction_proxy`: `1.000000`
- `spatial_covariance_score`: `0.325508`
- `spectral_entropy_delta`: `0.305321`
- `spectral_flatness_delta`: `0.292783`
- `spectral_ripple_z`: `20.000000`
- `stft_peak_ratio`: `0.335548`
- `tomographic_projection_proxy`: `0.806572`
- `wavelength_m`: `0.051688`

## Equation Coverage

- **E01 Received OFDM subcarrier model** — `input CSI model`
- **E02 Multipath CSI response** — `residual/multipath interpretation`
- **E03 CSI amplitude** — `amplitude_distortion, amplitude_ratio`
- **E04 CSI phase** — `phase_sanitize, phase_distortion`
- **E05 Wavelength** — `wavelength_m`
- **E06 Path phase shift** — `phase residual features`
- **E07 Propagation delay** — `delay profile interpretation`
- **E08 Complex permittivity** — `conductive prior metadata`
- **E09 Skin depth** — `skin_depth_proxy`
- **E10 Reflection coefficient** — `reflection_score_proxy`
- **E11 Baseline-normalized CSI** — `baseline_normalized_csi`
- **E12 CSI perturbation** — `baseline_residual`
- **E13 Amplitude residual** — `amplitude_residual_mean_z`
- **E14 Phase residual** — `phase_residual_mean_z`
- **E15 Antenna amplitude ratio** — `amplitude_ratio_anomaly`
- **E16 Antenna phase difference** — `phase_difference_anomaly`
- **E17 Phase sanitization** — `phase_sanitize`
- **E18 MAD filter** — `robust_z`
- **E19 Smoothed CSI** — `moving_average_csi`
- **E20 Kalman update** — `kalman_smooth_1d`
- **E21 STFT** — `stft_peak_ratio`
- **E22 Doppler estimate** — `doppler_phase_rate_z`
- **E23 Radial velocity estimate** — `radial_velocity_proxy`
- **E24 Temporal energy** — `energy_z`
- **E25 Motion-normalized residual** — `motion_normalized_residual`
- **E26 Static-object persistence** — `persistence`
- **E27 Static/dynamic separation** — `baseline_residual`
- **E28 Background-subtracted dynamic component** — `dynamic_component`
- **E29 Temporal autocorrelation** — `autocorr_lag1`
- **E30 Cross-link coherence** — `cross_stream_coherence`
- **E31 MIMO CSI matrix** — `shape-aware CSI features`
- **E32 Spatial covariance** — `spatial_covariance_score`
- **E33 Beamforming response** — `beamforming_concentration_proxy`
- **E34 MUSIC spectrum** — `music_sharpness_proxy`
- **E35 Delay profile** — `delay_profile_peakiness`
- **E36 Range resolution limit** — `range_resolution_m`
- **E37 Fresnel-zone radius** — `fresnel_radius_m`
- **E38 Tomographic projection** — `tomographic_projection_proxy`
- **E39 Regularized reconstruction** — `sparse_reconstruction_proxy`
- **E40 Spatial anomaly map** — `anomaly_map_proxy`
- **E41 Metalness vector** — `conductive_score_proxy`
- **E42 Inter-subcarrier variance** — `spectral_ripple_z`
- **E43 Phase curvature** — `phase_curvature_z`
- **E44 Conductive reflection score** — `conductive_score_proxy`
- **E45 Elongation from blob eigenvalues** — `elongation_proxy`
- **E46 Object orientation estimate** — `orientation_proxy_rad`
- **E47 Approximate object extent** — `extent_proxy`
- **E48 Bag/clutter compensation residual** — `bag residual`
- **E49 Class posterior** — `softmax_posteriors`
- **E50 Human-review alert score** — `score_features`