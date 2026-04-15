import csv
from collections import defaultdict

# Analyze font-related NAS access and timing
font_ops = []
model_ops = []
all_nas = []

with open('C:/HEC/Logfile.CSV', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        path = row['Path']
        if 'LYONTS3D-NAS' not in path:
            continue

        time = row['Time of Day']
        pid = row['PID']
        op = row['Operation']
        result = row['Result']

        all_nas.append((time, pid, op, result, path))

        if 'Fonts' in path or 'font' in path.lower():
            font_ops.append((time, pid, op, result, path))

# Group by PID
pids = set(e[1] for e in all_nas)
print(f'=== PIDs: {sorted(pids)} ===')
print(f'Total NAS ops: {len(all_nas)}, Font ops: {len(font_ops)}')

for pid in sorted(pids):
    pid_ops = [e for e in all_nas if e[1] == pid]
    pid_font = [e for e in font_ops if e[1] == pid]
    pid_non_font = [e for e in pid_ops if e not in pid_font]

    print(f'\n=== PID {pid}: {len(pid_ops)} NAS ops ({len(pid_font)} font, {len(pid_non_font)} non-font) ===')

    if pid_ops:
        print(f'  Time range: {pid_ops[0][0]} - {pid_ops[-1][0]}')

    # Font access details
    if pid_font:
        font_files = set(e[4].split('\\')[-1] for e in pid_font)
        print(f'  Font files accessed: {len(font_files)}')
        # First and last font access
        print(f'  First font access: {pid_font[0][0]}')
        print(f'  Last font access:  {pid_font[-1][0]}')

    # Non-font NAS access by directory
    dir_count = defaultdict(int)
    for t, p, o, r, path in pid_non_font:
        parts = path.rsplit('\\', 1)
        d = parts[0] if len(parts) == 2 else path
        d = d.replace('\\\\LYONTS3D-NAS\\', '')
        dir_count[d] += 1

    if dir_count:
        print(f'  Non-font NAS access by directory:')
        for d, c in sorted(dir_count.items(), key=lambda x: -x[1])[:10]:
            print(f'    {c:>5} ops  {d}')

# Check: did the child access fonts from cache or NAS?
print(f'\n=== Font access timeline ===')
for t, pid, op, result, path in font_ops[:20]:
    short = path.split('\\')[-1]
    print(f'  {t} PID={pid} {op:30s} {result:25s} {short}')
if len(font_ops) > 20:
    print(f'  ... ({len(font_ops) - 20} more font ops) ...')
    for t, pid, op, result, path in font_ops[-5:]:
        short = path.split('\\')[-1]
        print(f'  {t} PID={pid} {op:30s} {result:25s} {short}')
