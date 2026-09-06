import streamlit as st
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import spiceypy as spice

from ephemeris import EphemerisManager
import cppEngine

# Page Configuration
st.set_page_config(page_title="Trajectory Planner", layout="wide")
st.title("Interplanetary Mission Architect")

# Cache SPICE Kernels
@st.cache_resource # only once
def load_ephemeris():
    return EphemerisManager()

eph = load_ephemeris()

# Sidebar Controls
st.sidebar.header("Launch Window Constraints")
dep_start = st.sidebar.date_input("Departure Start Date", datetime(2026, 7, 1))
dep_end = st.sidebar.date_input("Departure End Date", datetime(2026, 11, 1))
arr_start = st.sidebar.date_input("Arrival Start Date", datetime(2027, 2, 1))
arr_end = st.sidebar.date_input("Arrival End Date", datetime(2027, 8, 1))
grid_resolution = st.sidebar.slider("Grid Resolution", 50, 200, 100, step=10)

# Constants
SUN_MU = 132712440018.0
EARTH_MU = 398600.4418
MARS_MU = 42828.3752
R_PARK_EARTH = 6371.0 + 400.0
R_PARK_MARS = 3389.5 + 400.0

if st.sidebar.button("Generate Porkchop Plot"):
    with st.spinner("Executing C++ Grid Search..."):
        # Generate arrays
        N = grid_resolution
        M = grid_resolution
        dep_dates = [dep_start + timedelta(days=x) for x in np.linspace(0, (dep_end - dep_start).days, N)]
        arr_dates = [arr_start + timedelta(days=x) for x in np.linspace(0, (arr_end - arr_start).days, M)]

        dep_states = np.zeros((N, 6))
        arr_states = np.zeros((M, 6))
        tofs = np.zeros((N, M))

        # Populate SPICE Data
        for i, d in enumerate(dep_dates):
            utc_str = d.strftime('%Y-%m-%d %H:%M:%S')
            dep_states[i] = eph.get_planet_state('EARTH', 'SUN', utc_str)

        for j, a in enumerate(arr_dates):
            utc_str = a.strftime('%Y-%m-%d %H:%M:%S')
            arr_states[j] = eph.get_planet_state('MARS BARYCENTER', 'SUN', utc_str)

        for i, d in enumerate(dep_dates):
            et_dep = spice.str2et(d.strftime('%Y-%m-%d %H:%M:%S'))
            for j, a in enumerate(arr_dates):
                et_arr = spice.str2et(a.strftime('%Y-%m-%d %H:%M:%S'))
                tof = et_arr - et_dep
                tofs[i, j] = tof if tof > 0 else 0

        # Execute C++ Optimizer
        solver = cppEngine.LambertSolver(100, SUN_MU, 1e-6)
        patched_conic = cppEngine.PatchedConic(EARTH_MU, MARS_MU, R_PARK_EARTH, R_PARK_MARS)
        optimizer = cppEngine.TrajectoryOptimizer(solver, patched_conic)

        dep_dv, arr_dv, tot_dv = optimizer.optimize_grid(dep_states, arr_states, tofs, True)

        # Render Interactive Plotly Graph
        fig = go.Figure(data=go.Contour(
            z=tot_dv,
            x=arr_dates,
            y=dep_dates,
            colorscale='Jet',
            contours=dict(
                start=8,
                end=20,
                size=0.5,
                showlines=True
            ),
            colorbar=dict(title='Total Delta-V (km/s)'),
            hovertemplate="Departure: %{y}<br>Arrival: %{x}<br>Delta-V: %{z:.2f} km/s<extra></extra>"
        ))

        fig.update_layout(
            title='Earth to Mars Total Mission Energy',
            xaxis_title='Arrival Date',
            yaxis_title='Departure Date',
            height=700
        )

        st.plotly_chart(fig, use_container_width=True)