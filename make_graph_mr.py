import sys
src = int(sys.argv[1])
n = sum(1 for _ in open("nodes.csv")) - 1
adj = [[] for _ in range(n)]
for line in open("edges.txt"):
    u, v, w = line.split()
    adj[int(u)].append(f"{v}:{w}")
INF = 2147483647
with open("graph_mr.txt", "w") as f:
    for u in range(n):
        d = 0 if u == src else INF
        f.write(f"{u}\tN|{d}|-1|{','.join(adj[u])}\n")