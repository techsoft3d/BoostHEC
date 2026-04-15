# BoostHEC

Scripts and configs for benchmarking and speeding up **HoopsExchangeChecker** (HEC) filelist test runs.

HEC loads CAD model files from a NAS (`\\LYONTS3D-NAS`) and checks them against expected results.
The core problem: NAS latency dominates test wall time. This repo explores the **prefetch** mechanism built into HEC that pre-downloads model files (and their dependencies) to a local cache before the test processes start.

---

## How the prefetch system works

HEC has a `-prefetch` mode that runs a separate phase before the main test:

1. **Dependency scan**: HEC reads the filelist and, for each model, resolves all referenced files (sub-parts, referenced assemblies, etc.) using the `.deps.ndjson` dependency graph.
2. **Parallel download**: It spawns threads to copy every required file from the NAS to a local `-cachedir` on disk.
3. **Cache-backed test run**: The worker processes (`-process N`) then load from the local cache instead of the NAS, cutting I/O wait dramatically.

The `-prefetch-boost N` flag (used in `full_with_prefetch.bat`) moves the N heaviest models (by total dependency size) to the front of the prefetch queue, so the most expensive tests are unblocked first.

### Dependency data

Dependency graphs are pre-computed by running HEC's function 231 (`ComputeFileDependencies`) via `run_all_deps.ps1`. Each filelist produces a `filelist_<FORMAT>.txt.deps.ndjson` file in `deps/`, with one JSON object per model:

```json
{"model": "\\\\NAS\\...\\part.prt", "size": 214360, "total_size": 850000, "deps": ["\\\\NAS\\...\\ref1.prt", ...]}
```

---

## Prerequisites

- `HoopsExchangeChecker.exe` built at `C:\git\exchange_core\build_irt\bin\RelWithDebInfo\`
- Filelists at `C:\git\exchange_core\exchange\admin\QA\Filelist\`
- Settings at `C:\git\exchange_core\exchange\admin\QA\Configuration\`
- NAS accessible at `\\LYONTS3D-NAS`

---

## Scripts

### Benchmark runs (NX filelist)

| Script | Description |
|--------|-------------|
| `without_prefetch.bat` | Mini NX filelist, 1 process, no prefetch |
| `with_prefetch.bat [N]` | Mini NX filelist, N processes, with prefetch |
| `1-process-run.bat` | Both back-to-back (baseline comparison) |
| `full_without_prefetch.bat [N]` | Full NX filelist, N processes, no prefetch |
| `full_with_prefetch.bat [N] [boost]` | Full NX filelist, N processes, with prefetch; optional boost for heaviest models |

**Examples:**

```bat
REM Quick comparison on mini filelist
1-process-run.bat

REM Full run, 8 processes, boost top 100 heaviest models
full_with_prefetch.bat 8 100

REM Full run without prefetch for baseline
full_without_prefetch.bat 8
```

### Dependency analysis (all formats)

```powershell
# Analyze all formats, output to deps\
.\run_all_deps.ps1

# Dry-run to see commands without executing
.\run_all_deps.ps1 -DryRun

# Custom parallelism
.\run_all_deps.ps1 -Process 20
```

`run_all_deps.ps1` iterates over ~100 format filelists (NX, CATIA V5, STEP, ProE, JT, IFC, Inventor, plus all export formats) and runs HEC function 231 on each, producing `.deps.ndjson` files incrementally (skips filelists already analyzed).

### Model selection

```bash
python pick_models.py
```

Selects a representative 20-model subset from the NX filelist, spread across the file-size spectrum and across dependency counts. Outputs a filelist ready to paste into `mini_filelist_NX.txt`.

### NAS I/O profiling

```bash
# Analyze a Process Monitor CSV export
python analyze_procmon3.py
```

Analyzes Process Monitor captures (`Logfile.CSV`) to profile per-process NAS access: separates font file reads from model reads, shows time ranges and directory breakdown per child PID. Useful for diagnosing whether child processes are hitting the NAS or the local cache.

---

## Config files

| File | Purpose |
|------|---------|
| `config_loadonly.xml` | Pure load benchmark — no check functions, just model loading |
| `config_deps_<FORMAT>.xml` | Per-format config for dependency analysis (function 231) |
| `config_deps.xml` | Generic dependency config template |

---

## Directory layout

```
BoostHEC/
├── *.bat                        # Benchmark run scripts
├── run_all_deps.ps1             # Batch dependency analysis
├── pick_models.py               # Mini-filelist selector
├── analyze_procmon*.py          # NAS I/O profilers
├── config_loadonly.xml          # Load-only HEC config
├── config_deps_*.xml            # Per-format dependency configs
├── mini_filelist_NX.txt         # 20-model NX subset
├── mini_filelist_NX.txt.deps.ndjson  # Dependency graph for mini filelist
├── cache/                       # Local prefetch cache (gitignored)
├── deps/                        # Dependency NDJSON output (gitignored)
├── out/                         # HEC run output (gitignored)
└── stats/                       # HTML test reports (gitignored)
```
