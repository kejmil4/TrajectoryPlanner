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

    # 2. Calculate the Time of Flight (tof) in seconds
    # SPICE str2et converts UTC strings to Ephemeris Time (seconds)
    et_dep = spice.str2et(departure_date)
    et_arr = spice.str2et(arrival_date)
    tof = et_arr - et_dep

    print(f"\nTime of flight: {tof / 86400:.2f} days")

    # 3. Fetch the exact 3D position vectors [km] for Earth and Mars
    earth_state = eph.get_planet_state('EARTH', 'SUN', departure_date)
    mars_state = eph.get_planet_state('MARS BARYCENTER', 'SUN', arrival_date)

    r1 = earth_state[0:3]  # only the position (X, Y, Z) for Lambert
    r2 = mars_state[0:3]

    print("\n--- Positions ---")
    print(f"Earth (r1): {r1} km")
    print(f"Mars  (r2): {r2} km")

    # 4. Initialize the C++ Lambert Solver
    # max_iter = 100, mu = SUN_MU, tolerance = 1e-6
    print("\nInitializing C++ Math Engine...")
    solver = cppEngine.LambertSolver(100, SUN_MU, 1e-6)

    # 5. Execute the cross-language call
    # Pybind11 automatically converts our Numpy arrays (r1, r2) into Eigen::Vector3d
    print("Solving Lambert Boundary Value Problem...")
    v1, v2 = solver.solve(r1, r2, tof, False)  # False = short-way transfer

    print("\n--- Transfer Velocities ---")
    print(f"Departure Velocity Vector (v1): {v1} km/s")
    print(f"Arrival Velocity Vector   (v2): {v2} km/s")

    # Quick magnitude check
    print(f"\nRequired Departure Speed: {np.linalg.norm(v1):.2f} km/s")
    print(f"Arrival Intercept Speed:  {np.linalg.norm(v2):.2f} km/s")


if __name__ == "__main__":
    main()