#ifndef DSU_HPP
#define DSU_HPP

#include <vector>
#include <numeric>

class DSU {
public:
    explicit DSU(int n = 0);

    void resize(int n);
    int find(int i);
    void unite(int i, int j);
    bool connected(int i, int j);

private:
    std::vector<int> parent;
    std::vector<int> rank;
};

inline DSU::DSU(int n) {
    if (n > 0) 
        resize(n);
}

inline void DSU::resize(int n) {
    parent.resize(n);
    rank.assign(n, 0);
    std::iota(parent.begin(), parent.end(), 0);
}

inline int DSU::find(int i) {
    if (parent[i] != i)
        parent[i] = find(parent[i]);

    return parent[i];
}

inline void DSU::unite(int i, int j) {
    int root_i = find(i);
    int root_j = find(j);

    if (root_i != root_j) {
        if (rank[root_i] < rank[root_j]) 
            std::swap(root_i, root_j);
        
        parent[root_j] = root_i;
        if (rank[root_i] == rank[root_j]) 
            rank[root_i]++;
    }
}

inline bool DSU::connected(int i, int j) {
    return find(i) == find(j);
}

#endif // DSU_HPP
