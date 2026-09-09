#!/usr/bin/env python3
"""
V1 Results Review UI -- a local desktop tool for browsing the real,
already-generated predictions in data/v1/v1_full_run_results.db (produced
by analysis/v1_full_run.py). Review/QA tool, not a user-facing product:
function over polish, per its own purpose.

Every value shown is read directly from the stored results -- narrative
text, temperature source/tier, species-presence tier and caveats, and any
disclosed threshold disputes are shown exactly as stored, never
simplified or summarized away. A visible staleness banner appears if the
underlying data is more than 24 hours old (Part 3).

Run directly:      python ui/v1_review_app.py
Packaged:           dist/V1ResultsReview.exe (see README note in this file)
"""

import datetime
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

sys.path.insert(0, str(Path(__file__).parent))
import v1_review_data as data  # noqa: E402

STALE_HOURS = 24


def fmt_timestamp(ts: str | None) -> str:
    if not ts:
        return "(no timestamp on file)"
    try:
        dt = data.parse_iso(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except ValueError:
        return ts


def fmt_age(age: datetime.timedelta | None) -> str:
    if age is None:
        return "unknown"
    total_hours = age.total_seconds() / 3600
    if total_hours < 1:
        return f"{int(age.total_seconds() / 60)} minutes ago"
    if total_hours < 48:
        return f"{total_hours:.1f} hours ago"
    return f"{total_hours / 24:.1f} days ago"


class App(tk.Tk):
    def __init__(self, db_path: Path):
        super().__init__()
        self.title("V1 Results Review (local QA tool)")
        self.geometry("1150x750")

        self.conn = data.connect(db_path)
        self.run_row = data.get_latest_run(self.conn)
        self.db_path = db_path

        self._build_staleness_banner()
        self._build_notebook()

    # ------------------------------------------------------------------
    # Staleness banner (Part 3)
    # ------------------------------------------------------------------
    def _build_staleness_banner(self):
        stale = data.is_stale(self.run_row, STALE_HOURS)
        age = data.data_age(self.run_row)

        if self.run_row is None:
            text = "⚠ No completed run found in this database. Run analysis/v1_full_run.py first."
            color = "#b00020"
        elif stale:
            text = (
                f"⚠ Data may be stale — generated {fmt_age(age)} "
                f"(finished {fmt_timestamp(self.run_row.get('finished_at'))}, "
                f"more than {STALE_HOURS}h ago). Re-run analysis/v1_full_run.py to refresh."
            )
            color = "#b00020"
        else:
            text = (
                f"Data current — generated {fmt_age(age)} "
                f"(finished {fmt_timestamp(self.run_row.get('finished_at'))})."
            )
            color = "#1a6b1a"

        banner = tk.Label(self, text=text, bg=color, fg="white", anchor="w", padx=10, pady=6, wraplength=1100)
        banner.pack(fill="x", side="top")

        db_label = tk.Label(
            self, text=f"Database: {self.db_path}", anchor="w", padx=10, fg="#555"
        )
        db_label.pack(fill="x", side="top")

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------
    def _build_notebook(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        self.browse_tab = ttk.Frame(nb)
        self.failures_tab = ttk.Frame(nb)
        self.summary_tab = ttk.Frame(nb)
        nb.add(self.browse_tab, text="Browse Results")
        nb.add(self.failures_tab, text="Failures")
        nb.add(self.summary_tab, text="Summary")

        self._build_browse_tab()
        self._build_failures_tab()
        self._build_summary_tab()

    # ------------------------------------------------------------------
    # Browse Results tab (Part 2)
    # ------------------------------------------------------------------
    def _build_browse_tab(self):
        frame = self.browse_tab
        filter_bar = ttk.Frame(frame, padding=8)
        filter_bar.pack(fill="x")

        ttk.Label(filter_bar, text="Waterbody name:").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar()
        ttk.Entry(filter_bar, textvariable=self.name_var, width=22).grid(row=0, column=1, padx=4)

        ttk.Label(filter_bar, text="County:").grid(row=0, column=2, sticky="w")
        self.county_var = tk.StringVar()
        ttk.Entry(filter_bar, textvariable=self.county_var, width=16).grid(row=0, column=3, padx=4)

        ttk.Label(filter_bar, text="Species:").grid(row=0, column=4, sticky="w")
        self.species_var = tk.StringVar()
        species_list = [""] + data.list_distinct_species(self.conn)
        ttk.Combobox(filter_bar, textvariable=self.species_var, values=species_list, width=22).grid(
            row=0, column=5, padx=4
        )

        ttk.Label(filter_bar, text="Tier:").grid(row=0, column=6, sticky="w")
        self.tier_var = tk.StringVar(value="all")
        ttk.Combobox(
            filter_bar, textvariable=self.tier_var, values=list(data.TIER_CHOICES), width=16, state="readonly"
        ).grid(row=0, column=7, padx=4)

        ttk.Button(filter_bar, text="Search", command=self._run_search).grid(row=0, column=8, padx=8)

        # Results list
        columns = ("name", "county", "type", "tier", "temp", "temp_kind")
        self.results_tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
        for col, label, width in [
            ("name", "Waterbody", 220), ("county", "County", 110), ("type", "Type", 70),
            ("tier", "Presence tier", 130), ("temp", "Temp (°F)", 90), ("temp_kind", "Temp source", 160),
        ]:
            self.results_tree.heading(col, text=label)
            self.results_tree.column(col, width=width, anchor="w")
        self.results_tree.pack(fill="both", expand=False, padx=8, pady=4)
        self.results_tree.bind("<<TreeviewSelect>>", self._on_select_result)

        # Detail pane
        detail_frame = ttk.LabelFrame(frame, text="Detail (select a row above)", padding=6)
        detail_frame.pack(fill="both", expand=True, padx=8, pady=4)

        self.detail_meta = tk.Label(detail_frame, text="", justify="left", anchor="w", wraplength=1080)
        self.detail_meta.pack(fill="x")

        self.detail_text = tk.Text(detail_frame, wrap="word", height=18)
        self.detail_text.pack(fill="both", expand=True, pady=(6, 0))
        self.detail_text.configure(state="disabled")

        self._run_search()

    def _run_search(self):
        for row in self.results_tree.get_children():
            self.results_tree.delete(row)
        results = data.search_waterbodies(
            self.conn,
            name=self.name_var.get().strip() or None,
            county=self.county_var.get().strip() or None,
            species=self.species_var.get().strip() or None,
            tier=self.tier_var.get(),
        )
        self._results_cache = {}
        for r in results:
            temp_f = "-"
            if r["temp_value_c"] is not None:
                temp_f = f"{r['temp_value_c'] * 9 / 5 + 32:.1f}"
            temp_kind = "real" if r["temp_is_real"] else ("no_data" if r["temp_method"] == "no_data" else "proxy")
            key = (r["waterbody_name"], r["county"])
            self._results_cache[key] = r
            self.results_tree.insert(
                "", "end", iid=f"{r['waterbody_name']}|||{r['county']}",
                values=(r["waterbody_name"], r["county"], r["waterbody_type"], r["presence_tier"], temp_f, temp_kind),
            )

    def _on_select_result(self, _event):
        selection = self.results_tree.selection()
        if not selection:
            return
        name, county = selection[0].split("|||")
        detail = data.get_waterbody_detail(self.conn, name, county)
        if detail is None:
            return
        wb = detail["waterbody"]

        temp_note = "no real or proxy temperature data" if wb["temp_value_c"] is None else (
            f"{wb['temp_value_c'] * 9/5 + 32:.1f}°F / {wb['temp_value_c']:.1f}°C "
            f"({'REAL measurement' if wb['temp_is_real'] else 'air-temperature PROXY'}), "
            f"method={wb['temp_method']}, source={wb['temp_source']}, observed_at={wb['temp_observed_at']}"
        )
        meta_lines = [
            f"Waterbody: {wb['waterbody_name']}  |  County: {wb['county']}  |  Type: {wb['waterbody_type']}",
            f"Presence tier: {wb['presence_tier']}  |  Species count: {wb['species_count']}",
            f"Temperature: {temp_note}",
            f"Run timestamp (generated/last-updated): {fmt_timestamp(wb['run_timestamp'])}",
        ]
        self.detail_meta.configure(text="\n".join(meta_lines))

        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("end", "=== FULL NARRATIVE (exactly as generated) ===\n\n")
        self.detail_text.insert("end", wb["narrative_text"] + "\n\n")

        self.detail_text.insert("end", "=== SPECIES PREDICTIONS (exactly as stored) ===\n\n")
        for sp in detail["species_predictions"]:
            self.detail_text.insert("end", f"--- {sp['species']} ---\n")
            self.detail_text.insert("end", f"has_threshold_data={sp['has_threshold_data']}  any_match={sp['any_match']}\n")
            if sp["match_description"]:
                self.detail_text.insert("end", f"Match: {sp['match_description']}\n")
                self.detail_text.insert("end", f"Evidence quality: {sp['evidence_quality']}\n")
            self.detail_text.insert("end", f"river_caveat_applied={sp['river_caveat_applied']}  diel_active={sp['diel_active']}\n\n")
        self.detail_text.configure(state="disabled")

    # ------------------------------------------------------------------
    # Failures tab (Part 2)
    # ------------------------------------------------------------------
    def _build_failures_tab(self):
        frame = self.failures_tab
        filter_bar = ttk.Frame(frame, padding=8)
        filter_bar.pack(fill="x")

        ttk.Label(filter_bar, text="Waterbody:").grid(row=0, column=0, sticky="w")
        self.fail_waterbody_var = tk.StringVar()
        ttk.Entry(filter_bar, textvariable=self.fail_waterbody_var, width=22).grid(row=0, column=1, padx=4)

        ttk.Label(filter_bar, text="Species:").grid(row=0, column=2, sticky="w")
        self.fail_species_var = tk.StringVar()
        ttk.Entry(filter_bar, textvariable=self.fail_species_var, width=18).grid(row=0, column=3, padx=4)

        ttk.Label(filter_bar, text="Failure type:").grid(row=0, column=4, sticky="w")
        self.fail_type_var = tk.StringVar(value="all")
        fail_types = ["all"] + data.list_distinct_failure_types(self.conn)
        ttk.Combobox(filter_bar, textvariable=self.fail_type_var, values=fail_types, width=28, state="readonly").grid(
            row=0, column=5, padx=4
        )

        ttk.Button(filter_bar, text="Search", command=self._run_failure_search).grid(row=0, column=6, padx=8)

        columns = ("waterbody", "county", "species", "type", "message")
        self.failures_tree = ttk.Treeview(frame, columns=columns, show="headings", height=25)
        for col, label, width in [
            ("waterbody", "Waterbody", 200), ("county", "County", 110), ("species", "Species", 140),
            ("type", "Failure type", 180), ("message", "Error message", 420),
        ]:
            self.failures_tree.heading(col, text=label)
            self.failures_tree.column(col, width=width, anchor="w")
        self.failures_tree.pack(fill="both", expand=True, padx=8, pady=4)

        self._run_failure_search()

    def _run_failure_search(self):
        for row in self.failures_tree.get_children():
            self.failures_tree.delete(row)
        results = data.search_failures(
            self.conn,
            waterbody=self.fail_waterbody_var.get().strip() or None,
            species=self.fail_species_var.get().strip() or None,
            failure_type=self.fail_type_var.get(),
        )
        for r in results:
            self.failures_tree.insert(
                "", "end",
                values=(r["waterbody_name"], r["county"], r["species"] or "-", r["failure_type"], r["error_message"]),
            )

    # ------------------------------------------------------------------
    # Summary tab (Part 2)
    # ------------------------------------------------------------------
    def _build_summary_tab(self):
        frame = self.summary_tab
        counts = data.get_summary_counts(self.conn)

        text = tk.Text(frame, wrap="word", padx=10, pady=10)
        text.pack(fill="both", expand=True)

        lines = []
        lines.append(f"Total waterbody results: {counts['total_waterbodies']}")
        lines.append(f"Total species-waterbody predictions: {counts['total_species_predictions']}")
        lines.append(f"Total logged failures: {counts['total_failures']}")
        lines.append("")
        lines.append("By presence tier:")
        for k, v in counts["by_tier"].items():
            lines.append(f"  {k}: {v}")
        lines.append("")
        lines.append("By waterbody type:")
        for k, v in counts["by_type"].items():
            lines.append(f"  {k}: {v}")
        lines.append("")
        lines.append("By temperature source method:")
        for k, v in counts["by_temp_method"].items():
            lines.append(f"  {k}: {v}")
        lines.append("")
        lines.append("Species predictions by match outcome (0=no match at current temp, 1=matched):")
        for k, v in counts["species_any_match"].items():
            lines.append(f"  any_match={k}: {v}")
        lines.append("")
        lines.append("Failures by type:")
        for k, v in counts["by_failure_type"].items():
            lines.append(f"  {k}: {v}")
        lines.append("")
        lines.append("Compare these totals against docs/v1_full_run_report.md to sanity-check the UI.")

        text.insert("end", "\n".join(lines))
        text.configure(state="disabled")


def main():
    db_path = data.find_db_path()
    if db_path is None:
        # Show a minimal error window rather than crashing silently --
        # this can genuinely happen if someone moves the .exe outside the
        # repo without also bringing the data/ directory.
        root = tk.Tk()
        root.title("V1 Results Review — Error")
        tk.Label(
            root,
            text=(
                "Could not find data/v1/v1_full_run_results.db.\n\n"
                "Run analysis/v1_full_run.py first, or place this app inside the\n"
                "fishin project directory tree so it can find the database."
            ),
            padx=20, pady=20, justify="left",
        ).pack()
        root.mainloop()
        return

    app = App(db_path)
    app.mainloop()


if __name__ == "__main__":
    main()
