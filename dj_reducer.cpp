#include <bits/stdc++.h>
using namespace std;
static const long long INF = 2147483647LL;
string cur, adjStr, bestPrev;
long long origD, bestD;
bool has = false;

void flush()
{
    if (!has)
        return;
    if (bestD < origD)
        cerr << "reporter:counter:Dijkstra,Updated,1\n"; // đếm node được cải thiện
    cout << cur << '\t' << "N|" << bestD << '|' << bestPrev << '|' << adjStr << '\n';
}
void reset(const string &k)
{
    cur = k;
    origD = INF;
    bestD = INF;
    bestPrev = "-1";
    adjStr = "";
    has = true;
}
int main()
{
    ios::sync_with_stdio(false);
    string line;
    while (getline(cin, line))
    {
        if (line.empty())
            continue;
        size_t tab = line.find('\t');
        string k = line.substr(0, tab);
        string rest = line.substr(tab + 1);
        if (!has || k != cur)
        {
            flush();
            reset(k);
        }
        size_t p2 = rest.find('|', 2);
        long long d = stoll(rest.substr(2, p2 - 2));
        if (rest[0] == 'N')
        {
            size_t p3 = rest.find('|', p2 + 1);
            origD = d;
            adjStr = rest.substr(p3 + 1);
            if (d < bestD)
            {
                bestD = d;
                bestPrev = rest.substr(p2 + 1, p3 - p2 - 1);
            }
        }
        else
        {
            if (d < bestD)
            {
                bestD = d;
                bestPrev = rest.substr(p2 + 1);
            }
        }
    }
    flush();
}