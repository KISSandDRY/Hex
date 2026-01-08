#include "HexAI.hpp"

#include <cmath>
#include <vector>
#include <chrono>
#include <cstring>
#include <algorithm>
#include <random>

namespace {

    namespace HeuristicWeights {
        constexpr int BRIDGE_BUILD  = 5'000;
        constexpr int CENTER_BIAS   = 100;
        constexpr int DIST_PENALTY  = 10;
    }

    namespace MCTSParams {
        constexpr double UCT_EXPLORATION = 0.2;
        constexpr double RAVE_BIAS_HARD  = 3'000.0;
        constexpr double RAVE_BIAS_OTHER = 500.0;
        constexpr int TIME_LIMITS[]      = {500, 900, 1'000};
        constexpr int NODE_POOL_SIZE     = 200'000;
    }

    struct MCTSNode {
        int move_idx;
        int parent_idx;
        int player_who_moved;
        
        int visits = 0;
        double wins = 0.0;
        
        double rave_visits = 0.0;
        double rave_wins = 0.0;

        std::vector<int> children;
        std::vector<int> untried;

        MCTSNode(int m, int p, int pl) 
            : move_idx(m), parent_idx(p), player_who_moved(pl) {
                children.reserve(8);
            }
    };

    // Thread Local Storage 
    
    struct ThreadLocalContext {
        std::mt19937 rng{std::random_device{}()};
        
        // Tree Memory
        std::vector<MCTSNode> m_nodes;

        // Simulation Buffers
        std::vector<int> sim_moves;
        std::vector<int> sim_move_pos;
        std::vector<int> p1_moves;
        std::vector<int> p2_moves;
        std::vector<bool> rave_lookup;

        ThreadLocalContext() {
            m_nodes.reserve(MCTSParams::NODE_POOL_SIZE);
            sim_moves.reserve(400);
            sim_move_pos.resize(400, -1);
            p1_moves.reserve(200);
            p2_moves.reserve(200);
            rave_lookup.resize(400, false);
        }

        void reset_tree() {
            m_nodes.clear();
        }

        void ensure_buffer_size(int N) {
            if (sim_move_pos.size() < static_cast<size_t>(N)) {
                sim_move_pos.resize(N, -1);
                rave_lookup.resize(N, false);
            }
        }
    };

    static thread_local ThreadLocalContext ctx;

    namespace Utility {
        inline int toggle_player(int player) { 
            return (player == PLAYER_1) ? PLAYER_2 : PLAYER_1; 
        }

        inline int rand_index(int limit) {
            std::uniform_int_distribution<int> dist(0, limit - 1);
            return dist(ctx.rng);
        }
    }

    namespace Heuristics {
        
        inline bool is_bridge_move(int r, int c, const HexBoard& board, int player) {
            static const int BRIDGE_OFFSETS[6][2] = {
                {-1, -1}, {-1, 2}, {1, -2}, {1, 1}, {-2, 1}, {2, -1}
            };

            for (const auto& off : BRIDGE_OFFSETS) {
                int tr = r + off[0]; 
                int tc = c + off[1];

                if (board.is_valid(tr, tc) && board.get_cell(tr, tc) == player) 
                    return true;
            }

            return false;
        }

        inline int find_common_empty_neighbor(const HexBoard& board, int u, int v, int exclude_idx) {
            const auto& nu = board.get_neighbors(u);
            const auto& nv = board.get_neighbors(v);
            const int N = board.rows * board.cols;

            for (int n1 : nu) {
                // Bounds check and ensure it's empty and not the opponent's move
                if (n1 >= N || n1 == exclude_idx || board.get_cell_by_index(n1) != EMPTY) 
                    continue;

                // Check intersection
                for (int n2 : nv) 
                    if (n1 == n2) 
                        return n1;
            }

            return -1;
        }

