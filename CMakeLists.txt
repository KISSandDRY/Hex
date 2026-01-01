cmake_minimum_required(VERSION 3.15)
project(hexlib)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(MSVC)
    add_compile_options(/O2)
    set(CMAKE_CXX_FLAGS_RELEASE "/O2 /Zi" CACHE STRING "" FORCE)
    set(CMAKE_CXX_FLAGS_DEBUG "/Od /Zi" CACHE STRING "" FORCE)
    set(CMAKE_CXX_FLAGS_RELWITHDEBINFO "/O2 /Zi" CACHE STRING "" FORCE)
else()
    add_compile_options(-O3 -march=native)
endif()

set(CORE_SRC_DIR "${CMAKE_SOURCE_DIR}/core/src")
set(CORE_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/core/include")
set(BINDINGS_DIR "${CMAKE_SOURCE_DIR}/core/bindings")

file(GLOB_RECURSE HEX_SOURCES
    "${CORE_SRC_DIR}/*.cpp"
)

file(GLOB_RECURSE HEX_HEADERS
    "${CORE_INCLUDE_DIR}/*.hpp"
)

add_library(hex_core STATIC ${HEX_SOURCES} ${HEX_HEADERS})
target_include_directories(hex_core PUBLIC ${CORE_INCLUDE_DIR})

set_target_properties(hex_core PROPERTIES POSITION_INDEPENDENT_CODE ON)

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

include(FetchContent)
FetchContent_Declare(
  pybind11
  GIT_REPOSITORY https://github.com/pybind/pybind11
  GIT_TAG        v2.11.1
)
FetchContent_MakeAvailable(pybind11)

pybind11_add_module(hexlib ${BINDINGS_DIR}/pybind.cpp)
target_link_libraries(hexlib PRIVATE hex_core)

add_custom_command(TARGET hexlib POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
    $<TARGET_FILE:hexlib>
    ${CMAKE_SOURCE_DIR}/gui/app/engine/$<TARGET_FILE_NAME:hexlib>
)

add_custom_command(TARGET hexlib POST_BUILD
    COMMAND ${Python3_EXECUTABLE} -m pybind11_stubgen hexlib --output-dir "${CMAKE_SOURCE_DIR}/gui/app/engine"
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}/gui/app/engine"
)

file(GLOB TEST_SOURCES "${CORE_SRC_DIR}/HexAITest.cpp")
add_executable(hex_test ${TEST_SOURCES})
target_link_libraries(hex_test PRIVATE hex_core)
target_include_directories(hex_test PRIVATE ${CORE_INCLUDE_DIR})
