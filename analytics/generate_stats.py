"""
Generate statistics dashboard for HEC nightly test reports.
Produces an HTML report with per-test duration charts over time.
Supports multiple platforms: Windows VS2019, Linux GCC, Mac LLVM.
"""

import os
import re
import json
import statistics

STATS_DIR = r"C:\HEC\stats"

PLATFORMS = {
    "Windows VS2019": "Windows_VS2019_report",
    "Linux GCC": "Linux_GCC_GLIBC212_DWG_report",
    "Mac LLVM": "Mac_LLVM_report",
}

# Build-ID to date mapping (from NAS file timestamps)
DATE_MAP = {
    # January 2026
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
}


def parse_report(filepath):
    """Extract summary data and per-test durations from a single HTML report."""
    with open(filepath, encoding="utf-8", errors="replace") as f:
        content = f.read()

    data = {}

    # Total duration
    m = re.search(r'it took <b>(\d+):(\d+):(\d+) machine-hours', content)
    if m:
        h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
        data["duration_hours"] = h + mi / 60 + s / 3600
        data["duration_str"] = f"{h}:{mi:02d}:{s:02d}"
    else:
        data["duration_hours"] = None
        data["duration_str"] = None

    # Green tests / total tests
    m = re.search(r'(\d+) green tests over (\d+) tests', content)
    if m:
        data["green_tests"] = int(m.group(1))
        data["total_tests"] = int(m.group(2))
    else:
        data["green_tests"] = None
        data["total_tests"] = None

    # Success rate
    m = re.search(r'([\d.]+)% test success rate', content)
    data["success_rate"] = float(m.group(1)) if m else None

    # Failures count
    m = re.search(r'<b>(\d+) failure', content)
    data["failures"] = int(m.group(1)) if m else 0

    # Per-test: extract (test_name, duration_seconds) pairs
    test_data = {}
    rows = re.findall(r'<tr[^>]*>\s*(.*?)\s*</tr>', content, re.DOTALL)
    for row in rows:
        name_m = re.search(r'<td><b>([^<]+)</b></td>', row)
        dur_m = re.search(r'<td>(\d+) s</td>', row)
        if name_m and dur_m:
            test_data[name_m.group(1)] = int(dur_m.group(1))
    data["test_data"] = test_data

    return data


def get_reports(file_prefix):
    """Scan directory for reports matching prefix and return sorted list with metadata."""
    reports = []
    prefix = file_prefix + "_"
    for fname in sorted(os.listdir(STATS_DIR)):
        if not fname.startswith(prefix) or not fname.endswith(".html"):
            continue
        m = re.match(re.escape(prefix) + r'(.+)\.html', fname)
        if not m:
            continue
        build_id = m.group(1)
        if build_id not in DATE_MAP:
            continue
        filepath = os.path.join(STATS_DIR, fname)
        data = parse_report(filepath)
        data["build_id"] = build_id
        data["date"] = DATE_MAP[build_id]
        data["filename"] = fname
        reports.append(data)

    reports.sort(key=lambda r: int(r["build_id"].split("-")[0]))
    return reports


def compute_platform_data(reports):
    """Compute all statistics for a single platform's reports."""
    all_test_names = set()
    for r in reports:
        all_test_names.update(r["test_data"].keys())
    all_test_names = sorted(all_test_names)

    test_series = {}
    for test_name in all_test_names:
        series = []
        for r in reports:
            if test_name in r["test_data"]:
                series.append((r["date"], r["test_data"][test_name]))
        test_series[test_name] = series

    test_stats = {}
    for test_name, series in test_series.items():
        durations = [d for _, d in series if d > 0]
        if len(durations) >= 2:
            test_stats[test_name] = {
                "mean": statistics.mean(durations),
                "median": statistics.median(durations),
                "stdev": statistics.stdev(durations),
                "min": min(durations),
                "max": max(durations),
                "count": len(durations),
            }
        elif len(durations) == 1:
            test_stats[test_name] = {
                "mean": durations[0], "median": durations[0],
                "stdev": 0, "min": durations[0], "max": durations[0],
                "count": 1,
            }

    normal_runs = [r for r in reports if r["total_tests"] and r["total_tests"] >= 2]
    valid_durations = [r["duration_hours"] for r in normal_runs if r["duration_hours"] and r["duration_hours"] > 0]
    if valid_durations:
        mean_dur = statistics.mean(valid_durations)
        median_dur = statistics.median(valid_durations)
        min_dur = min(valid_durations)
        max_dur = max(valid_durations)
    else:
        mean_dur = median_dur = min_dur = max_dur = 0

    valid_rates = [r["success_rate"] for r in normal_runs if r["success_rate"] is not None]
    mean_rate = statistics.mean(valid_rates) if valid_rates else 0

    overview_dates = [r["date"] for r in normal_runs]
    overview_durations = [round(r["duration_hours"], 2) if r["duration_hours"] else None for r in normal_runs]
    overview_builds = [r["build_id"] for r in normal_runs]

    charts_data = {}
    for test_name in all_test_names:
        series = test_series[test_name]
        if len(series) < 2:
            continue
        if test_name not in test_stats:
            continue
        valid_count = sum(1 for s in series if s[1] > 0)
        charts_data[test_name] = {
            "labels": [s[0] for s in series],
            "data": [s[1] for s in series],
            "mean": round(test_stats[test_name]["mean"], 1),
            "median": round(test_stats[test_name]["median"], 1),
            "stdev": round(test_stats[test_name]["stdev"], 1),
            "min": test_stats[test_name]["min"],
            "max": test_stats[test_name]["max"],
            "valid_count": valid_count,
        }

    sorted_tests = sorted(charts_data.keys(), key=lambda t: charts_data[t]["mean"], reverse=True)

    return {
        "reports": reports,
        "normal_runs": normal_runs,
        "mean_dur": mean_dur, "median_dur": median_dur,
        "min_dur": min_dur, "max_dur": max_dur,
        "mean_rate": mean_rate,
        "overview_dates": overview_dates,
        "overview_durations": overview_durations,
        "overview_builds": overview_builds,
        "charts_data": charts_data,
        "sorted_tests": sorted_tests,
    }


