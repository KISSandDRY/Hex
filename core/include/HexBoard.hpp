#ifndef HEX_BOARD_HPP
#define HEX_BOARD_HPP

#include "DSU.hpp"

#include <vector>
#include <memory>
#include <utility>

constexpr int EMPTY = 0;
constexpr int PLAYER_1 = 1;
constexpr int PLAYER_2 = 2;

class HexBoard {
public:
    const int rows;
    const int cols;

    HexBoard(int r = 6, int c = 6);

    bool is_valid(int r, int c) const;
    int get_index(int r, int c) const;
    int get_cell(int row, int col) const;
    int get_cell_by_index(int idx) const;
    std::pair<int, int> get_coord(int idx) const;
    const std::vector<int>& get_neighbors(int idx) const;
    std::vector<int> get_legal_moves() const;

    bool make_move(int r, int c, int player);
    int check_win();

    int get_shortest_distance(int player) const;
    std::vector<int> get_winning_path(int player);

    void print_board() const;

private:
    std::vector<int> board;
    DSU dsu_p1;
    DSU dsu_p2;

    int VIRT_TOP, VIRT_BOTTOM;
    int VIRT_LEFT, VIRT_RIGHT;

    std::shared_ptr<const std::vector<std::vector<int>>> adj;

    void build_adjacency();
    bool dfs(int idx, int player, std::vector<bool>& visited, std::vector<int>& path);
};

#endif // HEX_BOARD_HPP
