# Hex Game

Hex is a strategic board game played on a hexagonal grid where two players aim to connect their opposite sides with a continuous chain of stones.

This project implements a Hybrid C++/Python architecture:
* Core Logic & AI: Written in C++17 (using Monte Carlo Tree Search + RAVE + DSU).
* GUI: Written in Python (using Pygame).
* Integration: Pybind11 is used to compile the C++ core into a Python module (`hexlib`).

---

## Features

* Simple AI: Implements MCTS (Monte Carlo Tree Search) with RAVE (Rapid Action Value Estimation) heuristics.
* Performance: C++ backend allows for >100,000 simulations per second.
* GUI: Visualization using Pygame with move history and winning path highlighting.
* Algorithms: Uses Disjoint Set Union (DSU) for $O(1)$ win detection and memory pools for tree storage.

---

## Prerequisites

Before building, ensure you have the following installed:

1.  C++ Compiler supporting C++17 (GCC, Clang, or MSVC).
2.  CMake (version 3.10 or higher).
3.  Python (3.8+).
4.  Python Libraries:
    ```bash
    pip install -r requirements.txt
    ```

---

## Building the Project

The C++ core must be compiled into a shared library before running the game.

### 1. Clone the repository
```bash
git clone https://github.com/KISSandDRY/Hex.git
cd Hex
mkdir build
cd build
```

### 2. Build the project
#### 2.1 Windows
```
cmake ..
cmake --build . --config Release
```

#### 2.2 Linux 
```
cmake ..
make
```

### 3. Running Hex

To run Hex game, just run main.py file from gui.

```
cd gui
python main.py
```
---
