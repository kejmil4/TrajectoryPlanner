#pragma once

#include <Eigen/Dense>
#include <tuple>
#include "LambertSolver.hpp"
#include "PatchedConic.hpp"

class TrajectoryOptimizer {
private:
    LambertSolver solver;
    PatchedConic patched_conic;

public:
    // Initialize with our pre-configured physics engines
    TrajectoryOptimizer(const LambertSolver& solver, const PatchedConic& patched_conic);
    ~TrajectoryOptimizer() = default;

    // Executes the grid search
    // dep_states: N x 6 matrix of Earth states [x, y, z, vx, vy, vz]
    // arr_states: M x 6 matrix of Mars states [x, y, z, vx, vy, vz]
    // tofs: N x M matrix of times of flight in seconds
    // Returns a tuple of 3 matrices (N x M): [Departure dV, Arrival dV, Total dV]
    std::tuple<Eigen::MatrixXd, Eigen::MatrixXd, Eigen::MatrixXd> optimize_grid(
        const Eigen::MatrixXd& dep_states,
        const Eigen::MatrixXd& arr_states,
        const Eigen::MatrixXd& tofs,
        bool long_way = true
    ) const;
};