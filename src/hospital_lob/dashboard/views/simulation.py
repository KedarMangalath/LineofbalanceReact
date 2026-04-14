"""What-If Simulation page."""

import json

import plotly.graph_objects as go
import streamlit as st

from hospital_lob.config.settings import DEFAULT_STAGE_CAPACITY, PATIENT_FLOW_STAGES, STAGE_DISPLAY_NAMES, StageEnum
from hospital_lob.tools.simulation_engine import run_simulation


def render_simulation():
    st.title("What-If Simulation")
    st.markdown("*Adjust parameters and simulate patient flow scenarios*")

    # Scenario input panel
    st.subheader("Scenario Parameters")

    col1, col2 = st.columns(2)

    with col1:
        duration = st.slider("Simulation Duration (hours)", 24, 336, 168, step=24)
        arrival_rate = st.slider("Patient Arrival Rate (pts/hr)", 2.0, 20.0, 8.0, step=0.5)

    with col2:
        st.markdown("**Service Time Multipliers**")
        st.caption("< 1.0 = faster service, > 1.0 = slower")
        diag_mult = st.slider("Diagnostics", 0.3, 2.0, 1.0, step=0.1, key="diag")
        discharge_mult = st.slider("Discharge", 0.3, 2.0, 1.0, step=0.1, key="disc")

    st.markdown("**Capacity Overrides** (beds/slots per stage)")
    cap_cols = st.columns(len(PATIENT_FLOW_STAGES))
    capacity_overrides = {}

    for i, stage in enumerate(PATIENT_FLOW_STAGES):
        default = DEFAULT_STAGE_CAPACITY[stage]["capacity"]
        with cap_cols[i]:
            val = st.number_input(
                stage.value[:6],
                min_value=1,
                max_value=200,
                value=default,
                key=f"cap_{stage.value}",
            )
            if val != default:
                capacity_overrides[stage.value] = val

    service_multipliers = {}
    if diag_mult != 1.0:
        service_multipliers["diagnostics"] = diag_mult
    if discharge_mult != 1.0:
        service_multipliers["discharge"] = discharge_mult

    # Run simulation
    if st.button("Run Simulation", type="primary"):
        with st.spinner("Running simulation..."):
            baseline = run_simulation(
                duration_hours=duration,
                arrival_rate=arrival_rate,
            )
            scenario = run_simulation(
                duration_hours=duration,
                arrival_rate=arrival_rate,
                capacity_overrides=capacity_overrides,
                service_time_multipliers=service_multipliers,
            )
            st.session_state.sim_baseline = baseline
            st.session_state.sim_scenario = scenario

    # Display results
    if "sim_baseline" in st.session_state and "sim_scenario" in st.session_state:
        baseline = st.session_state.sim_baseline
        scenario = st.session_state.sim_scenario

        st.markdown("---")
        st.subheader("Results Comparison")

        # Summary KPIs
        col1, col2, col3 = st.columns(3)
        with col1:
            delta = scenario["patients_completed"] - baseline["patients_completed"]
            st.metric("Patients Completed", scenario["patients_completed"], delta=delta)
        with col2:
            delta = scenario["avg_total_time_hours"] - baseline["avg_total_time_hours"]
            st.metric("Avg Total Time (hrs)", f"{scenario['avg_total_time_hours']:.1f}", delta=f"{delta:.1f}", delta_color="inverse")
        with col3:
            st.metric(
                "Predicted Bottleneck",
                scenario["predicted_bottleneck"]["stage"],
            )

        # Throughput comparison chart
        st.subheader("Throughput Comparison by Stage")
        baseline_tp = baseline["stage_throughput_per_hour"]
        scenario_tp = scenario["stage_throughput_per_hour"]

        stages = list(baseline_tp.keys())
        display_names = [STAGE_DISPLAY_NAMES.get(StageEnum(s), s) if s in [e.value for e in StageEnum] else s for s in stages]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Baseline",
            x=display_names,
            y=[baseline_tp.get(s, 0) for s in stages],
            marker_color="#2196F3",
        ))
        fig.add_trace(go.Bar(
            name="Scenario",
            x=display_names,
            y=[scenario_tp.get(s, 0) for s in stages],
            marker_color="#4CAF50",
        ))
        fig.update_layout(
            barmode="group",
            yaxis_title="Throughput (pts/hr)",
            template="plotly_white",
            height=450,
        )
        st.plotly_chart(fig, width="stretch")

        # Wait time comparison
        st.subheader("Wait Time Comparison by Stage")
        baseline_wait = baseline["stage_avg_wait_minutes"]
        scenario_wait = scenario["stage_avg_wait_minutes"]

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            name="Baseline Wait (min)",
            x=display_names,
            y=[baseline_wait.get(s, 0) for s in stages],
            marker_color="#FF9800",
        ))
        fig2.add_trace(go.Bar(
            name="Scenario Wait (min)",
            x=display_names,
            y=[scenario_wait.get(s, 0) for s in stages],
            marker_color="#9C27B0",
        ))
        fig2.update_layout(
            barmode="group",
            yaxis_title="Avg Wait Time (minutes)",
            template="plotly_white",
            height=400,
        )
        st.plotly_chart(fig2, width="stretch")

        # Run CrewAI simulation crew
        st.markdown("---")
        if st.button("Run AI Simulation Analysis (CrewAI)"):
            with st.spinner("Running Simulation Crew..."):
                try:
                    from hospital_lob.crews.simulation_crew import create_simulation_crew
                    crew = create_simulation_crew(
                        duration_hours=duration,
                        arrival_rate=arrival_rate,
                        capacity_overrides=capacity_overrides,
                        service_time_multipliers=service_multipliers,
                    )
                    result = crew.kickoff()
                    st.markdown("### AI Analysis")
                    st.markdown(str(result))
                except Exception as e:
                    st.error(f"Crew execution failed: {e}")
