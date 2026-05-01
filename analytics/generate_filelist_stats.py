"""
Generate per-filelist detailed test duration dashboard.
Parses output.xml from NAS build folders to extract per-file test durations,
then produces an HTML dashboard with charts over time.

All filelists are auto-discovered from the NAS at runtime (falls back to
the original 5 if the NAS is not mounted).  NAS reads are parallelised with
a ThreadPoolExecutor to keep total runtime manageable.
"""

import os
import json
import statistics
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

NAS_DIR = r"Z:\master"
OUTPUT_DIR = r"C:\HEC\stats"

PLATFORMS = {
    "Windows": "Windows/x86_64/HEC",
    "Linux": "Linux/x86_64/with_oda/HEC",
    "Mac armv8": "Macos/armv8/HEC",
    "Mac x86_64": "Macos/x86_64/HEC",
}

PLATFORM_COLORS = {
    "Windows": "#3498db",
    "Linux": "#e67e22",
    "Mac armv8": "#9b59b6",
    "Mac x86_64": "#1abc9c",
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


def _category(fl):
    """Return a broad category label for a filelist name."""
    for prefix in ("Import", "Export", "Tessellation", "Dump", "ProgressBar"):
        if fl.startswith(prefix + "_"):
            return prefix
    return "Other"


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
            print(f"  Discovered {len(result)} filelists from build {build_id}")
            return result
    print("  Warning: NAS not accessible; using fallback filelist")
    return ["Import_NX", "Import_STEP", "Import_CATIA_V5", "Import_JT", "Import_ACIS"]

# Build-ID to date mapping (same as generate_stats.py)
DATE_MAP = {
    "5090-5c9a5dd3": "2026-01-01", "5091-5c9a5dd3": "2026-01-02",
    "5096-ffe0f6a7": "2026-01-06",
    "5107-1e458bcc": "2026-01-07", "5116-03ed1c0b": "2026-01-08",
    "5124-cc80c289": "2026-01-09", "5134-852866ef": "2026-01-11",
    "5140-f5b8d9bf": "2026-01-13", "5152-f253c36f": "2026-01-14",
    "5160-a3694a51": "2026-01-15", "5165-4a60e93a": "2026-01-16",
    "5183-6fe7fa56": "2026-01-20", "5191-364f551d": "2026-01-21",
    "5202-ddfda666": "2026-01-22", "5212-e4fb05c0": "2026-01-23",
    "5222-d5cc3123": "2026-01-24", "5223-d5cc3123": "2026-01-25",
    "5224-d5cc3123": "2026-01-26", "5233-d84cf92d": "2026-01-27",
    "5242-a6e524fc": "2026-01-28", "5247-ac48c8fd": "2026-01-29",
    "5251-0dac79f1": "2026-01-30", "5261-e59b915a": "2026-01-31",
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
    # March 24 – March 31
    "5555-47bcd231": "2026-03-24", "5562-331c1306": "2026-03-25",
    "5572-8a74dff5": "2026-03-26", "5583-7915fa42": "2026-03-27",
    "5596-b35031ff": "2026-03-28", "5597-b35031ff": "2026-03-29",
    "5598-b35031ff": "2026-03-30", "5605-73676998": "2026-03-31",
    # April 2026
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
    # avril 2026
    "5742-68be1c03": "2026-04-24",
    # avril 2026
    "5748-786368a9": "2026-04-25",
    "5749-786368a9": "2026-04-26",
    "5750-786368a9": "2026-04-27",
    # avril 2026
    "5754-8d979b4a": "2026-04-28",
    # avril 2026
    "5762-ece5e566": "2026-04-29",
    # avril 2026
    "5771-d4f2122a": "2026-04-30",
    # mai 2026
    "5779-3f2df2fc": "2026-05-01",
}


def parse_output_xml(filepath):
    """Parse Robot Framework output.xml and return per-test data."""
    try:
        tree = ET.parse(filepath)
    except (ET.ParseError, FileNotFoundError):
        return None

    root = tree.getroot()
    tests = []
    for test_el in root.iter("test"):
        name = test_el.get("name", "")
        status_el = test_el.find("status")
        if status_el is None:
            continue
        elapsed_str = status_el.get("elapsed", "0")
        try:
            elapsed = float(elapsed_str)
        except ValueError:
            elapsed = 0.0
        status = status_el.get("status", "UNKNOWN")
        tests.append({
            "name": name,
            "basename": name.rsplit("\\", 1)[-1].rsplit("/", 1)[-1] if name else name,
            "elapsed": elapsed,
            "status": status,
        })

    # Total suite elapsed
    suite_el = root.find(".//suite")
    total_elapsed = 0.0
    if suite_el is not None:
        suite_status = suite_el.find("status")
        if suite_status is not None:
            try:
                total_elapsed = float(suite_status.get("elapsed", "0"))
            except ValueError:
                total_elapsed = sum(t["elapsed"] for t in tests)

    return {
        "tests": tests,
        "total_elapsed": total_elapsed,
        "total_count": len(tests),
        "pass_count": sum(1 for t in tests if t["status"] == "PASS"),
        "fail_count": sum(1 for t in tests if t["status"] == "FAIL"),
    }


def _load_combo(sorted_builds, filelist, plat_name, plat_path):
    """Load all build data for one (filelist, platform) pair — runs in a thread."""
    builds_data = []
    for build_id in sorted_builds:
        xml_path = os.path.join(NAS_DIR, build_id, "HEC_Report",
                                plat_path.replace("/", os.sep), filelist, "output.xml")
        if not os.path.exists(xml_path):
            continue
        data = parse_output_xml(xml_path)
        if data is None or data["total_count"] == 0:
            continue
        builds_data.append({"build_id": build_id,
                             "date": DATE_MAP[build_id],
                             "data": data})
    return filelist, plat_name, builds_data


def collect_data(filelists):
    """Collect all data from NAS using parallel reads.
    Returns {filelist: {platform: [{build_id, date, data}, ...]}}
    """
    sorted_builds = sorted(DATE_MAP, key=lambda b: int(b.split("-")[0]))
    all_data = {fl: {} for fl in filelists}

    tasks = [(sorted_builds, fl, pname, ppath)
             for fl in filelists
             for pname, ppath in PLATFORMS.items()]

    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(_load_combo, *t) for t in tasks]
        for fut in as_completed(futures):
            fl, pname, builds_data = fut.result()
            if builds_data:
                all_data[fl][pname] = builds_data
                print(f"  {fl} / {pname}: {len(builds_data)} builds, "
                      f"{builds_data[-1]['data']['total_count']} tests in latest")

    return all_data


