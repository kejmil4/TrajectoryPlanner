import streamlit as st
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import spiceypy as spice

from ephemeris import EphemerisManager
import cppEngine
from planet_data import PLANET_DATA

# Page Configuration
st.set_page_config(page_title="Trajectory Planner", layout="wide")
st.title("Interplanetary Mission Architect")

# Cache SPICE Kernels
@st.cache_resource
def load_ephemeris():
    return EphemerisManager()

eph = load_ephemeris()

if 'target_dep_date' not in st.session_state:
    st.session_state['target_dep_date'] = datetime(2026, 8, 30)
if 'target_arr_date' not in st.session_state:
    st.session_state['target_arr_date'] = datetime(2027, 5, 15)

# Extract list of available planets (excluding the Sun for departures/arrivals)
available_bodies = [body for body in PLANET_DATA.keys() if body != 'SUN']

# Sidebar Controls - Generalized Planetary Selection
st.sidebar.header("Mission Architecture")
dep_planet = st.sidebar.selectbox("Departure Planet", available_bodies, index=available_bodies.index('EARTH'))
arr_planet = st.sidebar.selectbox("Arrival Planet", available_bodies, index=available_bodies.index('MARS'))

st.sidebar.markdown("---")
st.sidebar.header("Launch Window Constraints")
dep_start = st.sidebar.date_input("Departure Start Date", datetime(2026, 7, 1))
dep_end = st.sidebar.date_input("Departure End Date", datetime(2026, 11, 1))
arr_start = st.sidebar.date_input("Arrival Start Date", datetime(2027, 2, 1))
arr_end = st.sidebar.date_input("Arrival End Date", datetime(2027, 8, 1))
grid_resolution = st.sidebar.slider("Grid Resolution", 50, 200, 100, step=10)

st.sidebar.markdown("---")
st.sidebar.header("Trajectory Settings")
transfer_type = st.sidebar.radio("Transfer Geometry", ["Type I (Short Way, < 180°)", "Type II (Long Way, > 180°)"])
is_long_way = True if "Type II" in transfer_type else False

st.sidebar.markdown("---")
st.sidebar.header("Parking Orbits")
park_alt_dep = st.sidebar.number_input(f"{dep_planet.capitalize()} Parking Altitude (km)", value=PLANET_DATA[dep_planet]['default_park_alt'])
park_alt_arr = st.sidebar.number_input(f"{arr_planet.capitalize()} Parking Altitude (km)", value=PLANET_DATA[arr_planet]['default_park_alt'])

# Extract Dynamic Constants
SUN_MU = PLANET_DATA['SUN']['mu']
mu_dep = PLANET_DATA[dep_planet]['mu']
mu_arr = PLANET_DATA[arr_planet]['mu']
spice_dep = PLANET_DATA[dep_planet]['spice_name']
spice_arr = PLANET_DATA[arr_planet]['spice_name']
r_park_dep = PLANET_DATA[dep_planet]['radius'] + park_alt_dep
r_park_arr = PLANET_DATA[arr_planet]['radius'] + park_alt_arr

st.sidebar.markdown("---")
max_dv = st.sidebar.slider("Max Delta-V Scale (km/s)", 10, 100, 20, step=5)