        inline int get_bridge_save_move(const HexBoard& board, int last_move_idx, int player_defending) {
            if (last_move_idx == -1) 
                return -1;
            
            const auto& neighbors = board.get_neighbors(last_move_idx);
            const int N = board.rows * board.cols;
            
            // 1. Collect friendly stones touching the opponent's move
            // Using a fixed size buffer on stack is faster than vector for small N
            int friendly[6]; 
            int count = 0;

            for (int n : neighbors) 
                if (n < N && board.get_cell_by_index(n) == player_defending) 
                    friendly[count++] = n;

            if (count < 2) 
                return -1;

            // 2. Check all pairs for a connected bridge that was just intruded
            for (int i = 0; i < count; ++i) {
                for (int j = i + 1; j < count; ++j) {
                    int repair = find_common_empty_neighbor(board, friendly[i], friendly[j], last_move_idx);

                    if (repair != -1) 
                        return repair;
                }
            }

            return -1;
        }

        void sort_untried_moves(std::vector<int>& moves, const HexBoard& board, int player) {
            if (moves.empty()) 
                return;

            // Reuse static buffer to avoid allocation
            static thread_local std::vector<std::pair<int, int>> sort_buffer;
            sort_buffer.clear();
            if(sort_buffer.capacity() < moves.size()) sort_buffer.reserve(moves.size());

            const int center_r = board.rows / 2;
            const int center_c = board.cols / 2;

            for (int m : moves) {
                int score = 0;
                auto [r, c] = board.get_coord(m);

                // Center Bias (Manhattan approximation)
                int dist = std::abs(r - center_r) + std::abs(c - center_c);
                score += (HeuristicWeights::CENTER_BIAS - dist * HeuristicWeights::DIST_PENALTY);

                if (is_bridge_move(r, c, board, player)) 
                    score += HeuristicWeights::BRIDGE_BUILD;

                sort_buffer.push_back({score, m});
            }

            // Sort: Ascending score means highest scores are at the back (efficient for pop_back)
            std::sort(sort_buffer.begin(), sort_buffer.end(), [](const auto& a, const auto& b) {
                return a.first < b.first; 
            });

            for(size_t i = 0; i < moves.size(); ++i) 
                moves[i] = sort_buffer[i].second;
        }
    }

    class MCTS {
        double m_rave_bias;

    public:
        MCTS(const HexBoard& root_board, int root_player, Difficulty diff) {
            // Reset the global thread-local tree
            ctx.reset_tree();
            
            // Configure RAVE
            m_rave_bias = (diff == Difficulty::HARD) ? MCTSParams::RAVE_BIAS_HARD : MCTSParams::RAVE_BIAS_OTHER;

            // Create Root Node
            int opponent = Utility::toggle_player(root_player);
            // Emplace back into the ctx.nodes vector
            ctx.m_nodes.emplace_back(-1, -1, opponent);

            // Init Root Moves
            MCTSNode& root = ctx.m_nodes[0];
            root.untried = root_board.get_legal_moves();

            Heuristics::sort_untried_moves(root.untried, root_board, root_player);
        }

        int run(HexBoard root_board, int time_limit_ms);

    private:
        int select_child(int node_idx) const; 
        int expand(int node_idx, HexBoard& board); 
        std::pair<int, const std::vector<int>&> simulate(HexBoard board, int current_player); 
        void backpropagate(int leaf_idx, int winner, const std::vector<int>& winning_moves); 
        int get_best_move() const;
    };

    int MCTS::select_child(int node_idx) const {
        const auto& node = ctx.m_nodes[node_idx];
        double best_score = -1e9;
        int best_child = -1;

        // Pre-calculate log for UCT
        double log_visits = std::log((double)node.visits + 1);

        for (int child_idx : node.children) {
            const auto& child = ctx.m_nodes[child_idx];
            
            double v  = child.visits + 1e-9;
            double rv = child.rave_visits + 1e-9;
            
            double w  = child.wins / v;
            double rw = child.rave_wins / rv;

            // RAVE Beta
            double beta = rv / (rv + v + m_rave_bias * v * w);
            if (child.visits == 0) 
                beta = 1.0;
            
            double q_rave = (1.0 - beta) * w + beta * rw;

            double explore = MCTSParams::UCT_EXPLORATION * std::sqrt(log_visits / v);
            double score   = q_rave + explore;

            if (score > best_score) {
                best_score = score;
                best_child = child_idx;
            }
        }

        return best_child;
    }

