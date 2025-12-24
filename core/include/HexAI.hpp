#ifndef HEX_AI_HPP
#define HEX_AI_HPP

#include "HexBoard.hpp"

enum class Difficulty { 
    EASY, MEDIUM, HARD 
};

class HexAI {
public:
    static int get_move(HexBoard& game, int player, Difficulty diff);
};

#endif // HEX_AI_HPP
