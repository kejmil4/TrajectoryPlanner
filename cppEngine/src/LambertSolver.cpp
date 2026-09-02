#include "../../cppEngine/include/LambertSolver.hpp"
#include <cmath>

LambertSolver::LambertSolver(int max_iter, double mu, double tolerance)
 : max_iter(max_iter), mu(mu), tolerance(tolerance) {}

int LambertSolver::GetMaxIter() const {
    return max_iter;
}

double LambertSolver::GetTolerance() const {
    return tolerance;
}

double LambertSolver::GetMu() const {
    return mu;
}

double LambertSolver::x2tof(double x, double s, double c, int lw) {
    double a = s / (2.0 * (1.0 - x * x));
    double alpha, beta, t;

    if (x < 0.999999) { // Ellipse
        alpha = 2.0 * std::acos(x);
        beta = 2.0 * std::asin(std::sqrt((s - c) / (2.0 * a)));
        if (lw == 1) beta *= -1.0;

        t = a * std::sqrt(a) * (alpha - std::sin(alpha) - (beta - std::sin(beta)));
        return t;
    }
    else if (x > 1.000001) { // Hyperbola
        alpha = 2.0 * std::acosh(x);
        beta = 2.0 * std::asinh(std::sqrt((c - s) / (2.0 * a)));

        t = -a * std::sqrt(-a) * (std::sinh(alpha) - alpha - (std::sinh(beta) - beta));
        return t;
    }
    else { // Parabola
        if (lw == 1) {
            return (std::sqrt(2.0) / 3.0) * (std::pow(s, 1.5) + std::pow(s - c, 1.5));
        }
        return (std::sqrt(2.0) / 3.0) * (std::pow(s, 1.5) - std::pow(s - c, 1.5));
    }
}

std::tuple<Eigen::Vector3d, Eigen::Vector3d> LambertSolver::solve(const Eigen::Vector3d& r1, const Eigen::Vector3d& r2, double tof, bool long_way) {
    // Non-Dimensionalization
    double R = r1.norm();
    double V = std::sqrt(mu / R);
    double T = R / V;

    double t = tof / T;
    Eigen::Vector3d r1_nd = r1 / R;
    Eigen::Vector3d r2_nd = r2 / R;

    // Space Triangle Geometry
    double r2_mod = r2_nd.norm();
    double dot_prod = r1_nd.dot(r2_nd);
    double theta = std::acos(dot_prod / r2_mod);

    int lw = long_way ? 1 : 0;
    if (lw == 1) theta = 2.0 * M_PI - theta;

    double c = std::sqrt(1.0 + r2_mod * r2_mod - 2.0 * r2_mod * std::cos(theta));
    double s = (1.0 + r2_mod + c) / 2.0;
    double am = s / 2.0;
    double lambda = std::sqrt(r2_mod) * std::cos(theta / 2.0) / s;

    // Logarithmic Root-Finding (Regula Falsi)
    double x1 = std::log(0.4767);
    double x2 = std::log(1.5233);
    double y1 = std::log(x2tof(std::exp(x1) - 1.0, s, c, lw)) - std::log(t);
    double y2 = std::log(x2tof(std::exp(x2) - 1.0, s, c, lw)) - std::log(t);

    double err = 1.0;
    double x_new = 0.0, y_new = 0.0;
    int iter = 0;

    while ((err > tolerance) && (y1 != y2) && (iter < max_iter)) {
        iter++;
        x_new = (x1 * y2 - y1 * x2) / (y2 - y1);
        y_new = std::log(x2tof(std::exp(x_new) - 1.0, s, c, lw)) - std::log(t);

        x1 = x2;
        y1 = y2;
        x2 = x_new;
        y2 = y_new;

        err = std::abs(x1 - x_new);
    }

    double x = std::exp(x_new) - 1.0;
    double a = am / (1.0 - x * x);

    // Orbital Elements Reconstruction
    double alfa, beta, psi, eta2, eta;
    if (x < 1.0) { // Ellipse
        beta = 2.0 * std::asin(std::sqrt((s - c) / (2.0 * a)));
        if (lw == 1) beta = -beta;
        alfa = 2.0 * std::acos(x);
        psi = (alfa - beta) / 2.0;
        eta2 = 2.0 * a * std::pow(std::sin(psi), 2) / s;
        eta = std::sqrt(eta2);
    } else { // Hyperbola
        beta = 2.0 * std::asinh(std::sqrt((c - s) / (2.0 * a)));
        if (lw == 1) beta = -beta;
        alfa = 2.0 * std::acosh(x);
        psi = (alfa - beta) / 2.0;
        eta2 = -2.0 * a * std::pow(std::sinh(psi), 2) / s;
        eta = std::sqrt(eta2);
    }

    //  Generate Velocity Vectors
    double p = (r2_mod / (am * eta2)) * std::pow(std::sin(theta / 2.0), 2);
    double sigma1 = (1.0 / (eta * std::sqrt(am))) * (2.0 * lambda * am - (lambda + x * eta));

    Eigen::Vector3d ih = r1_nd.cross(r2_nd).normalized();
    if (lw == 1) ih = -ih;

    double vr1 = sigma1;
    double vt1 = std::sqrt(p);
    Eigen::Vector3d dum = ih.cross(r1_nd); // Local horizontal vector

    Eigen::Vector3d v1_nd = vr1 * r1_nd + vt1 * dum;

    double vt2 = vt1 / r2_mod;
    double vr2 = -vr1 + (vt1 - vt2) / std::tan(theta / 2.0);
    Eigen::Vector3d r2_vers = r2_nd.normalized();
    Eigen::Vector3d dum2 = ih.cross(r2_vers);

    Eigen::Vector3d v2_nd = vr2 * r2_vers + vt2 * dum2;

    // Re-dimensionalize and Return
    Eigen::Vector3d v1 = v1_nd * V;
    Eigen::Vector3d v2 = v2_nd * V;

    return std::make_tuple(v1, v2);
}
