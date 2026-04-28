Yes—as a **hypothetical advanced sensing model**, you could train on RF/CSI signatures of **elongated conductive objects** and classify “possible long metal object in bag/area.” But I would **not** claim it can detect *rifling* or uniquely identify “a rifle” from ordinary WiFi CSI. Rifling is internal, small-scale geometry; ordinary WiFi wavelengths and bandwidth mostly see coarse scattering, material contrast, orientation, motion, and multipath—not fine barrel-groove structure.

The closest realistic target is:

> **“Possible elongated conductive object inconsistent with the zone context.”**

The WiFi-DensePose project you shared is pose/CSI oriented, not weapon-object recognition; it describes CSI collection, phase sanitization, DensePose-like pose inference, tracking, activity/fall analytics, and real-time APIs.  Research has shown proof-of-concept WiFi/CSI detection of concealed metallic objects, but in controlled experiments: one commodity-WiFi prototype used CSI and a CNN to distinguish metal vs. non-metal with 86.44% average accuracy using subjects carrying a metal sheet, and the authors explicitly noted more validation was needed before deployment. ([Asif Hanif][1]) WiFi material-identification work also supports the idea that amplitude ratios and phase differences can carry material information, but it is strongly affected by CSI noise, position, shape, and multipath. ([Tech Science][2])

Core CSI model:

H(f,t)=\sum_{p=1}^{P} a_p(t)e^{-j2\pi f\tau_p(t)}

Here are **50 equations** for shaping a hypothetical WiFi-CSI long-metal-object detector.

### Signal and channel model

1. Received OFDM subcarrier model
   [
   y_k(t)=H_k(t)x_k(t)+n_k(t)
   ]

2. Multipath CSI response
   [
   H_k(t)=\sum_{p=1}^{P} a_p(t)e^{-j2\pi f_k\tau_p(t)}
   ]

3. CSI amplitude
   [
   A_k(t)=|H_k(t)|
   ]

4. CSI phase
   [
   \phi_k(t)=\arg(H_k(t))
   ]

5. Wavelength
   [
   \lambda=\frac{c}{f}
   ]

6. Path phase shift
   [
   \Delta \phi_k=-2\pi f_k\Delta\tau
   ]

7. Propagation delay
   [
   \tau_p=\frac{d_p}{c}
   ]

8. Complex permittivity
   [
   \epsilon^*=\epsilon'-j\epsilon''
   ]

9. Skin depth for conductive material
   [
   \delta=\sqrt{\frac{2}{\omega\mu\sigma}}
   ]

10. Reflection coefficient approximation
    [
    \Gamma=\frac{Z_2-Z_1}{Z_2+Z_1}
    ]

### CSI preprocessing

11. Baseline-normalized CSI
    [
    \tilde{H}*k(t)=\frac{H_k(t)}{H*{k,0}}
    ]

12. CSI perturbation
    [
    \Delta H_k(t)=H_k(t)-H_{k,0}
    ]

13. Amplitude residual
    [
    \Delta A_k(t)=|H_k(t)|-|H_{k,0}|
    ]

14. Phase residual
    [
    \Delta \phi_k(t)=\operatorname{unwrap}(\phi_k(t))-\operatorname{unwrap}(\phi_{k,0})
    ]

15. Antenna amplitude ratio
    [
    R^{A}*{i,j,k}(t)=\frac{|H*{i,k}(t)|}{|H_{j,k}(t)|+\epsilon}
    ]

16. Antenna phase difference
    [
    R^{\phi}*{i,j,k}(t)=\angle H*{i,k}(t)-\angle H_{j,k}(t)
    ]

17. Phase sanitization by linear trend removal
    [
    \phi'_k(t)=\phi_k(t)-(\alpha f_k+\beta)
    ]

18. Median absolute deviation filter
    [
    z_k(t)=\frac{A_k(t)-\operatorname{median}(A_k)}{\operatorname{MAD}(A_k)}
    ]

19. Smoothed CSI
    [
    \bar{H}*k(t)=\frac{1}{W}\sum*{u=t-W+1}^{t}H_k(u)
    ]

