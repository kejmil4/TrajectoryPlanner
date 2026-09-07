#include <pybind11/pybind11.h>
#include <pybind11/eigen.h>
#include "../include/LambertSolver.hpp"
#include "../include/KeplerPropagator.hpp"
#include "../include/PatchedConic.hpp"
#include "../include/TrajectoryOptimizer.hpp"

namespace py = pybind11;


int test_connection(int a, int b) {
    return a + b;
}

PYBIND11_MODULE(cppEngine, m) {
    m.doc() = "C++ Math Engine for Trajectory Planning";

    py::class_<LambertSolver>(m, "LambertSolver")
        .def(py::init<int, double, double>(),
             py::arg("max_iter"), py::arg("mu"), py::arg("tolerance"))
        .def("solve", &LambertSolver::solve,
             "Solves Lambert's problem",
             py::arg("r1"), py::arg("r2"), py::arg("tof"), py::arg("long_way") = false);

    py::class_<KeplerPropagator>(m, "KeplerPropagator")
        .def(py::init<double, double, int>(),
             py::arg("mu"), py::arg("tolerance") = 1e-8, py::arg("max_iter") = 100)
        .def("propagate", &KeplerPropagator::propagate,
             "Propagates an initial state vector forward in time",
             py::arg("r0"), py::arg("v0"), py::arg("dt"));

     py::class_<PatchedConic>(m, "PatchedConic")
         .def(py::init<>())
         .def("get_departure_delta_v", &PatchedConic::get_departure_delta_v,
              "Calculates departure Delta V",
              py::arg("v_lambert_dep"), py::arg("v_planet_dep"), py::arg("mu_dep"), py::arg("r_park_dep"))
         .def("get_arrival_delta_v", &PatchedConic::get_arrival_delta_v,
              "Calculates arrival Delta V",
              py::arg("v_lambert_arr"), py::arg("v_planet_arr"), py::arg("mu_arr"), py::arg("r_park_arr"))
         .def("get_total_delta_v", &PatchedConic::get_total_delta_v,
              "Calculates total mission Delta V",
              py::arg("v_lambert_dep"), py::arg("v_planet_dep"), py::arg("mu_dep"), py::arg("r_park_dep"),
              py::arg("v_lambert_arr"), py::arg("v_planet_arr"), py::arg("mu_arr"), py::arg("r_park_arr"));

     py::class_<TrajectoryOptimizer>(m, "TrajectoryOptimizer")
        .def(py::init<const LambertSolver&, const PatchedConic&>(),
             py::arg("solver"), py::arg("patched_conic"))
        .def("optimize_grid", &TrajectoryOptimizer::optimize_grid,
             "Executes the grid search for delta-V costs over a matrix of departure and arrival states",
             py::arg("dep_states"), py::arg("arr_states"), py::arg("tofs"),
             py::arg("mu_dep"), py::arg("r_park_dep"), py::arg("mu_arr"), py::arg("r_park_arr"), py::arg("long_way") = true);
}