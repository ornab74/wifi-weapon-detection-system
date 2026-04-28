#!/usr/bin/env python3
"""
csi_anomaly_gui.py — CustomTkinter GUI for main.py v0.3

Install:
    pip install customtkinter numpy

Run:
    python csi_anomaly_gui.py

This GUI imports main.py from the same folder and runs the detector locally.
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict
from pathlib import Path
from tkinter import filedialog, messagebox

try:
    import customtkinter as ctk
except ImportError as exc:
    raise SystemExit(
        "customtkinter is not installed. Run: pip install customtkinter"
    ) from exc

try:
    from main import (
        CLAIM_BOUNDARY,
        EQUATION_REGISTRY,
        VERSION,
        detect_from_files,
        generate_demo_pair,
        write_json,
        write_feature_csv,
        write_equations_markdown,
        write_concept_report,
    )
except Exception as exc:
    raise SystemExit(
        "Could not import main.py. Put csi_anomaly_gui.py in the same folder as main.py."
    ) from exc


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class CSIAnomalyGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"WiFi CSI Long Conductive-Object Anomaly Research GUI v{VERSION}")
        self.geometry("1260x820")
        self.minsize(1120, 720)

        self.empty_path = ctk.StringVar()
        self.scan_path = ctk.StringVar()
        self.zone = ctk.StringVar(value="bag_scan")
        self.threshold = ctk.DoubleVar(value=0.85)
        self.quality_threshold = ctk.DoubleVar(value=0.35)
        self.restricted_zone_prior = ctk.DoubleVar(value=0.50)
        self.bag_transition_prior = ctk.DoubleVar(value=0.50)
        self.carrier_hz = ctk.StringVar(value="5.8e9")
        self.bandwidth_hz = ctk.StringVar(value="80e6")
        self.link_distance_m = ctk.StringVar(value="3.0")
        self.sample_rate_hz = ctk.StringVar(value="100.0")
        self.status = ctk.StringVar(value="Ready")
        self.latest_result = None

        self._build_layout()

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkScrollableFrame(self, width=390, corner_radius=18)
        left.grid(row=0, column=0, padx=14, pady=14, sticky="nsw")
        left.grid_propagate(False)

        right = ctk.CTkFrame(self, corner_radius=18)
        right.grid(row=0, column=1, padx=(0, 14), pady=14, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(3, weight=1)

        title = ctk.CTkLabel(left, text="CSI Anomaly Console", font=ctk.CTkFont(size=22, weight="bold"))
        title.pack(padx=18, pady=(18, 4), anchor="w")

        subtitle = ctk.CTkLabel(
            left,
            text=f"v{VERSION}\nBounded output: anomaly score only.\nNo weapon confirmation.",
            justify="left",
            text_color=("gray30", "gray70"),
        )
        subtitle.pack(padx=18, pady=(0, 16), anchor="w")

        self._file_row(left, "Empty/safe bag CSI", self.empty_path, self._choose_empty)
        self._file_row(left, "Target bag scan CSI", self.scan_path, self._choose_scan)

        ctk.CTkLabel(left, text="Zone label").pack(padx=18, pady=(12, 4), anchor="w")
        ctk.CTkEntry(left, textvariable=self.zone).pack(padx=18, fill="x")

        self._slider(left, "Alert threshold", self.threshold, 0.1, 0.99)
        self._slider(left, "Quality threshold", self.quality_threshold, 0.0, 0.95)
        self._slider(left, "Restricted-zone prior", self.restricted_zone_prior, 0.0, 1.0)
        self._slider(left, "Bag-transition prior", self.bag_transition_prior, 0.0, 1.0)

        self._entry(left, "Carrier Hz", self.carrier_hz)
        self._entry(left, "Bandwidth Hz", self.bandwidth_hz)
        self._entry(left, "Link distance m", self.link_distance_m)
        self._entry(left, "Sample rate Hz", self.sample_rate_hz)

        ctk.CTkButton(left, text="Run Detection", height=42, command=self._run_detection_threaded).pack(
            padx=18, pady=(18, 8), fill="x"
        )
        ctk.CTkButton(left, text="Generate Demo CSI Pair", command=self._make_demo).pack(padx=18, pady=8, fill="x")
        ctk.CTkButton(left, text="Save Result JSON", command=self._save_json).pack(padx=18, pady=8, fill="x")
        ctk.CTkButton(left, text="Save Features CSV", command=self._save_csv).pack(padx=18, pady=8, fill="x")
        ctk.CTkButton(left, text="Save Concept Report", command=self._save_report).pack(padx=18, pady=8, fill="x")
        ctk.CTkButton(left, text="Save Equation Registry", command=self._save_equations).pack(padx=18, pady=8, fill="x")

        ctk.CTkLabel(left, textvariable=self.status, wraplength=330, justify="left").pack(
            padx=18, pady=(16, 8), anchor="w"
        )

        ctk.CTkLabel(
            left,
            text=CLAIM_BOUNDARY,
            wraplength=330,
            justify="left",
            text_color=("gray35", "gray65"),
            font=ctk.CTkFont(size=12),
        ).pack(padx=18, pady=(4, 18), anchor="w")

        header = ctk.CTkFrame(right, fg_color="transparent")
        header.grid(row=0, column=0, padx=18, pady=(18, 8), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Result", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, sticky="w")
        self.score_label = ctk.CTkLabel(header, text="Score: —", font=ctk.CTkFont(size=20, weight="bold"))
        self.score_label.grid(row=0, column=1, sticky="e")

        self.progress = ctk.CTkProgressBar(right, height=18)
        self.progress.grid(row=1, column=0, padx=18, pady=(0, 10), sticky="ew")
        self.progress.set(0)

        cards = ctk.CTkFrame(right, fg_color="transparent")
        cards.grid(row=2, column=0, padx=18, pady=(0, 12), sticky="ew")
        cards.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.alert_card = self._metric_card(cards, 0, "Alert", "—")
        self.severity_card = self._metric_card(cards, 1, "Severity", "—")
        self.quality_card = self._metric_card(cards, 2, "Sensor Quality", "—")
        self.posterior_card = self._metric_card(cards, 3, "Long Cond. Posterior", "—")
        self.zone_card = self._metric_card(cards, 4, "Zone", "—")

        tabs = ctk.CTkTabview(right, corner_radius=14)
        tabs.grid(row=3, column=0, padx=18, pady=(0, 18), sticky="nsew")
        for name in ["Summary", "Features", "Equations", "JSON"]:
            tabs.add(name)
            tabs.tab(name).grid_columnconfigure(0, weight=1)
            tabs.tab(name).grid_rowconfigure(0, weight=1)

        self.summary_box = ctk.CTkTextbox(tabs.tab("Summary"), wrap="word")
        self.summary_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.summary_box.insert("1.0", "Run a scan to see the interpreted summary.\n")

        self.features_box = ctk.CTkTextbox(tabs.tab("Features"), wrap="none")
        self.features_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.features_box.insert("1.0", "Feature table will appear here.\n")

        self.equations_box = ctk.CTkTextbox(tabs.tab("Equations"), wrap="word")
        self.equations_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.equations_box.insert("1.0", self._equation_text())

        self.json_box = ctk.CTkTextbox(tabs.tab("JSON"), wrap="none")
        self.json_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.json_box.insert("1.0", "{}\n")

    def _file_row(self, parent, label, var, command):
        ctk.CTkLabel(parent, text=label).pack(padx=18, pady=(8, 4), anchor="w")
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(padx=18, fill="x")
        row.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(row, textvariable=var).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(row, text="Browse", width=80, command=command).grid(row=0, column=1, padx=(8, 0))

    def _entry(self, parent, label, var):
        ctk.CTkLabel(parent, text=label).pack(padx=18, pady=(12, 4), anchor="w")
        ctk.CTkEntry(parent, textvariable=var).pack(padx=18, fill="x")

    def _slider(self, parent, label, var, lo, hi):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(padx=18, pady=(12, 0), fill="x")
        frame.grid_columnconfigure(0, weight=1)
        value_label = ctk.CTkLabel(frame, text=f"{var.get():.2f}", width=42)
        ctk.CTkLabel(frame, text=label).grid(row=0, column=0, sticky="w")
        value_label.grid(row=0, column=1, sticky="e")
        slider = ctk.CTkSlider(
            frame,
            from_=lo,
            to=hi,
            variable=var,
            command=lambda v: value_label.configure(text=f"{float(v):.2f}"),
        )
        slider.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 0))

    def _metric_card(self, parent, col, title, value):
        card = ctk.CTkFrame(parent, corner_radius=14)
        card.grid(row=0, column=col, padx=5, sticky="ew")
        ctk.CTkLabel(card, text=title, text_color=("gray35", "gray65")).pack(padx=10, pady=(10, 0), anchor="w")
        label = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=16, weight="bold"))
        label.pack(padx=10, pady=(0, 10), anchor="w")
        return label

    def _equation_text(self):
        lines = [f"Equation registry: {len(EQUATION_REGISTRY)} concepts", "", CLAIM_BOUNDARY, ""]
        current = None
        for eq in EQUATION_REGISTRY:
            if eq["group"] != current:
                current = eq["group"]
                lines.extend(["", current, "-" * len(current)])
            lines.append(f"{eq['id']} {eq['name']}")
            lines.append(f"  {eq['latex']}")
            lines.append(f"  implemented_as: {eq['implemented_as']}")
        return "\n".join(lines)

    def _choose_empty(self):
        path = filedialog.askopenfilename(title="Choose empty/safe bag CSI .npz", filetypes=[("NumPy compressed CSI", "*.npz"), ("All files", "*.*")])
        if path:
            self.empty_path.set(path)

    def _choose_scan(self):
        path = filedialog.askopenfilename(title="Choose target bag scan CSI .npz", filetypes=[("NumPy compressed CSI", "*.npz"), ("All files", "*.*")])
        if path:
            self.scan_path.set(path)

    def _set_status(self, text):
        self.status.set(text)
        self.update_idletasks()

    def _run_detection_threaded(self):
        threading.Thread(target=self._run_detection, daemon=True).start()

    def _float_entry(self, var, fallback):
        try:
            return float(var.get())
        except Exception:
            return fallback

    def _run_detection(self):
        try:
            empty = Path(self.empty_path.get())
            scan = Path(self.scan_path.get())
            if not empty.exists() or not scan.exists():
                self.after(0, lambda: messagebox.showerror("Missing files", "Choose both empty and target .npz files."))
                return

            self.after(0, lambda: self._set_status("Running detection..."))

            result = detect_from_files(
                empty,
                scan,
                zone=self.zone.get().strip() or "bag_scan",
                threshold=float(self.threshold.get()),
                quality_threshold=float(self.quality_threshold.get()),
                restricted_zone_prior=float(self.restricted_zone_prior.get()),
                bag_transition_prior=float(self.bag_transition_prior.get()),
                carrier_hz=self._float_entry(self.carrier_hz, 5.8e9),
                bandwidth_hz=self._float_entry(self.bandwidth_hz, 80e6),
                link_distance_m=self._float_entry(self.link_distance_m, 3.0),
                sample_rate_hz=self._float_entry(self.sample_rate_hz, 100.0),
            )

            self.latest_result = result
            self.after(0, lambda: self._render_result(result))

        except Exception as exc:
            self.after(0, lambda: messagebox.showerror("Detection failed", str(exc)))
            self.after(0, lambda: self._set_status("Detection failed."))

    def _render_result(self, result):
        data = asdict(result)
        score = float(data["score"])
        features = data.get("features", {})
        contributions = data.get("contributions", {})

        self.progress.set(max(0.0, min(score, 1.0)))
        self.score_label.configure(text=f"Score: {score:.3f}")
        self.alert_card.configure(text="YES" if data["alert"] else "NO")
        self.severity_card.configure(text=str(data["severity"]))
        self.quality_card.configure(text=f"{features.get('sensor_quality', 0.0):.3f}")
        self.posterior_card.configure(text=f"{features.get('posterior_long_conductive', 0.0):.3f}")
        self.zone_card.configure(text=str(data["zone"]))

        summary = [
            f"Event: {data['event']}",
            f"Zone: {data['zone']}",
            f"Score: {score:.4f}",
            f"Threshold: {data['threshold']:.4f}",
            f"Alert: {data['alert']}",
            f"Severity: {data['severity']}",
            "",
            f"Claim boundary: {data['claim_boundary']}",
            "",
            "Core readings:",
            f"  sensor_quality: {features.get('sensor_quality', 0.0):.4f}",
            f"  conductive_score_proxy: {features.get('conductive_score_proxy', 0.0):.4f}",
            f"  elongation_proxy: {features.get('elongation_proxy', 0.0):.4f}",
            f"  persistence: {features.get('persistence', 0.0):.4f}",
            f"  posterior_long_conductive: {features.get('posterior_long_conductive', 0.0):.4f}",
            "",
            "Top positive contributions:",
        ]

        positives = sorted(
            [(k, v) for k, v in contributions.items() if k != "bias"],
            key=lambda kv: abs(float(kv[1])),
            reverse=True,
        )[:14]
        for k, v in positives:
            summary.append(f"  {k}: {float(v): .4f}")

        self.summary_box.delete("1.0", "end")
        self.summary_box.insert("1.0", "\n".join(summary))

        lines = ["FEATURES", "-" * 92]
        for k, v in sorted(features.items()):
            try:
                lines.append(f"{k:42s} {float(v): .8f}")
            except Exception:
                lines.append(f"{k:42s} {v}")
        lines.extend(["", "CONTRIBUTIONS", "-" * 92])
        for k, v in sorted(contributions.items()):
            lines.append(f"{k:42s} {float(v): .8f}")

        self.features_box.delete("1.0", "end")
        self.features_box.insert("1.0", "\n".join(lines))

        self.json_box.delete("1.0", "end")
        self.json_box.insert("1.0", json.dumps(data, indent=2))

        self._set_status("Detection complete.")

    def _make_demo(self):
        out_dir = filedialog.askdirectory(title="Choose folder for demo CSI files")
        if not out_dir:
            return
        try:
            empty, scan = generate_demo_pair(Path(out_dir))
            self.empty_path.set(str(empty))
            self.scan_path.set(str(scan))
            self._set_status(f"Demo CSI files created in {out_dir}")
        except Exception as exc:
            messagebox.showerror("Demo generation failed", str(exc))

    def _save_json(self):
        if self.latest_result is None:
            messagebox.showinfo("No result", "Run detection first.")
            return
        path = filedialog.asksaveasfilename(title="Save result JSON", defaultextension=".json", filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if path:
            write_json(Path(path), self.latest_result)
            self._set_status(f"Saved JSON: {path}")

    def _save_csv(self):
        if self.latest_result is None:
            messagebox.showinfo("No result", "Run detection first.")
            return
        path = filedialog.asksaveasfilename(title="Save feature CSV", defaultextension=".csv", filetypes=[("CSV", "*.csv"), ("All files", "*.*")])
        if path:
            write_feature_csv(Path(path), self.latest_result)
            self._set_status(f"Saved CSV: {path}")

    def _save_report(self):
        if self.latest_result is None:
            messagebox.showinfo("No result", "Run detection first.")
            return
        path = filedialog.asksaveasfilename(title="Save concept report", defaultextension=".md", filetypes=[("Markdown", "*.md"), ("All files", "*.*")])
        if path:
            write_concept_report(Path(path), self.latest_result)
            self._set_status(f"Saved concept report: {path}")

    def _save_equations(self):
        path = filedialog.asksaveasfilename(title="Save equation registry", defaultextension=".md", filetypes=[("Markdown", "*.md"), ("All files", "*.*")])
        if path:
            write_equations_markdown(Path(path))
            self._set_status(f"Saved equation registry: {path}")


def main():
    app = CSIAnomalyGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