    int MCTS::expand(int node_idx, HexBoard& board) {
        int move = ctx.m_nodes[node_idx].untried.back();
        ctx.m_nodes[node_idx].untried.pop_back();

        int player     = ctx.m_nodes[node_idx].player_who_moved;
        int next_player = Utility::toggle_player(player);
        
        // Add new node to the pool
        ctx.m_nodes.emplace_back(move, node_idx, next_player);
        int child_idx = (int)ctx.m_nodes.size() - 1;
        
        // Safely link parent to child using index
        ctx.m_nodes[node_idx].children.push_back(child_idx);

        // Update Board
        auto [r, c] = board.get_coord(move);
        board.make_move(r, c, next_player);

        // If not terminal, generate moves for the child
        if (board.check_win() == EMPTY) {
            auto& child = ctx.m_nodes[child_idx];
            child.untried = board.get_legal_moves();
            Heuristics::sort_untried_moves(child.untried, board, Utility::toggle_player(next_player));
        }

        return child_idx;
    }

    std::pair<int, const std::vector<int>&> MCTS::simulate(HexBoard board, int current_player) {
        // Clear reuse buffers
        ctx.p1_moves.clear(); 
        ctx.p2_moves.clear(); 
        ctx.sim_moves.clear();
        
        int N = board.rows * board.cols;
        
        // Fast Clear of lookup table (Memset is fastest for POD types)
        // Note: vector::assign or fill is safer, but memset is valid for -1 on 2s complement
        std::memset(ctx.sim_move_pos.data(), -1, N * sizeof(int));
        
        // Populate available moves
        int k = 0;
        for (int i = 0; i < N; ++i) {
            if (board.get_cell_by_index(i) == EMPTY) {
                ctx.sim_moves.push_back(i);
                ctx.sim_move_pos[i] = k++;
            }
        }

        int winner = board.check_win();
        int last_move = -1; 

        while (winner == EMPTY && !ctx.sim_moves.empty()) {
            int selected = -1;

            // 1. Smart Defense (Bridge Save)
            if (last_move != -1) {
                int save = Heuristics::get_bridge_save_move(board, last_move, current_player);

                if (save != -1 && ctx.sim_move_pos[save] != -1) 
                    selected = save;
            }

            // 2. Random Selection
            if (selected == -1) 
                selected = ctx.sim_moves[Utility::rand_index(ctx.sim_moves.size())];

            // 3. Fast Removal (Swap & Pop)
            int idx_in_vec = ctx.sim_move_pos[selected];
            int last_val   = ctx.sim_moves.back();

            ctx.sim_moves[idx_in_vec] = last_val;
            ctx.sim_move_pos[last_val] = idx_in_vec;
            
            ctx.sim_moves.pop_back();
            ctx.sim_move_pos[selected] = -1; // Mark as taken

            // 4. Apply Move
            auto [r, c] = board.get_coord(selected);
            board.make_move(r, c, current_player);
            
            if (current_player == PLAYER_1) 
                ctx.p1_moves.push_back(selected);
            else                            
                ctx.p2_moves.push_back(selected);

            last_move = selected;
            winner = board.check_win();
            current_player = Utility::toggle_player(current_player);
        }

        return {winner, (winner == PLAYER_1 ? ctx.p1_moves : ctx.p2_moves)};
    }

