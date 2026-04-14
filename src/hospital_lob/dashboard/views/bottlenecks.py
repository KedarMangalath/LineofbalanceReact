"""Bottleneck Analysis page."""

from datetime import datetime, timedelta

import plotly.graph_objects as go
import streamlit as st

from hospital_lob.config.settings import PATIENT_FLOW_STAGES, STAGE_DISPLAY_NAMES
from hospital_lob.data.store import get_store
from hospital_lob.tools.bottleneck_analyzer import analyze_bottlenecks
from hospital_lob.tools.metrics_calculator import compute_lob_metrics


def render_bottlenecks(time_window: int = 24):
    st.title("Bottleneck Analysis")
    st.markdown("*Theory of Constraints approach to identifying flow constraints*")

    store = get_store()
    now = datetime.now()
    patients = store.get_patients(start_time=now - timedelta(hours=time_window))
    capacities = store.get_stage_capacities()
    metrics = compute_lob_metrics(patients, capacities, time_window)
    analysis = analyze_bottlenecks(metrics)

    # Constraint heatmap
    st.subheader("Constraint Score Heatmap")
    ranked = analysis["all_stages_ranked"]

    stages = [r["display_name"] for r in ranked]
    scores = [r["constraint_score"] for r in ranked]
    colors = ["#F44336" if s > 0.5 else "#FF9800" if s > 0.3 else "#4CAF50" for s in scores]

    fig = go.Figure(go.Bar(
        x=stages,
        y=scores,
        marker_color=colors,
        text=[f"{s:.3f}" for s in scores],
        textposition="auto",
    ))
    fig.update_layout(
        title="Constraint Score by Stage (higher = more constrained)",
        yaxis_title="Constraint Score",
        template="plotly_white",
        height=400,
    )
    st.plotly_chart(fig, width="stretch")

    # Primary and secondary bottleneck cards
    col1, col2 = st.columns(2)

    primary = analysis.get("primary_bottleneck")
    secondary = analysis.get("secondary_bottleneck")

    with col1:
        st.subheader("Primary Constraint")
        if primary:
            st.error(f"**{primary['display_name']}**")
            st.metric("Constraint Score", f"{primary['constraint_score']:.3f}")
            st.metric("Throughput", f"{primary['actual_throughput']:.1f} / {primary['target_throughput']:.1f} pts/hr")
            st.metric("Deviation", f"{primary['throughput_deviation']:.1%}")
            st.metric("WIP", primary["wip_count"])
            st.metric("Utilization", f"{primary['utilization_percent']:.1f}%")

    with col2:
        st.subheader("Secondary Constraint")
        if secondary:
            st.warning(f"**{secondary['display_name']}**")
            st.metric("Constraint Score", f"{secondary['constraint_score']:.3f}")
            st.metric("Throughput", f"{secondary['actual_throughput']:.1f} / {secondary['target_throughput']:.1f} pts/hr")
            st.metric("Deviation", f"{secondary['throughput_deviation']:.1%}")

    # Analysis report
    st.markdown("---")
    st.subheader("Analysis Report")
    st.markdown(analysis["analysis"])

    # Run CrewAI analysis
    st.markdown("---")
    st.subheader("AI-Powered Analysis")
    if st.button("Run Full LOB Analysis (CrewAI)"):
        with st.spinner("Running LOB Analysis Crew... This may take a few minutes."):
            try:
                from hospital_lob.crews.lob_analysis_crew import create_lob_analysis_crew
                crew = create_lob_analysis_crew(time_window)
                result = crew.kickoff()
                st.session_state.crew_result = str(result)
                st.success("Analysis complete!")
            except Exception as e:
                st.error(f"Crew execution failed: {e}")
                st.info("Ensure your API key is set in .env (OPENAI_API_KEY or ANTHROPIC_API_KEY)")

    if "crew_result" in st.session_state:
        st.markdown("### Crew Analysis Output")
        st.markdown(st.session_state.crew_result)
