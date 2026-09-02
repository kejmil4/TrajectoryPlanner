#include <pybind11/pybind11.h>
#include <pybind11/eigen.h>
#include "../include/LambertSolver.hpp"

namespace py = pybind11;


int test_connection(int a, int b) {
    return a + b;
}

PYBIND11_MODULE(cppEngine, m) {
    m.doc() = "C++ Math Engine for Trajectory Planning";
    
    // m.def("test_connection", &test_connection, "Adds two numbers to test the Python-C++ bridge");

    py::class_<LambertSolver>(m, "LambertSolver")
        .def(py::init<int, double, double>(),
             py::arg("max_iter"), py::arg("mu"), py::arg("tolerance"))
        .def("solve", &LambertSolver::solve,
             "Solves Lambert's problem",
             py::arg("r1"), py::arg("r2"), py::arg("tof"), py::arg("long_way") = false);
}