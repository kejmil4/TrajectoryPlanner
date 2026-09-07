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

# Interactive 3D Trajectory Visualization
st.markdown("---")
st.header("3D Orbit Visualization")
st.write("Select specific dates from the porkchop plot above to visualize the physical flight path.")

col1, col2 = st.columns(2)
with col1:
    sim_dep_date = st.date_input("Selected Departure Date", datetime(2026, 8, 30))
with col2:
    sim_arr_date = st.date_input("Selected Arrival Date", datetime(2027, 5, 15))

# Compute and cache the heavy orbital mechanics data
if st.button("Calculate Trajectory Data"):
    with st.spinner("Propagating orbits and transfer path..."):
        dep_str = sim_dep_date.strftime('%Y-%m-%d 12:00:00')
        arr_str = sim_arr_date.strftime('%Y-%m-%d 12:00:00')

        et_dep = spice.str2et(dep_str)
        et_arr = spice.str2et(arr_str)
        tof = et_arr - et_dep

        r1 = eph.get_planet_state('EARTH', 'SUN', dep_str)[0:3]
        r2 = eph.get_planet_state('MARS BARYCENTER', 'SUN', arr_str)[0:3]

        solver = cppEngine.LambertSolver(100, SUN_MU, 1e-6)
        v1, v2 = solver.solve(r1, r2, tof, True)

        propagator = cppEngine.KeplerPropagator(SUN_MU)
        steps = 100
        transfer_path = np.zeros((steps + 1, 3))

        for i in range(steps + 1):
            dt = (tof / steps) * i
            r_t, _ = propagator.propagate(r1, v1, dt)
            transfer_path[i] = r_t

        earth_orbit = np.array(
            [eph.get_planet_state('EARTH', 'SUN', (sim_dep_date + timedelta(days=i)).strftime('%Y-%m-%d 12:00:00'))[0:3]
             for i in range(365)])
        mars_orbit = np.array([eph.get_planet_state('MARS BARYCENTER', 'SUN',
                                                    (sim_dep_date + timedelta(days=i)).strftime('%Y-%m-%d 12:00:00'))[
                                   0:3] for i in range(687)])

        # Save to session state
        st.session_state['sim_data'] = {
            'r1': r1, 'v1': v1, 'tof': tof,
            'dep_date': sim_dep_date,
            'transfer_path': transfer_path,
            'earth_orbit': earth_orbit,
            'mars_orbit': mars_orbit
        }

# Render the interactive slider and plot if the data exists in memory
if 'sim_data' in st.session_state:
    data = st.session_state['sim_data']
    tof_days = data['tof'] / 86400.0

    # The Time Slider
    current_day = st.slider("Mission Time (Days since Launch)", min_value=0.0, max_value=float(tof_days), value=0.0,
                            step=1.0)

    # Calculate exact positions for the chosen day
    current_date = data['dep_date'] + timedelta(days=current_day)
    current_date_str = current_date.strftime('%Y-%m-%d 12:00:00')

    propagator = cppEngine.KeplerPropagator(SUN_MU)
    r_sc, _ = propagator.propagate(data['r1'], data['v1'], current_day * 86400.0)

    r_earth = eph.get_planet_state('EARTH', 'SUN', current_date_str)[0:3]
    r_mars = eph.get_planet_state('MARS BARYCENTER', 'SUN', current_date_str)[0:3]

    fig3d = go.Figure()

    fig3d.add_trace(go.Scatter3d(x=[0], y=[0], z=[0], mode='markers', marker=dict(size=8, color='yellow'), name='Sun'))
    fig3d.add_trace(go.Scatter3d(x=data['earth_orbit'][:, 0], y=data['earth_orbit'][:, 1], z=data['earth_orbit'][:, 2],
                                 mode='lines', line=dict(color='cyan', width=2, dash='dot'), name='Earth Orbit',
                                 hoverinfo='skip'))
    fig3d.add_trace(
        go.Scatter3d(x=data['mars_orbit'][:, 0], y=data['mars_orbit'][:, 1], z=data['mars_orbit'][:, 2], mode='lines',
                     line=dict(color='orangered', width=2, dash='dot'), name='Mars Orbit', hoverinfo='skip'))
    fig3d.add_trace(
        go.Scatter3d(x=data['transfer_path'][:, 0], y=data['transfer_path'][:, 1], z=data['transfer_path'][:, 2],
                     mode='lines', line=dict(color='white', width=1), name='Transfer Path', hoverinfo='skip'))

    # Dynamic Moving Markers
    fig3d.add_trace(
        go.Scatter3d(x=[r_earth[0]], y=[r_earth[1]], z=[r_earth[2]], mode='markers', marker=dict(size=6, color='cyan'),
                     name='Earth Current'))
    fig3d.add_trace(go.Scatter3d(x=[r_mars[0]], y=[r_mars[1]], z=[r_mars[2]], mode='markers',
                                 marker=dict(size=6, color='orangered'), name='Mars Current'))
    fig3d.add_trace(go.Scatter3d(x=[r_sc[0]], y=[r_sc[1]], z=[r_sc[2]], mode='markers',
                                 marker=dict(size=5, color='white', symbol='cross'), name='Spacecraft'))

    fig3d.update_layout(
        scene=dict(
            aspectmode="data",
            xaxis_title='X (km)',
            yaxis_title='Y (km)',
            zaxis_title='Z (km)'
        ),
        height=700,
        margin=dict(l=0, r=0, b=0, t=30),
        template="plotly_dark"
    )

    st.plotly_chart(fig3d, use_container_width=True)