# Porkchop Plot Generator
if st.sidebar.button("Generate Porkchop Plot"):
    with st.spinner("Executing C++ Grid Search..."):
        N = grid_resolution
        M = grid_resolution
        dep_dates = [dep_start + timedelta(days=x) for x in np.linspace(0, (dep_end - dep_start).days, N)]
        arr_dates = [arr_start + timedelta(days=x) for x in np.linspace(0, (arr_end - arr_start).days, M)]

        dep_states = np.zeros((N, 6))
        arr_states = np.zeros((M, 6))
        tofs = np.zeros((N, M))

        for i, d in enumerate(dep_dates):
            utc_str = d.strftime('%Y-%m-%d %H:%M:%S')
            dep_states[i] = eph.get_planet_state(spice_dep, 'SUN', utc_str)

        for j, a in enumerate(arr_dates):
            utc_str = a.strftime('%Y-%m-%d %H:%M:%S')
            arr_states[j] = eph.get_planet_state(spice_arr, 'SUN', utc_str)

        for i, d in enumerate(dep_dates):
            et_dep = spice.str2et(d.strftime('%Y-%m-%d %H:%M:%S'))
            for j, a in enumerate(arr_dates):
                et_arr = spice.str2et(a.strftime('%Y-%m-%d %H:%M:%S'))
                tofs[i, j] = et_arr - et_dep if et_arr > et_dep else 0

        solver = cppEngine.LambertSolver(100, SUN_MU, 1e-6)
        patched_conic = cppEngine.PatchedConic()
        optimizer = cppEngine.TrajectoryOptimizer(solver, patched_conic)

        dep_dv, arr_dv, tot_dv = optimizer.optimize_grid(
            dep_states, arr_states, tofs,
            mu_dep, r_park_dep, mu_arr, r_park_arr, is_long_way
        )

        fig = go.Figure(data=go.Contour(
            z=tot_dv, x=arr_dates, y=dep_dates, colorscale='Jet',
            contours=dict(start=8, end=max_dv, size=0.5, showlines=True),
            colorbar=dict(title='Total Delta-V (km/s)'),
            hovertemplate="Departure: %{y}<br>Arrival: %{x}<br>Delta-V: %{z:.2f} km/s<extra></extra>"
        ))

        X, Y = np.meshgrid(arr_dates, dep_dates)
        fig.add_trace(go.Scatter(
            x=X.flatten(),
            y=Y.flatten(),
            mode='markers',
            marker=dict(color='rgba(0,0,0,0)', size=5),
            hoverinfo='skip',
            showlegend=False
        ))

        fig.update_layout(
            title=f'{dep_planet.capitalize()} to {arr_planet.capitalize()} Total Mission Energy',
            xaxis_title='Arrival Date', yaxis_title='Departure Date', height=700
        )

        # Save results to session state so it survives UI interactions
        st.session_state['porkchop_data'] = {
            'fig': fig, 'tot_dv': tot_dv, 'dep_dates': dep_dates, 'arr_dates': arr_dates
        }

# Render Plot and Handle Interactions
if 'porkchop_data' in st.session_state:
    data = st.session_state['porkchop_data']

    # Render the graph and capture any user clicks (Requires Streamlit 1.35+)
    selection = st.plotly_chart(data['fig'], use_container_width=True, on_select="rerun")

    # Auto-Optimizer Button
    if st.button("Auto-Load Lowest Energy Trajectory"):
        # Mathematically find the absolute minimum Delta-V on the grid
        min_idx = np.unravel_index(np.nanargmin(data['tot_dv']), data['tot_dv'].shape)

        # Removed the .date() calls since the arrays already contain date objects
        st.session_state['target_dep_date'] = data['dep_dates'][min_idx[0]]
        st.session_state['target_arr_date'] = data['arr_dates'][min_idx[1]]
        st.rerun()

    # Process Graph Clicks
    if selection and len(selection.selection.points) > 0:
        pt = selection.selection.points[0]
        # Extract the exact dates the user clicked
        click_arr = datetime.strptime(pt['x'][:10], '%Y-%m-%d').date()
        click_dep = datetime.strptime(pt['y'][:10], '%Y-%m-%d').date()

        # Update memory and refresh the UI
        if click_arr != st.session_state['target_arr_date'] or click_dep != st.session_state['target_dep_date']:
            st.session_state['target_arr_date'] = click_arr
            st.session_state['target_dep_date'] = click_dep
            st.rerun()

# Interactive 3D Trajectory Visualization
st.markdown("---")
st.header("3D Orbit Visualization")
st.write("Select specific dates from the porkchop plot above to visualize the physical flight path.")

col1, col2 = st.columns(2)
with col1:
    sim_dep_date = st.date_input("Selected Departure Date", st.session_state['target_dep_date'])
with col2:
    sim_arr_date = st.date_input("Selected Arrival Date", st.session_state['target_arr_date'])