def generate_html(all_platform_data):
    """Generate HTML dashboard with tabs for each platform."""
    platform_names = list(all_platform_data.keys())
    platform_ids = [name.lower().replace(" ", "_") for name in platform_names]
    tab_colors = {"windows_vs2019": "#3498db", "linux_gcc": "#e67e22", "mac_llvm": "#9b59b6"}

    html = """<!DOCTYPE html>
<html>
<head>
    <title>HEC Per-Test Duration Statistics - All Platforms</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1600px; margin: 0 auto; }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #2c3e50; margin-top: 40px; }
        h3 { color: #34495e; margin-top: 10px; cursor: pointer; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 15px 0; }
        .stat-card { background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .stat-card .value { font-size: 24px; font-weight: bold; color: #3498db; }
        .stat-card .label { font-size: 12px; color: #7f8c8d; margin-top: 4px; }
        .chart-container { background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 15px 0; }
        .test-section { border-left: 4px solid #3498db; padding-left: 15px; margin: 25px 0; }
        .test-stats { display: flex; gap: 20px; font-size: 13px; color: #555; margin: 5px 0 10px 0; flex-wrap: wrap; }
        .test-stats span { background: #ecf0f1; padding: 3px 8px; border-radius: 4px; }
        table { border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 20px 0; }
        th { background: #3498db; color: white; padding: 10px 8px; text-align: left; font-size: 13px; }
        td { padding: 6px 8px; border-bottom: 1px solid #eee; font-size: 13px; }
        tr:hover { background: #f0f8ff; }
        .toc { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 20px 0; columns: 3; column-gap: 20px; }
        .toc a { display: block; padding: 2px 0; color: #2980b9; text-decoration: none; font-size: 13px; break-inside: avoid; }
        .toc a:hover { text-decoration: underline; }
        .filter-box { margin: 15px 0; }
        .filter-box input { padding: 8px 12px; width: 300px; border: 2px solid #bdc3c7; border-radius: 6px; font-size: 14px; }
        .tab-bar { display: flex; gap: 0; margin: 20px 0 0 0; }
        .tab-btn { padding: 12px 28px; border: none; cursor: pointer; font-size: 15px; font-weight: bold;
                   border-radius: 8px 8px 0 0; background: #ddd; color: #555; transition: all 0.2s; }
        .tab-btn.active { color: white; box-shadow: 0 -2px 8px rgba(0,0,0,0.1); position: relative; z-index: 1; }
        .tab-btn:hover:not(.active) { background: #ccc; }
        .platform-content { display: none; border-top: 3px solid #ddd; padding-top: 20px; }
        .platform-content.active { display: block; }
    </style>
</head>
<body>
<div class="container">
    <h1>HEC Per-Test Duration Statistics</h1>
    <p>Jan 1 to avr. 22, 2026 - All Platforms</p>

    <div class="tab-bar">
"""
    for i, (pname, pid) in enumerate(zip(platform_names, platform_ids)):
        active = " active" if i == 0 else ""
        color = tab_colors.get(pid, "#3498db")
        style = f' style="background: {color}; color: white;"' if i == 0 else ""
        html += f'        <button class="tab-btn{active}" data-tab="{pid}" data-color="{color}"{style} onclick="switchTab(\'{pid}\')">{pname}</button>\n'

    html += "    </div>\n"

    # Generate content for each platform
    global_chart_idx = 0
    platform_chart_ranges = {}

    for pi, (pname, pid) in enumerate(zip(platform_names, platform_ids)):
        pdata = all_platform_data[pname]
        reports = pdata["reports"]
        normal_runs = pdata["normal_runs"]
        mean_dur = pdata["mean_dur"]
        median_dur = pdata["median_dur"]
        min_dur = pdata["min_dur"]
        max_dur = pdata["max_dur"]
        mean_rate = pdata["mean_rate"]
        charts_data = pdata["charts_data"]
        sorted_tests = pdata["sorted_tests"]

        active = " active" if pi == 0 else ""
        color = tab_colors.get(pid, "#3498db")
        chart_start = global_chart_idx

        html += f"""
    <div class="platform-content{active}" id="tab_{pid}">
        <p>Analysis of <b>{len(reports)}</b> builds.
           {len(normal_runs)} with test data, {len(reports) - len(normal_runs)} empty/partial.
           {len(charts_data)} tests tracked over time.</p>

        <h2>Overall Total Duration (machine-hours)</h2>
        <div class="stats-grid">
            <div class="stat-card"><div class="value" style="color:{color}">{mean_dur:.1f}h</div><div class="label">Mean</div></div>
            <div class="stat-card"><div class="value" style="color:{color}">{median_dur:.1f}h</div><div class="label">Median</div></div>
            <div class="stat-card"><div class="value" style="color:{color}">{min_dur:.1f}h</div><div class="label">Min</div></div>
            <div class="stat-card"><div class="value" style="color:{color}">{max_dur:.1f}h</div><div class="label">Max</div></div>
            <div class="stat-card"><div class="value" style="color:{color}">{mean_rate:.1f}%</div><div class="label">Mean Success Rate</div></div>
        </div>
        <div class="chart-container">
            <canvas id="overview_{pid}" height="70"></canvas>
        </div>

        <h2>Per-Test Duration Charts</h2>
        <div class="filter-box">
            <input type="text" id="filter_{pid}" onkeyup="filterTests('{pid}')" placeholder="Filter tests by name...">
        </div>

        <div class="toc" id="toc_{pid}">
"""
        for i, test_name in enumerate(sorted_tests):
            s = charts_data[test_name]
            html += f'            <a href="#{pid}_test_{i}">{test_name} ({s["mean"]}s avg)</a>\n'

        html += "        </div>\n"

        for i, test_name in enumerate(sorted_tests):
            s = charts_data[test_name]
            chart_id = f"{pid}_chart_{i}"
            html += f"""
        <div class="test-section test-block-{pid}" data-testname="{test_name.lower()}" id="{pid}_test_{i}" style="border-left-color: {color}">
            <h3>{test_name}</h3>
            <div class="test-stats">
                <span>Mean: <b>{s['mean']}s</b></span>
                <span>Median: <b>{s['median']}s</b></span>
                <span>Stdev: <b>{s['stdev']}s</b></span>
                <span>Min: <b>{s['min']}s</b></span>
                <span>Max: <b>{s['max']}s</b></span>
                <span>Runs: <b>{len(s['data'])}</b></span>
                <span>Valid: <b>{s['valid_count']}</b></span>
            </div>
            <div class="chart-container">
                <canvas id="{chart_id}" height="50"></canvas>
            </div>
        </div>
"""
            global_chart_idx += 1

        # Summary table
        html += f"""
        <h2>Per-Test Summary Table</h2>
        <table>
            <tr>
                <th style="background:{color}">Test Name</th>
                <th style="background:{color}">Runs</th>
                <th style="background:{color}">Valid</th>
                <th style="background:{color}">Mean (s)</th>
                <th style="background:{color}">Median (s)</th>
                <th style="background:{color}">Stdev (s)</th>
                <th style="background:{color}">Min (s)</th>
                <th style="background:{color}">Max (s)</th>
            </tr>
"""
        for i, test_name in enumerate(sorted_tests):
            s = charts_data[test_name]
            html += f"""            <tr>
                <td><a href="#{pid}_test_{i}">{test_name}</a></td>
                <td>{len(s['data'])}</td>
                <td>{s['valid_count']}</td>
                <td>{s['mean']}</td>
                <td>{s['median']}</td>
                <td>{s['stdev']}</td>
                <td>{s['min']}</td>
                <td>{s['max']}</td>
            </tr>
"""
        html += "        </table>\n"
        html += "    </div>\n"

        platform_chart_ranges[pid] = (chart_start, global_chart_idx)

    # JavaScript
    html += "\n<script>\n"

    # Emit per-platform data
    html += "const platformData = {};\n"
    for pname, pid in zip(platform_names, platform_ids):
        pdata = all_platform_data[pname]
        html += f"platformData['{pid}'] = {json.dumps({'overview_dates': pdata['overview_dates'], 'overview_durations': pdata['overview_durations'], 'overview_builds': pdata['overview_builds'], 'mean_dur': round(pdata['mean_dur'], 2), 'charts_data': {t: pdata['charts_data'][t] for t in pdata['sorted_tests']}, 'sorted_tests': pdata['sorted_tests']})};\n"

    html += f"const tabColors = {json.dumps(tab_colors)};\n"
    html += f"const platformIds = {json.dumps(platform_ids)};\n"

    html += """
let chartsCreated = {};

function createCharts(pid) {
    if (chartsCreated[pid]) return;
    chartsCreated[pid] = true;
    const pd = platformData[pid];
    const color = tabColors[pid] || '#3498db';

    // Overview chart
    new Chart(document.getElementById('overview_' + pid), {
        type: 'line',
        data: {
            labels: pd.overview_dates,
            datasets: [
                {
                    label: 'Total Duration (hours)',
                    data: pd.overview_durations,
                    borderColor: color,
                    backgroundColor: color + '1a',
                    fill: true, tension: 0.3, pointRadius: 4, pointHoverRadius: 7,
                },
                {
                    label: 'Mean (' + pd.mean_dur.toFixed(1) + 'h)',
                    data: Array(pd.overview_dates.length).fill(pd.mean_dur),
                    borderColor: '#e74c3c', borderDash: [10, 5], pointRadius: 0, fill: false,
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: {
                    callbacks: {
                        afterLabel: function(ctx) { return 'Build: ' + pd.overview_builds[ctx.dataIndex]; }
                    }
                }
            },
            scales: { y: { title: { display: true, text: 'Machine-Hours' } } }
        }
    });

    // Per-test charts
    const lineColors = ['#3498db','#e74c3c','#2ecc71','#9b59b6','#f39c12','#1abc9c','#e67e22','#34495e'];
    pd.sorted_tests.forEach(function(testName, i) {
        const d = pd.charts_data[testName];
        new Chart(document.getElementById(pid + '_chart_' + i), {
            type: 'line',
            data: {
                labels: d.labels,
                datasets: [
                    {
                        label: testName + ' (seconds)',
                        data: d.data,
                        borderColor: lineColors[i % 8],
                        backgroundColor: 'rgba(52, 152, 219, 0.05)',
                        fill: true, tension: 0.2, pointRadius: 3, pointHoverRadius: 6,
                    },
                    {
                        label: 'Mean (' + d.mean + 's)',
                        data: Array(d.labels.length).fill(d.mean),
                        borderColor: '#e74c3c', borderDash: [8, 4], pointRadius: 0, fill: false, borderWidth: 1.5,
                    }
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

function switchTab(pid) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(function(btn) {
        btn.classList.remove('active');
        btn.style.background = '#ddd';
        btn.style.color = '#555';
    });
    const activeBtn = document.querySelector('.tab-btn[data-tab="' + pid + '"]');
    activeBtn.classList.add('active');
    activeBtn.style.background = activeBtn.dataset.color;
    activeBtn.style.color = 'white';

    // Update tab border color
    document.querySelectorAll('.platform-content').forEach(function(el) {
        el.classList.remove('active');
        el.style.borderTopColor = '#ddd';
    });
    const activeTab = document.getElementById('tab_' + pid);
    activeTab.classList.add('active');
    activeTab.style.borderTopColor = activeBtn.dataset.color;

    // Lazy-create charts on first view
    createCharts(pid);
}

function filterTests(pid) {
    const filter = document.getElementById('filter_' + pid).value.toLowerCase();
    document.querySelectorAll('.test-block-' + pid).forEach(function(el) {
        const name = el.getAttribute('data-testname');
        el.style.display = name.includes(filter) ? '' : 'none';
    });
    document.querySelectorAll('#toc_' + pid + ' a').forEach(function(a) {
        a.style.display = a.textContent.toLowerCase().includes(filter) ? '' : 'none';
    });
}

// Create charts for the initially active tab
createCharts(platformIds[0]);
</script>
</div>
</body>
</html>"""

    return html


if __name__ == "__main__":
    all_platform_data = {}
    for pname, prefix in PLATFORMS.items():
        reports = get_reports(prefix)
        print(f"\n=== {pname} ({prefix}) ===")
        print(f"Parsed {len(reports)} reports")
        all_tests = set()
        for r in reports:
            all_tests.update(r["test_data"].keys())
            print(f"  {r['date']} | {r['build_id']} | {r['duration_str']} | "
                  f"{r['total_tests']} tests | {len(r['test_data'])} parsed | "
                  f"{r['success_rate']}%")
        print(f"Total unique tests found: {len(all_tests)}")
        all_platform_data[pname] = compute_platform_data(reports)

    html = generate_html(all_platform_data)
    output_path = os.path.join(STATS_DIR, "per_test_stats.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\nDashboard written to: {output_path}")
