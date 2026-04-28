# WiFi CSI Long Conductive-Object Anomaly Detection System

**Version:** 0.4 advanced research README  
**Primary implementation:** `main_v0_4_advanced.py`  
**Interface helpers:** `csi_anomaly_gui (1).py`, `result.json`, `features.csv`, `report.md`, `calibration.json`  
**Core claim boundary:** this project estimates whether a WiFi Channel State Information scan is consistent with a **long conductive-object anomaly** relative to a local baseline. It does **not** confirm weapons, identity, intent, dangerousness, or criminal activity.

---

## Table of Contents

1. [Purpose](#purpose)
2. [Why WiFi CSI Can Be Useful](#why-wifi-csi-can-be-useful)
3. [Plain-Language Summary](#plain-language-summary)
4. [Safety, Civil Rights, and Claim Boundaries](#safety-civil-rights-and-claim-boundaries)
5. [How This Can Help Protect Schools](#how-this-can-help-protect-schools)
6. [How This Can Help Protect Concerts, Stadiums, and Large Gatherings](#how-this-can-help-protect-concerts-stadiums-and-large-gatherings)
7. [How This Can Support Protective Operations for High-Profile Guests](#how-this-can-support-protective-operations-for-high-profile-guests)
8. [System Architecture](#system-architecture)
9. [Input Data Model](#input-data-model)
10. [Mathematical Foundations](#mathematical-foundations)
11. [Feature Groups](#feature-groups)
12. [Scoring Model](#scoring-model)
13. [Calibration Philosophy](#calibration-philosophy)
14. [Installation](#installation)
15. [Quick Start](#quick-start)
16. [Command-Line Usage](#command-line-usage)
17. [Outputs and Reports](#outputs-and-reports)
18. [Operational Modes](#operational-modes)
19. [Deployment Design for Schools](#deployment-design-for-schools)
20. [Deployment Design for Large Venues](#deployment-design-for-large-venues)
21. [Human Review Workflow](#human-review-workflow)
22. [False Positives, False Negatives, and Limitations](#false-positives-false-negatives-and-limitations)
23. [Privacy and Governance](#privacy-and-governance)
24. [Testing Strategy](#testing-strategy)
25. [Roadmap](#roadmap)
26. [Ethical Use Statement](#ethical-use-statement)
27. [License](#license)

---

## Purpose

This repository explores a research-oriented WiFi CSI anomaly head for detecting patterns consistent with a long, rigid, conductive object inside or near a bag, checkpoint lane, entry area, controlled corridor, or other bounded sensing zone. The goal is not to build a magical weapon detector. The goal is to create an additional safety signal that can be combined with trained staff, clear policy, respectful screening, visible deterrence, emergency planning, camera review, access control, and established legal safeguards.

The system compares two measurements:

1. an **empty or known-safe baseline** CSI sample, and
2. a **target scan** CSI sample.

It extracts a feature vector from the difference between those two measurements. The features are then combined into a bounded score. A high score means the scan differs from the baseline in a way that resembles a persistent, rigid, conductive, elongated perturbation. The output is intentionally phrased as an **anomaly**, not a weapon label.

This distinction matters. WiFi CSI does not see an object the way a camera sees an object. It measures changes in a radio channel. A metallic umbrella, tripod, instrument case, laptop cluster, camera rig, tool, crutch, or maintenance object can also perturb a channel. A responsible implementation must therefore treat the model as a **decision-support layer** rather than a stand-alone enforcement authority.

---

## Why WiFi CSI Can Be Useful

WiFi devices transmit signals through physical environments. Walls, bodies, bags, furniture, metal objects, and motion can alter the multipath structure of those signals. Channel State Information, or CSI, describes how each OFDM subcarrier is changed by the channel between transmitter and receiver. CSI includes amplitude and phase, both of which can shift when a conductive object changes the scattering geometry inside the sensing zone.

The basic subcarrier model is:

$$
y_k(t)=H_k(t)x_k(t)+n_k(t)
$$

where `x_k(t)` is the transmitted symbol on subcarrier `k`, `H_k(t)` is the channel response, `n_k(t)` is noise, and `y_k(t)` is the received symbol. The channel itself is often represented as a sum of multipath components:

$$
H_k(t)=\sum_{p=1}^{P}a_p(t)e^{-j2\pi f_k\tau_p(t)}
$$

Each path has an amplitude `a_p(t)`, a delay `tau_p(t)`, and a frequency-dependent phase. When a person carries or places a conductive object in a sensing region, the path mixture can shift. This repository turns those shifts into engineered features such as amplitude residuals, phase residuals, spectral ripple, cross-stream coherence, persistence, elongation proxies, and sensor-quality estimates.

WiFi CSI is attractive because it can be inexpensive, passive from the user perspective, and deployable with commodity or near-commodity hardware. It may work in lighting conditions where cameras are less informative, and it may add a layer of environmental awareness without storing face imagery. But it is also noisy, environment-specific, and strongly affected by geometry. Its correct role is **layered risk reduction**, not absolute detection.

---

## Plain-Language Summary

Imagine an entry table or controlled bag-check lane at a school, arena, theater, city hall, conference, or outdoor checkpoint. A local WiFi transmitter and receiver create a radio link through a defined zone. When the zone is empty or contains a known-safe reference condition, the system records a baseline. Later, when a bag or object passes through the zone, the system records a target scan. The detector compares the two.

It asks questions such as:

- Did the amplitude pattern change sharply across subcarriers?
- Did phase behavior change in a way that suggests a new reflective object?
- Is the disturbance persistent rather than a momentary motion artifact?
- Is it coherent across multiple antennas or links?
- Does the reconstructed disturbance look elongated rather than diffuse?
- Is the sensor quality high enough to trust the score?
- Is this a context where a review is appropriate?

The final result is a score between 0 and 1, a severity label, a feature dictionary, a contribution table, and a machine-readable report. The system can write JSON, CSV, Markdown reports, and an equation registry. It is designed to provide explainable evidence for human review.

---

## Safety, Civil Rights, and Claim Boundaries

This project must be used with strict boundaries.

The detector **does not identify a weapon**. It identifies a channel anomaly that may be consistent with a long conductive object. It cannot determine intent. It cannot decide that a person is dangerous. It cannot replace trained personnel. It cannot justify force, discipline, exclusion, arrest, or public accusation on its own.

A safe deployment uses the output to trigger proportionate, respectful, human-led review. For example, the model might recommend that staff route a bag to secondary inspection under a clearly posted policy. The system should never be configured to automatically lock doors on a person, trigger panic messaging, target a person based on protected characteristics, or broadcast accusations.

Recommended guardrails:

- Use visible signage and policy disclosure where required.
- Use the same process for everyone in a screening lane.
- Store the minimum data necessary.
- Avoid identity linkage unless required by a lawful and approved security workflow.
- Treat all alerts as uncertain until reviewed.
- Track false positives and false negatives.
- Use local calibration data before deployment.
- Document who can access results.
- Require human review for any operational response.
- Do not use the system for covert monitoring of lawful assembly, protest, worship, or ordinary movement.

A responsible deployment explicitly separates **sensor evidence** from **security judgment**. The model can say: “the RF channel changed in a way that resembles an elongated conductive-object anomaly.” It should not say: “this person has a weapon.”

---

## How This Can Help Protect Schools

Schools need security approaches that are effective, proportional, non-traumatizing, and compatible with a learning environment. A WiFi CSI anomaly layer could support school safety when used as part of a broader plan that includes mental health resources, access control, visitor management, staff training, emergency communication, anonymous reporting channels, and age-appropriate safety procedures.

Potential school use cases include:

### 1. Visitor and delivery screening

A controlled entry point can include a defined sensing lane for visitor bags, delivery containers, instrument cases, maintenance kits, or large carried objects. The system can compare scans against local baselines and flag unusual long conductive-object patterns for staff review. This can add a quiet layer of screening without making every entry experience feel like an airport checkpoint.

### 2. After-hours access monitoring

Schools often have after-hours events: sports, theater, board meetings, tutoring, club activities, and community programs. A low-cost CSI checkpoint can help staff detect unexpected anomalies at a limited entry door while still maintaining a welcoming environment.

### 3. Event-specific risk reduction

Graduations, assemblies, rivalry games, award ceremonies, and large parent events concentrate people in predictable places. CSI sensing can be temporarily placed near bag-check tables, staff entrances, or equipment intake zones. In this role it functions like an additional instrument, not a command system.

### 4. Reducing overreliance on subjective visual judgment

Human staff are imperfect. Visual screening can be inconsistent, biased, distracted, or overwhelmed. A calibrated sensor can help standardize which bags receive a second look, provided the review process is applied equally and respectfully.

### 5. Maintaining privacy compared with image-heavy systems

CSI does not need to store facial images to estimate RF anomalies. That does not automatically make it privacy-safe, but it can reduce certain types of image surveillance. Schools should still publish retention rules, access rules, and appeal procedures.

A school deployment should use conservative thresholds, frequent calibration, clear signage, and human-centered procedures. The desired outcome is not dramatic enforcement. The desired outcome is early, calm, proportionate attention to unusual objects before a situation escalates.

---

## How This Can Help Protect Concerts, Stadiums, and Large Gatherings

Large events face high throughput, limited staff attention, bag clutter, weather complications, vendor equipment, temporary infrastructure, and crowd pressure. Security teams must avoid creating dangerous bottlenecks while still screening for prohibited items. A WiFi CSI anomaly detector can support this environment by acting as a **non-contact anomaly triage layer**.

Possible venue use cases include:

### Bag-lane augmentation

At a concert or stadium gate, the system can sit near a bag table or inspection lane. Each lane can have a local transmitter/receiver pair. A baseline can be captured before opening, then refreshed during quiet intervals. The detector can write an alert score and explanation for bags that strongly perturb the RF channel.

### Vendor and equipment intake

Large gatherings involve cases, carts, tripods, instruments, camera gear, tools, cables, and stage equipment. Rather than treating all metal as suspicious, the detector should be tuned to support a declared intake policy: authorized vendor equipment goes through an expected route, while unexpected long conductive-object anomalies in public entry lanes receive review.

### Crowd-safe queue management

Security technology can create risk if it slows entry too much. The best deployment avoids public alarm. Alerts should be routed privately to trained staff. Secondary review should be physically designed so that a short review does not block the whole crowd.

### Temporary high-risk zones

Some events include dignitary appearances, nationally televised performances, controversial speakers, or large public attention. A temporary CSI layer can be placed around specific controlled paths, backstage entrances, media check-in points, credentialing desks, or restricted corridors. The system should still use the same principle: anomaly support, not automatic judgment.

### Post-event improvement

The feature reports and false-positive logs can help venue managers improve policy and layout. For instance, if tripods repeatedly cause alerts at one entrance, the venue can create a separate camera-equipment intake lane rather than raising thresholds for everyone.

---

## How This Can Support Protective Operations for High-Profile Guests

When high-profile guests, public officials, performers, athletes, executives, or community leaders attend an event, security teams often create layered protective perimeters. This project can contribute to the outer layers of that design by helping identify unexpected long conductive-object anomalies in controlled zones.

The right use is defensive and procedural:

- screening credentialed and non-credentialed access paths,
- helping staff decide when a bag needs secondary inspection,
- monitoring controlled object-transfer points,
- documenting sensor quality and review outcomes,
- reducing dependence on hurried visual inspection alone.

The system should not be used to track, profile, or target people because of viewpoint, appearance, affiliation, or status. It also should not expose alert details to crowds or bystanders. Protective deployments should use private alert channels, trained review teams, and documented escalation rules.

In VIP or high-profile environments, false positives are still important. A harmless camera rig or musical instrument case can look unusual to RF sensing. The model’s contribution table helps staff understand why the score rose. A high `spectral_ripple_z`, high `cross_stream_coherence`, and high `persistence` might justify calm secondary review, while low sensor quality should suppress action.

---

## System Architecture

The advanced implementation is organized around a simple pipeline:

```text
CSI baseline file  ─┐
                   ├── load_csi_npz() ── normalize shape ── extract_features() ── score_features()
CSI target file    ┘                                                                  │
                                                                                      ▼
                                                                        DetectionResult dataclass
                                                                                      │
                                      ┌───────────────────────────────────────────────┼───────────────────────────────┐
                                      ▼                                               ▼                               ▼
                                 JSON output                                      CSV features                  Markdown report
```

Important files:

| File | Role |
|---|---|
| `main_v0_4_advanced.py` | Primary CLI and feature extraction engine. |
| `csi_anomaly_gui (1).py` | GUI helper for running the detector in a more visual workflow. |
| `calibration.json` | Example calibration output. |
| `features.csv` | Example feature/contribution export. |
| `result.json` | Example machine-readable result. |
| `report.md` | Example concept report generated from a result. |
| `main_v0_4_advanced.patch` | Patch showing advanced modifications. |
| `original_uploaded_main_v0_3_pasted.txt` | Earlier reference version. |

The detector accepts CSI arrays stored in `.npz` files under the key `csi`. Supported shapes include:

```text
[time, rx, tx, subcarrier]
[time, stream, subcarrier]
[time, subcarrier]
[..., 2] final real/imag channel
```

The program normalizes CSI shapes into a comparable internal representation, extracts robust features, computes a score, applies quality and threshold logic, and exports a result.

---

## Input Data Model

The baseline and scan files should be captured under similar geometry:

- same transmitter and receiver positions,
- same antenna configuration,
- same carrier and bandwidth assumptions,
- same bag lane or sensing region,
- similar environmental conditions,
- sufficient frame count,
- stable link quality.

The minimum conceptual input is:

```python
import numpy as np

# Example shape: time x stream x subcarrier
csi = np.zeros((128, 3, 64), dtype=np.complex64)
np.savez("example_csi.npz", csi=csi)
```

A baseline should represent the local safe condition. A target scan should represent the same region with the object or bag being reviewed. The model is not trained to generalize across every building. It needs local calibration because WiFi CSI is strongly shaped by walls, reflections, furniture, people, humidity, antenna placement, and hardware.

---

## Mathematical Foundations

### CSI amplitude and phase

The detector works with complex CSI:

$$
H_k(t)=A_k(t)e^{j\phi_k(t)}
$$

Amplitude and phase are:

$$
A_k(t)=|H_k(t)|
$$

$$
\phi_k(t)=\arg(H_k(t))
$$

A conductive object can alter amplitude through reflection and absorption effects, while phase changes through path-length and multipath delay changes.

### Baseline residual

The key object of comparison is the difference between a target channel and a safe baseline:

$$
\Delta H_k(t)=H^{scan}_k(t)-H^{base}_k(t)
$$

A normalized form reduces sensitivity to absolute signal level:

$$
\widetilde{H}_k(t)=\frac{H^{scan}_k(t)}{H^{base}_k(t)+\epsilon}
$$

Amplitude residual:

$$
\Delta A_k(t)=|H^{scan}_k(t)|-|H^{base}_k(t)|
$$

Phase residual:

$$
\Delta \phi_k(t)=\operatorname{unwrap}(\phi^{scan}_k(t))-\operatorname{unwrap}(\phi^{base}_k(t))
$$

### Robust standardization

CSI is noisy. The implementation uses robust statistics so outliers do not dominate every decision:

$$
z_i=\frac{x_i-\operatorname{median}(x)}{\operatorname{MAD}(x)+\epsilon}
$$

where MAD is the median absolute deviation:

$$
\operatorname{MAD}(x)=\operatorname{median}(|x_i-\operatorname{median}(x)|)
$$

### Temporal energy

Persistent channel distortion is summarized with energy-like features:

$$
E(t)=\sum_{k}|\Delta H_k(t)|^2
$$

A static or slowly moving object should produce a different temporal signature from a brief motion artifact.

### Cross-link coherence

A credible RF anomaly should often appear coherently across multiple streams or links:

$$
C_{m,n}=\frac{|\sum_t\Delta H_m(t)\Delta H_n^*(t)|}{\sqrt{\sum_t|\Delta H_m(t)|^2\sum_t|\Delta H_n(t)|^2}+\epsilon}
$$

High coherence can support confidence, while incoherent changes may indicate noise, motion clutter, or poor hardware alignment.

### Wavelength and Fresnel effects

Carrier frequency controls wavelength:

$$
\lambda=\frac{c}{f}
$$

The first Fresnel zone radius for link distances `d_1` and `d_2` is approximated by:

$$
r_F=\sqrt{\frac{\lambda d_1d_2}{d_1+d_2}}
$$

This reminds operators that the detector is not looking at a point. It is sensing perturbations across a volume shaped by transmitter-receiver geometry.

### Range resolution proxy

For bandwidth `B`, a simple range-resolution limit is:

$$
\Delta r=\frac{c}{2B}
$$

Commodity WiFi bandwidths do not provide fine object imaging. This is another reason to avoid claiming that the system identifies exact object type.

### Conductive reflection proxy

An idealized reflection coefficient is:

$$
\Gamma=\frac{Z_2-Z_1}{Z_2+Z_1}
$$

Real-world bags, bodies, and objects are more complex than this simple boundary model. The implementation therefore uses reflection as a proxy feature, not a physical proof.

### Elongation proxy

If a reconstructed disturbance is represented by a spatial covariance matrix, an elongation proxy can be defined as:

$$
E_{long}=\frac{\lambda_{max}(\Sigma_{blob})}{\lambda_{min}(\Sigma_{blob})+\epsilon}
$$

Orientation can be estimated from covariance terms:

$$
\theta_{obj}=\frac{1}{2}\tan^{-1}\left(\frac{2\Sigma_{xy}}{\Sigma_{xx}-\Sigma_{yy}}\right)
$$

This does not mean the system has a camera-like image. It means the feature extractor has a way to summarize whether the RF disturbance is more line-like than blob-like.

### Posterior scoring

The model can express a class-style posterior over broad concepts:

$$
P(c|\mathbf{z})=\frac{e^{g_c(\mathbf{z})}}{\sum_{c'}e^{g_{c'}(\mathbf{z})}}
$$

The final alert score combines anomaly evidence, contextual priors, and sensor quality:

$$
S_{alert}=P(c=long\_conductive|\mathbf{z})\cdot P(restricted\_zone)\cdot C_{sensor}
$$

The implementation also uses weighted feature contributions and a sigmoid-style bounded score. The exact score is less important than disciplined calibration and human review.

---

## Feature Groups

The detector’s feature vector is organized into six groups.

### 1. Signal and channel features

These features describe the underlying RF geometry: wavelength, skin-depth proxy, reflection proxy, baseline-normalized delta, amplitude residual, phase residual, antenna amplitude ratios, phase differences, and smoothed energy.

### 2. Motion, Doppler, and temporal features

These features help separate persistent objects from transient movement. They include temporal energy, spectral ripple, phase distortion, amplitude distortion, phase curvature, group delay, STFT peak ratio, Doppler phase-rate proxy, radial-velocity proxy, autocorrelation, and cross-stream coherence.

### 3. Spatial and imaging abstraction features

These features summarize how structured the anomaly appears across streams and subcarriers. They include coherence rank, spatial covariance score, beamforming concentration proxy, MUSIC sharpness proxy, delay-profile peakiness, range-resolution estimate, Fresnel-radius estimate, tomographic projection proxy, sparse reconstruction proxy, and anomaly-map proxy.

### 4. Metalness and elongation features

These features estimate whether the disturbance has conductive, rigid, and elongated structure. They include elongation proxy, orientation proxy, orientation stability, extent proxy, rigidity proxy, persistence, conductive score proxy, spectral entropy delta, spectral flatness delta, residual kurtosis, Mahalanobis proxy, and broad posterior probabilities.

### 5. Sensor-quality features

A strong score should not be trusted if the link is unstable. Sensor quality acts as a brake on alerts. Poor antenna alignment, packet loss, moving crowds, multipath churn, or corrupted input should reduce trust.

### 6. Context and governance features

The model accepts restricted-zone and bag-transition priors. These priors should be explicit and bounded. They are not shortcuts for profiling. They exist so a controlled checkpoint lane can be treated differently from an unrestricted hallway, and so a declared bag scan can be treated differently from ordinary ambient movement.

---

## Scoring Model

The scoring model is intentionally explainable. Each feature can contribute to the final score. A simplified expression is:

$$
z=w_0+\sum_iw_i f_i
$$

$$
S=\sigma(z)=\frac{1}{1+e^{-z}}
$$

The detector then applies threshold and quality checks:

$$
alert = (S \geq \tau)\land(C_{sensor}\geq q)
$$

where `tau` is the alert threshold and `q` is the quality threshold. In the default configuration, the threshold is conservative and human review is required. Operators should tune thresholds using local safe scans rather than assuming the defaults are correct for every site.

The output includes a contribution table. This is operationally important. A black-box “yes/no” alert is not enough for safety-critical environments. Staff need to see whether the score came from amplitude distortion, spectral ripple, sensor quality, context priors, or some combination of features.

---

## Calibration Philosophy

Calibration is the difference between a research demo and a responsible deployment.

A venue should collect known-safe scans from the actual sensing zone. Those scans should include normal bags, backpacks, musical instruments, sports equipment, camera gear, umbrellas, laptops, binders, lunch boxes, water bottles, maintenance tools, mobility aids, and other common objects. The purpose is to understand normal variation and reduce false alarms.

Let the safe-scan scores be:

$$
\mathcal{S}_{safe}=\{S_1,S_2,\ldots,S_N\}
$$

A threshold can be selected from an upper quantile:

$$
\tau=Q_{1-\alpha}(\mathcal{S}_{safe})+m
$$

where `alpha` is a target false-alarm rate and `m` is a safety margin. This repository includes a `--safe-scan` calibration path to estimate a local threshold. Calibration should be repeated when hardware moves, firmware changes, furniture changes, seasonal crowd conditions change, or the sensing lane is redesigned.

A calibration set should not include only “easy” examples. It should include the weird but harmless objects that actually appear in schools and venues. Good calibration makes the system less dramatic and more useful.

---

## Installation

This repository is intentionally lightweight. The core detector uses Python and NumPy.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install numpy
```

The GUI helper may use standard desktop GUI dependencies already available in many Python installations. For production deployment, pin versions, document the hardware, and keep a reproducible environment file.

---

## Quick Start

Generate synthetic demo data:

```bash
python main_v0_4_advanced.py --make-demo --demo-dir demo_csi
```

Run the detector:

```bash
python main_v0_4_advanced.py \
  --empty demo_csi/empty_bag_csi.npz \
  --scan demo_csi/target_bag_csi.npz \
  --pretty
```

Write all major outputs:

```bash
python main_v0_4_advanced.py \
  --empty demo_csi/empty_bag_csi.npz \
  --scan demo_csi/target_bag_csi.npz \
  --json-out result.json \
  --csv-out features.csv \
  --equations-out equations.md \
  --concept-report report.md \
  --pretty
```

Generate known-safe demo data:

```bash
python main_v0_4_advanced.py --make-demo-safe --demo-dir demo_safe
```

Calibrate from a safe scan:

```bash
python main_v0_4_advanced.py \
  --empty demo_safe/empty_bag_csi.npz \
  --safe-scan demo_safe/safe_bag_csi.npz \
  --calibration-out calibration.json \
  --pretty
```

---

## Command-Line Usage

The primary script supports the following operational categories.

### Required detection inputs

```bash
--empty PATH      # empty/safe baseline .npz containing key "csi"
--scan PATH       # target .npz containing key "csi"
```

### Context and thresholds

```bash
--zone LABEL
--threshold FLOAT
--quality-threshold FLOAT
--min-frames INT
--restricted-zone-prior FLOAT
--bag-transition-prior FLOAT
```

### RF metadata

```bash
--carrier-hz FLOAT
--bandwidth-hz FLOAT
--link-distance-m FLOAT
--sample-rate-hz FLOAT
```

These values influence wavelength, range-resolution, Fresnel, and Doppler proxies. They should match the actual sensing hardware and environment.

### Configuration and calibration

```bash
--config-in config.json
--config-out resolved_config.json
--safe-scan safe_1.npz
--safe-scan safe_2.npz
--calibration-out calibration.json
--false-alarm-rate 0.01
```

### Output formats

```bash
--json-out result.json
--csv-out features.csv
--equations-out equations.md
--concept-report report.md
--pretty
```

### Demo and tests

```bash
--make-demo
--make-demo-safe
--self-test
--demo-dir demo_csi
--demo-seed 7
```

---

## Outputs and Reports

A detection result contains:

```json
{
  "event": "long_conductive_object_anomaly",
  "zone": "bag_scan",
  "score": 0.91,
  "threshold": 0.85,
  "alert": true,
  "severity": "high_human_review",
  "claim_boundary": "Possible long conductive-object anomaly in bag; not weapon confirmation and not intent detection.",
  "features": {},
  "contributions": {},
  "equation_coverage": [],
  "model": {}
}
```

The JSON output is best for machine integration. The CSV output is best for spreadsheet review, calibration, and comparison across test runs. The Markdown concept report is best for human explanation. The equation registry is best for documentation and audits.

Severity should be interpreted carefully:

| Severity | Meaning |
|---|---|
| `low` | No meaningful review signal. |
| `medium_review` | Some anomaly evidence; consider context. |
| `high_human_review` | Stronger anomaly evidence; human review required. |
| `quality_blocked` | Score may be unreliable because sensor quality is too low. |

Operational systems should record both alerts and non-alerts during evaluation. Only recording alerts creates blind spots.

---

## Operational Modes

### Research mode

Use synthetic demos, saved `.npz` files, and offline analysis. This is the correct mode for development, classroom demonstrations, and feature validation. No operational decisions should be made from research-mode results.

### Pilot mode

Use real hardware in a controlled setting with consenting participants and known-safe objects. Measure false positives, false negatives, throughput, sensor quality, and staff workload. Do not connect pilot alerts to enforcement.

### Assisted screening mode

Use the system at a clearly defined screening point where policy already allows object review. Alerts route to trained staff. Staff use respectful secondary inspection procedures. The model output is one input among many.

### Audit mode

Periodically replay stored, privacy-minimized CSI sessions to evaluate drift, threshold performance, and feature stability. Audit mode should include checks for disparate impact and procedural fairness.

---

## Deployment Design for Schools

A school deployment should be calm, transparent, and narrow.

### Suggested physical design

Create a limited sensing zone at a visitor entrance, event entrance, or bag-check table. Keep transmitter and receiver positions fixed. Avoid putting the sensing zone where students casually gather, socialize, or pass throughout the day. The system works best when it measures a specific checkpoint condition, not a chaotic hallway.

### Suggested process

1. Capture a baseline before the screening period.
2. Confirm sensor quality.
3. Screen bags through the same lane and policy.
4. Route high-scoring anomalies to respectful secondary review.
5. Log final human outcomes.
6. Review false positives weekly during pilot stages.
7. Recalibrate after layout or hardware changes.

### School-specific fairness issues

Students may carry assistive devices, medical supplies, band instruments, sports gear, art tools, robotics parts, science equipment, and family items. A model that flags conductive or elongated objects may interact with these ordinary needs. Schools should create clear accommodation procedures and ensure staff never treat an alert as misconduct by itself.

### Emergency integration

The system should not replace emergency planning. It can provide early review signals, but emergency response still depends on trained personnel, communication plans, reunification procedures, drills, local law, and coordination with first responders.

---

## Deployment Design for Large Venues

Large venues need throughput and resilience.

### Lane design

Each screening lane should have its own baseline, hardware identity, calibration profile, and staff workflow. Do not share thresholds blindly across lanes if antenna geometry differs.

### Weather and temporary infrastructure

Outdoor events introduce rain, wind, tents, metal barricades, generators, lighting rigs, temporary fencing, and crowd motion. These can alter the RF environment. Calibration should include event-day conditions.

### Authorized equipment

Many venues allow authorized long conductive items: camera tripods, microphone stands, instrument cases, stage parts, tools, and mobility aids. A mature deployment should separate public guest screening from vendor intake and credentialed equipment routes.

### Alert routing

Alerts should go to a private console or staff device, not to public screens. The alert should include score, sensor quality, and top feature contributions. Avoid audible alarms that can embarrass guests or create crowd anxiety.

### Post-event review

After an event, security leadership should review aggregate performance: number of scans, alert rate, secondary-review outcomes, sensor-quality blocks, throughput effects, and complaints. The goal is continuous improvement, not simply more alerts.

---

## Human Review Workflow

A safe review workflow has four layers.

### 1. Sensor check

Before acting, verify that sensor quality is above threshold. If the sensor is unstable, do not treat the alert as reliable.

### 2. Context check

Confirm that the scan occurred in a declared screening zone. Context priors should be explicit, not improvised.

### 3. Feature explanation

Review the top contributing features. A score driven by coherent, persistent, elongated, conductive proxies is more meaningful than a score driven mostly by noise or low-quality artifacts.

### 4. Respectful secondary review

If policy allows, ask for a secondary review of the object or bag. Use neutral language such as “the screening lane needs a second check.” Do not accuse. Do not reveal technical conclusions to bystanders. Document the result.

A good workflow protects both safety and dignity. The system should help staff slow down and check carefully; it should not push staff toward panic.

---

## False Positives, False Negatives, and Limitations

### False positives

The system may alert on harmless objects, including:

- umbrellas,
- tripods,
- musical instruments,
- sports gear,
- laptops and chargers,
- camera rigs,
- mobility aids,
- maintenance tools,
- metal water bottles,
- clustered electronics,
- dense foil packaging,
- metal binders or art supplies.

False positives are not merely inconvenience. In schools and public venues, false positives can create embarrassment, delay, fear, or unequal treatment. This is why calibration, policy, signage, and human review matter.

### False negatives

The system may miss objects when:

- the object orientation does not perturb the link strongly,
- the bag is shielded by other materials,
- the person moves too quickly,
- the hardware is poorly aligned,
- the baseline is stale,
- the environment is too dynamic,
- the object is not conductive enough,
- the object is outside the effective Fresnel zone,
- the threshold is too high,
- the input CSI is corrupted.

A non-alert must not be treated as proof of safety. This tool is one layer, not a guarantee.

### Technical limitations

Commodity WiFi is limited by bandwidth, multipath ambiguity, hardware noise, phase offsets, packet timing, antenna placement, and environmental drift. It cannot resolve fine internal structure. It cannot infer intent. It cannot reliably distinguish every object class. It cannot replace trained screening or emergency planning.

---

## Privacy and Governance

A WiFi CSI security system still processes data about physical environments and human movement. Treat it as sensitive.

Recommended governance controls:

- Publish a clear purpose statement.
- Limit collection to defined screening zones.
- Avoid continuous monitoring of ordinary spaces.
- Minimize retention duration.
- Store derived features instead of raw CSI when possible.
- Restrict access to trained personnel.
- Encrypt stored reports.
- Log access to results.
- Review false-positive patterns.
- Provide a complaint and correction process.
- Disable the system when the policy basis no longer applies.

For schools, governance should involve administrators, safety teams, families, students where appropriate, accessibility coordinators, legal counsel, and community stakeholders. For public venues, governance should involve security leadership, operations, legal, privacy, guest services, and accessibility teams.

---

## Testing Strategy

A serious test program should include:

### Unit tests

Validate shape normalization, feature extraction, robust statistics, scoring, config loading, report writing, and error handling.

### Synthetic tests

Use generated CSI to confirm that known perturbations move features in expected directions. Synthetic tests are useful for regression but not proof of field performance.

### Bench tests

Use fixed hardware in a controlled room. Test common safe objects, empty bags, cluttered bags, and known conductive objects under documented conditions.

### Field pilots

Run the system at real entrances without operational enforcement. Compare alert scores to human-reviewed outcomes. Measure throughput and user experience.

### Drift tests

Repeat calibration after environmental changes. Track score distributions over time:

$$
D_{KL}(P_{week1}(S)\|P_{week2}(S))=\sum_sP_{week1}(s)\log\frac{P_{week1}(s)}{P_{week2}(s)}
$$

Large distribution shifts may indicate that thresholds are stale.

### Fairness checks

Evaluate whether alerts cluster around specific groups, activities, equipment types, entrances, or times. If they do, investigate process design and calibration before deployment.

---

## Roadmap

Potential future improvements:

- hardware-specific CSI adapters,
- live stream ingestion,
- multi-link fusion,
- better drift detection,
- stronger calibration tooling,
- richer GUI review panels,
- privacy-preserving aggregate dashboards,
- lane-by-lane threshold management,
- dataset cards and model cards,
- automated sensor-quality diagnostics,
- integration with access-control logs under strict governance,
- exportable audit bundles,
- simulation tools for antenna placement,
- additional non-weapon safety applications such as detecting abandoned conductive equipment in restricted maintenance zones.

Any roadmap item that increases operational power should also increase oversight, logging, and appealability.

---

## Ethical Use Statement

This project is intended for defensive research, safety engineering, and responsible anomaly detection. It should be used only in lawful, clearly governed settings where people are treated with dignity and where human review is mandatory.

Do not use this project to:

- make automatic accusations,
- infer intent,
- profile protected classes,
- secretly monitor lawful gatherings,
- bypass required consent or notice,
- replace trained staff,
- trigger force automatically,
- punish a person based only on a sensor score.

Use this project to:

- study CSI anomaly features,
- improve safe screening workflows,
- support respectful secondary review,
- reduce blind spots in crowded environments,
- document uncertainty,
- improve calibration,
- design layered safety systems that protect people without sacrificing civil rights.

---

## License

This repository includes a `LICENSE` file. Review it before copying, modifying, or deploying the code.

---

## Final Note

The most important engineering principle in this repository is restraint. WiFi CSI can provide useful information about changes in a radio channel. It cannot provide certainty about people or intent. The right goal is not to build a sensational detector. The right goal is to build a careful, calibrated, auditable safety layer that helps trained humans protect schools, concerts, public meetings, and large gatherings while preserving dignity, privacy, and due process.


---

## Equation Registry

The implementation maintains a 50-equation registry so every major feature can be connected to a mathematical concept. The registry is useful for documentation, audits, technical reviews, and future model-card generation.

| ID | Concept | Equation | Implemented as |
|---|---|---|---|
| E01 | Received OFDM subcarrier model | `$y_k(t)=H_k(t)x_k(t)+n_k(t)$` | input CSI model |
| E02 | Multipath CSI response | `$H_k(t)=\sum_{p=1}^{P}a_p(t)e^{-j2\pi f_k	au_p(t)}$` | residual/multipath interpretation |
| E03 | CSI amplitude | `$A_k(t)=|H_k(t)|$` | amplitude distortion and amplitude ratio |
| E04 | CSI phase | `$\phi_k(t)=rg(H_k(t))$` | phase sanitization and phase distortion |
| E05 | Wavelength | `$\lambda=c/f$` | wavelength proxy |
| E06 | Path phase shift | `$\Delta\phi_k=-2\pi f_k\Delta	au$` | phase residual features |
| E07 | Propagation delay | `$	au_p=d_p/c$` | delay profile interpretation |
| E08 | Complex permittivity | `$\epsilon^*=\epsilon'-j\epsilon''$` | conductive prior metadata |
| E09 | Skin depth | `$\delta=\sqrt{2/(\omega\mu\sigma)}$` | skin-depth proxy |
| E10 | Reflection coefficient | `$\Gamma=(Z_2-Z_1)/(Z_2+Z_1)$` | reflection score proxy |
| E11 | Baseline-normalized CSI | `$	ilde{H}_k(t)=H_k(t)/H_{k,0}$` | normalized CSI |
| E12 | CSI perturbation | `$\Delta H_k(t)=H_k(t)-H_{k,0}$` | baseline residual |
| E13 | Amplitude residual | `$\Delta A_k(t)=|H_k(t)|-|H_{k,0}|$` | amplitude residual z-score |
| E14 | Phase residual | `$\Delta\phi_k(t)=unwrap(\phi_k(t))-unwrap(\phi_{k,0})$` | phase residual z-score |
| E15 | Antenna amplitude ratio | `$R^A_{i,j,k}=|H_{i,k}|/(|H_{j,k}|+\epsilon)$` | amplitude ratio anomaly |
| E16 | Antenna phase difference | `$R^\phi_{i,j,k}=ngle H_{i,k}-ngle H_{j,k}$` | phase difference anomaly |
| E17 | Phase sanitization | `$\phi'_k(t)=\phi_k(t)-(lpha f_k+eta)$` | phase sanitize |
| E18 | MAD filter | `$z_k=(A_k-median(A_k))/(MAD(A_k)+\epsilon)$` | robust z |
| E19 | Smoothed CSI | `$ar{H}_k(t)=rac{1}{W}\sum_{u=t-W+1}^{t}H_k(u)$` | moving average CSI |
| E20 | Kalman update | `$\hat{x}_{t|t}=\hat{x}_{t|t-1}+K_t(z_t-\hat{x}_{t|t-1})$` | Kalman smoothing |
| E21 | STFT | `$S_k(t,\omega)=\sum_	au H_k(	au)w(	au-t)e^{-j\omega	au}$` | STFT peak ratio |
| E22 | Doppler estimate | `$f_D=(1/2\pi)d\phi(t)/dt$` | Doppler phase-rate proxy |
| E23 | Radial velocity | `$v_r=\lambda f_D/2$` | radial velocity proxy |
| E24 | Temporal energy | `$E(t)=\sum_k|\Delta H_k(t)|^2$` | energy z-score |
| E25 | Motion-normalized residual | `$M_k=\Delta H_k/\sqrt{\sum_u|\Delta H_k(u)|^2+\epsilon}$` | motion normalized residual |
| E26 | Static-object persistence | `$P_s=rac{1}{T}\sum_t\mathbb{1}(|\Delta H(t)|>\eta)$` | persistence |
| E27 | Static/dynamic separation | `$H_k(t)=H_k^{static}+H_k^{dynamic}(t)+n_k(t)$` | baseline residual |
| E28 | Background subtraction | `$H_k^{dynamic}=H_k-rac{1}{T_0}\sum_{u=1}^{T_0}H_k(u)$` | dynamic component |
| E29 | Autocorrelation | `$
ho(\ell)=\sum_tx(t)x(t-\ell)/\sum_tx(t)^2$` | lag-1 autocorrelation |
| E30 | Cross-link coherence | `$C_{m,n}=|\sum_t\Delta H_m\Delta H_n^*|/\sqrt{\sum_t|\Delta H_m|^2\sum_t|\Delta H_n|^2}$` | cross-stream coherence |
| E31 | MIMO CSI matrix | `$\mathbf{H}_k(t)\in\mathbb{C}^{N_r	imes N_t}$` | shape-aware CSI features |
| E32 | Spatial covariance | `$\mathbf{R}_k=\mathbb{E}[\mathbf{h}_k\mathbf{h}_k^H]$` | spatial covariance score |
| E33 | Beamforming response | `$B(	heta)=\mathbf{a}^H(	heta)\mathbf{R}\mathbf{a}(	heta)$` | beamforming proxy |
| E34 | MUSIC spectrum | `$P_{MUSIC}(	heta)=1/(\mathbf{a}^H\mathbf{E}_n\mathbf{E}_n^H\mathbf{a})$` | MUSIC sharpness proxy |
| E35 | Delay profile | `$P(	au)=|\sum_kH_ke^{j2\pi f_k	au}|^2$` | delay profile peakiness |
| E36 | Range resolution | `$\Delta r=c/(2B)$` | range resolution estimate |
| E37 | Fresnel radius | `$r_F=\sqrt{\lambda d_1d_2/(d_1+d_2)}$` | Fresnel radius estimate |
| E38 | Tomographic projection | `$\mathbf{y}=\mathbf{A}\mathbf{x}+\mathbf{n}$` | tomographic projection proxy |
| E39 | Regularized reconstruction | `$\hat{\mathbf{x}}=rg\min_x||y-Ax||_2^2+\lambda||x||_1$` | sparse reconstruction proxy |
| E40 | Spatial anomaly map | `$\mathcal{A}(x,y)=|\hat{x}(x,y)-\hat{x}_0(x,y)|$` | anomaly map proxy |
| E41 | Metalness vector | `$\mathbf{m}=[\Delta A,\Delta\phi,\sigma_A^2,\sigma_\phi^2,C_{m,n},P_s]$` | conductive score proxy |
| E42 | Inter-subcarrier variance | `$\sigma^2=rac{1}{K-1}\sum_k(A_k-ar{A})^2$` | spectral ripple z-score |
| E43 | Phase curvature | `$\kappa_\phi=\partial^2\phi(f)/\partial f^2$` | phase curvature z-score |
| E44 | Conductive reflection score | `$S_c=w_1|\Gamma|+w_2\sigma_A^2+w_3\sigma_\phi^2$` | conductive score proxy |
| E45 | Blob elongation | `$E_{long}=\lambda_{max}(\Sigma)/(\lambda_{min}(\Sigma)+\epsilon)$` | elongation proxy |
| E46 | Object orientation | `$	heta=rac{1}{2}	an^{-1}(2\Sigma_{xy}/(\Sigma_{xx}-\Sigma_{yy}))$` | orientation proxy |
| E47 | Approximate extent | `$L_{est}=\max_{i,j}||p_i-p_j||_2$` | extent proxy |
| E48 | Bag residual | `$\Delta H^{obj}=H^{bag+obj}-H^{bag}$` | bag compensation residual |
| E49 | Class posterior | `$P(c|z)=e^{g_c(z)}/\sum_{c'}e^{g_{c'}(z)}$` | softmax posteriors |
| E50 | Human-review alert score | `$S_{alert}=P(long\ conductive|z)P(restricted\ zone)C_{sensor}$` | score features |

---

## Model Card Summary

**Intended use:** research and assisted screening in a controlled, clearly disclosed, human-reviewed environment.  
**Not intended for:** autonomous enforcement, covert monitoring, person identification, intent detection, or unsupervised use in open public space.  
**Input:** paired CSI baseline and target scan.  
**Output:** anomaly score, severity, feature table, contribution table, equation coverage, and safety boundary.  
**Primary risk:** overclaiming. The model can be technically impressive while still being uncertain. The README therefore repeats the boundary often: long conductive-object anomaly is not weapon confirmation.

### Recommended acceptance criteria before real use

A deployment should not move beyond pilot mode until it demonstrates:

1. stable sensor quality across normal operating hours,
2. documented false-positive rate on local safe objects,
3. documented false-negative evaluation using approved test articles and lawful procedures,
4. written human-review protocol,
5. data retention and access policy,
6. accessibility accommodation process,
7. staff training records,
8. incident-review process,
9. community or stakeholder communication plan,
10. legal review for the jurisdiction and venue type.

### Operational success metric

The best metric is not the raw alert rate. A useful system lowers unmanaged risk while keeping the environment respectful and functional. Suggested metrics include:

- review precision,
- review workload,
- missed-test-object rate during controlled testing,
- sensor-quality block rate,
- median added screening time,
- complaint rate,
- accessibility accommodation success,
- threshold drift,
- calibration freshness,
- documented staff adherence to protocol.

Security systems fail when they become theater, panic, or bias. They succeed when they quietly improve the quality of human attention.


---

## Appendix A: Practical Deployment Checklist

Before turning on any pilot, answer these questions in writing.

**Purpose:** What exact safety problem is this system meant to reduce? What risks will it not address? Who owns the policy? Who can pause the system?

**Place:** Where is the sensing zone? Is it a controlled checkpoint, or is it an ordinary public space? Are people informed? Can people choose an alternative screening path when policy allows?

**People:** Who reviews alerts? What training do they receive? How do they speak to students, guests, staff, performers, vendors, or visitors? Who handles complaints?

**Process:** What happens when the score is high? What happens when sensor quality is low? How is secondary review documented? How are harmless outcomes recorded for calibration?

**Data:** What raw data is stored? What derived data is stored? How long is it retained? Who can export it? Is it encrypted? Are logs reviewed?

**Performance:** What false-positive rate is acceptable? What false-negative evaluation is required? How often is calibration refreshed? What conditions shut the system down?

**Fairness:** Are alerts distributed evenly across lanes and contexts? Are common student or guest items causing avoidable reviews? Are assistive devices handled respectfully?

**Review:** Who receives monthly reports? What changes are made when the system causes delay, confusion, or unfair burden?

---

## Appendix B: Example Human-Friendly Alert Language

Avoid accusatory language. Prefer neutral operational language.

Good internal wording:

> Lane 2 scan produced a high long-conductive-object anomaly score with acceptable sensor quality. Please route the item to standard secondary review.

Good guest-facing wording:

> This lane needs a second check of the item. Thank you for your patience.

Avoid wording such as:

> The system detected a weapon.

That statement exceeds the technical capability and can create unnecessary fear or reputational harm.

---

## Appendix C: Integration Notes

A production system might wrap the detector with:

- a CSI collector service,
- a lane controller,
- a calibration manager,
- a private review dashboard,
- a local encrypted event store,
- a policy engine,
- a staff authentication layer,
- a drift monitor,
- an audit exporter.

A minimal service boundary can look like:

```text
POST /scan
  body: baseline_id, scan_id, zone, rf_metadata
  returns: score, alert, severity, sensor_quality, top_contributions

POST /review
  body: scan_id, reviewer_id, outcome, notes
  returns: stored review record

GET /calibration/{lane_id}
  returns: current threshold, safe-scan count, freshness, quality statistics
```

Do not expose raw alert feeds publicly. Do not integrate directly with automated punitive systems. Keep the system boring, reviewable, and interruptible.

---

## Appendix D: Research Notes on Signal Interpretation

A long conductive object can produce strong reflections, but the exact CSI signature depends on object orientation, polarization, antenna geometry, carrier frequency, bandwidth, bag material, body position, and environmental multipath. The same object can look different in two lanes. Two different objects can look similar in one lane. This is why the model emphasizes local residuals and calibration rather than universal object labels.

The most trustworthy evidence is multi-feature consistency: high persistence, high coherence, strong residuals, stable orientation, strong conductive proxy, and acceptable sensor quality. The least trustworthy evidence is a single spiky feature in a low-quality channel.

When interpreting a report, ask:

1. Was the baseline fresh?
2. Was the target scan comparable to the baseline?
3. Was sensor quality high?
4. Which features contributed most?
5. Are there common harmless objects that could explain the pattern?
6. Did staff follow the same procedure used for other reviews?
7. Was the outcome recorded for future calibration?

This discipline turns an experimental sensing method into a careful safety-support tool.




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