if st.button("Calculate Trajectory Data"):
    with st.spinner("Propagating orbits and transfer path..."):
        dep_str = sim_dep_date.strftime('%Y-%m-%d 12:00:00')
        arr_str = sim_arr_date.strftime('%Y-%m-%d 12:00:00')

        et_dep = spice.str2et(dep_str)
        et_arr = spice.str2et(arr_str)
        tof = et_arr - et_dep

        # Use dynamic SPICE names
        r1 = eph.get_planet_state(spice_dep, 'SUN', dep_str)[0:3]
        r2 = eph.get_planet_state(spice_arr, 'SUN', arr_str)[0:3]

        solver = cppEngine.LambertSolver(100, SUN_MU, 1e-6)
        v1, v2 = solver.solve(r1, r2, tof, is_long_way)

        propagator = cppEngine.KeplerPropagator(SUN_MU)
        steps = 100
        transfer_path = np.zeros((steps + 1, 3))

        for i in range(steps + 1):
            dt = (tof / steps) * i
            r_t, _ = propagator.propagate(r1, v1, dt)
            transfer_path[i] = r_t


        orbital_periods = {
            'MERCURY': 88, 'VENUS': 225, 'EARTH': 365, 'MARS': 687,
            'JUPITER': 4333, 'SATURN': 10759, 'URANUS': 30688, 'NEPTUNE': 60182
        }

        dep_days = max(int(tof / 86400), orbital_periods.get(dep_planet.upper(), 365))
        arr_days = max(int(tof / 86400), orbital_periods.get(arr_planet.upper(), 365))

        dep_step = 1 if dep_days <= 1000 else 10
        arr_step = 1 if arr_days <= 1000 else 10

        dep_orbit = np.array([eph.get_planet_state(spice_dep, 'SUN',
                                                   (sim_dep_date + timedelta(days=i)).strftime('%Y-%m-%d 12:00:00'))[
                                  0:3] for i in range(0, dep_days + dep_step, dep_step)])
        arr_orbit = np.array([eph.get_planet_state(spice_arr, 'SUN',
                                                   (sim_dep_date + timedelta(days=i)).strftime('%Y-%m-%d 12:00:00'))[
                                  0:3] for i in range(0, arr_days + arr_step, arr_step)])

        st.session_state['sim_data'] = {
            'r1': r1, 'v1': v1, 'tof': tof,
            'dep_date': sim_dep_date,
            'transfer_path': transfer_path,
            'dep_orbit': dep_orbit,
            'arr_orbit': arr_orbit,
            'spice_dep': spice_dep,
            'spice_arr': spice_arr,
            'name_dep': dep_planet.capitalize(),
            'name_arr': arr_planet.capitalize()
        }

if 'sim_data' in st.session_state:
    data = st.session_state['sim_data']
    tof_days = data['tof'] / 86400.0

    current_day = st.slider("Mission Time (Days since Launch)", min_value=0.0, max_value=float(tof_days), value=0.0, step=1.0)

    current_date = data['dep_date'] + timedelta(days=current_day)
    current_date_str = current_date.strftime('%Y-%m-%d 12:00:00')

    propagator = cppEngine.KeplerPropagator(SUN_MU)
    r_sc, _ = propagator.propagate(data['r1'], data['v1'], current_day * 86400.0)

    r_curr_dep = eph.get_planet_state(data['spice_dep'], 'SUN', current_date_str)[0:3]
    r_curr_arr = eph.get_planet_state(data['spice_arr'], 'SUN', current_date_str)[0:3]

    fig3d = go.Figure()

    # Static elements
    fig3d.add_trace(go.Scatter3d(x=[0], y=[0], z=[0], mode='markers', marker=dict(size=8, color='yellow'), name='Sun'))
    fig3d.add_trace(go.Scatter3d(x=data['dep_orbit'][:, 0], y=data['dep_orbit'][:, 1], z=data['dep_orbit'][:, 2], mode='lines', line=dict(color='cyan', width=2, dash='dot'), name=f"{data['name_dep']} Orbit", hoverinfo='skip'))
    fig3d.add_trace(go.Scatter3d(x=data['arr_orbit'][:, 0], y=data['arr_orbit'][:, 1], z=data['arr_orbit'][:, 2], mode='lines', line=dict(color='orangered', width=2, dash='dot'), name=f"{data['name_arr']} Orbit", hoverinfo='skip'))
    fig3d.add_trace(go.Scatter3d(x=data['transfer_path'][:, 0], y=data['transfer_path'][:, 1], z=data['transfer_path'][:, 2], mode='lines', line=dict(color='white', width=1), name='Transfer Path', hoverinfo='skip'))

    # Dynamic elements
    fig3d.add_trace(go.Scatter3d(x=[r_curr_dep[0]], y=[r_curr_dep[1]], z=[r_curr_dep[2]], mode='markers', marker=dict(size=6, color='cyan'), name=f"{data['name_dep']} Current"))
    fig3d.add_trace(go.Scatter3d(x=[r_curr_arr[0]], y=[r_curr_arr[1]], z=[r_curr_arr[2]], mode='markers', marker=dict(size=6, color='orangered'), name=f"{data['name_arr']} Current"))
    fig3d.add_trace(go.Scatter3d(x=[r_sc[0]], y=[r_sc[1]], z=[r_sc[2]], mode='markers', marker=dict(size=5, color='white', symbol='cross'), name='Spacecraft'))

    fig3d.update_layout(
        scene=dict(aspectmode="data", xaxis_title='X (km)', yaxis_title='Y (km)', zaxis_title='Z (km)'),
        height=700, margin=dict(l=0, r=0, b=0, t=30), template="plotly_dark"
    )

    st.plotly_chart(fig3d, use_container_width=True)
