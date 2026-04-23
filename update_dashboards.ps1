#Requires -Version 5.1
<#
.SYNOPSIS
    Refresh BoostHEC analytics dashboards with the latest NAS build data.

.DESCRIPTION
    Runs daily via Windows Task Scheduler (registered with -Register).
    Steps:
      1. Read the last known build from DATE_MAP in the analytics scripts.
      2. Scan Z:\master for new build directories.
      3. Copy the three platform HTML reports per build to C:\HEC\stats\.
      4. Patch DATE_MAP + date-range labels in all three analytics scripts.
      5. Run generate_stats.py, generate_filelist_stats.py, generate_pngs.py.
      6. Copy the regenerated HTML dashboards to docs\.
      7. Commit and push to GitHub.

.PARAMETER RepoDir
    Path to the BoostHEC git repo. Default: C:\git\BoostHEC

.PARAMETER StatsDir
    Path to the local stats HTML directory. Default: C:\HEC\stats

.PARAMETER NasDir
    Path to the NAS build root (must be mounted). Default: Z:\master

.PARAMETER DryRun
    Print every action without writing any files or running any scripts.

.PARAMETER Register
    Register this script as a daily Windows Task Scheduler job (Mon-Fri, 08:00)
    and exit. Run once as administrator after placing this file in the repo.

.EXAMPLE
    .\update_dashboards.ps1 -DryRun          # preview what would happen
    .\update_dashboards.ps1                   # run the full update
    .\update_dashboards.ps1 -Register         # set up the scheduled task
#>

