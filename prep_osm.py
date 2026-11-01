import json, math, os, sys, urllib.request, urllib.parse
from collections import defaultdict, deque

# ====== CẤU HÌNH ======
# bbox: nam, tây, bắc, đông (lõi thành phố Đà Nẵng)
BBOX = (15.97, 108.12, 16.14, 108.28)
RAW_FILE = "danang.json"
HONOR_ONEWAY = True   # False = coi mọi đường là hai chiều
HIGHWAYS = ("motorway|trunk|primary|secondary|tertiary|unclassified|residential|"
            "motorway_link|trunk_link|primary_link|secondary_link|tertiary_link|living_street")

# ====== 1. TẢI DỮ LIỆU TỪ OVERPASS ======
def download():
    if os.path.exists(RAW_FILE):
        print("Đã có", RAW_FILE, "- bỏ qua bước tải")
        return
    s, w, n, e = BBOX
    q = f'[out:json][timeout:300];way["highway"~"^({HIGHWAYS})$"]({s},{w},{n},{e});out body;>;out skel qt;'
    data = urllib.parse.urlencode({"data": q}).encode()
    print("Đang tải từ Overpass (có thể mất 1-2 phút)...")
    req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=data,
                                 headers={"User-Agent": "dijkstra-student-project"})
    with urllib.request.urlopen(req, timeout=400) as r, open(RAW_FILE, "wb") as f:
        f.write(r.read())

# ====== 2. TÍNH KHOẢNG CÁCH ======
def haversine(a, b):
    R = 6371000.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 2 * R * math.asin(math.sqrt(h))

# ====== 3. DỰNG ĐỒ THỊ ======
def build():
    with open(RAW_FILE, encoding="utf-8") as f:
        els = json.load(f)["elements"]
    coords = {e["id"]: (e["lat"], e["lon"]) for e in els if e["type"] == "node"}
    edges = {}   # (u, v) -> trọng số (mét, số nguyên)

    def add(u, v, w):
        if u != v:
            edges[(u, v)] = min(w, edges.get((u, v), w))

    for e in els:
        if e["type"] != "way":
            continue
        nds = [n for n in e["nodes"] if n in coords]
        oneway = e.get("tags", {}).get("oneway", "no")
        for a, b in zip(nds, nds[1:]):
            w = max(1, round(haversine(coords[a], coords[b])))
            if HONOR_ONEWAY and oneway in ("yes", "true", "1"):
                add(a, b, w)
            elif HONOR_ONEWAY and oneway == "-1":
                add(b, a, w)
            else:
                add(a, b, w); add(b, a, w)
    return coords, edges

# ====== 4. GIỮ THÀNH PHẦN LIÊN THÔNG LỚN NHẤT ======
def largest_component(edges):
    und = defaultdict(set)
    for (u, v) in edges:
        und[u].add(v); und[v].add(u)
    seen, best = set(), set()
    for s in und:
        if s in seen:
            continue
        comp, dq = {s}, deque([s])
        seen.add(s)
        while dq:
            x = dq.popleft()
            for y in und[x]:
                if y not in seen:
                    seen.add(y); comp.add(y); dq.append(y)
        if len(comp) > len(best):
            best = comp
    return best

# ====== 5. XUẤT FILE ======
def main():
    download()
    coords, edges = build()
    keep = largest_component(edges)
    ids = sorted(keep)
    new_id = {old: i for i, old in enumerate(ids)}   # đánh lại ID 0..N-1

    adj = defaultdict(list)
    for (u, v), w in edges.items():
        if u in keep and v in keep:
            adj[new_id[u]].append((new_id[v], w))

    # nodes.csv: dùng để vẽ bản đồ ở bước sau
    with open("nodes.csv", "w") as f:
        f.write("id,osm_id,lat,lon\n")
        for old in ids:
            f.write(f"{new_id[old]},{old},{coords[old][0]},{coords[old][1]}\n")

    # edges.txt: mỗi dòng "u v w" (dùng cho bản tuần tự)
    with open("edges.txt", "w") as f:
        for u in sorted(adj):
            for v, w in adj[u]:
                f.write(f"{u} {v} {w}\n")

    n_edges = sum(len(x) for x in adj.values())
    print(f"Số node: {len(ids)}, số cạnh: {n_edges}")
    print("Đã tạo: nodes.csv, edges.txt")

    # graph.txt: dạng danh sách kề cho MapReduce
    source = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    INF = 2**31 - 1
    with open("graph.txt", "w") as f:
        for u in range(len(ids)):
            d = 0 if u == source else INF
            path = str(u) if u == source else ""
            nb = ",".join(f"{v}:{w}" for v, w in adj[u])
            f.write(f"{u}\t{d}|{path}|{nb}\n")      # <-- chỉnh dòng này cho khớp mapper của bạn
    print(f"Đã tạo graph.txt (nguồn = node {source})")

if __name__ == "__main__":
    main()