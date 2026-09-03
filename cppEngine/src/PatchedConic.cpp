#include "../include/PatchedConic.hpp"
#include <cmath>

PatchedConic::PatchedConic(double mu_earth, double mu_mars, double r_park_earth, double r_park_mars)
    : mu_earth(mu_earth), mu_mars(mu_mars), r_park_earth(r_park_earth), r_park_mars(r_park_mars)
{}

double PatchedConic::get_departure_delta_v(const Eigen::Vector3d &v_lambert_dep, const Eigen::Vector3d &v_earth) const {
    //  Hyperbolic Excess Velocity (v_inf)
    double v_inf = (v_lambert_dep - v_earth).norm();

    // Parking Orbit Velocity
    double v_park = std::sqrt(mu_earth / r_park_earth);

    // Velocity at Periapsis (Energy Conservation)
    double v_peri = std::sqrt(v_inf * v_inf + (2.0 * mu_earth) / r_park_earth);

    // Required Delta V
    return v_peri - v_park;
}

double PatchedConic::get_arrival_delta_v(const Eigen::Vector3d &v_lambert_arr, const Eigen::Vector3d &v_mars) const {
    // Hyperbolic Excess Velocity (v_inf) relative to Mars
    double v_inf = (v_lambert_arr - v_mars).norm();

    // Parking Orbit Velocity around Mars
    double v_park = std::sqrt(mu_mars / r_park_mars);

    // Velocity at Periapsis (Energy Conservation)
    double v_peri = std::sqrt(v_inf * v_inf + (2.0 * mu_mars) / r_park_mars);

    // Required Delta V for circularization insertion
    return v_peri - v_park;
}

double PatchedConic::get_total_delta_v(const Eigen::Vector3d &v_lambert_dep, const Eigen::Vector3d &v_earth,
                                       const Eigen::Vector3d &v_lambert_arr, const Eigen::Vector3d &v_mars) const {
    return get_departure_delta_v(v_lambert_dep, v_earth) + get_arrival_delta_v(v_lambert_arr, v_mars);
}