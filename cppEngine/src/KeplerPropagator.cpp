#include "../include/KeplerPropagator.hpp"
#include <cmath>

KeplerPropagator::KeplerPropagator(double mu, double tolerance, int max_iter)
    : mu(mu), tolerance(tolerance), max_iter(max_iter) {}

int KeplerPropagator::GetMaxIter() const { return max_iter; }
double KeplerPropagator::GetTolerance() const { return tolerance; }
double KeplerPropagator::GetMu() const { return mu; }

double KeplerPropagator::stumpff_C(double z) const {
    if (z > 1e-6) { // Ellipse
        return (1.0 - std::cos(std::sqrt(z))) / z;
    } else if (z < -1e-6) { // Hyperbola
        return (std::cosh(std::sqrt(-z)) - 1.0) / (-z);
    } else { // Parabola (Taylor series expansion to prevent divide-by-zero)
        return 1.0 / 2.0 - z / 24.0 + (z * z) / 720.0;
    }
}

double KeplerPropagator::stumpff_S(double z) const {
    if (z > 1e-6) { // Ellipse
        return (std::sqrt(z) - std::sin(std::sqrt(z))) / std::pow(std::sqrt(z), 3);
    } else if (z < -1e-6) { // Hyperbola
        return (std::sinh(std::sqrt(-z)) - std::sqrt(-z)) / std::pow(std::sqrt(-z), 3);
    } else { // Parabola (Taylor series expansion)
        return 1.0 / 6.0 - z / 120.0 + (z * z) / 5040.0;
    }
}

std::tuple<Eigen::Vector3d, Eigen::Vector3d> KeplerPropagator::propagate(
    const Eigen::Vector3d& r0_vec, const Eigen::Vector3d& v0_vec, double dt) const {

    double r0 = r0_vec.norm();
    double v0 = v0_vec.norm();

    // Calculate radial velocity using the dot product
    double vr0 = r0_vec.dot(v0_vec) / r0;

    // Calculate alpha
    double alpha = (2.0 / r0) - (v0 * v0 / mu);

    // Initial guess for the universal anomaly (chi)
    double chi = std::sqrt(mu) * std::abs(alpha) * dt;

    double z, C, S, f_chi, r, chi_new;
    double err = 1.0;
    int iter = 0;

    // Newton-Raphson Root-Finding Loop
    while (err > tolerance && iter < max_iter) {
        z = alpha * chi * chi;
        C = stumpff_C(z);
        S = stumpff_S(z);

        // Universal Kepler Equation: f(chi)
        f_chi = (r0 * vr0 / std::sqrt(mu)) * chi * chi * C
              + (1.0 - alpha * r0) * std::pow(chi, 3) * S
              + r0 * chi
              - std::sqrt(mu) * dt;

        // Derivative: f'(chi) which equals the radial distance 'r'
        r = (r0 * vr0 / std::sqrt(mu)) * chi * (1.0 - z * S)
          + (1.0 - alpha * r0) * chi * chi * C
          + r0;

        // Newton step
        chi_new = chi - (f_chi / r);
        err = std::abs(chi_new - chi);
        chi = chi_new;
        iter++;
    }

    // Calculate Lagrange f and g coefficients using the converged chi
    z = alpha * chi * chi;
    C = stumpff_C(z);
    S = stumpff_S(z);

    double f = 1.0 - (chi * chi / r0) * C;
    double g = dt - (1.0 / std::sqrt(mu)) * std::pow(chi, 3) * S;

    // Project the position forward
    Eigen::Vector3d r_final = f * r0_vec + g * v0_vec;
    double r_norm = r_final.norm();

    double f_dot = (std::sqrt(mu) / (r_norm * r0)) * (alpha * std::pow(chi, 3) * S - chi);
    double g_dot = 1.0 - (chi * chi / r_norm) * C;

    // Project the velocity forward
    Eigen::Vector3d v_final = f_dot * r0_vec + g_dot * v0_vec;

    return std::make_tuple(r_final, v_final);
}