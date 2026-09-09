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

double PatchedConic::get_arrival_delta_v(const Eigen::Vector3d &v_lambert_arr, const Eigen::Vector3d &v_planet_arr, double mu_arr, double r_park_arr, double e_arr) const {
    if (e_arr < 0.0) { // direct entry
        return 0.0;
    }
    double v_inf = (v_lambert_arr - v_planet_arr).norm();

    // Parking Orbit Velocity at periapsis of the chosen elliptical orbit
    double v_park = std::sqrt((mu_arr / r_park_arr) * (1.0 + e_arr));

    double v_peri = std::sqrt(v_inf * v_inf + (2.0 * mu_arr) / r_park_arr);

    return std::max(0.0, v_peri - v_park);
}

double PatchedConic::get_total_delta_v(const Eigen::Vector3d &v_lambert_dep, const Eigen::Vector3d &v_planet_dep, double mu_dep, double r_park_dep,
                                       const Eigen::Vector3d &v_lambert_arr, const Eigen::Vector3d &v_planet_arr, double mu_arr, double r_park_arr, double e_arr) const {
    return get_departure_delta_v(v_lambert_dep, v_planet_dep, mu_dep, r_park_dep) +
           get_arrival_delta_v(v_lambert_arr, v_planet_arr, mu_arr, r_park_arr, e_arr);
}