"""
Generate per-filelist detailed test duration dashboard.
Parses output.xml from NAS build folders to extract per-file test durations,
then produces an HTML dashboard with charts over time.
"""

import os
import re
import json
import statistics
import xml.etree.ElementTree as ET

NAS_DIR = r"Z:\master"
OUTPUT_DIR = r"C:\HEC\stats"

FILELISTS = ["Import_NX", "Import_STEP", "Import_CATIA_V5", "Import_JT", "Import_ACIS"]

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

FILELIST_COLORS = {
    "Import_NX": "#3498db",
    "Import_STEP": "#e74c3c",
    "Import_CATIA_V5": "#2ecc71",
    "Import_JT": "#9b59b6",
    "Import_ACIS": "#f39c12",
}

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


def collect_data():
    """Collect all data from NAS: {filelist: {platform: [{build_id, date, data}, ...]}}"""
    all_data = {}
    sorted_builds = sorted(DATE_MAP.keys(), key=lambda b: int(b.split("-")[0]))

    for filelist in FILELISTS:
        all_data[filelist] = {}
        for plat_name, plat_path in PLATFORMS.items():
            builds_data = []
            for build_id in sorted_builds:
                xml_path = os.path.join(NAS_DIR, build_id, "HEC_Report", plat_path, filelist, "output.xml")
                xml_path = xml_path.replace("/", os.sep)
                if not os.path.exists(xml_path):
                    continue
                data = parse_output_xml(xml_path)
                if data is None or data["total_count"] == 0:
                    continue
                builds_data.append({
                    "build_id": build_id,
                    "date": DATE_MAP[build_id],
                    "data": data,
                })
            if builds_data:
                all_data[filelist][plat_name] = builds_data
                print(f"  {filelist} / {plat_name}: {len(builds_data)} builds, "
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
    # Limit to top 50
    sorted_tests = sorted_tests[:50]

    return {
        "overview": overview,
        "charts_data": {t: charts_data[t] for t in sorted_tests},
        "sorted_tests": sorted_tests,
        "total_unique_tests": len(all_tests),
    }


def generate_html(all_data):
    """Generate the HTML dashboard."""
    # Pre-compute stats for all filelist/platform combos
    all_computed = {}
    for filelist in FILELISTS:
        all_computed[filelist] = {}
        for plat_name, builds_data in all_data.get(filelist, {}).items():
            all_computed[filelist][plat_name] = compute_test_stats(builds_data)

    html = """<!DOCTYPE html>
<html>
<head>
    <title>HEC Per-Filelist Detailed Test Durations</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1600px; margin: 0 auto; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #2c3e50; margin-top: 30px; }
        h3 { color: #34495e; margin-top: 10px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin: 12px 0; }
        .stat-card { background: white; border-radius: 8px; padding: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .stat-card .value { font-size: 20px; font-weight: bold; }
        .stat-card .label { font-size: 11px; color: #7f8c8d; margin-top: 3px; }
        .chart-container { background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 12px 0; }
        .test-section { border-left: 4px solid #3498db; padding-left: 12px; margin: 20px 0; }
        .test-stats { display: flex; gap: 15px; font-size: 12px; color: #555; margin: 4px 0 8px 0; flex-wrap: wrap; }
        .test-stats span { background: #ecf0f1; padding: 2px 7px; border-radius: 4px; }
        table { border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 15px 0; font-size: 12px; }
        th { color: white; padding: 8px 6px; text-align: left; }
        td { padding: 5px 6px; border-bottom: 1px solid #eee; }
        tr:hover { background: #f0f8ff; }
        .toc { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
               margin: 15px 0; columns: 3; column-gap: 15px; max-height: 400px; overflow-y: auto; }
        .toc a { display: block; padding: 1px 0; color: #2980b9; text-decoration: none; font-size: 12px; break-inside: avoid; }
        .toc a:hover { text-decoration: underline; }
        .filter-box { margin: 10px 0; }
        .filter-box input { padding: 7px 10px; width: 300px; border: 2px solid #bdc3c7; border-radius: 6px; font-size: 13px; }

        /* Filelist tabs (top level) */
        .fl-tab-bar { display: flex; gap: 0; margin: 20px 0 0 0; }
        .fl-tab-btn { padding: 10px 22px; border: none; cursor: pointer; font-size: 14px; font-weight: bold;
                      border-radius: 8px 8px 0 0; background: #ddd; color: #555; transition: all 0.2s; }
        .fl-tab-btn.active { color: white; box-shadow: 0 -2px 8px rgba(0,0,0,0.1); }
        .fl-tab-btn:hover:not(.active) { background: #ccc; }
        .fl-content { display: none; border-top: 3px solid #ddd; padding-top: 15px; }
        .fl-content.active { display: block; }

        /* Platform sub-tabs */
        .pl-tab-bar { display: flex; gap: 0; margin: 10px 0 0 0; }
        .pl-tab-btn { padding: 8px 18px; border: none; cursor: pointer; font-size: 13px; font-weight: 600;
                      border-radius: 6px 6px 0 0; background: #eee; color: #666; transition: all 0.2s; }
        .pl-tab-btn.active { color: white; }
        .pl-tab-btn:hover:not(.active) { background: #ddd; }
        .pl-content { display: none; border-top: 2px solid #eee; padding-top: 12px; }
        .pl-content.active { display: block; }
    </style>
</head>
<body>
<div class="container">
    <h1>HEC Per-Filelist Detailed Test Durations</h1>
    <p>Jan 1 to Apr 14, 2026 — Per-file durations within each filelist, across platforms.
       Top 50 slowest tests shown per filelist/platform.</p>

    <div class="fl-tab-bar">
"""

    # Filelist tabs
    active_filelists = [fl for fl in FILELISTS if fl in all_data and all_data[fl]]
    for i, fl in enumerate(active_filelists):
        active = " active" if i == 0 else ""
        color = FILELIST_COLORS.get(fl, "#3498db")
        style = f' style="background:{color};color:white;"' if i == 0 else ""
        fl_id = fl.lower()
        html += f'        <button class="fl-tab-btn{active}" data-fltab="{fl_id}" data-flcolor="{color}"{style} onclick="switchFilelistTab(\'{fl_id}\')">{fl.replace("_", " ")}</button>\n'

    html += "    </div>\n"

    # Per-filelist content
    for fi, fl in enumerate(active_filelists):
        fl_id = fl.lower()
        fl_color = FILELIST_COLORS.get(fl, "#3498db")
        active = " active" if fi == 0 else ""
        computed = all_computed[fl]
        active_platforms = [p for p in PLATFORMS if p in computed]

        html += f'\n    <div class="fl-content{active}" id="fl_{fl_id}">\n'
        html += f'        <div class="pl-tab-bar">\n'

        for pi, plat in enumerate(active_platforms):
            pactive = " active" if pi == 0 else ""
            pcolor = PLATFORM_COLORS.get(plat, "#3498db")
            pstyle = f' style="background:{pcolor};color:white;"' if pi == 0 else ""
            pid = f"{fl_id}_{plat.lower().replace(' ', '_')}"
            html += f'            <button class="pl-tab-btn{pactive}" data-pltab="{pid}" data-plcolor="{pcolor}" data-flid="{fl_id}"{pstyle} onclick="switchPlatformTab(\'{fl_id}\', \'{pid}\')">{plat}</button>\n'

        html += '        </div>\n'

        # Per-platform content
        for pi, plat in enumerate(active_platforms):
            pactive = " active" if pi == 0 else ""
            pcolor = PLATFORM_COLORS.get(plat, "#3498db")
            pid = f"{fl_id}_{plat.lower().replace(' ', '_')}"
            pdata = computed[plat]
            overview = pdata["overview"]
            charts_data = pdata["charts_data"]
            sorted_tests = pdata["sorted_tests"]

            # Compute overview stats
            durations = [o["total_elapsed"] for o in overview if o["total_elapsed"] > 0]
            if durations:
                mean_dur = round(statistics.mean(durations), 1)
                median_dur = round(statistics.median(durations), 1)
                min_dur = round(min(durations), 1)
                max_dur = round(max(durations), 1)
            else:
                mean_dur = median_dur = min_dur = max_dur = 0
            rates = [o["pass_rate"] for o in overview]
            mean_rate = round(statistics.mean(rates), 1) if rates else 0

            html += f'\n        <div class="pl-content{pactive}" id="pl_{pid}">\n'
            html += f'            <p>{len(overview)} builds with data. {pdata["total_unique_tests"]} unique test files. Showing top {len(sorted_tests)} by mean duration.</p>\n'

            # Stats cards
            html += f"""            <div class="stats-grid">
                <div class="stat-card"><div class="value" style="color:{pcolor}">{mean_dur}s</div><div class="label">Mean Total</div></div>
                <div class="stat-card"><div class="value" style="color:{pcolor}">{median_dur}s</div><div class="label">Median Total</div></div>
                <div class="stat-card"><div class="value" style="color:{pcolor}">{min_dur}s</div><div class="label">Min Total</div></div>
                <div class="stat-card"><div class="value" style="color:{pcolor}">{max_dur}s</div><div class="label">Max Total</div></div>
                <div class="stat-card"><div class="value" style="color:{pcolor}">{mean_rate}%</div><div class="label">Mean Pass Rate</div></div>
            </div>
"""
            # Overview chart
            html += f'            <div class="chart-container"><canvas id="ov_{pid}" height="60"></canvas></div>\n'

            # Filter + TOC
            html += f'            <h2>Per-File Test Charts</h2>\n'
            html += f'            <div class="filter-box"><input type="text" id="filt_{pid}" onkeyup="filterFileTests(\'{pid}\')" placeholder="Filter by filename..."></div>\n'
            html += f'            <div class="toc" id="toc_{pid}">\n'
            for ti, test_name in enumerate(sorted_tests):
                s = charts_data[test_name]
                html += f'                <a href="#{pid}_t{ti}">{s["basename"]} ({s["mean"]}s avg)</a>\n'
            html += '            </div>\n'

            # Per-test sections
            for ti, test_name in enumerate(sorted_tests):
                s = charts_data[test_name]
                html += f"""
            <div class="test-section ftb-{pid}" data-testname="{s['basename'].lower()}" id="{pid}_t{ti}" style="border-left-color:{pcolor}">
                <h3 title="{test_name}">{s['basename']}</h3>
                <div class="test-stats">
                    <span>Mean: <b>{s['mean']}s</b></span>
                    <span>Median: <b>{s['median']}s</b></span>
                    <span>Stdev: <b>{s['stdev']}s</b></span>
                    <span>Min: <b>{s['min']}s</b></span>
                    <span>Max: <b>{s['max']}s</b></span>
                    <span>Runs: <b>{len(s['data'])}</b></span>
                    <span>Valid: <b>{s['valid_count']}</b></span>
                </div>
                <div class="chart-container"><canvas id="ch_{pid}_{ti}" height="45"></canvas></div>
            </div>
"""

            # Summary table
            html += f"""
            <h2>Summary Table</h2>
            <table>
                <tr>
                    <th style="background:{pcolor}">File</th>
                    <th style="background:{pcolor}">Runs</th>
                    <th style="background:{pcolor}">Valid</th>
                    <th style="background:{pcolor}">Mean (s)</th>
                    <th style="background:{pcolor}">Median (s)</th>
                    <th style="background:{pcolor}">Stdev (s)</th>
                    <th style="background:{pcolor}">Min (s)</th>
                    <th style="background:{pcolor}">Max (s)</th>
                </tr>
"""
            for ti, test_name in enumerate(sorted_tests):
                s = charts_data[test_name]
                html += f'                <tr><td><a href="#{pid}_t{ti}" title="{test_name}">{s["basename"]}</a></td><td>{len(s["data"])}</td><td>{s["valid_count"]}</td><td>{s["mean"]}</td><td>{s["median"]}</td><td>{s["stdev"]}</td><td>{s["min"]}</td><td>{s["max"]}</td></tr>\n'
            html += '            </table>\n'
            html += '        </div>\n'  # pl-content

        html += '    </div>\n'  # fl-content

    # JavaScript: emit all platform data for lazy chart creation
    html += "\n<script>\n"
    html += "const allPlatData = {};\n"

    for fl in active_filelists:
        fl_id = fl.lower()
        computed = all_computed[fl]
        for plat in PLATFORMS:
            if plat not in computed:
                continue
            pid = f"{fl_id}_{plat.lower().replace(' ', '_')}"
            pdata = computed[plat]
            pcolor = PLATFORM_COLORS.get(plat, "#3498db")

            js_data = {
                "color": pcolor,
                "overview_dates": [o["date"] for o in pdata["overview"]],
                "overview_durations": [o["total_elapsed"] for o in pdata["overview"]],
                "overview_builds": [o["build_id"] for o in pdata["overview"]],
                "mean_dur": round(statistics.mean([o["total_elapsed"] for o in pdata["overview"] if o["total_elapsed"] > 0]) if pdata["overview"] else 0, 1),
                "sorted_tests": pdata["sorted_tests"],
                "charts_data": {t: {
                    "basename": pdata["charts_data"][t]["basename"],
                    "labels": pdata["charts_data"][t]["labels"],
                    "data": pdata["charts_data"][t]["data"],
                    "mean": pdata["charts_data"][t]["mean"],
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

    // Overview chart
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

    // Per-test charts
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

function switchFilelistTab(flId) {
    document.querySelectorAll('.fl-tab-btn').forEach(function(btn) {
        btn.classList.remove('active');
        btn.style.background = '#ddd'; btn.style.color = '#555';
    });
    const btn = document.querySelector('.fl-tab-btn[data-fltab="' + flId + '"]');
    btn.classList.add('active');
    btn.style.background = btn.dataset.flcolor; btn.style.color = 'white';

    document.querySelectorAll('.fl-content').forEach(el => { el.classList.remove('active'); });
    document.getElementById('fl_' + flId).classList.add('active');

    // Create charts for the first active platform sub-tab
    const firstPlBtn = document.querySelector('#fl_' + flId + ' .pl-tab-btn.active');
    if (firstPlBtn) createPlatCharts(firstPlBtn.dataset.pltab);
}

function switchPlatformTab(flId, pid) {
    document.querySelectorAll('#fl_' + flId + ' .pl-tab-btn').forEach(function(btn) {
        btn.classList.remove('active');
        btn.style.background = '#eee'; btn.style.color = '#666';
    });
    const btn = document.querySelector('.pl-tab-btn[data-pltab="' + pid + '"]');
    btn.classList.add('active');
    btn.style.background = btn.dataset.plcolor; btn.style.color = 'white';

    document.querySelectorAll('#fl_' + flId + ' .pl-content').forEach(el => { el.classList.remove('active'); });
    document.getElementById('pl_' + pid).classList.add('active');

    createPlatCharts(pid);
}

function filterFileTests(pid) {
    const filter = document.getElementById('filt_' + pid).value.toLowerCase();
    document.querySelectorAll('.ftb-' + pid).forEach(function(el) {
        el.style.display = el.getAttribute('data-testname').includes(filter) ? '' : 'none';
    });
    document.querySelectorAll('#toc_' + pid + ' a').forEach(function(a) {
        a.style.display = a.textContent.toLowerCase().includes(filter) ? '' : 'none';
    });
}

// Initialize first tab
(function() {
    const firstFlBtn = document.querySelector('.fl-tab-btn.active');
    if (!firstFlBtn) return;
    const flId = firstFlBtn.dataset.fltab;
    const firstPlBtn = document.querySelector('#fl_' + flId + ' .pl-tab-btn.active');
    if (firstPlBtn) createPlatCharts(firstPlBtn.dataset.pltab);
})();
</script>
</div>
</body>
</html>"""

    return html


if __name__ == "__main__":
    print("Collecting data from NAS...")
    all_data = collect_data()

    print("\nGenerating HTML dashboard...")
    html = generate_html(all_data)
    output_path = os.path.join(OUTPUT_DIR, "filelist_stats.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard written to: {output_path}")
