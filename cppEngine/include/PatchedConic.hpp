#pragma once

#include <Eigen/Dense>

class PatchedConic {
public:
    PatchedConic() = default;
    ~PatchedConic() = default;

    double get_departure_delta_v(const Eigen::Vector3d& v_lambert_dep,
                                 const Eigen::Vector3d& v_planet_dep,
                                 double mu_dep,
                                 double r_park_dep) const;

    double get_arrival_delta_v(const Eigen::Vector3d& v_lambert_arr,
                               const Eigen::Vector3d& v_planet_arr,
                               double mu_arr,
                               double r_park_arr,
                               double e_arr) const;

    double get_total_delta_v(const Eigen::Vector3d& v_lambert_dep, const Eigen::Vector3d& v_planet_dep, double mu_dep, double r_park_dep,
                             const Eigen::Vector3d& v_lambert_arr, const Eigen::Vector3d& v_planet_arr, double mu_arr, double r_park_arr, double e_arr) const;
};