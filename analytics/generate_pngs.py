"""
Generate static PNG charts from HEC test data for mobile/offline viewing.

Outputs to docs/charts/ — high-DPI, phone-readable.
Run from repo root:  python analytics/generate_pngs.py

All filelists are auto-discovered from the NAS at runtime (falls back to
the original 5 if the NAS is not mounted).

Charts produced:
  per_test_overview.png                    — total run duration per platform
  per_test_slowest_{windows,linux,mac}.png — top-30 slowest tests per platform
  filelist_overview_{import,export,...}.png — overview grids per filelist category
  filelist_<NAME>_slowest.png              — top-25 slowest files per filelist (all platforms)
"""

import os
import re
import statistics
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ── Paths ──────────────────────────────────────────────────────────────────
STATS_DIR = r"C:\HEC\stats"
NAS_DIR   = r"Z:\master"
OUT_DIR   = Path(__file__).parent.parent / "docs" / "charts"
DPI       = 180

# ── Full DATE_MAP ──────────────────────────────────────────────────────────
DATE_MAP = {
    # January 2026
    "5090-5c9a5dd3": "2026-01-01", "5091-5c9a5dd3": "2026-01-02",
    "5096-ffe0f6a7": "2026-01-06",
    "5107-1e458bcc": "2026-01-07", "5116-03ed1c0b": "2026-01-08",
    "5124-cc80c289": "2026-01-09", "5134-852886ef": "2026-01-11",
    "5134-852866ef": "2026-01-11",
    "5140-f5b8d9bf": "2026-01-13", "5152-f253c36f": "2026-01-14",
    "5160-a3694a51": "2026-01-15", "5165-4a60e93a": "2026-01-16",
    "5183-6fe7fa56": "2026-01-20", "5191-364f551d": "2026-01-21",
    "5202-ddfda666": "2026-01-22", "5212-e4fb05c0": "2026-01-23",
    "5222-d5cc3123": "2026-01-24", "5223-d5cc3123": "2026-01-25",
    "5224-d5cc3123": "2026-01-26", "5233-d84cf92d": "2026-01-27",
    "5242-a6e524fc": "2026-01-28", "5247-ac48c8fd": "2026-01-29",
    "5251-0dac79f1": "2026-01-30", "5261-e59b915a": "2026-01-31",
    # February 2026
    "5262-e59b915a": "2026-02-01", "5263-e59b915a": "2026-02-02",
    "5281-2dbb2f3c": "2026-02-03", "5293-d0add6f6": "2026-02-04",
    "5307-37cda420": "2026-02-05", "5313-5e340a3a": "2026-02-06",
    "5319-9babde2a": "2026-02-07", "5320-9babde2a": "2026-02-08",
    "5321-9babde2a": "2026-02-09", "5325-09b6ca6f": "2026-02-10",
    "5330-1d57118d": "2026-02-11", "5337-557bca27": "2026-02-12",
    "5351-f7abbbf8": "2026-02-14", "5352-f7abbbf8": "2026-02-15",
    "5353-f7abbbf8": "2026-02-16", "5357-a3f1cf85": "2026-02-17",
    "5360-749571a2": "2026-02-18", "5363-274708c8": "2026-02-19",
    "5369-0d41ea2a": "2026-02-20", "5378-8ec7ae81": "2026-02-21",
    "5379-8ec7ae81": "2026-02-22", "5380-8ec7ae81": "2026-02-23",
    "5388-21bd6ffe": "2026-02-24", "5395-b8611ab3": "2026-02-25",
    "5403-e5acbccc": "2026-02-26", "5413-4434d839": "2026-02-27",
    "5421-fdd4cce6": "2026-02-28",
    # March 2026
    "5422-fdd4cce6": "2026-03-01", "5423-fdd4cce6": "2026-03-02",
    "5440-c04fcbca": "2026-03-04", "5444-eac4708e": "2026-03-05",
    "5453-60f69ab4": "2026-03-06", "5464-377f3f4d": "2026-03-07",
    "5465-377f3f4d": "2026-03-08", "5466-377f3f4d": "2026-03-09",
    "5476-df941688": "2026-03-10", "5488-9c875682": "2026-03-11",
    "5493-7ec54d03": "2026-03-12",
    "5501-25756162": "2026-03-13", "5504-44ee87a3": "2026-03-14",
    "5505-44ee87a3": "2026-03-15", "5506-44ee87a3": "2026-03-16",
    "5517-8621619d": "2026-03-17", "5537-decb58e2": "2026-03-20",
    "5544-bdd23ded": "2026-03-23", "5545-bdd23ded": "2026-03-23",
    "5546-bdd23ded": "2026-03-23",
    # March 24 – April 14
    "5555-47bcd231": "2026-03-24", "5562-331c1306": "2026-03-25",
    "5572-8a74dff5": "2026-03-26", "5583-7915fa42": "2026-03-27",
    "5596-b35031ff": "2026-03-28", "5597-b35031ff": "2026-03-29",
    "5598-b35031ff": "2026-03-30", "5605-73676998": "2026-03-31",
    "5616-7299e68b": "2026-04-01", "5626-66d6736e": "2026-04-02",
    "5647-6f1c4c16": "2026-04-04",
    "5648-6f1c4c16": "2026-04-05", "5649-6f1c4c16": "2026-04-05",
    "5650-6f1c4c16": "2026-04-07",
    "5654-c566b818": "2026-04-09", "5665-01af7fef": "2026-04-09",
    "5675-9538c500": "2026-04-10",
    "5683-6950a04b": "2026-04-11", "5684-6950a04b": "2026-04-12",
    "5685-6950a04b": "2026-04-13", "5693-5b14060a": "2026-04-14",
    # avril 2026
    "5697-d9fa86b8": "2026-04-15",
    "5702-5a14d16f": "2026-04-16",
    "5713-7cc05f39": "2026-04-18",
    "5714-7cc05f39": "2026-04-19",
    "5715-7cc05f39": "2026-04-20",
    "5718-e0587709": "2026-04-21",
    "5728-c6865d81": "2026-04-22",
    # avril 2026
    "5732-c9277c52": "2026-04-23",
}

