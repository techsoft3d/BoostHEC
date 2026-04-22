"""
Generate static PNG charts from HEC test data for mobile/offline viewing.

Outputs to docs/charts/ — high-DPI, phone-readable.
Run from repo root:  python analytics/generate_pngs.py

Charts produced:
  per_test_overview.png              — total run duration per platform, Jan-avr. 2026
  per_test_slowest_windows.png       — top-30 slowest tests (Windows VS2019)
  per_test_slowest_linux.png         — top-30 slowest tests (Linux GCC)
  per_test_slowest_mac.png           — top-30 slowest tests (Mac LLVM)
  filelist_overview.png              — total filelist duration over time (Windows)
  filelist_<NAME>_slowest.png        — top-25 slowest files per filelist, all platforms
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

FILELISTS = ["Import_NX", "Import_STEP", "Import_CATIA_V5", "Import_JT", "Import_ACIS"]

FILELIST_COLORS = {
    "Import_NX":       "#2980b9",
    "Import_STEP":     "#c0392b",
    "Import_CATIA_V5": "#27ae60",
    "Import_JT":       "#8e44ad",
    "Import_ACIS":     "#d35400",
}


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


def chart_filelist_overview():
    """5-panel timeline — total filelist duration (Windows) over time."""
    fig, axes = plt.subplots(len(FILELISTS), 1,
                             figsize=(13, 3.8 * len(FILELISTS)), sharex=False)
    fig.suptitle("HEC Per-Filelist Total Duration (Windows)  ·  Jan-avr. 2026",
                 fontsize=14, fontweight="bold", y=0.998)

    win_path = FILELIST_PLATFORMS["Windows"][0]

    for ax, fl in zip(axes, FILELISTS):
        color = FILELIST_COLORS[fl]
        builds = load_filelist_builds(fl, win_path)
        if not builds:
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    transform=ax.transAxes, color="#999", fontsize=11)
            ax.set_title(fl.replace("_", " "), fontsize=11,
                         color=color, fontweight="bold")
            continue

        dates  = [to_dt(b["date"]) for b in builds]
        totals = [b["data"]["total_elapsed"] for b in builds]
        mean   = statistics.mean(t for t in totals if t > 0)

        ax.fill_between(dates, totals, alpha=0.12, color=color)
        ax.plot(dates, totals, color=color, linewidth=2,
                marker="o", markersize=4, zorder=3)
        ax.axhline(mean, color="#e74c3c", linewidth=1.5,
                   linestyle="--", alpha=0.85, label=f"Mean {mean:.0f} s")
        ax.set_ylabel("Seconds", fontsize=10)
        ax.set_title(
            f"{fl.replace('_', ' ')}  ·  {len(builds)} builds  ·  mean {mean:.0f} s",
            fontsize=11, color=color, fontweight="bold", pad=3)
        ax.legend(fontsize=9, loc="upper right", framealpha=0.9)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=2))
        ax.tick_params(axis="x", labelsize=8.5, rotation=25)
        ax.tick_params(axis="y", labelsize=9)
        ax.set_xlim(min(dates), max(dates))
        ax.yaxis.grid(True, alpha=0.35)

    fig.tight_layout(rect=[0, 0, 1, 0.997])
    _save(fig, "filelist_overview.png")


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
    fl_color = FILELIST_COLORS.get(filelist, "#333")
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

    print("\n-- Per-test duration charts --")
    chart_per_test_overview()
    for pname, (prefix, color) in STAT_PLATFORMS.items():
        short = pname.split()[0]   # "Windows" / "Linux" / "Mac"
        chart_per_test_slowest(short, prefix, color)

    print("\n-- Per-filelist charts --")
    chart_filelist_overview()
    for fl in FILELISTS:
        chart_filelist_slowest(fl)

    pngs = sorted(OUT_DIR.glob("*.png"))
    total_kb = sum(p.stat().st_size for p in pngs) // 1024
    print(f"\nDone: {len(pngs)} PNGs in {OUT_DIR} ({total_kb} KB total)")