def compute_test_stats(builds_data):
    """Compute per-test time series and stats for one filelist+platform combo."""
    # Collect all unique test names (full path as key)
    all_tests = set()
    for bd in builds_data:
        for t in bd["data"]["tests"]:
            all_tests.add(t["name"])

    # Build time series per test
    test_series = {}
    for test_name in sorted(all_tests):
        series = []
        for bd in builds_data:
            for t in bd["data"]["tests"]:
                if t["name"] == test_name:
                    series.append((bd["date"], t["elapsed"], t["status"]))
                    break
        test_series[test_name] = series

    # Compute stats
    test_stats = {}
    for test_name, series in test_series.items():
        durations = [d for _, d, _ in series if d > 0]
        if not durations:
            continue
        basename = test_name.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]
        if len(durations) >= 2:
            test_stats[test_name] = {
                "basename": basename,
                "mean": round(statistics.mean(durations), 2),
                "median": round(statistics.median(durations), 2),
                "stdev": round(statistics.stdev(durations), 2),
                "min": round(min(durations), 2),
                "max": round(max(durations), 2),
                "count": len(durations),
            }
        else:
            test_stats[test_name] = {
                "basename": basename,
                "mean": round(durations[0], 2), "median": round(durations[0], 2),
                "stdev": 0, "min": round(durations[0], 2), "max": round(durations[0], 2),
                "count": 1,
            }

    # Overview: total duration per build
    overview = []
    for bd in builds_data:
        overview.append({
            "date": bd["date"],
            "build_id": bd["build_id"],
            "total_elapsed": round(bd["data"]["total_elapsed"], 1),
            "total_tests": bd["data"]["total_count"],
            "pass_rate": round(100 * bd["data"]["pass_count"] / bd["data"]["total_count"], 1)
                         if bd["data"]["total_count"] > 0 else 0,
        })

    # Charts data: only tests with >= 2 data points, sorted by mean desc
    # Limit to top 50 slowest tests per filelist/platform to keep dashboard manageable
    charts_data = {}
    for test_name, series in test_series.items():
        if len(series) < 2:
            continue
        if test_name not in test_stats:
            continue
        valid_count = sum(1 for s in series if s[1] > 0)
        charts_data[test_name] = {
            "basename": test_stats[test_name]["basename"],
            "labels": [s[0] for s in series],
            "data": [round(s[1], 2) for s in series],
            "statuses": [s[2] for s in series],
            "mean": test_stats[test_name]["mean"],
            "median": test_stats[test_name]["median"],
            "stdev": test_stats[test_name]["stdev"],
            "min": test_stats[test_name]["min"],
            "max": test_stats[test_name]["max"],
            "valid_count": valid_count,
        }

    sorted_tests = sorted(charts_data.keys(), key=lambda t: charts_data[t]["mean"], reverse=True)
    # Limit to top 25 to keep HTML size manageable across many filelists
    sorted_tests = sorted_tests[:25]

    return {
        "overview": overview,
        "charts_data": {t: charts_data[t] for t in sorted_tests},
        "sorted_tests": sorted_tests,
        "total_unique_tests": len(all_tests),
    }