SORTED_BUILDS = sorted(DATE_MAP, key=lambda b: int(b.split("-")[0]))

# ── Platform / filelist config ─────────────────────────────────────────────
STAT_PLATFORMS = {
    "Windows VS2019": ("Windows_VS2019_report",          "#2980b9"),
    "Linux GCC":      ("Linux_GCC_GLIBC212_DWG_report",  "#e67e22"),
    "Mac LLVM":       ("Mac_LLVM_report",                "#8e44ad"),
}

FILELIST_PLATFORMS = {
    "Windows":   ("Windows/x86_64/HEC",          "#2980b9"),
    "Linux":     ("Linux/x86_64/with_oda/HEC",   "#e67e22"),
    "Mac armv8": ("Macos/armv8/HEC",              "#8e44ad"),
    "Mac x86_64":("Macos/x86_64/HEC",            "#16a085"),
}

# 36-color palette — assigned by filelist name hash for stable, distinct colors
_COLOR_POOL = [
    "#2980b9", "#16a085", "#27ae60", "#8e44ad", "#e67e22", "#e74c3c", "#f39c12", "#1abc9c",
    "#d35400", "#2471a3", "#117a65", "#1e8449", "#6c3483", "#ca6f1e", "#922b21", "#b7950b",
    "#148f77", "#76448a", "#1f618d", "#a93226", "#935116", "#7d3c98", "#d4ac0d", "#884ea0",
    "#1a9482", "#196f3d", "#5b2c6f", "#7b241c", "#17a589", "#1d8348", "#145a32", "#4a235a",
    "#0e6655", "#29b06e", "#7f8c8d", "#c0392b",
]


def _color_for(fl):
    """Return a stable, distinct color for a filelist name."""
    h = sum(ord(c) * (i + 1) for i, c in enumerate(fl))
    return _COLOR_POOL[h % len(_COLOR_POOL)]


def discover_filelists():
    """Auto-discover all filelists with output.xml on the Windows platform from the NAS."""
    sorted_builds = sorted(DATE_MAP, key=lambda b: int(b.split("-")[0]), reverse=True)
    plat_path = os.path.join("Windows", "x86_64", "HEC")
    for build_id in sorted_builds:
        hec_dir = os.path.join(NAS_DIR, build_id, "HEC_Report", plat_path)
        if not os.path.isdir(hec_dir):
            continue
        result = sorted(
            d for d in os.listdir(hec_dir)
            if os.path.isdir(os.path.join(hec_dir, d)) and
               os.path.exists(os.path.join(hec_dir, d, "output.xml"))
        )
        if result:
            return result
    # Fallback to original five filelists if NAS not accessible
    return ["Import_NX", "Import_STEP", "Import_CATIA_V5", "Import_JT", "Import_ACIS"]