    void MCTS::backpropagate(int leaf_idx, int winner, const std::vector<int>& winning_moves) {
        std::fill(ctx.rave_lookup.begin(), ctx.rave_lookup.end(), false);
        for (int m : winning_moves) 
            ctx.rave_lookup[m] = true;

        int node_idx = leaf_idx;
        while (node_idx != -1) {
            MCTSNode& node = ctx.m_nodes[node_idx];
            node.visits++;
            
            if (node.player_who_moved == winner) 
                node.wins += 1.0;

            // RAVE Update
            // Iterate children to update their AMAF stats
            for (int c_idx : node.children) {
                MCTSNode& child = ctx.m_nodes[c_idx];

                if (ctx.rave_lookup[child.move_idx]) {
                    child.rave_visits++;

                    if (child.player_who_moved == winner) 
                        child.rave_wins += 1.0;
                }
            }

            node_idx = node.parent_idx;
        }
    }

    int MCTS::get_best_move() const {
        int best_move = -1, max_visits = -1;
        
        if (ctx.m_nodes.empty() || ctx.m_nodes[0].children.empty()) 
            return -1;
        
        // Robust child selection (Most Visited)
        for (int child_idx : ctx.m_nodes[0].children) {
            if (ctx.m_nodes[child_idx].visits > max_visits) {
                max_visits = ctx.m_nodes[child_idx].visits;
                best_move = ctx.m_nodes[child_idx].move_idx;
            }
        }

        return best_move;
    }

    int MCTS::run(HexBoard root_board, int time_limit_ms) {
        auto start_time = std::chrono::steady_clock::now();
        int iterations = 0;

        while (true) {
            // Check time every 256 iterations to reduce syscall overhead
            if ((iterations & 0xFF) == 0) {
                auto now = std::chrono::steady_clock::now();

                if (std::chrono::duration_cast<std::chrono::milliseconds>(now - start_time).count() >= time_limit_ms) 
                    break;
                
                // Safety: Stop if we run out of node memory
                if (ctx.m_nodes.size() >= MCTSParams::NODE_POOL_SIZE - 200) 
                    break; 
            }

            int node_idx = 0;
            HexBoard board = root_board;

            // 1. Selection
            while (ctx.m_nodes[node_idx].untried.empty() && !ctx.m_nodes[node_idx].children.empty()) {
                int child = select_child(node_idx);

                if (child == -1) 
                    break;

                node_idx = child;
                auto [r, c] = board.get_coord(ctx.m_nodes[node_idx].move_idx);
                board.make_move(r, c, ctx.m_nodes[node_idx].player_who_moved);
            }

            // 2. Expansion
            if (!ctx.m_nodes[node_idx].untried.empty()) 
                node_idx = expand(node_idx, board);

            // 3. Simulation
            int sim_player = Utility::toggle_player(ctx.m_nodes[node_idx].player_who_moved);
            auto result = simulate(board, sim_player);

            // 4. Backpropagation
            backpropagate(node_idx, result.first, result.second);
            
            iterations++;
        }

        return get_best_move();
    }

} // anonymous namespace

int HexAI::get_move(HexBoard& game, int player, Difficulty diff) {
    ctx.ensure_buffer_size(game.rows * game.cols);

    // Instant Win/Loss Check (Depth 1)
    auto legal = game.get_legal_moves();
    int opponent = Utility::toggle_player(player);

    auto find_instant_outcome = [&](int who) -> int {
        for (int m : legal) {
            HexBoard tmp = game;

            auto [r, c] = tmp.get_coord(m);
            tmp.make_move(r, c, who);

            if (tmp.check_win() == who) 
                return m;
        }

        return -1;
    };

    // Check for immediate win
    if (int win = find_instant_outcome(player); win != -1) 
        return win;

    // Check for immediate loss (Block)
    if (int block = find_instant_outcome(opponent); block != -1) 
        return block;
    
    // Run MCTS
    int time_limit = MCTSParams::TIME_LIMITS[static_cast<int>(diff)];
    MCTS solver(game, player, diff);
    
    return solver.run(game, time_limit);
}