20. Kalman update for denoised feature
    [
    \hat{x}*{t|t}=\hat{x}*{t|t-1}+K_t(z_t-\hat{x}_{t|t-1})
    ]

### Motion, Doppler, and temporal structure

21. Short-time Fourier transform
    [
    S_k(t,\omega)=\sum_{\tau}H_k(\tau)w(\tau-t)e^{-j\omega\tau}
    ]

22. Doppler estimate
    [
    f_D=\frac{1}{2\pi}\frac{d\phi(t)}{dt}
    ]

23. Radial velocity estimate
    [
    v_r=\frac{\lambda f_D}{2}
    ]

24. Temporal energy
    [
    E(t)=\sum_k|\Delta H_k(t)|^2
    ]

25. Motion-normalized residual
    [
    M_k(t)=\frac{\Delta H_k(t)}{\sqrt{\sum_u|\Delta H_k(u)|^2+\epsilon}}
    ]

26. Static-object persistence score
    [
    P_s=\frac{1}{T}\sum_{t=1}^{T}\mathbb{1}\left(|\Delta H(t)|>\eta\right)
    ]

27. Motion-object separation
    [
    H_k(t)=H^{static}_k+H^{dynamic}_k(t)+n_k(t)
    ]

28. Background-subtracted dynamic component
    [
    H^{dynamic}*k(t)=H_k(t)-\frac{1}{T_0}\sum*{u=1}^{T_0}H_k(u)
    ]

29. Temporal autocorrelation
    [
    \rho(\ell)=\frac{\sum_t x(t)x(t-\ell)}{\sum_t x(t)^2}
    ]

30. Cross-link coherence
    [
    C_{m,n}=\frac{|\sum_t \Delta H_m(t)\Delta H_n^*(t)|}{\sqrt{\sum_t|\Delta H_m(t)|^2\sum_t|\Delta H_n(t)|^2}}
    ]

### Spatial sensing and imaging abstractions

31. MIMO CSI matrix
    [
    \mathbf{H}_k(t)\in \mathbb{C}^{N_r\times N_t}
    ]

32. Spatial covariance
    [
    \mathbf{R}_k=\mathbb{E}[\mathbf{h}_k\mathbf{h}_k^{H}]
    ]

33. Beamforming response
    [
    B(\theta)=\mathbf{a}^{H}(\theta)\mathbf{R}\mathbf{a}(\theta)
    ]

34. MUSIC spectrum
    [
    P_{\text{MUSIC}}(\theta)=\frac{1}{\mathbf{a}^{H}(\theta)\mathbf{E}_n\mathbf{E}_n^{H}\mathbf{a}(\theta)}
    ]

35. Delay profile
    [
    P(\tau)=\left|\sum_k H_k e^{j2\pi f_k\tau}\right|^2
    ]

36. Range-resolution limit
    [
    \Delta r=\frac{c}{2B}
    ]

37. Fresnel-zone radius
    [
    r_F=\sqrt{\frac{\lambda d_1d_2}{d_1+d_2}}
    ]

38. Tomographic projection model
    [
    \mathbf{y}=\mathbf{A}\mathbf{x}+\mathbf{n}
    ]

39. Regularized scene reconstruction
    [
    \hat{\mathbf{x}}=\arg\min_{\mathbf{x}}|\mathbf{y}-\mathbf{A}\mathbf{x}|_2^2+\lambda|\mathbf{x}|_1
    ]

40. Spatial anomaly map
    [
    \mathcal{A}(x,y)=|\hat{x}(x,y)-\hat{x}_0(x,y)|
    ]

### Metalness, elongation, and object-class features

41. Metalness feature vector
    [
    \mathbf{m}=[\Delta A,\Delta\phi,\sigma_A^2,\sigma_\phi^2,C_{m,n},P_s]
    ]

42. Inter-subcarrier variance
    [
    \sigma^2(t)=\frac{1}{K-1}\sum_{k=1}^{K}\left(A_k(t)-\bar{A}(t)\right)^2
    ]

43. Phase-curvature feature
    [
    \kappa_\phi=\frac{\partial^2 \phi(f)}{\partial f^2}
    ]