def to_dt(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")


# ═══════════════════════════════════════════════════════════════════════════
# Part 1 — Per-test stats  (reads HTML reports from C:\HEC\stats)
# ═══════════════════════════════════════════════════════════════════════════

def parse_report(filepath):
    with open(filepath, encoding="utf-8", errors="replace") as f:
        content = f.read()
    m = re.search(r'it took <b>(\d+):(\d+):(\d+) machine-hours', content)
    duration_hours = None
    if m:
        h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
        duration_hours = h + mi / 60 + s / 3600
    m = re.search(r'(\d+) green tests over (\d+) tests', content)
    total_tests = int(m.group(2)) if m else None
    test_data = {}
    for row in re.findall(r'<tr[^>]*>\s*(.*?)\s*</tr>', content, re.DOTALL):
        nm = re.search(r'<td><b>([^<]+)</b></td>', row)
        dm = re.search(r'<td>(\d+) s</td>', row)
        if nm and dm:
            test_data[nm.group(1)] = int(dm.group(1))
    return {"duration_hours": duration_hours, "total_tests": total_tests,
            "test_data": test_data}


def load_stat_platform(prefix):
    """Return sorted list of (date, duration_hours, test_data) for full runs only."""
    rows = []
    pfx = prefix + "_"
    for fname in sorted(os.listdir(STATS_DIR)):
        if not fname.startswith(pfx) or not fname.endswith(".html"):
            continue
        m = re.match(re.escape(pfx) + r"(.+)\.html", fname)
        if not m:
            continue
        build_id = m.group(1)
        if build_id not in DATE_MAP:
            continue
        d = parse_report(os.path.join(STATS_DIR, fname))
        if d["total_tests"] and d["total_tests"] >= 10 and d["duration_hours"]:
            rows.append((DATE_MAP[build_id], d["duration_hours"], d["test_data"],
                         int(build_id.split("-")[0])))
    rows.sort(key=lambda r: r[3])
    return rows


def chart_per_test_overview():
    """3-panel timeline — total run duration per platform."""
    fig, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=False)
    fig.suptitle("HEC Nightly Run Duration  ·  Jan 1 - avr. 22, 2026",
                 fontsize=15, fontweight="bold", y=0.99)

    for ax, (pname, (prefix, color)) in zip(axes, STAT_PLATFORMS.items()):
        rows = load_stat_platform(prefix)
        if not rows:
            ax.text(0.5, 0.5, f"No data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=12, color="#999")
            ax.set_title(pname, fontsize=12, color=color, fontweight="bold")
            continue

        dates = [to_dt(r[0]) for r in rows]
        durs  = [r[1] for r in rows]
        mean  = statistics.mean(durs)

        ax.fill_between(dates, durs, alpha=0.12, color=color)
        ax.plot(dates, durs, color=color, linewidth=2,
                marker="o", markersize=4, zorder=3)
        ax.axhline(mean, color="#e74c3c", linewidth=1.5,
                   linestyle="--", alpha=0.85, label=f"Mean {mean:.1f} h")

        ax.set_ylabel("Machine-hours", fontsize=11)
        ax.set_title(f"{pname}  ({len(rows)} builds)", fontsize=12,
                     color=color, fontweight="bold", pad=4)
        ax.legend(fontsize=10, loc="upper right", framealpha=0.9)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2))
        ax.tick_params(axis="x", labelsize=9, rotation=25)
        ax.tick_params(axis="y", labelsize=9)
        ax.set_xlim(min(dates), max(dates))
        ax.yaxis.grid(True, alpha=0.35)

    fig.tight_layout(rect=[0, 0, 1, 0.98])
    _save(fig, "per_test_overview.png")


def chart_per_test_slowest(short_name, prefix, color, top_n=30):
    """Horizontal bar chart — top N slowest tests by mean duration."""
    rows = load_stat_platform(prefix)
    if not rows:
        print(f"  [{short_name}] no data, skipped.")
        return

    # Aggregate per-test means across all builds
    accum = {}
    for _, _, test_data, _ in rows:
        for name, dur in test_data.items():
            if dur > 0:
                accum.setdefault(name, []).append(dur)

    means = {n: statistics.mean(v) for n, v in accum.items() if len(v) >= 3}
    if not means:
        return

    top = sorted(means.items(), key=lambda x: x[1], reverse=True)[:top_n]
    labels = [t[0] for t in top]
    values = [t[1] for t in top]
    max_v  = max(values)

    fig_h = max(6, len(labels) * 0.38 + 2.0)
    fig, ax = plt.subplots(figsize=(13, fig_h))
    bars = ax.barh(range(len(labels)), values, color=color,
                   alpha=0.82, edgecolor="white", linewidth=0.5)

    for bar, val in zip(bars, values):
        ax.text(val + max_v * 0.006, bar.get_y() + bar.get_height() / 2,
                f"{val:.0f} s", va="center", ha="left", fontsize=9, color="#333")

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel("Mean Duration (seconds)", fontsize=11)
    ax.set_title(f"{short_name}  ·  Top {len(labels)} Slowest Tests  ·  Jan-avr. 2026",
                 fontsize=13, fontweight="bold", color=color)
    ax.xaxis.grid(True, alpha=0.35)
    ax.set_axisbelow(True)

    fig.tight_layout()
    _save(fig, f"per_test_slowest_{short_name.lower().replace(' ', '_')}.png")