def generate_html(all_data, filelists):
    """Generate the HTML dashboard with a searchable sidebar for all filelists."""
    # Pre-compute stats for every filelist/platform combo
    all_computed = {}
    for fl in filelists:
        all_computed[fl] = {}
        for plat_name, builds_data in all_data.get(fl, {}).items():
            all_computed[fl][plat_name] = compute_test_stats(builds_data)

    active_filelists = [fl for fl in filelists if all_computed.get(fl)]

    # Group filelists by category for the sidebar
    cats_order = ["Import", "Export", "Tessellation", "Dump", "ProgressBar", "Other"]
    cats = {c: [] for c in cats_order}
    for fl in active_filelists:
        cats[_category(fl)].append(fl)

    first_fl = active_filelists[0] if active_filelists else None

    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>HEC Per-Filelist Detailed Test Durations</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, sans-serif; margin: 0; background: #f5f5f5; }
        /* Layout */
        .layout { display: flex; align-items: flex-start; min-height: 100vh; }
        .sidebar { width: 230px; min-width: 230px; background: white; border-right: 2px solid #dde;
                   padding: 10px; position: sticky; top: 0; max-height: 100vh; overflow-y: auto; flex-shrink: 0; }
        .main { flex: 1; padding: 16px 20px; min-width: 0; }
        /* Sidebar elements */
        .sidebar h2 { font-size: 13px; color: #2c3e50; margin: 0 0 8px 0; border-bottom: 2px solid #3498db; padding-bottom: 6px; }
        #flSearch { width: 100%; padding: 6px 8px; border: 1.5px solid #bdc3c7; border-radius: 5px;
                    font-size: 12px; margin-bottom: 8px; }
        .cat-header { padding: 5px 4px; cursor: pointer; font-size: 11px; font-weight: bold;
                      color: #7f8c8d; border-bottom: 1px solid #eee; margin-top: 6px;
                      user-select: none; }
        .cat-header:hover { color: #2c3e50; }
        .cat-items { overflow: hidden; }
        .sb-item { display: block; width: 100%; padding: 4px 8px; border: none; background: none;
                   cursor: pointer; font-size: 11.5px; color: #34495e; text-align: left;
                   border-radius: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .sb-item:hover { background: #ecf0f1; }
        .sb-item.active { font-weight: bold; color: white !important; }
        /* Main content */
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 8px; margin-top: 0; font-size: 20px; }
        h2 { color: #2c3e50; margin-top: 22px; font-size: 16px; }
        h3 { color: #34495e; margin-top: 8px; font-size: 14px; }
        .fl-content { display: none; }
        .fl-content.active { display: block; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; margin: 10px 0; }
        .stat-card { background: white; border-radius: 7px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .stat-card .value { font-size: 18px; font-weight: bold; }
        .stat-card .label  { font-size: 10px; color: #7f8c8d; margin-top: 2px; }
        .chart-container { background: white; border-radius: 7px; padding: 13px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 10px 0; }
        .test-section { border-left: 4px solid #3498db; padding-left: 11px; margin: 16px 0; }
        .test-stats { display: flex; gap: 10px; font-size: 11px; color: #555; margin: 3px 0 7px 0; flex-wrap: wrap; }
        .test-stats span { background: #ecf0f1; padding: 2px 6px; border-radius: 3px; }
        table { border-collapse: collapse; width: 100%; background: white; border-radius: 7px; overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 12px 0; font-size: 11.5px; }
        th { color: white; padding: 7px 6px; text-align: left; }
        td { padding: 4px 6px; border-bottom: 1px solid #eee; }
        tr:hover { background: #f0f8ff; }
        .toc { background: white; padding: 12px; border-radius: 7px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
               margin: 12px 0; columns: 3; column-gap: 12px; max-height: 320px; overflow-y: auto; }
        .toc a { display: block; padding: 1px 0; color: #2980b9; text-decoration: none; font-size: 11px; break-inside: avoid; }
        .toc a:hover { text-decoration: underline; }
        .filter-box { margin: 8px 0; }
        .filter-box input { padding: 6px 9px; width: 280px; border: 2px solid #bdc3c7; border-radius: 5px; font-size: 12px; }
        /* Platform sub-tabs */
        .pl-tab-bar { display: flex; gap: 0; margin: 10px 0 0 0; flex-wrap: wrap; }
        .pl-tab-btn { padding: 7px 16px; border: none; cursor: pointer; font-size: 12px; font-weight: 600;
                      border-radius: 5px 5px 0 0; background: #eee; color: #666; transition: all 0.15s; }
        .pl-tab-btn.active { color: white; }
        .pl-tab-btn:hover:not(.active) { background: #ddd; }
        .pl-content { display: none; border-top: 2px solid #eee; padding-top: 10px; }
        .pl-content.active { display: block; }
    </style>
</head>
<body>
<div class="layout">
  <div class="sidebar">
    <h2>HEC Filelists</h2>
    <input type="text" id="flSearch" placeholder="Search..." oninput="filterSidebar()">
    <div id="sidebar-list">
"""

    # Sidebar categories
    for cat in cats_order:
        items = cats[cat]
        if not items:
            continue
        cat_id = cat.lower()
        html += f'      <div class="cat-header" onclick="toggleCat(\'{cat_id}\')">\u25bc {cat} ({len(items)})</div>\n'
        html += f'      <div class="cat-items" id="cat-{cat_id}">\n'
        for fl in items:
            fl_id = fl.lower()
            color = _color_for(fl)
            is_first = (fl == first_fl)
            active_cls = " active" if is_first else ""
            bg_style = f' style="background:{color}"' if is_first else ""
            html += (f'        <button class="sb-item{active_cls}" data-fltab="{fl_id}" '
                     f'data-color="{color}" data-name="{fl.lower()}"{bg_style} '
                     f'onclick="showFilelist(\'{fl_id}\')">{fl.replace("_", " ")}</button>\n')
        html += '      </div>\n'

    html += """    </div>
  </div>
  <div class="main">
    <h1>HEC Per-Filelist Detailed Test Durations</h1>
    <p>Jan 1 to mai 1, 2026 &mdash; Per-file durations within each filelist, across platforms.
       Top 25 slowest tests shown per filelist/platform.</p>
"""

    # Per-filelist content panels
    for fi, fl in enumerate(active_filelists):
        fl_id    = fl.lower()
        fl_color = _color_for(fl)
        active   = " active" if fi == 0 else ""
        computed = all_computed[fl]
        active_platforms = [p for p in PLATFORMS if p in computed]

        html += f'\n    <div class="fl-content{active}" id="fl_{fl_id}">\n'
        html += f'      <div class="pl-tab-bar">\n'

        for pi, plat in enumerate(active_platforms):
            pactive = " active" if pi == 0 else ""
            pcolor  = PLATFORM_COLORS.get(plat, "#3498db")
            pstyle  = f' style="background:{pcolor};color:white;"' if pi == 0 else ""
            pid     = f"{fl_id}_{plat.lower().replace(' ', '_')}"
            html += (f'        <button class="pl-tab-btn{pactive}" data-pltab="{pid}" '
                     f'data-plcolor="{pcolor}" data-flid="{fl_id}"{pstyle} '
                     f'onclick="switchPlatTab(\'{fl_id}\', \'{pid}\')">{plat}</button>\n')

        html += '      </div>\n'

        for pi, plat in enumerate(active_platforms):
            pactive     = " active" if pi == 0 else ""
            pcolor      = PLATFORM_COLORS.get(plat, "#3498db")
            pid         = f"{fl_id}_{plat.lower().replace(' ', '_')}"
            pdata       = computed[plat]
            overview    = pdata["overview"]
            charts_data = pdata["charts_data"]
            sorted_tests = pdata["sorted_tests"]

            durations = [o["total_elapsed"] for o in overview if o["total_elapsed"] > 0]
            mean_dur   = round(statistics.mean(durations), 1)   if durations else 0
            median_dur = round(statistics.median(durations), 1) if durations else 0
            min_dur    = round(min(durations), 1)               if durations else 0
            max_dur    = round(max(durations), 1)               if durations else 0
            rates      = [o["pass_rate"] for o in overview]
            mean_rate  = round(statistics.mean(rates), 1)       if rates else 0

            html += f'\n      <div class="pl-content{pactive}" id="pl_{pid}">\n'
            html += (f'        <p>{len(overview)} builds &bull; '
                     f'{pdata["total_unique_tests"]} unique files &bull; '
                     f'top {len(sorted_tests)} shown by mean duration.</p>\n')
            html += f"""        <div class="stats-grid">
          <div class="stat-card"><div class="value" style="color:{pcolor}">{mean_dur}s</div><div class="label">Mean Total</div></div>
          <div class="stat-card"><div class="value" style="color:{pcolor}">{median_dur}s</div><div class="label">Median Total</div></div>
          <div class="stat-card"><div class="value" style="color:{pcolor}">{min_dur}s</div><div class="label">Min Total</div></div>
          <div class="stat-card"><div class="value" style="color:{pcolor}">{max_dur}s</div><div class="label">Max Total</div></div>
          <div class="stat-card"><div class="value" style="color:{pcolor}">{mean_rate}%</div><div class="label">Mean Pass Rate</div></div>
        </div>
"""
            html += f'        <div class="chart-container"><canvas id="ov_{pid}" height="55"></canvas></div>\n'
            html += f'        <h2>Per-File Test Charts</h2>\n'
            html += (f'        <div class="filter-box"><input type="text" id="filt_{pid}" '
                     f'onkeyup="filterFileTests(\'{pid}\')" placeholder="Filter by filename..."></div>\n')
            html += f'        <div class="toc" id="toc_{pid}">\n'
            for ti, tn in enumerate(sorted_tests):
                s = charts_data[tn]
                html += f'          <a href="#{pid}_t{ti}">{s["basename"]} ({s["mean"]}s avg)</a>\n'
            html += '        </div>\n'

            for ti, tn in enumerate(sorted_tests):
                s = charts_data[tn]
                html += f"""
      <div class="test-section ftb-{pid}" data-testname="{s['basename'].lower()}" id="{pid}_t{ti}" style="border-left-color:{pcolor}">
        <h3 title="{tn}">{s['basename']}</h3>
        <div class="test-stats">
          <span>Mean: <b>{s['mean']}s</b></span><span>Median: <b>{s['median']}s</b></span>
          <span>Stdev: <b>{s['stdev']}s</b></span><span>Min: <b>{s['min']}s</b></span>
          <span>Max: <b>{s['max']}s</b></span><span>Runs: <b>{len(s['data'])}</b></span>
          <span>Valid: <b>{s['valid_count']}</b></span>
        </div>
        <div class="chart-container"><canvas id="ch_{pid}_{ti}" height="42"></canvas></div>
      </div>
"""

            html += f"""
      <h2>Summary Table</h2>
      <table>
        <tr>
          <th style="background:{pcolor}">File</th><th style="background:{pcolor}">Runs</th>
          <th style="background:{pcolor}">Valid</th><th style="background:{pcolor}">Mean (s)</th>
          <th style="background:{pcolor}">Median (s)</th><th style="background:{pcolor}">Stdev (s)</th>
          <th style="background:{pcolor}">Min (s)</th><th style="background:{pcolor}">Max (s)</th>
        </tr>
"""
            for ti, tn in enumerate(sorted_tests):
                s = charts_data[tn]
                html += (f'        <tr><td><a href="#{pid}_t{ti}" title="{tn}">{s["basename"]}</a></td>'
                         f'<td>{len(s["data"])}</td><td>{s["valid_count"]}</td>'
                         f'<td>{s["mean"]}</td><td>{s["median"]}</td><td>{s["stdev"]}</td>'
                         f'<td>{s["min"]}</td><td>{s["max"]}</td></tr>\n')
            html += '      </table>\n'
            html += '      </div>\n'  # pl-content

        html += '    </div>\n'  # fl-content

    # Embed all JSON data for lazy chart rendering
    html += "\n<script>\nconst allPlatData = {};\n"

    for fl in active_filelists:
        fl_id    = fl.lower()
        computed = all_computed[fl]
        for plat in PLATFORMS:
            if plat not in computed:
                continue
            pid    = f"{fl_id}_{plat.lower().replace(' ', '_')}"
            pdata  = computed[plat]
            pcolor = PLATFORM_COLORS.get(plat, "#3498db")
            durs   = [o["total_elapsed"] for o in pdata["overview"] if o["total_elapsed"] > 0]
            js_data = {
                "color": pcolor,
                "overview_dates":     [o["date"]            for o in pdata["overview"]],
                "overview_durations": [o["total_elapsed"]   for o in pdata["overview"]],
                "overview_builds":    [o["build_id"]        for o in pdata["overview"]],
                "mean_dur": round(statistics.mean(durs), 1) if durs else 0,
                "sorted_tests": pdata["sorted_tests"],
                "charts_data": {t: {
                    "basename": pdata["charts_data"][t]["basename"],
                    "labels":   pdata["charts_data"][t]["labels"],
                    "data":     pdata["charts_data"][t]["data"],
                    "mean":     pdata["charts_data"][t]["mean"],
                } for t in pdata["sorted_tests"]},
            }
            html += f"allPlatData['{pid}'] = {json.dumps(js_data)};\n"

    html += """
let chartsCreated = {};

function createPlatCharts(pid) {
    if (chartsCreated[pid]) return;
    chartsCreated[pid] = true;
    const pd = allPlatData[pid];
    if (!pd) return;

    new Chart(document.getElementById('ov_' + pid), {
        type: 'line',
        data: {
            labels: pd.overview_dates,
            datasets: [
                { label: 'Total Duration (s)', data: pd.overview_durations,
                  borderColor: pd.color, backgroundColor: pd.color + '1a',
                  fill: true, tension: 0.3, pointRadius: 3, pointHoverRadius: 6 },
                { label: 'Mean (' + pd.mean_dur + 's)',
                  data: Array(pd.overview_dates.length).fill(pd.mean_dur),
                  borderColor: '#e74c3c', borderDash: [8, 4], pointRadius: 0, fill: false, borderWidth: 1.5 }
            ]
        },
        options: {
            responsive: true,
            plugins: { tooltip: { callbacks: {
                afterLabel: function(ctx) { return 'Build: ' + pd.overview_builds[ctx.dataIndex]; }
            }}},
            scales: { y: { title: { display: true, text: 'Seconds' } } }
        }
    });

    const colors = ['#3498db','#e74c3c','#2ecc71','#9b59b6','#f39c12','#1abc9c','#e67e22','#34495e'];
    pd.sorted_tests.forEach(function(testName, i) {
        const d = pd.charts_data[testName];
        new Chart(document.getElementById('ch_' + pid + '_' + i), {
            type: 'line',
            data: {
                labels: d.labels,
                datasets: [
                    { label: d.basename + ' (s)', data: d.data,
                      borderColor: colors[i % 8], backgroundColor: 'rgba(52,152,219,0.05)',
                      fill: true, tension: 0.2, pointRadius: 3, pointHoverRadius: 5 },
                    { label: 'Mean (' + d.mean + 's)',
                      data: Array(d.labels.length).fill(d.mean),
                      borderColor: '#e74c3c', borderDash: [6, 3], pointRadius: 0, fill: false, borderWidth: 1 }
                ]
            },
            options: {
                responsive: true,
                scales: { y: { title: { display: true, text: 'Seconds' }, beginAtZero: true } },
                plugins: { legend: { display: true, position: 'top' } }
            }
        });
    });
}

function showFilelist(flId) {
    document.querySelectorAll('.fl-content').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.sb-item').forEach(el => {
        el.classList.remove('active'); el.style.background = ''; el.style.color = '';
    });
    document.getElementById('fl_' + flId).style.display = 'block';
    const btn = document.querySelector('.sb-item[data-fltab="' + flId + '"]');
    if (btn) { btn.classList.add('active'); btn.style.background = btn.dataset.color; btn.style.color = 'white'; }
    const firstPl = document.querySelector('#fl_' + flId + ' .pl-tab-btn.active');
    if (firstPl) createPlatCharts(firstPl.dataset.pltab);
}

function switchPlatTab(flId, pid) {
    document.querySelectorAll('#fl_' + flId + ' .pl-tab-btn').forEach(function(btn) {
        btn.classList.remove('active'); btn.style.background = '#eee'; btn.style.color = '#666';
    });
    const btn = document.querySelector('.pl-tab-btn[data-pltab="' + pid + '"]');
    btn.classList.add('active'); btn.style.background = btn.dataset.plcolor; btn.style.color = 'white';
    document.querySelectorAll('#fl_' + flId + ' .pl-content').forEach(el => el.style.display = 'none');
    document.getElementById('pl_' + pid).style.display = 'block';
    createPlatCharts(pid);
}

function filterSidebar() {
    const q = document.getElementById('flSearch').value.toLowerCase();
    document.querySelectorAll('.sb-item').forEach(el => {
        el.style.display = el.dataset.name.includes(q) ? '' : 'none';
    });
    document.querySelectorAll('.cat-items').forEach(sec => {
        const any = [...sec.querySelectorAll('.sb-item')].some(el => el.style.display !== 'none');
        sec.style.display = any ? '' : 'none';
        const hdr = sec.previousElementSibling;
        if (hdr) hdr.style.display = any ? '' : 'none';
    });
}

function toggleCat(cat) {
    const el = document.getElementById('cat-' + cat);
    el.style.display = el.style.display === 'none' ? '' : 'none';
    const hdr = el.previousElementSibling;
    if (hdr) hdr.textContent = hdr.textContent.replace(/^[\\u25bc\\u25ba]/, el.style.display === 'none' ? '\\u25ba' : '\\u25bc');
}

function filterFileTests(pid) {
    const f = document.getElementById('filt_' + pid).value.toLowerCase();
    document.querySelectorAll('.ftb-' + pid).forEach(el => {
        el.style.display = el.getAttribute('data-testname').includes(f) ? '' : 'none';
    });
    document.querySelectorAll('#toc_' + pid + ' a').forEach(a => {
        a.style.display = a.textContent.toLowerCase().includes(f) ? '' : 'none';
    });
}

// Init: render charts for the first visible filelist/platform
(function() {
    const firstPl = document.querySelector('.fl-content.active .pl-tab-btn.active');
    if (firstPl) createPlatCharts(firstPl.dataset.pltab);
})();
</script>
  </div><!-- .main -->
</div><!-- .layout -->
</body>
</html>"""

    return html


if __name__ == "__main__":
    print("Discovering filelists from NAS...")
    filelists = discover_filelists()

    print(f"\nCollecting data from NAS ({len(filelists)} filelists x {len(PLATFORMS)} platforms)...")
    all_data = collect_data(filelists)

    print("\nGenerating HTML dashboard...")
    html = generate_html(all_data, filelists)
    output_path = os.path.join(OUTPUT_DIR, "filelist_stats.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard written to: {output_path}")
