import numpy as np
import spiceypy as spice
from ephemeris import EphemerisManager

import cppEngine


def main():
    SUN_MU = 132712440018.0  # Sun's gravitational parameter in km^3/s^2

    # 2026 is a standard Earth-to-Mars launch window
    departure_date = '2026-08-30 12:00:00'
    arrival_date = '2027-05-15 12:00:00'

    print("Initializing NASA SPICE Kernels...")
    eph = EphemerisManager()

    #  Calculate the Time of Flight (tof) in seconds
    # SPICE str2et converts UTC strings to Ephemeris Time (seconds)
    et_dep = spice.str2et(departure_date)
    et_arr = spice.str2et(arrival_date)
    tof = et_arr - et_dep

    print(f"\nTime of flight: {tof / 86400:.2f} days")

    # Fetch the exact 3D position vectors [km] for Earth and Mars
    earth_state = eph.get_planet_state('EARTH', 'SUN', departure_date)
    mars_state = eph.get_planet_state('MARS BARYCENTER', 'SUN', arrival_date)

    r1 = earth_state[0:3]  # only the position (X, Y, Z) for Lambert
    r2 = mars_state[0:3]

    print("\n--- Positions ---")
    print(f"Earth (r1): {r1} km")
    print(f"Mars  (r2): {r2} km")

    # Initialize the C++ Lambert Solver
    # max_iter = 100, mu = SUN_MU, tolerance = 1e-6
    print("\nInitializing C++ Math Engine...")
    solver = cppEngine.LambertSolver(100, SUN_MU, 1e-6)

    # Execute the cross-language call
    # Pybind11 automatically converts our Numpy arrays (r1, r2) into Eigen::Vector3d
    print("Solving Lambert Boundary Value Problem...")
    # v1, v2 = solver.solve(r1, r2, tof, False)  # False = short-way transfer
    v1, v2 = solver.solve(r1, r2, tof, True)  # True = long-way transfer

    print("\n--- Transfer Velocities ---")
    print(f"Departure Velocity Vector (v1): {v1} km/s")
    print(f"Arrival Velocity Vector   (v2): {v2} km/s")

    # Quick magnitude check
    print(f"\nRequired Departure Speed: {np.linalg.norm(v1):.2f} km/s")
    print(f"Arrival Intercept Speed:  {np.linalg.norm(v2):.2f} km/s")

    # Initialize Kepler Propagator and Verify
    print("\nInitializing C++ Kepler Propagator for Verification...")
    # Using default tolerance (1e-8) and max_iter (100) from Pybind11
    propagator = cppEngine.KeplerPropagator(SUN_MU)

    # Propagate the Earth departure position (r1) forward using the calculated
    # departure velocity (v1) over the exact time of flight (tof)
    print("Simulating spacecraft trajectory...")
    r_final, v_final = propagator.propagate(r1, v1, tof)

    print("\n--- Verification Results ---")
    print(f"Target Mars Position (r2): {r2} km")
    print(f"Simulated Final Position:  {r_final} km")

    # Calculate the exact miss distance (error margin)
    miss_distance = np.linalg.norm(r_final - r2)
    print(f"\nFinal Miss Distance: {miss_distance:.6f} km")

    print("\n--- Patched Conic Fuel Analysis ---")
    # Define Planetary Constants
    EARTH_MU = 398600.4418  # km^3/s^2
    MARS_MU = 42828.3752  # km^3/s^2

    # Parking Orbits (Planet Radius + 400 km altitude)
    R_PARK_EARTH = 6371.0 + 400.0
    R_PARK_MARS = 3389.5 + 400.0

    # SPICE state vectors contain [x, y, z, vx, vy, vz]
    # We slice [3:6] to get the actual 3D velocity vectors of the planets
    v_earth = earth_state[3:6]
    v_mars = mars_state[3:6]

    print(f"Earth Orbital Velocity: {np.linalg.norm(v_earth):.2f} km/s")
    print(f"Mars Orbital Velocity:  {np.linalg.norm(v_mars):.2f} km/s")

    # Initialize C++ Patched Conic Engine
    delta_v_calc = cppEngine.PatchedConic(EARTH_MU, MARS_MU, R_PARK_EARTH, R_PARK_MARS)

    # Calculate actual rocket Delta V
    dv_dep = delta_v_calc.get_departure_delta_v(v1, v_earth)
    dv_arr = delta_v_calc.get_arrival_delta_v(v2, v_mars)
    dv_tot = delta_v_calc.get_total_delta_v(v1, v_earth, v2, v_mars)

    print("\n--- Required Rocket Delta V ---")
    print(f"Earth Departure Burn (LEO): {dv_dep:.3f} km/s")
    print(f"Mars Arrival Burn (LMO):    {dv_arr:.3f} km/s")
    print(f"Total Mission Delta V:      {dv_tot:.3f} km/s")


if __name__ == "__main__":
    main()