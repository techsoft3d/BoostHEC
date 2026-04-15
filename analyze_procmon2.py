import csv
from collections import defaultdict

child_pid = '474156'
prefetch_pid = '476716'

# Categorize child NAS accesses
child_files = defaultdict(list)
child_dirs = set()
child_createfile = []

with open('C:/HEC/Logfile.CSV', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['PID'] != child_pid:
            continue
        path = row['Path']
        if 'LYONTS3D-NAS' not in path:
            continue

        op = row['Operation']
        result = row['Result']
        time = row['Time of Day']

        # Extract the file/folder part after the share
        parts = path.split('\\')
        filename = parts[-1] if parts else path

        child_files[path].append((time, op, result))

        if op == 'CreateFile':
            child_createfile.append((time, result, path))

# Group by directory
dir_files = defaultdict(set)
for path in child_files:
    parts = path.rsplit('\\', 1)
    if len(parts) == 2:
        dir_files[parts[0]].add(parts[1])

print(f'=== Child (PID {child_pid}) NAS file access summary ===')
print(f'Total unique paths accessed: {len(child_files)}')
print(f'Total directories accessed: {len(dir_files)}')

print(f'\n=== Directories and files accessed ===')
for d in sorted(dir_files):
    files = sorted(dir_files[d])
    print(f'\n  {d}/ ({len(files)} files)')
    for f in files[:20]:
        ops_for_file = child_files[d + '\\' + f]
        op_types = set(o for _, o, _ in ops_for_file)
        results_set = set(r for _, _, r in ops_for_file)
        print(f'    {f:60s} ops={len(ops_for_file):>3}  {",".join(sorted(op_types))[:50]}  results={",".join(sorted(results_set))}')
    if len(files) > 20:
        print(f'    ... and {len(files) - 20} more files')

print(f'\n=== CreateFile operations (file opens) ===')
print(f'Total: {len(child_createfile)}')
# Group by result
by_result = defaultdict(list)
for t, r, p in child_createfile:
    by_result[r].append((t, p))

for result, entries in sorted(by_result.items()):
    print(f'\n  {result}: {len(entries)}')
    for t, p in entries[:10]:
        short = p.split('LYONTS3D-NAS\\')[-1] if 'LYONTS3D-NAS' in p else p
        print(f'    {t} {short}')
    if len(entries) > 10:
        print(f'    ... and {len(entries) - 10} more')
