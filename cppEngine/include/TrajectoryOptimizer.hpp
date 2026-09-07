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
    TrajectoryOptimizer(const LambertSolver& solver, const PatchedConic& patched_conic);
    ~TrajectoryOptimizer() = default;

    // Executes the grid search using dynamic planetary parameters
    std::tuple<Eigen::MatrixXd, Eigen::MatrixXd, Eigen::MatrixXd> optimize_grid(
        const Eigen::MatrixXd& dep_states,
        const Eigen::MatrixXd& arr_states,
        const Eigen::MatrixXd& tofs,
        double mu_dep,
        double r_park_dep,
        double mu_arr,
        double r_park_arr,
        bool long_way = true
    ) const;
};