44. Conductive-reflection score
    [
    S_c=w_1|\Gamma|+w_2\sigma_A^2+w_3\sigma_\phi^2
    ]

45. Elongation from reconstructed blob eigenvalues
    [
    E_{\text{long}}=\frac{\lambda_{\max}(\Sigma_{\text{blob}})}{\lambda_{\min}(\Sigma_{\text{blob}})+\epsilon}
    ]

46. Orientation estimate
    [
    \theta_{\text{obj}}=\frac{1}{2}\tan^{-1}\left(\frac{2\Sigma_{xy}}{\Sigma_{xx}-\Sigma_{yy}}\right)
    ]

47. Approximate object extent
    [
    L_{\text{est}}=\max_{i,j}|p_i-p_j|_2
    ]

48. Bag/clutter compensation residual
    [
    \Delta H^{obj}=H^{bag+obj}-H^{bag}
    ]

49. Class posterior
    [
    P(c|\mathbf{z})=\frac{e^{g_c(\mathbf{z})}}{\sum_{c'}e^{g_{c'}(\mathbf{z})}}
    ]

50. Alert score with human-review constraint
    [
    S_{\text{alert}}=P(c=\text{elongated conductive object}|\mathbf{z})\cdot P(\text{restricted zone})\cdot C_{\text{sensor}}
    ]

The important design correction is: **do not train the model to say “rifle.”** Train it to say **“elongated conductive-object anomaly,”** then require corroboration. That avoids overclaiming from CSI and reduces false positives from umbrellas, tripods, instruments, laptops, tools, crutches, metal water bottles, or maintenance equipment.

For the “rifling of the barrel” part specifically: ordinary WiFi CSI would almost certainly not resolve it. A better hypothetical sensor for that level of detail would move toward **wideband radar, millimeter-wave imaging, SAR-like reconstruction, or multi-modal screening**, not commodity WiFi alone. WiFi can contribute a useful low-cost anomaly layer, but it should not be the only basis for a threat decision.

[1]: https://asif-hanif.github.io/_pages/GLOBCOMM2018.pdf "Non-Obtrusive Detection of Concealed Metallic Objects Using Commodity WiFi Radios"
[2]: https://www.techscience.com/cmc/v69n3/44188/html "A Material Identification Approach Based on Wi-Fi Signal"




# WiFi CSI Long Conductive-Object Anomaly Equation Registry

Version: `0.3.0`

Claim boundary: Possible long conductive-object anomaly in bag; not weapon confirmation and not intent detection.

## Signal and channel model

### E01 — Received OFDM subcarrier model

`y_k(t)=H_k(t)x_k(t)+n_k(t)`

Implemented as: `input CSI model`

### E02 — Multipath CSI response

`H_k(t)=\sum_{p=1}^{P} a_p(t)e^{-j2\pi f_k\tau_p(t)}`

Implemented as: `residual/multipath interpretation`

### E03 — CSI amplitude

`A_k(t)=|H_k(t)|`

Implemented as: `amplitude_distortion, amplitude_ratio`

### E04 — CSI phase

`\phi_k(t)=\arg(H_k(t))`

Implemented as: `phase_sanitize, phase_distortion`

### E05 — Wavelength

`\lambda=\frac{c}{f}`

Implemented as: `wavelength_m`

### E06 — Path phase shift

`\Delta \phi_k=-2\pi f_k\Delta\tau`

Implemented as: `phase residual features`

### E07 — Propagation delay

`\tau_p=\frac{d_p}{c}`

Implemented as: `delay profile interpretation`

### E08 — Complex permittivity

`\epsilon^*=\epsilon'-j\epsilon''`

Implemented as: `conductive prior metadata`

### E09 — Skin depth

`\delta=\sqrt{\frac{2}{\omega\mu\sigma}}`

Implemented as: `skin_depth_proxy`

### E10 — Reflection coefficient

`\Gamma=\frac{Z_2-Z_1}{Z_2+Z_1}`

Implemented as: `reflection_score_proxy`

## CSI preprocessing

### E11 — Baseline-normalized CSI

`\tilde{H}_k(t)=\frac{H_k(t)}{H_{k,0}}`