param(
    [string]$RepoDir  = "C:\git\BoostHEC",
    [string]$StatsDir = "C:\HEC\stats",
    [string]$NasDir   = "Z:\master",
    [switch]$DryRun,
    [switch]$Register
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Register scheduled task and exit ──────────────────────────────────────
if ($Register) {
    $scriptPath = $MyInvocation.MyCommand.Path
    $action     = New-ScheduledTaskAction `
                    -Execute  "powershell.exe" `
                    -Argument "-NonInteractive -ExecutionPolicy Bypass -File `"$scriptPath`""
    $trigger    = New-ScheduledTaskTrigger `
                    -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
                    -At "08:00"
    $settings   = New-ScheduledTaskSettingsSet `
                    -StartWhenAvailable `
                    -RunOnlyIfNetworkAvailable `
                    -ExecutionTimeLimit (New-TimeSpan -Hours 2)
    Register-ScheduledTask `
        -TaskName "BoostHEC Dashboard Update" `
        -Action   $action `
        -Trigger  $trigger `
        -Settings $settings `
        -RunLevel Highest `
        -Force | Out-Null
    Write-Host "Scheduled task registered: 'BoostHEC Dashboard Update'" -ForegroundColor Green
    Write-Host "Runs Mon-Fri at 08:00 local time. View in Task Scheduler." -ForegroundColor Gray
    exit 0
}

# ── Logging helpers ────────────────────────────────────────────────────────
function Write-Step($n, $msg) { Write-Host "`n=== $n/7  $msg ===" -ForegroundColor Cyan }
function Write-OK($msg)       { Write-Host "  [ok]   $msg" -ForegroundColor Green }
function Write-Info($msg)     { Write-Host "  $msg"  -ForegroundColor Gray }
function Write-Warn($msg)     { Write-Host "  [warn] $msg" -ForegroundColor Yellow }
function Fail($msg)           { Write-Host "`n  [FAIL] $msg" -ForegroundColor Red; exit 1 }

if ($DryRun) {
    Write-Host "[DRY RUN - no files will be written or committed]`n" -ForegroundColor Magenta
}

$Platforms = @(
    "Linux_GCC_GLIBC212_DWG_report",
    "Mac_LLVM_report",
    "Windows_VS2019_report"
)

$AnalyticsScripts = @(
    "analytics\generate_stats.py",
    "analytics\generate_filelist_stats.py",
    "analytics\generate_pngs.py"
)

# ═══════════════════════════════════════════════════════════════════════════
# 1  Read the current DATE_MAP to find the last known build
# ═══════════════════════════════════════════════════════════════════════════
Write-Step 1 "Reading current DATE_MAP"

$refScript = Join-Path $RepoDir "analytics\generate_stats.py"
if (-not (Test-Path $refScript)) { Fail "Script not found: $refScript" }

$refText   = Get-Content $refScript -Raw -Encoding UTF8
$knownIds  = [regex]::Matches($refText, '"(\d{4,}-[0-9a-f]+)"\s*:') |
                 ForEach-Object { $_.Groups[1].Value }

if (-not $knownIds) { Fail "No build IDs found in DATE_MAP" }

$lastBuildNum = ($knownIds |
    ForEach-Object { [int]($_ -split '-')[0] } |
    Measure-Object -Maximum).Maximum

Write-Info "$($knownIds.Count) known builds; last build number: $lastBuildNum"

# ═══════════════════════════════════════════════════════════════════════════
# 2  Scan NAS for new build directories
# ═══════════════════════════════════════════════════════════════════════════
Write-Step 2 "Scanning NAS: $NasDir"

if (-not (Test-Path $NasDir)) {
    Fail "NAS not accessible at $NasDir — is the drive mounted?"
}

$newBuilds = @(
    Get-ChildItem -Path $NasDir -Directory |
    Where-Object { $_.Name -match '^\d{4,}-[0-9a-f]+$' } |
    Where-Object { [int]($_.Name -split '-')[0] -gt $lastBuildNum } |
    Sort-Object   { [int]($_.Name -split '-')[0] }
)

if ($newBuilds.Count -eq 0) {
    Write-Info "No new builds found — dashboards are already current."
    exit 0
}

Write-Info "$($newBuilds.Count) new build(s):"
$newBuilds | ForEach-Object {
    Write-Info "    $($_.Name)    $($_.LastWriteTime.ToString('yyyy-MM-dd'))"
}

# ═══════════════════════════════════════════════════════════════════════════
# 3  Copy platform HTML reports to C:\HEC\stats\
# ═══════════════════════════════════════════════════════════════════════════
Write-Step 3 "Copying HTML reports -> $StatsDir"

$copied = 0
foreach ($build in $newBuilds) {
    foreach ($plat in $Platforms) {
        $src = Join-Path $build.FullName "$plat.html"
        $dst = Join-Path $StatsDir "${plat}_$($build.Name).html"
        if ((Test-Path $src) -and -not (Test-Path $dst)) {
            if (-not $DryRun) { Copy-Item $src $dst }
            Write-Info "    $($build.Name) / $plat"
            $copied++
        }
    }
}
Write-OK "Copied $copied file(s)"

# ═══════════════════════════════════════════════════════════════════════════
# 4  Patch DATE_MAP + date-range labels in all three analytics scripts
# ═══════════════════════════════════════════════════════════════════════════
Write-Step 4 "Patching DATE_MAP in analytics scripts"

# Build new entry lines, with a month-comment whenever the month changes
$entryLines = [System.Collections.Generic.List[string]]::new()
$curMonth   = ""
foreach ($build in $newBuilds) {
    $date  = $build.LastWriteTime.ToString("yyyy-MM-dd")
    $month = $build.LastWriteTime.ToString("MMMM yyyy")   # "April 2026"
    if ($month -ne $curMonth) {
        $entryLines.Add("    # $month")
        $curMonth = $month
    }
    $entryLines.Add("    `"$($build.Name)`": `"$date`",")
}

# Labels derived from the last new build
$last          = $newBuilds[-1]
$lastDateFull  = $last.LastWriteTime.ToString("MMM d, yyyy")  # "Apr 22, 2026"
$lastMonthAbbr = $last.LastWriteTime.ToString("MMM")           # "Apr"
$lastYear      = $last.LastWriteTime.ToString("yyyy")          # "2026"

# Regex patterns for the three date-range string styles used across the scripts:
#   generate_stats.py, generate_filelist_stats.py  -> "Jan 1 to Apr 14, 2026"  (or locale month)
#   generate_pngs.py (suptitle)                    -> "Jan 1 - Apr 14, 2026" or with en-dash
#   generate_pngs.py (axis / category titles)      -> "Jan-Apr 2026" or with en-dash
# Patterns use a locale-neutral month match ([A-Za-z]{2,5}\.?) so they keep working
# on non-English Windows locales (e.g. French "avr." for April).
$patternFull    = 'Jan 1 to [A-Za-z]{2,5}\.? \d{1,2}, \d{4}'
$patternDash    = 'Jan 1 [–\-] [A-Za-z]{2,5}\.? \d{1,2}, \d{4}'
$patternMonths  = 'Jan[–\-][A-Za-z]{2,5}\.? \d{4}'

foreach ($relPath in $AnalyticsScripts) {
    $fullPath = Join-Path $RepoDir $relPath
    if (-not (Test-Path $fullPath)) { Write-Warn "Not found: $relPath"; continue }

    $lines = [System.Collections.Generic.List[string]](
        Get-Content $fullPath -Encoding UTF8)

    # Find the last line containing a DATE_MAP entry (e.g. "5693-5b14060a": "2026-04-14")
    $lastEntryIdx = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^\s+"[0-9]+-[0-9a-f]+"\s*:\s*"\d{4}-\d{2}-\d{2}"') {
            $lastEntryIdx = $i
        }
    }
    if ($lastEntryIdx -lt 0) { Write-Warn "No DATE_MAP entries in $relPath"; continue }

    # Find the closing } that immediately follows the last entry
    $closingIdx = -1
    for ($i = $lastEntryIdx + 1; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^}') { $closingIdx = $i; break }
    }
    if ($closingIdx -lt 0) { Write-Warn "No closing } after DATE_MAP in $relPath"; continue }

    # Splice: original[0..lastEntry] + newEntries + original[closing..end]
    $spliced = [System.Collections.Generic.List[string]]::new()
    $spliced.AddRange([string[]]$lines[0..$lastEntryIdx])
    $spliced.AddRange($entryLines)
    $spliced.AddRange([string[]]$lines[$closingIdx..($lines.Count - 1)])

    # Update all three date-range string formats
    for ($i = 0; $i -lt $spliced.Count; $i++) {
        $spliced[$i] = $spliced[$i] -replace $patternFull,   "Jan 1 to $lastDateFull"
        $spliced[$i] = $spliced[$i] -replace $patternDash,   "Jan 1 - $lastDateFull"
        $spliced[$i] = $spliced[$i] -replace $patternMonths, "Jan-$lastMonthAbbr $lastYear"
    }

    if (-not $DryRun) {
        Set-Content $fullPath -Value $spliced -Encoding UTF8
    }
    Write-OK "$(Split-Path $fullPath -Leaf)  (+$($entryLines.Count) lines)"
}

