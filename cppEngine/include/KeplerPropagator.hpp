#pragma once

#include <Eigen/Dense>
#include <tuple>

class KeplerPropagator {
private:
    double mu;
    double tolerance;
    int max_iter;

    double stumpff_C(double z) const;
    double stumpff_S(double z) const;

public:
    KeplerPropagator(double mu, double tolerance = 1e-8, int max_iter = 100);
    ~KeplerPropagator() = default;

    double GetMu() const;
    double GetTolerance() const;
    int GetMaxIter() const;

    std::tuple<Eigen::Vector3d, Eigen::Vector3d> propagate(
        const Eigen::Vector3d& r0, 
        const Eigen::Vector3d& v0, 
        double dt) const;
};