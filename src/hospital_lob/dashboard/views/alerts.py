"""Alerts page."""

import streamlit as st

from hospital_lob.config.settings import ALERT_THRESHOLDS, SeverityEnum
from hospital_lob.crews.alerting_crew import check_alerts_direct


def render_alerts():
    st.title("Alerts & Monitoring")
    st.markdown("*Real-time threshold monitoring for hospital operations*")

    # Run alert check
    alerts = check_alerts_direct()

    # Summary
    critical = [a for a in alerts if a.severity == SeverityEnum.CRITICAL]
    warnings = [a for a in alerts if a.severity == SeverityEnum.WARNING]
    info = [a for a in alerts if a.severity == SeverityEnum.INFO]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Alerts", len(alerts))
    with col2:
        if critical:
            st.metric("Critical", len(critical))
        else:
            st.metric("Critical", 0)
    with col3:
        st.metric("Warning", len(warnings))
    with col4:
        st.metric("Info", len(info))

    st.markdown("---")

    # Critical alerts
    if critical:
        st.subheader("Critical Alerts")
        for alert in critical:
            st.error(f"**{alert.metric_name}** | {alert.message}")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.write(f"Current: **{alert.current_value:.1f}**")
            with col_b:
                st.write(f"Threshold: **{alert.threshold_value:.1f}**")
            with col_c:
                if alert.stage:
                    st.write(f"Stage: **{alert.stage.value}**")

    # Warning alerts
    if warnings:
        st.subheader("Warning Alerts")
        for alert in warnings:
            st.warning(f"**{alert.metric_name}** | {alert.message}")

    # Info alerts
    if info:
        st.subheader("Info")
        for alert in info:
            st.info(f"**{alert.metric_name}** | {alert.message}")

    if not alerts:
        st.success("All metrics within normal thresholds.")

    # Threshold configuration
    st.markdown("---")
    st.subheader("Alert Thresholds Configuration")

    threshold_data = []
    for metric, thresholds in ALERT_THRESHOLDS.items():
        threshold_data.append({
            "Metric": metric.replace("_", " ").title(),
            "Warning": thresholds["warning"],
            "Critical": thresholds["critical"],
        })
    st.dataframe(threshold_data, width="stretch")
