"""Overview page: LOB chart + KPI cards + stage occupancy."""

from datetime import datetime, timedelta

import plotly.graph_objects as go
import streamlit as st

from hospital_lob.config.settings import PATIENT_FLOW_STAGES, STAGE_DISPLAY_NAMES, StageEnum
from hospital_lob.data.store import get_store
from hospital_lob.tools.lob_chart_generator import (
    build_lob_chart_data,
    create_cumulative_lob_chart,
    create_lob_chart,
    create_wip_chart,
)
from hospital_lob.tools.metrics_calculator import compute_lob_metrics


def render_overview(time_window: int = 24):
    st.title("Hospital Line of Balance Overview")
    st.markdown(f"*Data window: last {time_window} hours*")

    store = get_store()
    now = datetime.now()
    patients = store.get_patients(start_time=now - timedelta(hours=time_window))
    capacities = store.get_stage_capacities()
    metrics = compute_lob_metrics(patients, capacities, time_window)

    # KPI Cards
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Total Patients", len(patients))
    with col2:
        active = sum(1 for p in patients if p.is_active)
        st.metric("Active", active)
    with col3:
        st.metric("ALOS", f"{metrics.alos_hours:.1f}h")
    with col4:
        st.metric("Bed Turnover", f"{metrics.bed_turnover_rate:.2f}")
    with col5:
        st.metric("ED Wait", f"{metrics.ed_door_to_provider_minutes:.0f} min")
    with col6:
        st.metric("OR Util", f"{metrics.or_utilization_percent:.1f}%")

    st.markdown("---")

    # LOB Chart
    chart_data = build_lob_chart_data(metrics)
    fig = create_lob_chart(chart_data)
    st.plotly_chart(fig, width="stretch")

    # Two columns: cumulative chart + WIP
    col_left, col_right = st.columns(2)

    with col_left:
        cum_fig = create_cumulative_lob_chart(chart_data)
        st.plotly_chart(cum_fig, width="stretch")

    with col_right:
        wip_fig = create_wip_chart(metrics.wip_by_stage)
        st.plotly_chart(wip_fig, width="stretch")

    # Stage details table
    st.subheader("Stage Details")
    stage_data = []
    for stage in PATIENT_FLOW_STAGES:
        sm = metrics.stage_metrics.get(stage)
        if sm:
            cap = capacities.get(stage)
            stage_data.append({
                "Stage": STAGE_DISPLAY_NAMES.get(stage, stage.value),
                "Throughput (pts/hr)": f"{sm.actual_throughput_per_hour:.1f}",
                "Target (pts/hr)": f"{sm.target_throughput_per_hour:.1f}",
                "Deviation": f"{sm.deviation_from_target:.1%}",
                "WIP": sm.current_wip,
                "Utilization": f"{sm.utilization_percent:.1f}%",
                "Avg Service (min)": f"{sm.avg_service_time_minutes:.0f}",
                "Takt Time (min)": f"{sm.takt_time_minutes:.1f}",
            })
    st.dataframe(stage_data, width="stretch")

    # Bottleneck indicator
    if metrics.bottleneck_stage:
        st.error(
            f"**Bottleneck Detected:** {STAGE_DISPLAY_NAMES.get(metrics.bottleneck_stage, metrics.bottleneck_stage.value)} "
            f"| Balance Score: {metrics.balance_score:.3f}"
        )
    else:
        st.success(f"System balanced | Balance Score: {metrics.balance_score:.3f}")
