cmake_minimum_required(VERSION 3.15)
project(hexlib)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

if(MSVC)
    add_compile_options(/O2)
else()
    add_compile_options(-O3 -march=native)
endif()

set(HEX_SOURCES
    src/HexBoard.cpp
    src/HexAI.cpp
)

set(HEX_HEADERS
    include/HexBoard.hpp
    include/HexAI.hpp
    include/DSU.hpp
)

add_library(hex_core STATIC ${HEX_SOURCES} ${HEX_HEADERS})
target_include_directories(hex_core PUBLIC include)

set(Python3_FIND_VIRTUALENV FIRST)

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

include(FetchContent)
FetchContent_Declare(
  pybind11
  GIT_REPOSITORY https://github.com/pybind/pybind11
  GIT_TAG        v2.11.1
)
FetchContent_MakeAvailable(pybind11)

pybind11_add_module(hexlib bindings/pybind.cpp)

target_link_libraries(hexlib PRIVATE hex_core)

add_custom_command(TARGET hexlib POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
    $<TARGET_FILE:hexlib>
    ${CMAKE_SOURCE_DIR}/../gui/hexlib.pyd
)
