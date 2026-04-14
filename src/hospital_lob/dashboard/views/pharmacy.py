"""Pharmacy LOB page."""

from datetime import datetime, timedelta

import plotly.graph_objects as go
import streamlit as st

from hospital_lob.config.settings import PharmacyStageEnum
from hospital_lob.data.store import get_store
from hospital_lob.tools.pharmacy_metrics import compute_pharmacy_metrics


PHARMACY_STAGE_NAMES = {
    PharmacyStageEnum.ORDER_RECEIPT: "Order Receipt",
    PharmacyStageEnum.VERIFICATION: "Pharmacist Verification",
    PharmacyStageEnum.COMPOUNDING: "Compounding / IV Prep",
    PharmacyStageEnum.LABELLING: "Labelling & Dispensing",
    PharmacyStageEnum.ADMINISTRATION: "Nursing Administration",
}


def render_pharmacy(time_window: int = 24):
    st.title("Pharmacy Line of Balance")
    st.markdown("*Medication turnaround pipeline analysis*")

    store = get_store()
    now = datetime.now()
    orders = store.get_pharmacy_orders(start_time=now - timedelta(hours=time_window))
    metrics = compute_pharmacy_metrics(orders, time_window)

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Orders", len(orders))
    with col2:
        st.metric("Avg MTAT", f"{metrics.avg_mtat_minutes:.0f} min")
    with col3:
        st.metric("Avg Verify Wait", f"{metrics.avg_verification_wait_minutes:.0f} min")
    with col4:
        st.metric("Avg Compound Time", f"{metrics.avg_compounding_time_minutes:.0f} min")

    st.markdown("---")

    # Pharmacy LOB chart (throughput by stage)
    stages = list(PharmacyStageEnum)
    stage_names = [PHARMACY_STAGE_NAMES[s] for s in stages]
    throughputs = [metrics.throughput_per_hour.get(s, 0) for s in stages]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=stage_names,
        y=throughputs,
        marker_color=["#4CAF50" if t > 2 else "#FF9800" if t > 1 else "#F44336" for t in throughputs],
        text=[f"{t:.1f}" for t in throughputs],
        textposition="auto",
    ))
    fig.update_layout(
        title="Pharmacy Throughput by Stage (orders/hour)",
        yaxis_title="Throughput (orders/hr)",
        template="plotly_white",
        height=400,
    )
    st.plotly_chart(fig, width="stretch")

    # Queue depths
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Queue Depths")
        queue_names = [PHARMACY_STAGE_NAMES[s] for s in stages]
        queue_vals = [metrics.orders_in_queue.get(s, 0) for s in stages]

        fig2 = go.Figure(go.Bar(
            x=queue_names,
            y=queue_vals,
            marker_color="#FF5722",
            text=queue_vals,
            textposition="auto",
        ))
        fig2.update_layout(
            title="Orders in Queue per Stage",
            yaxis_title="Orders",
            template="plotly_white",
            height=350,
        )
        st.plotly_chart(fig2, width="stretch")

    with col_right:
        st.subheader("MTAT Distribution")
        completed = [o for o in orders if o.is_complete and o.mtat_minutes]
        if completed:
            mtat_values = [o.mtat_minutes for o in completed]
            fig3 = go.Figure(go.Histogram(
                x=mtat_values,
                nbinsx=30,
                marker_color="#2196F3",
            ))
            fig3.add_vline(x=45, line_dash="dash", line_color="red", annotation_text="Warning (45 min)")
            fig3.add_vline(x=90, line_dash="dash", line_color="darkred", annotation_text="Critical (90 min)")
            fig3.update_layout(
                title="Medication Turnaround Time Distribution",
                xaxis_title="MTAT (minutes)",
                yaxis_title="Count",
                template="plotly_white",
                height=350,
            )
            st.plotly_chart(fig3, width="stretch")
        else:
            st.info("No completed orders in the time window.")

    # Bottleneck indicator
    if metrics.bottleneck_stage:
        st.error(f"**Pharmacy Bottleneck:** {PHARMACY_STAGE_NAMES.get(metrics.bottleneck_stage, metrics.bottleneck_stage.value)}")

    # Run pharmacy crew
    st.markdown("---")
    if st.button("Run Pharmacy LOB Analysis (CrewAI)"):
        with st.spinner("Running Pharmacy Crew..."):
            try:
                from hospital_lob.crews.pharmacy_crew import create_pharmacy_crew
                crew = create_pharmacy_crew(time_window)
                result = crew.kickoff()
                st.markdown("### Pharmacy Crew Analysis")
                st.markdown(str(result))
            except Exception as e:
                st.error(f"Crew execution failed: {e}")
