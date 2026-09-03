cmake_minimum_required(VERSION 3.15)
project(TrajectoryPlanner LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(EIGEN_BUILD_TESTING OFF CACHE BOOL "" FORCE)
set(EIGEN_BUILD_DOC OFF CACHE BOOL "" FORCE)

include(FetchContent)
FetchContent_Declare(
        eigen
        GIT_REPOSITORY https://gitlab.com/libeigen/eigen.git
        GIT_TAG 3.4.0
)
FetchContent_MakeAvailable(eigen)

set(Python3_EXECUTABLE "${CMAKE_SOURCE_DIR}/venv/bin/python")

find_package(Python3 COMPONENTS Interpreter Development.Module REQUIRED)

execute_process(
        COMMAND "${Python3_EXECUTABLE}" -m pybind11 --cmakedir
        OUTPUT_VARIABLE PYBIND11_CMAKE_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
)
list(APPEND CMAKE_PREFIX_PATH "${PYBIND11_CMAKE_DIR}")
find_package(pybind11 CONFIG REQUIRED)


pybind11_add_module(cppEngine
        cppEngine/src/bindings.cpp
        cppEngine/src/LambertSolver.cpp
        cppEngine/src/KeplerPropagator.cpp
        cppEngine/src/PatchedConic.cpp
)

target_include_directories(cppEngine PRIVATE ${eigen_SOURCE_DIR})

set_target_properties(cppEngine PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/pythonApp"
)