# ═══════════════════════════════════════════════════════════════════════════
# Part 2 — Per-filelist stats  (reads output.xml from Z:\master)
# ═══════════════════════════════════════════════════════════════════════════

def parse_output_xml(filepath):
    try:
        tree = ET.parse(filepath)
    except (ET.ParseError, FileNotFoundError, OSError):
        return None
    root = tree.getroot()
    tests = []
    for el in root.iter("test"):
        st = el.find("status")
        if st is None:
            continue
        try:
            elapsed = float(st.get("elapsed", "0"))
        except ValueError:
            elapsed = 0.0
        name = el.get("name", "")
        basename = name.replace("\\", "/").rsplit("/", 1)[-1]
        tests.append({"name": name, "basename": basename,
                      "elapsed": elapsed, "status": st.get("status", "")})
    suite = root.find(".//suite")
    total = 0.0
    if suite is not None:
        ss = suite.find("status")
        if ss is not None:
            try:
                total = float(ss.get("elapsed", "0"))
            except ValueError:
                total = sum(t["elapsed"] for t in tests)
    return {"tests": tests, "total_elapsed": total, "count": len(tests)}


def load_filelist_builds(filelist, plat_path):
    builds = []
    for build_id in SORTED_BUILDS:
        xml = os.path.join(NAS_DIR, build_id, "HEC_Report",
                           plat_path, filelist, "output.xml")
        data = parse_output_xml(xml)
        if data and data["count"] > 0:
            builds.append({"build_id": build_id,
                           "date": DATE_MAP[build_id], "data": data})
    return builds


def chart_filelist_overview(filelists, title, outfile, ncols=4):
    """Grid overview — total filelist duration (Windows) over time, ncols per row."""
    win_path = FILELIST_PLATFORMS["Windows"][0]

    # Pre-load only filelists that have data
    fl_builds = []
    for fl in filelists:
        builds = load_filelist_builds(fl, win_path)
        if builds:
            fl_builds.append((fl, builds))

    if not fl_builds:
        print(f"  [{outfile}] no data, skipped.")
        return

    n      = len(fl_builds)
    nrows  = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(4.5 * ncols, 2.6 * nrows),
                             sharex=False)
    # Normalize axes to a flat list
    if nrows == 1 and ncols == 1:
        flat_axes = [axes]
    elif nrows == 1:
        flat_axes = list(axes)
    elif ncols == 1:
        flat_axes = list(axes)
    else:
        flat_axes = [ax for row in axes for ax in row]

    fig.suptitle(title, fontsize=13, fontweight="bold", y=1.001)

    for i, (fl, builds) in enumerate(fl_builds):
        ax    = flat_axes[i]
        color = _color_for(fl)
        dates  = [to_dt(b["date"]) for b in builds]
        totals = [b["data"]["total_elapsed"] for b in builds]
        nonzero = [t for t in totals if t > 0]
        mean = statistics.mean(nonzero) if nonzero else 0

        ax.fill_between(dates, totals, alpha=0.14, color=color)
        ax.plot(dates, totals, color=color, linewidth=1.5,
                marker="o", markersize=2.5, zorder=3)
        if mean > 0:
            ax.axhline(mean, color="#e74c3c", linewidth=1,
                       linestyle="--", alpha=0.8)
        ax.set_title(fl.replace("_", " "), fontsize=8,
                     color=color, fontweight="bold", pad=2)
        ax.tick_params(axis="x", labelsize=6, rotation=20)
        ax.tick_params(axis="y", labelsize=6)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        if dates:
            ax.set_xlim(min(dates), max(dates))
        ax.yaxis.grid(True, alpha=0.3)
        ax.set_ylabel("s", fontsize=7)

    # Hide unused panels
    for i in range(len(fl_builds), len(flat_axes)):
        flat_axes[i].set_visible(False)

    fig.tight_layout(rect=[0, 0, 1, 0.998])
    _save(fig, outfile)


