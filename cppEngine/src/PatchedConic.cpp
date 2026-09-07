#include "../include/PatchedConic.hpp"
#include <cmath>

double PatchedConic::get_departure_delta_v(const Eigen::Vector3d &v_lambert_dep, const Eigen::Vector3d &v_planet_dep, double mu_dep, double r_park_dep) const {
    // Hyperbolic Excess Velocity (v_inf)
    double v_inf = (v_lambert_dep - v_planet_dep).norm();

    // Parking Orbit Velocity
    double v_park = std::sqrt(mu_dep / r_park_dep);

    // Velocity at Periapsis (Energy Conservation)
    double v_peri = std::sqrt(v_inf * v_inf + (2.0 * mu_dep) / r_park_dep);

    // Required Delta V
    return v_peri - v_park;
}

double PatchedConic::get_arrival_delta_v(const Eigen::Vector3d &v_lambert_arr, const Eigen::Vector3d &v_planet_arr, double mu_arr, double r_park_arr) const {
    // Hyperbolic Excess Velocity (v_inf) relative to the arrival planet
    double v_inf = (v_lambert_arr - v_planet_arr).norm();

    // Parking Orbit Velocity around the arrival planet
    double v_park = std::sqrt(mu_arr / r_park_arr);

    // Velocity at Periapsis (Energy Conservation)
    double v_peri = std::sqrt(v_inf * v_inf + (2.0 * mu_arr) / r_park_arr);

    // Required Delta V for circularization insertion
    return v_peri - v_park;
}

double PatchedConic::get_total_delta_v(const Eigen::Vector3d &v_lambert_dep, const Eigen::Vector3d &v_planet_dep, double mu_dep, double r_park_dep,
                                       const Eigen::Vector3d &v_lambert_arr, const Eigen::Vector3d &v_planet_arr, double mu_arr, double r_park_arr) const {
    return get_departure_delta_v(v_lambert_dep, v_planet_dep, mu_dep, r_park_dep) +
           get_arrival_delta_v(v_lambert_arr, v_planet_arr, mu_arr, r_park_arr);
}