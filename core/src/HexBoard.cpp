#include "HexBoard.hpp"

#include <deque>
#include <iomanip>
#include <iostream>

namespace Colors {
    const std::string RESET = "\033[0m";
    const std::string BLUE  = "\033[34m";
    const std::string RED   = "\033[31m";
    const std::string GRAY  = "\033[90m";
}

HexBoard::HexBoard(int r, int c)
    : rows(r), cols(c) 
{
    int N = r * c;
    board.assign(r * c, EMPTY);

    // Virtual Nodes for DSU
    VIRT_TOP  = N;     
    VIRT_BOTTOM = N + 1;
    VIRT_LEFT = N + 2;     
    VIRT_RIGHT = N + 3;

    dsu_p1.resize(N + 4);
    dsu_p2.resize(N + 4);

    build_adjacency();
}

int HexBoard::get_index(int r, int c) const {
    return r * cols + c;
}

int HexBoard::get_cell(int row, int col) const {
    if (!is_valid(row, col)) 
        return -1;

    return board[get_index(row, col)];
}

int HexBoard::get_cell_by_index(int idx) const {
    return board[idx];
}

std::pair<int, int> HexBoard::get_coord(int idx) const {
    return {idx / cols, idx % cols};
}

bool HexBoard::is_valid(int r, int c) const {
    return r >= 0 && r < rows && c >= 0 && c < cols;
}

const std::vector<int>& HexBoard::get_neighbors(int idx) const {
    return (*adj)[idx];
}

std::vector<int> HexBoard::get_legal_moves() const {
    std::vector<int> legal;
    legal.reserve(board.size());

    for (size_t i = 0; i < board.size(); ++i) 
        if (board[i] == EMPTY) 
            legal.push_back(static_cast<int>(i));
    
    return legal;
}

bool HexBoard::make_move(int r, int c, int player) {
    if (!is_valid(r, c)) 
        return false;

    int idx = get_index(r, c);
    if (board[idx] != EMPTY) 
        return false;

    board[idx] = player;

    // Update DSU based on adjacency
    const auto& neighbors = (*adj)[idx];

    for (int nb : neighbors) {

        // Handle Virtual connections
        if (nb >= rows * cols) {
            if (player == PLAYER_1) {
                if (nb == VIRT_LEFT || nb == VIRT_RIGHT)
                    dsu_p1.unite(idx, nb);
            } else {
                if (nb == VIRT_TOP || nb == VIRT_BOTTOM)
                    dsu_p2.unite(idx, nb);
            }

        } 
        // Handle Physical connections
        else if (board[nb] == player) {
            if (player == PLAYER_1) 
                dsu_p1.unite(idx, nb);
            else 
                dsu_p2.unite(idx, nb);
        }
    }

    return true;
}

int HexBoard::check_win() {
    if (dsu_p1.connected(VIRT_LEFT, VIRT_RIGHT)) 
        return PLAYER_1;

    if (dsu_p2.connected(VIRT_TOP, VIRT_BOTTOM)) 
        return PLAYER_2;

    return EMPTY;
}

// Graph Logic, Heuristics
void HexBoard::build_adjacency() {
    auto new_adj = std::make_shared<std::vector<std::vector<int>>>();
    int N = rows * cols;

    new_adj->assign(N + 4, {});

    for (int r = 0; r < rows; ++r) {
        for (int c = 0; c < cols; ++c) {
            int idx = get_index(r, c);

            // Connect to Virtual Nodes
            if (r == 0) {
                (*new_adj)[idx].push_back(VIRT_TOP);
                (*new_adj)[VIRT_TOP].push_back(idx);
            }

            if (r == rows - 1) {
                (*new_adj)[idx].push_back(VIRT_BOTTOM);
                (*new_adj)[VIRT_BOTTOM].push_back(idx);
            }

            if (c == 0) {
                (*new_adj)[idx].push_back(VIRT_LEFT);
                (*new_adj)[VIRT_LEFT].push_back(idx);
            }

            if (c == cols - 1) {
                (*new_adj)[idx].push_back(VIRT_RIGHT);
                (*new_adj)[VIRT_RIGHT].push_back(idx);
            }

            // Hex Grid Offsets
            static const std::vector<std::pair<int, int>> odd_offsets = {{-1, 0}, {-1, 1}, {0, -1}, {0, 1}, {1, 0}, {1, 1}};
            static const std::vector<std::pair<int, int>> even_offsets = {{-1, -1}, {-1, 0}, {0, -1}, {0, 1}, {1, -1}, {1, 0}};
            
            const auto& offsets = (r % 2 == 0) ? even_offsets : odd_offsets;

            for (const auto& [dr, dc] : offsets) {
                int nr = r + dr, nc = c + dc;

                if (is_valid(nr, nc)) 
                    (*new_adj)[idx].push_back(get_index(nr, nc));
            }
        }
    }

    this->adj = new_adj;
}

