import spiceypy as spice
import numpy as np


class EphemerisManager:
    def __init__(self, lsk_path="kernels/naif0012.tls", spk_path="kernels/de432s.bsp"):
        """Loads the NASA SPICE kernels into memory."""
        spice.furnsh(lsk_path)
        spice.furnsh(spk_path)
        print("SPICE kernels loaded successfully.")

    def __del__(self):
        """Unloads kernels when the object is destroyed to free memory."""
        spice.kclear()

    def get_planet_state(self, target, observer, utc_time):
        """
        Fetches the state vector (position and velocity) of a target relative to an observer.

        :param target: Name of the body (e.g., 'MARS', 'EARTH')
        :param observer: Center of your coordinate system (e.g., 'SUN')
        :param utc_time: Time string (e.g., '2026-08-30 12:00:00')
        :return: A 6-element numpy array [x, y, z, vx, vy, vz] in km and km/s
        """
        et = spice.str2et(utc_time)

        state_vector, light_time = spice.spkezr(target, et, 'J2000', 'NONE', observer)

        return np.array(state_vector)


if __name__ == "__main__":

    try:
        eph = EphemerisManager()

        earth_state = eph.get_planet_state('EARTH', 'SUN', '2026-08-30 12:00:00')

        print("\nEarth State Vector [km, km/s]:")
        print(f"Position (X, Y, Z): {earth_state[0:3]}")
        print(f"Velocity (Vx, Vy, Vz): {earth_state[3:6]}")

    except Exception as e:
        print(f"Error: {e}")
        print("Did you download the kernel files and put them in the 'kernels' directory?")