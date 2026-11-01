#include <bits/stdc++.h>
using namespace std;

int main(int argc, char** argv) {
    if (argc < 3) { cerr << "Cach dung: ./dijkstra_seq SRC DST\n"; return 1; }
    int src = atoi(argv[1]), dst = atoi(argv[2]);

    ifstream in("edges.txt");
    vector<array<int,3>> E;
    int u, v, w, maxid = -1;
    while (in >> u >> v >> w) {
        E.push_back({u, v, w});
        maxid = max(maxid, max(u, v));
    }
    int n = maxid + 1;
    if (src >= n || dst >= n) { cerr << "Node khong ton tai\n"; return 1; }
    vector<vector<pair<int,int>>> adj(n);
    for (auto& e : E) adj[e[0]].push_back({e[1], e[2]});

    const long long INF = LLONG_MAX / 4;
    vector<long long> dist(n, INF);
    vector<int> prev(n, -1);
    priority_queue<pair<long long,int>, vector<pair<long long,int>>, greater<>> pq;

    auto t0 = chrono::steady_clock::now();
    dist[src] = 0;
    pq.push({0, src});
    while (!pq.empty()) {
        auto [d, x] = pq.top(); pq.pop();
        if (d > dist[x]) continue;
        for (auto [y, wt] : adj[x]) {
            if (dist[x] + wt < dist[y]) {
                dist[y] = dist[x] + wt;
                prev[y] = x;
                pq.push({dist[y], y});
            }
        }
    }
    auto t1 = chrono::steady_clock::now();
    double ms = chrono::duration<double, milli>(t1 - t0).count();

    // Ghi khoảng cách tới mọi node (để đối chiếu với bản MapReduce)
    ofstream fd("seq_dist.txt");
    for (int i = 0; i < n; i++) fd << i << "\t" << (dist[i] >= INF ? -1 : dist[i]) << "\n";

    if (dist[dst] >= INF) {
        cout << "Khong co duong di tu " << src << " den " << dst << "\n";
        return 0;
    }
    // Truy vết đường đi
    vector<int> path;
    for (int x = dst; x != -1; x = prev[x]) path.push_back(x);
    reverse(path.begin(), path.end());
    ofstream fp("path.txt");
    for (int x : path) fp << x << "\n";

    cout << "Khoang cach: " << dist[dst] << " m (" << dist[dst] / 1000.0 << " km)\n";
    cout << "So node tren duong di: " << path.size() << "\n";
    cout << "Thoi gian chay: " << ms << " ms\n";
    return 0;
}