int HexBoard::get_shortest_distance(int player) const {
    int start = (player == PLAYER_1) ? VIRT_LEFT : VIRT_TOP;
    int end   = (player == PLAYER_1) ? VIRT_RIGHT : VIRT_BOTTOM;

    std::deque<std::pair<int, int>> dq;
    std::vector<int> dist(adj->size(), 9999);

    dist[start] = 0;
    dq.push_front({start, 0});

    while (!dq.empty()) {
        auto [u, d] = dq.front();
        dq.pop_front();

        if (u == end) 
            return d;

        if (d > dist[u]) 
            continue;

        for (int v : (*adj)[u]) {
            int weight = 1;

            // Handle physical node logic
            if (v < rows * cols) {
                if (board[v] == player) 
                    weight = 0; // Already owned = free travel
                else if (board[v] != EMPTY) 
                    continue; // Blocked by opponent

            } else {
                // Virtual nodes have 0 weight
                weight = 0; 
            }

            if (dist[v] > d + weight) {
                dist[v] = d + weight;
                if (weight == 0) 
                    dq.push_front({v, dist[v]});
                else 
                    dq.push_back({v, dist[v]});
            }
        }
    }

    return 9999;
}

bool HexBoard::dfs(int idx, int player, std::vector<bool>& visited, std::vector<int>& path) {
    visited[idx] = true;
    path.push_back(idx);

    int r = idx / cols, c = idx % cols;
    if ((player == PLAYER_1 && c == cols - 1) || (player == PLAYER_2 && r == rows - 1)) 
        return true;

    for (int nb : (*adj)[idx]) {
        // skip virtual nodes
        if (nb >= rows * cols) 
            continue;

        if (board[nb] == player && !visited[nb]) 
            if (dfs(nb, player, visited, path)) 
                return true;
    }

    path.pop_back();

    return false;
}

std::vector<int> HexBoard::get_winning_path(int player) {
    std::vector<bool> visited(rows * cols, false);
    std::vector<int> path;

    if (player == PLAYER_1) {
        for (int r = 0; r < rows; ++r) {
            int idx = get_index(r, 0);

            if (board[idx] == player && dfs(idx, player, visited, path)) 
                return path;
        }

    } else {
        for (int c = 0; c < cols; ++c) {
            int idx = get_index(0, c);
            
            if (board[idx] == player && dfs(idx, player, visited, path)) 
                return path;
        }
    }

    return {};
}

void HexBoard::print_board() const {
    using namespace Colors;

    std::cout << "\n   ";
    for (int c = 0; c < cols; ++c)
        std::cout << BLUE << std::setw(3) << c << " " << RESET;

    std::cout << "\n";

    for (int r = 0; r < rows; ++r) {
        std::string indent = (r % 2 != 0) ? "  " : "";
        
        std::cout << indent << RED << std::setw(2) << r << " " << RESET;

        for (int c = 0; c < cols; ++c) {
            int val = board[get_index(r, c)];

            if (val == PLAYER_1) 
                std::cout << RED << " X  " << RESET;
            else if (val == PLAYER_2) 
                std::cout << BLUE << " O  " << RESET;
            else 
                std::cout << GRAY << " .  " << RESET;
        }

        std::cout << "\n";
    }
}
