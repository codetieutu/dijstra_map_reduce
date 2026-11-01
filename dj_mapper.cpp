#include <bits/stdc++.h>
using namespace std;
int main()
{
    ios::sync_with_stdio(false);
    const long long INF = 2147483647LL;
    string line;
    while (getline(cin, line))
    {
        if (line.empty())
            continue;
        size_t tab = line.find('\t');
        string u = line.substr(0, tab);
        string rest = line.substr(tab + 1);
        // rest = N|d|prev|adj  hoặc  M|d|prev
        cout << u << '\t' << rest << '\n'; // giữ nguyên bản ghi của node
        if (rest[0] != 'N')
            continue;
        size_t p2 = rest.find('|', 2);
        size_t p3 = rest.find('|', p2 + 1);
        long long d = stoll(rest.substr(2, p2 - 2));
        string adj = rest.substr(p3 + 1);
        if (d >= INF || adj.empty())
            continue;
        stringstream ss(adj);
        string tok;
        while (getline(ss, tok, ','))
        {
            size_t c = tok.find(':');
            string v = tok.substr(0, c);
            long long w = stoll(tok.substr(c + 1));
            cout << v << '\t' << "M|" << (d + w) << '|' << u << '\n'; // đề xuất khoảng cách mới cho v
        }
    }
}