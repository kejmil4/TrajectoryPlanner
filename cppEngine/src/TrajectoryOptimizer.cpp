#include "../include/TrajectoryOptimizer.hpp"
#include <limits>
#include <cmath>

TrajectoryOptimizer::TrajectoryOptimizer(const LambertSolver& solver, const PatchedConic& patched_conic)
    : solver(solver), patched_conic(patched_conic) {}

std::tuple<Eigen::MatrixXd, Eigen::MatrixXd, Eigen::MatrixXd> TrajectoryOptimizer::optimize_grid(
    const Eigen::MatrixXd& dep_states,
    const Eigen::MatrixXd& arr_states,
    const Eigen::MatrixXd& tofs,
    double mu_dep,
    double r_park_dep,
    double mu_arr,
    double r_park_arr,
    bool long_way
) const {

    int num_deps = dep_states.rows();
    int num_arrs = arr_states.rows();

    double nan = std::numeric_limits<double>::quiet_NaN();
    Eigen::MatrixXd dep_dv_grid = Eigen::MatrixXd::Constant(num_deps, num_arrs, nan);
    Eigen::MatrixXd arr_dv_grid = Eigen::MatrixXd::Constant(num_deps, num_arrs, nan);
    Eigen::MatrixXd tot_dv_grid = Eigen::MatrixXd::Constant(num_deps, num_arrs, nan);

    for (int i = 0; i < num_deps; ++i) {
        // Extract 3D position (head) and 3D velocity (tail) for the departure planet[cite: 11]
        Eigen::Vector3d r1 = dep_states.row(i).head<3>();
        Eigen::Vector3d v_planet_dep = dep_states.row(i).tail<3>();

        for (int j = 0; j < num_arrs; ++j) {
            double tof = tofs(i, j);

            if (tof <= 0) {
                continue;
            }

            // Extract 3D position (head) and 3D velocity (tail) for the arrival planet[cite: 11]
            Eigen::Vector3d r2 = arr_states.row(j).head<3>();
            Eigen::Vector3d v_planet_arr = arr_states.row(j).tail<3>();

            try {
                auto [v1, v2] = solver.solve(r1, r2, tof, long_way);

                // Pass the dynamic parameters directly into the stateless evaluator[cite: 12]
                double dv_dep = patched_conic.get_departure_delta_v(v1, v_planet_dep, mu_dep, r_park_dep);
                double dv_arr = patched_conic.get_arrival_delta_v(v2, v_planet_arr, mu_arr, r_park_arr);

                dep_dv_grid(i, j) = dv_dep;
                arr_dv_grid(i, j) = dv_arr;
                tot_dv_grid(i, j) = dv_dep + dv_arr;
                
            } catch (...) {
                continue;
            }
        }
    }

    return std::make_tuple(dep_dv_grid, arr_dv_grid, tot_dv_grid);
}