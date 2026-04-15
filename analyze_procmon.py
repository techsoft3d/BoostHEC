import csv

ops = {}
paths = set()
results = {}
pids = set()
cache_ops = []
nas_ops = []

with open('C:/HEC/Logfile.CSV', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        op = row['Operation']
        path = row['Path']
        result = row['Result']
        pid = row['PID']
        time = row['Time of Day']

        ops[op] = ops.get(op, 0) + 1
        results[result] = results.get(result, 0) + 1
        pids.add(pid)

        if 'LYONTS3D-NAS' in path:
            paths.add(path)
            nas_ops.append((time, pid, op, result, path))

        if 'HEC' in path and 'cache' in path:
            cache_ops.append((time, pid, op, result, path))

print('=== PIDs ===')
for p in sorted(pids):
    print(f'  {p}')

print(f'\n=== Operations ({sum(ops.values())} total) ===')
for k, v in sorted(ops.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v}')

print(f'\n=== Results ===')
for k, v in sorted(results.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v}')

print(f'\n=== NAS access: {len(nas_ops)} operations to {len(paths)} unique paths ===')

# Group NAS ops by PID
nas_by_pid = {}
for time, pid, op, result, path in nas_ops:
    nas_by_pid.setdefault(pid, []).append((time, op, result, path))

for pid, entries in sorted(nas_by_pid.items()):
    print(f'\n  PID {pid}: {len(entries)} NAS operations')
    # Show first 10 and last 5
    for time, op, result, path in entries[:10]:
        short = path.split('\\')[-1] if '\\' in path else path
        print(f'    {time} {op:30s} {result:20s} {short}')
    if len(entries) > 15:
        print(f'    ... ({len(entries) - 15} more) ...')
    if len(entries) > 10:
        for time, op, result, path in entries[-5:]:
            short = path.split('\\')[-1] if '\\' in path else path
            print(f'    {time} {op:30s} {result:20s} {short}')

print(f'\n=== Cache operations: {len(cache_ops)} ===')
# Check for failures
cache_failures = [(t, p, o, r, path) for t, p, o, r, path in cache_ops if r != 'SUCCESS']
if cache_failures:
    print(f'  FAILURES: {len(cache_failures)}')
    for t, p, o, r, path in cache_failures[:20]:
        short = path.replace('c:\\HEC\\cache\\Import_NX\\', '')
        print(f'    {t} {o:30s} {r:30s} {short}')
else:
    print('  All cache operations succeeded.')

# Check for DELETE/CLEANUP operations on cache
cache_deletes = [(t, p, o, r, path) for t, p, o, r, path in cache_ops if 'Delete' in o or 'SetDisposition' in o or 'Cleanup' in o]
print(f'\n=== Cache delete/cleanup operations: {len(cache_deletes)} ===')
for t, p, o, r, path in cache_deletes[:30]:
    short = path.replace('c:\\HEC\\cache\\Import_NX\\', '')
    print(f'  {t} PID={p} {o:30s} {r:30s} {short}')
