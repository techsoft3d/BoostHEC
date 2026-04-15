import json

models = []
with open("c:/HEC/filelist_NX.txt.deps.ndjson") as f:
    for line in f:
        d = json.loads(line)
        models.append({
            "model": d["model"],
            "size": d["size"],
            "total_size": d["total_size"],
            "dep_count": len(d["deps"])
        })

# Sort by total_size
models.sort(key=lambda m: m["total_size"])

print(f"Total models: {len(models)}")
print(f"Size range: {models[0]['total_size']} - {models[-1]['total_size']}")
print()

# Pick 20 spread across the size spectrum with varying dep counts
# Split into 4 buckets of 5
n = len(models)
bucket_size = n // 4
selected = []

for bucket_idx in range(4):
    start = bucket_idx * bucket_size
    end = start + bucket_size if bucket_idx < 3 else n
    bucket = models[start:end]

    # Sort bucket by dep_count to get variety
    bucket.sort(key=lambda m: m["dep_count"])

    # Pick 5 evenly spaced from this bucket
    step = max(1, len(bucket) // 5)
    for i in range(5):
        idx = min(i * step, len(bucket) - 1)
        selected.append(bucket[idx])

# Deduplicate
seen = set()
final = []
for m in selected:
    if m["model"] not in seen:
        seen.add(m["model"])
        final.append(m)

final = final[:20]

print(f"Selected {len(final)} models:")
print(f"{'Model':<80} {'Size':>10} {'TotalSize':>12} {'Deps':>5}")
print("-" * 115)
for m in final:
    parts = m["model"].split("\\")
    short = parts[-1] if len(parts) > 1 else m["model"][-60:]
    print(f"{short:<80} {m['size']:>10,} {m['total_size']:>12,} {m['dep_count']:>5}")

print()
print("=== FILELIST ===")
for m in final:
    print(m["model"])
