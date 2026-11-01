import csv, sys, math

lat0, lon0 = float(sys.argv[1]), float(sys.argv[2])
best = None
with open("nodes.csv") as f:
    for r in csv.DictReader(f):
        d = (float(r["lat"]) - lat0) ** 2 + ((float(r["lon"]) - lon0) * math.cos(math.radians(lat0))) ** 2
        if best is None or d < best[0]:
            best = (d, r["id"], r["lat"], r["lon"])
print("node", best[1], "tại", best[2], best[3])