Implemented as: `baseline_normalized_csi`

### E12 — CSI perturbation

`\Delta H_k(t)=H_k(t)-H_{k,0}`

Implemented as: `baseline_residual`

### E13 — Amplitude residual

`\Delta A_k(t)=|H_k(t)|-|H_{k,0}|`

Implemented as: `amplitude_residual_mean_z`

### E14 — Phase residual

`\Delta \phi_k(t)=\operatorname{unwrap}(\phi_k(t))-\operatorname{unwrap}(\phi_{k,0})`

Implemented as: `phase_residual_mean_z`

### E15 — Antenna amplitude ratio

`R^A_{i,j,k}(t)=\frac{|H_{i,k}(t)|}{|H_{j,k}(t)|+\epsilon}`

Implemented as: `amplitude_ratio_anomaly`

### E16 — Antenna phase difference

`R^\phi_{i,j,k}(t)=\angle H_{i,k}(t)-\angle H_{j,k}(t)`

Implemented as: `phase_difference_anomaly`

### E17 — Phase sanitization

`\phi'_k(t)=\phi_k(t)-(\alpha f_k+\beta)`

Implemented as: `phase_sanitize`

### E18 — MAD filter

`z_k(t)=\frac{A_k(t)-\operatorname{median}(A_k)}{\operatorname{MAD}(A_k)}`

Implemented as: `robust_z`

### E19 — Smoothed CSI

`\bar{H}_k(t)=\frac{1}{W}\sum_{u=t-W+1}^{t}H_k(u)`

Implemented as: `moving_average_csi`

### E20 — Kalman update

`\hat{x}_{t|t}=\hat{x}_{t|t-1}+K_t(z_t-\hat{x}_{t|t-1})`

Implemented as: `kalman_smooth_1d`

## Motion, Doppler, and temporal structure

### E21 — STFT

`S_k(t,\omega)=\sum_{\tau}H_k(\tau)w(\tau-t)e^{-j\omega\tau}`

Implemented as: `stft_peak_ratio`

### E22 — Doppler estimate

`f_D=\frac{1}{2\pi}\frac{d\phi(t)}{dt}`

Implemented as: `doppler_phase_rate_z`

### E23 — Radial velocity estimate

`v_r=\frac{\lambda f_D}{2}`

Implemented as: `radial_velocity_proxy`

### E24 — Temporal energy

`E(t)=\sum_k|\Delta H_k(t)|^2`

Implemented as: `energy_z`

### E25 — Motion-normalized residual

`M_k(t)=\frac{\Delta H_k(t)}{\sqrt{\sum_u|\Delta H_k(u)|^2+\epsilon}}`

Implemented as: `motion_normalized_residual`

### E26 — Static-object persistence

`P_s=\frac{1}{T}\sum_{t=1}^{T}\mathbb{1}(|\Delta H(t)|>\eta)`

Implemented as: `persistence`

### E27 — Static/dynamic separation

`H_k(t)=H^{static}_k+H^{dynamic}_k(t)+n_k(t)`

Implemented as: `baseline_residual`

### E28 — Background-subtracted dynamic component

`H^{dynamic}_k(t)=H_k(t)-\frac{1}{T_0}\sum_{u=1}^{T_0}H_k(u)`

Implemented as: `dynamic_component`

### E29 — Temporal autocorrelation

`\rho(\ell)=\frac{\sum_t x(t)x(t-\ell)}{\sum_t x(t)^2}`

Implemented as: `autocorr_lag1`

### E30 — Cross-link coherence

`C_{m,n}=\frac{|\sum_t \Delta H_m(t)\Delta H_n^*(t)|}{\sqrt{\sum_t|\Delta H_m(t)|^2\sum_t|\Delta H_n(t)|^2}}`

Implemented as: `cross_stream_coherence`

## Spatial sensing and imaging abstractions

### E31 — MIMO CSI matrix

`\mathbf{H}_k(t)\in \mathbb{C}^{N_r\times N_t}`

Implemented as: `shape-aware CSI features`

### E32 — Spatial covariance

`\mathbf{R}_k=\mathbb{E}[\mathbf{h}_k\mathbf{h}_k^{H}]`

