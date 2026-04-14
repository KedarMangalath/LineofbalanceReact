"""Streamlit main app for Hospital LOB Dashboard."""

import streamlit as st

st.set_page_config(
    page_title="Hospital LOB Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    st.sidebar.title("Hospital LOB")
    st.sidebar.markdown("**Line of Balance Framework**")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Navigation",
        [
            "Overview",
            "Bottleneck Analysis",
            "Simulation",
            "Pharmacy LOB",
            "Alerts",
            "Agent Chat",
        ],
    )

    # Initialize data store in session state
    if "store_initialized" not in st.session_state:
        with st.spinner("Generating hospital data..."):
            from hospital_lob.data.store import get_store
            get_store()
            st.session_state.store_initialized = True

    # Sidebar controls
    st.sidebar.markdown("---")
    st.sidebar.subheader("Controls")
    if st.sidebar.button("Refresh Data"):
        from hospital_lob.data.store import get_store
        get_store().refresh()
        st.rerun()

    time_window = st.sidebar.slider("Time Window (hours)", 6, 72, 24, step=6)
    st.session_state.time_window = time_window

    # Route to page
    if page == "Overview":
        from hospital_lob.dashboard.views.overview import render_overview
        render_overview(time_window)
    elif page == "Bottleneck Analysis":
        from hospital_lob.dashboard.views.bottlenecks import render_bottlenecks
        render_bottlenecks(time_window)
    elif page == "Simulation":
        from hospital_lob.dashboard.views.simulation import render_simulation
        render_simulation()
    elif page == "Pharmacy LOB":
        from hospital_lob.dashboard.views.pharmacy import render_pharmacy
        render_pharmacy(time_window)
    elif page == "Alerts":
        from hospital_lob.dashboard.views.alerts import render_alerts
        render_alerts()
    elif page == "Agent Chat":
        from hospital_lob.dashboard.views.agent_chat import render_agent_chat
        render_agent_chat()


if __name__ == "__main__":
    main()
