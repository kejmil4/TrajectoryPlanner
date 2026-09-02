#pragma once

#include <Eigen/Dense>
#include <tuple>

class LambertSolver {
private:
    double mu;
    double tolerance;
    int max_iter;

    double x2tof(double x, double s, double c, int lw);
public:

    LambertSolver(int max_iter, double mu, double tolerance);
    ~LambertSolver() = default;

    double GetMu() const;
    double GetTolerance() const;
    int GetMaxIter() const;

    std::tuple<Eigen::Vector3d, Eigen::Vector3d> solve(const Eigen::Vector3d& r1, const Eigen::Vector3d& r2, double tof, bool long_way = false);

};