Implemented as: `spatial_covariance_score`

### E33 — Beamforming response

`B(\theta)=\mathbf{a}^{H}(\theta)\mathbf{R}\mathbf{a}(\theta)`

Implemented as: `beamforming_concentration_proxy`

### E34 — MUSIC spectrum

`P_{\text{MUSIC}}(\theta)=\frac{1}{\mathbf{a}^{H}(\theta)\mathbf{E}_n\mathbf{E}_n^{H}\mathbf{a}(\theta)}`

Implemented as: `music_sharpness_proxy`

### E35 — Delay profile

`P(\tau)=\left|\sum_k H_k e^{j2\pi f_k\tau}\right|^2`

Implemented as: `delay_profile_peakiness`

### E36 — Range resolution limit

`\Delta r=\frac{c}{2B}`

Implemented as: `range_resolution_m`

### E37 — Fresnel-zone radius

`r_F=\sqrt{\frac{\lambda d_1d_2}{d_1+d_2}}`

Implemented as: `fresnel_radius_m`

### E38 — Tomographic projection

`\mathbf{y}=\mathbf{A}\mathbf{x}+\mathbf{n}`

Implemented as: `tomographic_projection_proxy`

### E39 — Regularized reconstruction

`\hat{\mathbf{x}}=\arg\min_{\mathbf{x}}\|\mathbf{y}-\mathbf{A}\mathbf{x}\|_2^2+\lambda\|\mathbf{x}\|_1`

Implemented as: `sparse_reconstruction_proxy`

### E40 — Spatial anomaly map

`\mathcal{A}(x,y)=|\hat{x}(x,y)-\hat{x}_0(x,y)|`

Implemented as: `anomaly_map_proxy`

## Metalness, elongation, and object-class features

### E41 — Metalness vector

`\mathbf{m}=[\Delta A,\Delta\phi,\sigma_A^2,\sigma_\phi^2,C_{m,n},P_s]`

Implemented as: `conductive_score_proxy`

### E42 — Inter-subcarrier variance

`\sigma^2(t)=\frac{1}{K-1}\sum_{k=1}^{K}(A_k(t)-\bar{A}(t))^2`

Implemented as: `spectral_ripple_z`

### E43 — Phase curvature

`\kappa_\phi=\frac{\partial^2 \phi(f)}{\partial f^2}`

Implemented as: `phase_curvature_z`

### E44 — Conductive reflection score

`S_c=w_1|\Gamma|+w_2\sigma_A^2+w_3\sigma_\phi^2`

Implemented as: `conductive_score_proxy`

### E45 — Elongation from blob eigenvalues

`E_{\text{long}}=\frac{\lambda_{\max}(\Sigma_{\text{blob}})}{\lambda_{\min}(\Sigma_{\text{blob}})+\epsilon}`

Implemented as: `elongation_proxy`

### E46 — Object orientation estimate

`\theta_{\text{obj}}=\frac{1}{2}\tan^{-1}\left(\frac{2\Sigma_{xy}}{\Sigma_{xx}-\Sigma_{yy}}\right)`

Implemented as: `orientation_proxy_rad`

### E47 — Approximate object extent

`L_{\text{est}}=\max_{i,j}\|p_i-p_j\|_2`

Implemented as: `extent_proxy`

### E48 — Bag/clutter compensation residual

`\Delta H^{obj}=H^{bag+obj}-H^{bag}`

Implemented as: `bag residual`

### E49 — Class posterior

`P(c|\mathbf{z})=\frac{e^{g_c(\mathbf{z})}}{\sum_{c'}e^{g_{c'}(\mathbf{z})}}`

Implemented as: `softmax_posteriors`

### E50 — Human-review alert score

`S_{\text{alert}}=P(c=\text{elongated conductive object}|\mathbf{z})P(\text{restricted zone})C_{\text{sensor}}`

Implemented as: `score_features`


# CSI Concept Report

Event: `barrel_like_long_conductive_object_anomaly`
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
- `phase_difference_anomaly`: `0.251527`
- `phase_distortion_z`: `20.000000`
- `phase_residual_mean_z`: `0.000000`
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
