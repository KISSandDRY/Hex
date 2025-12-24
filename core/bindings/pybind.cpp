#include <pybind11/pybind11.h>
#include <pybind11/stl.h> 

#include "HexBoard.hpp"
#include "HexAI.hpp"

namespace py = pybind11;

PYBIND11_MODULE(hexlib, m) {
    m.doc() = "Hex Engine";

    m.attr("PLAYER_1") = PLAYER_1;
    m.attr("PLAYER_2") = PLAYER_2;
    m.attr("EMPTY") = EMPTY;

    py::enum_<Difficulty>(m, "Difficulty")
        .value("EASY", Difficulty::EASY)
        .value("MEDIUM", Difficulty::MEDIUM)
        .value("HARD", Difficulty::HARD)
        .export_values();

    py::class_<HexBoard>(m, "HexBoard")
        .def(py::init<int, int>(), "Initialize Board (rows, cols)")
        
        .def_readonly("rows", &HexBoard::rows)
        .def_readonly("cols", &HexBoard::cols)
        
        .def("make_move", &HexBoard::make_move)
        .def("check_win", &HexBoard::check_win)
        .def("get_legal_moves", &HexBoard::get_legal_moves)
        .def("get_winning_path", &HexBoard::get_winning_path)
        .def("get_shortest_distance", &HexBoard::get_shortest_distance)
        
        .def("get_coord", &HexBoard::get_coord)
        .def("get_index", &HexBoard::get_index)
        .def("get_cell", &HexBoard::get_cell)
        
        .def("print_board", &HexBoard::print_board);

    py::class_<HexAI>(m, "HexAI")
        .def_static("get_move", &HexAI::get_move,
                py::arg("game"), py::arg("player"), py::arg("difficulty"),
                py::call_guard<py::gil_scoped_release>());
}
