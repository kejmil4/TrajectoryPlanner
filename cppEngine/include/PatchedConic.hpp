#pragma once

#include <Eigen/Dense>

class PatchedConic {
private:
    double mu_earth;
    double mu_mars;
    
    // Standard parking orbit radii (km)
    double r_park_earth; 
    double r_park_mars;  

public:
    PatchedConic(double mu_earth, double mu_mars, double r_park_earth, double r_park_mars);
    ~PatchedConic() = default;

    double get_departure_delta_v(const Eigen::Vector3d& v_lambert_dep, const Eigen::Vector3d& v_earth) const;

    double get_arrival_delta_v(const Eigen::Vector3d& v_lambert_arr, const Eigen::Vector3d& v_mars) const;

    double get_total_delta_v(const Eigen::Vector3d& v_lambert_dep, const Eigen::Vector3d& v_earth,
                             const Eigen::Vector3d& v_lambert_arr, const Eigen::Vector3d& v_mars) const;
};