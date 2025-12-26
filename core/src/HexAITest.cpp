#include "HexBoard.hpp"
#include "HexAI.hpp"

#include <chrono>
#include <string>
#include <thread>
#include <iomanip>
#include <iostream>

// Constants

namespace Console {
    const std::string RED   = "\033[31m";
    const std::string BLUE  = "\033[34m";
    const std::string RESET = "\033[0m";
    const std::string CLS   = "\033[2J";   // Clear Screen
    const std::string HOME  = "\033[H";    // Move cursor to top-left
    const std::string ERASE_DOWN = "\033[J"; // Erase everything below cursor
    
    const std::string PAD   = "                "; 

    void clear() { 
        std::cout << CLS; 
    }

    void home() { 
        std::cout << HOME; 
    }
}

Difficulty int_to_diff(int d) {
    if (d == 1) 
        return Difficulty::EASY;

    if (d == 2) 
        return Difficulty::MEDIUM;

    return Difficulty::HARD;
}

std::string diff_to_string(Difficulty d) {
    if (d == Difficulty::EASY) 
        return "EASY";

    if (d == Difficulty::MEDIUM) 
        return "MED";

    return "HARD";
}

// Data structures

struct SimConfig {
    int board_size;
    int num_games;
    Difficulty d1;
    Difficulty d2;
    std::string name1;
    std::string name2;
};

struct SimStats {
    int wins1 = 0;
    int wins2 = 0;
    int moves_total = 0;
};

struct GameState {
    int game_idx;
    int move_count;
    int current_player;
    int last_r = -1;
    int last_c = -1;
    bool p1_is_algo1; // True if AI#1 is playing RED (Player 1)
};

// UI

void draw_progress_bar(int current, int total) {
    double progress = (double)current / total;
    int bar_width = 20;

    std::cout << "[";
    int pos = bar_width * progress;
    for (int j = 0; j < bar_width; ++j) {
        if (j < pos) std::cout << "=";
        else if (j == pos) std::cout << ">";
        else std::cout << " ";
    }
    std::cout << "] " << int(progress * 100.0) << "%\n";
}

void draw_matchup_info(const SimConfig& cfg, const GameState& state) {
    std::string p1_label = state.p1_is_algo1 ? cfg.name1 : cfg.name2;
    std::string p2_label = state.p1_is_algo1 ? cfg.name2 : cfg.name1;

    std::cout << "CURRENT MATCHUP:\n";
    std::cout << "  " << Console::RED  << "RED (P1)"  << Console::RESET << "  = " << p1_label << Console::PAD << "\n";
    std::cout << "  " << Console::BLUE << "BLUE (P2)" << Console::RESET << " = " << p2_label << Console::PAD << "\n";
    std::cout << std::string(40, '-') << "\n";

    std::string mover_name = (state.current_player == PLAYER_1) ? p1_label : p2_label;
    std::string color_code = (state.current_player == PLAYER_1) ? Console::RED : Console::BLUE;

    std::cout << "Last Move: " << color_code << mover_name << Console::RESET
              << " -> (" << state.last_r << ", " << state.last_c << ")" << Console::PAD << "\n";
}

void update_screen(const HexBoard& game, const SimConfig& cfg, const SimStats& stats, const GameState& state) {
    Console::home(); // Move cursor to top without clearing (anti-flicker)

    // 1. Header & Progress
    std::cout << "=== SIMULATION (" << (state.game_idx + 1) << "/" << cfg.num_games << ") ===\n";
    draw_progress_bar(state.game_idx, cfg.num_games);

    // 2. Scoreboard
    std::cout << "Total Score: " << cfg.name1 << ": " << stats.wins1 
              << " | " << cfg.name2 << ": " << stats.wins2 << Console::PAD << "\n";
    std::cout << std::string(40, '-') << "\n";

    // 3. Match Details
    draw_matchup_info(cfg, state);

    // 4. Board
    game.print_board();

    // 5. Cleanup bottom of screen
    std::cout << Console::ERASE_DOWN;
    std::cout.flush();
}

// Input

SimConfig get_user_input() {
    SimConfig cfg;
    int d1_in, d2_in;

    std::cout << "\n=== AI vs AI TOURNAMENT ===\n";
    std::cout << "Board Size: "; std::cin >> cfg.board_size;
    
    std::cout << "Select AI #1 Difficulty (1-Easy, 2-Med, 3-Hard): "; std::cin >> d1_in;
    std::cout << "Select AI #2 Difficulty (1-Easy, 2-Med, 3-Hard): "; std::cin >> d2_in;
    std::cout << "Number of games: "; std::cin >> cfg.num_games;

    cfg.d1 = int_to_diff(d1_in);
    cfg.d2 = int_to_diff(d2_in);
    cfg.name1 = "AI#1(" + diff_to_string(cfg.d1) + ")";
    cfg.name2 = "AI#2(" + diff_to_string(cfg.d2) + ")";

    return cfg;
}

void run_benchmark() {
    Console::clear();
    SimConfig cfg = get_user_input();
    SimStats stats;

    Console::clear();
    auto start_time = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < cfg.num_games; ++i) {
        HexBoard game(cfg.board_size, cfg.board_size);
        
        // Even games: AI#1 is Red. Odd games: AI#2 is Red.
        bool p1_is_algo1 = (i % 2 == 0); 
        
        Difficulty red_diff  = p1_is_algo1 ? cfg.d1 : cfg.d2;
        Difficulty blue_diff = p1_is_algo1 ? cfg.d2 : cfg.d1;

        GameState state;
        state.game_idx = i;
        state.current_player = PLAYER_1;
        state.p1_is_algo1 = p1_is_algo1;
        state.move_count = 0;

        while (true) {
            int winner = game.check_win();

            if (winner != EMPTY) {
                // Determine which Algorithm won based on who was playing which color
                if (winner == PLAYER_1) {
                    if (p1_is_algo1) 
                        stats.wins1++; 
                    else 
                        stats.wins2++;
                } else {
                    if (p1_is_algo1) 
                        stats.wins2++; 
                    else 
                        stats.wins1++;
                }

                break; // Game Over
            }

            // AI Turn
            Difficulty current_diff = (state.current_player == PLAYER_1) ? red_diff : blue_diff;
            int move = HexAI::get_move(game, state.current_player, current_diff);
            
            auto [r, c] = game.get_coord(move);
            game.make_move(r, c, state.current_player);
            
            // Update State
            state.move_count++;
            state.last_r = r;
            state.last_c = c;

            // Render
            update_screen(game, cfg, stats, state);
            std::this_thread::sleep_for(std::chrono::milliseconds(50));

            // Switch Turn
            state.current_player = (state.current_player == PLAYER_1) ? PLAYER_2 : PLAYER_1;
        }
        stats.moves_total += state.move_count;
    }

    // Final Results
    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end_time - start_time;

    std::cout << "\n\n=== FINAL STATISTICS ===\n";
    std::cout << cfg.name1 << " Total Wins: " << stats.wins1 << "\n";
    std::cout << cfg.name2 << " Total Wins: " << stats.wins2 << "\n";
    std::cout << "Total Time: " << std::setprecision(2) << elapsed.count() << "s\n";
    std::cout << "Avg Moves:  " << (int)(stats.moves_total / cfg.num_games) << "\n";
}

int main() {
    run_benchmark();
    return 0;
}