# ═══════════════════════════════════════════════════════════════════════════
# 5  Run the three analytics scripts
# ═══════════════════════════════════════════════════════════════════════════
Write-Step 5 "Regenerating dashboards"

foreach ($relPath in $AnalyticsScripts) {
    $fullPath = Join-Path $RepoDir $relPath
    $name     = Split-Path $fullPath -Leaf
    Write-Info "Running $name ..."
    if (-not $DryRun) {
        $out = & python $fullPath 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`n  $name FAILED output:" -ForegroundColor Red
            $out | ForEach-Object { Write-Host "    $_" }
            Fail "$name exited with code $LASTEXITCODE"
        }
        # Surface only the final summary line
        $summary = ($out | Where-Object { $_ -match '\S' } | Select-Object -Last 1)
        if ($summary) { Write-Info "    $summary" }
    }
    Write-OK $name
}

# ═══════════════════════════════════════════════════════════════════════════
# 6  Copy regenerated HTML to docs/
# ═══════════════════════════════════════════════════════════════════════════
Write-Step 6 "Updating docs/"

$docsDir = Join-Path $RepoDir "docs"
foreach ($f in @("per_test_stats.html", "filelist_stats.html")) {
    $src = Join-Path $StatsDir $f
    $dst = Join-Path $docsDir  $f
    if (Test-Path $src) {
        if (-not $DryRun) { Copy-Item $src $dst -Force }
        Write-OK $f
    } else {
        Write-Warn "$f not found in StatsDir — skipped"
    }
}
Write-Info "PNGs already written to docs\charts\ by generate_pngs.py"

# ═══════════════════════════════════════════════════════════════════════════
# 7  Commit and push to GitHub
# ═══════════════════════════════════════════════════════════════════════════
Write-Step 7 "Committing to GitHub"

Push-Location $RepoDir
try {
    $firstDate = $newBuilds[0].LastWriteTime.ToString("MMM d")
    $lastDate  = $last.LastWriteTime.ToString("MMM d, yyyy")
    $range     = if ($newBuilds.Count -eq 1) { $lastDate } else { "$firstDate - $lastDate" }
    $msg       = "Update dashboards: +$($newBuilds.Count) build(s), $range"

    if (-not $DryRun) {
        git add analytics\generate_stats.py `
                analytics\generate_filelist_stats.py `
                analytics\generate_pngs.py `
                docs\
        git commit -m $msg
        git push
    } else {
        Write-Info "[DryRun] Would commit: $msg"
    }
    Write-OK $msg
} finally {
    Pop-Location
}

Write-Host "`nAll done." -ForegroundColor Green