def chart_filelist_slowest(filelist, top_n=25):
    """Grouped bar chart — top N slowest files per platform."""
    plat_means = {}
    for pname, (plat_path, _) in FILELIST_PLATFORMS.items():
        builds = load_filelist_builds(filelist, plat_path)
        if not builds:
            continue
        accum = {}
        for b in builds:
            for t in b["data"]["tests"]:
                if t["elapsed"] > 0:
                    accum.setdefault(t["basename"], []).append(t["elapsed"])
        plat_means[pname] = {n: statistics.mean(v)
                             for n, v in accum.items() if len(v) >= 3}

    if not plat_means:
        print(f"  [{filelist}] no data, skipped.")
        return

    all_names = set()
    for pm in plat_means.values():
        all_names.update(pm)

    # Rank by maximum mean across platforms
    ranked = sorted(all_names,
                    key=lambda n: max(pm.get(n, 0) for pm in plat_means.values()),
                    reverse=True)[:top_n]

    plat_names = list(plat_means.keys())
    n_plats    = len(plat_names)
    n_tests    = len(ranked)
    width      = 0.75 / n_plats

    fig_h = max(7, n_tests * 0.42 + 2.5)
    fig, ax = plt.subplots(figsize=(13, fig_h))

    for i, pname in enumerate(plat_names):
        pm     = plat_means[pname]
        color  = FILELIST_PLATFORMS[pname][1]
        vals   = [pm.get(n, 0) for n in ranked]
        offset = (i - n_plats / 2 + 0.5) * width
        ax.barh([xi + offset for xi in range(n_tests)], vals,
                height=width * 0.88, color=color, label=pname,
                alpha=0.85, edgecolor="white", linewidth=0.4)

    ax.set_yticks(range(n_tests))
    ax.set_yticklabels(ranked, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlabel("Mean Duration (seconds)", fontsize=11)
    fl_color = _color_for(filelist)
    ax.set_title(
        f"{filelist.replace('_', ' ')}  ·  Top {n_tests} Slowest Files  ·  Jan-avr. 2026",
        fontsize=12, fontweight="bold", color=fl_color)
    ax.legend(fontsize=10, loc="lower right", framealpha=0.9)
    ax.xaxis.grid(True, alpha=0.35)
    ax.set_axisbelow(True)

    fig.tight_layout()
    fl_safe = filelist.lower().replace("_", "-")
    _save(fig, f"filelist_{fl_safe}_slowest.png")


# ── Helpers ────────────────────────────────────────────────────────────────

def _save(fig, name):
    path = OUT_DIR / name
    fig.savefig(path, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    size_kb = path.stat().st_size // 1024
    print(f"  {name}  ({size_kb} KB)")


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    print("\n-- Discovering filelists from NAS --")
    all_filelists = discover_filelists()
    print(f"  {len(all_filelists)} filelists found")

    # Group by prefix category
    import_fls       = [fl for fl in all_filelists if fl.startswith("Import_")]
    export_fls       = [fl for fl in all_filelists if fl.startswith("Export_")]
    tess_fls         = [fl for fl in all_filelists if fl.startswith("Tessellation_")]
    other_fls        = [fl for fl in all_filelists
                        if not fl.startswith(("Import_", "Export_", "Tessellation_"))]

    print("\n-- Per-test duration charts --")
    chart_per_test_overview()
    for pname, (prefix, color) in STAT_PLATFORMS.items():
        short = pname.split()[0]   # "Windows" / "Linux" / "Mac"
        chart_per_test_slowest(short, prefix, color)

    print("\n-- Per-filelist overview charts (by category) --")
    for cat_name, cat_fls in [
        ("Import",       import_fls),
        ("Export",       export_fls),
        ("Tessellation", tess_fls),
        ("Other",        other_fls),
    ]:
        if not cat_fls:
            continue
        title  = (f"HEC {cat_name} Filelists -- Total Duration (Windows)"
                  f"  .  Jan-avr. 2026")
        fname  = f"filelist_overview_{cat_name.lower()}.png"
        print(f"  {cat_name}: {len(cat_fls)} filelists -> {fname}")
        chart_filelist_overview(cat_fls, title, fname)

    print("\n-- Per-filelist slowest-files charts --")
    for fl in all_filelists:
        chart_filelist_slowest(fl)

    pngs = sorted(OUT_DIR.glob("*.png"))
    total_kb = sum(p.stat().st_size for p in pngs) // 1024
    print(f"\nDone: {len(pngs)} PNGs in {OUT_DIR} ({total_kb} KB total)")
