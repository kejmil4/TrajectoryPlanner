import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import spiceypy as spice

from ephemeris import EphemerisManager
import cppEngine


def main():
    # Planetary and Orbital Constants
    SUN_MU = 132712440018.0
    EARTH_MU = 398600.4418
    MARS_MU = 42828.3752
    R_PARK_EARTH = 6371.0 + 400.0
    R_PARK_MARS = 3389.5 + 400.0

    print("Initializing NASA SPICE Kernels...")
    eph = EphemerisManager()

    # Define the Launch Window Search Grid
    dep_start = datetime(2026, 7, 1)
    dep_end = datetime(2026, 11, 1)
    arr_start = datetime(2027, 2, 1)
    arr_end = datetime(2027, 8, 1)

    # Resolution of the grid (100x100 = 10,000 Lambert transfers)
    N = 100  # Departure rows
    M = 100  # Arrival columns

    dep_dates = [dep_start + timedelta(days=x) for x in np.linspace(0, (dep_end - dep_start).days, N)]
    arr_dates = [arr_start + timedelta(days=x) for x in np.linspace(0, (arr_end - arr_start).days, M)]

    dep_states = np.zeros((N, 6))
    arr_states = np.zeros((M, 6))
    tofs = np.zeros((N, M))

    print("Fetching planetary state vectors...")
    # Populate Earth departure states
    for i, d in enumerate(dep_dates):
        utc_str = d.strftime('%Y-%m-%d %H:%M:%S')
        dep_states[i] = eph.get_planet_state('EARTH', 'SUN', utc_str)

    # Populate Mars arrival states
    for j, a in enumerate(arr_dates):
        utc_str = a.strftime('%Y-%m-%d %H:%M:%S')
        arr_states[j] = eph.get_planet_state('MARS BARYCENTER', 'SUN', utc_str)

    # Populate Time of Flight matrix
    for i, d in enumerate(dep_dates):
        et_dep = spice.str2et(d.strftime('%Y-%m-%d %H:%M:%S'))
        for j, a in enumerate(arr_dates):
            et_arr = spice.str2et(a.strftime('%Y-%m-%d %H:%M:%S'))
            tof = et_arr - et_dep
            # Zero out impossible flights (arriving before departing)
            tofs[i, j] = tof if tof > 0 else 0

    print("Initializing C++ Math Engines...")
    solver = cppEngine.LambertSolver(100, SUN_MU, 1e-6)
    patched_conic = cppEngine.PatchedConic(EARTH_MU, MARS_MU, R_PARK_EARTH, R_PARK_MARS)
    optimizer = cppEngine.TrajectoryOptimizer(solver, patched_conic)

    print("C++ Grid Search Running (Calculating 10,000 transfers)...")
    # True = force a Type II (long-way) prograde transfer
    dep_dv, arr_dv, tot_dv = optimizer.optimize_grid(dep_states, arr_states, tofs, True)

    #  Render the Porkchop Plot
    print("Rendering Visualization...")
    X, Y = np.meshgrid(arr_dates, dep_dates)

    plt.figure(figsize=(10, 8))

    levels = np.arange(8, 20, 0.5)

    # Draw filled contours (the heat map)
    cp = plt.contourf(X, Y, tot_dv, levels=levels, cmap='jet', extend='both')
    plt.colorbar(cp, label='Total Delta-V (km/s)')

    # Draw black contour lines for readability
    plt.contour(X, Y, tot_dv, levels=levels, colors='black', linewidths=0.5, alpha=0.5)

    # Date formatting for the axes
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().yaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gcf().autofmt_xdate()

    plt.title('Earth to Mars 2026/2027 Total Delta-V (Type II Transfer)')
    plt.xlabel('Arrival Date')
    plt.ylabel('Departure Date')
    plt.grid(True, linestyle='--', alpha=0.5)

    # Save the file and display it
    plt.savefig('porkchop_2026.png', dpi=300)
    plt.show()


if __name__ == "__main__":
    main()