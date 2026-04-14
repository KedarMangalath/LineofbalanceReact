"""LOB chart generation tool using Plotly."""

import json
from datetime import datetime, timedelta
from typing import Optional

import plotly.graph_objects as go
from hospital_lob.tools._compat import BaseTool
from pydantic import BaseModel, Field

from hospital_lob.config.settings import PATIENT_FLOW_STAGES, STAGE_DISPLAY_NAMES, StageEnum
from hospital_lob.models.metrics import LOBChartData, LOBMetrics


class ChartInput(BaseModel):
    time_window_hours: int = Field(default=24, description="Time window for chart data")


class LOBChartGeneratorTool(BaseTool):
    name: str = "lob_chart_generator"
    description: str = (
        "Generates Line of Balance charts showing planned vs actual throughput "
        "across all hospital stages. Returns Plotly figure JSON."
    )
    args_schema: type[BaseModel] = ChartInput

    def _run(self, time_window_hours: int = 24) -> str:
        from hospital_lob.data.store import get_store
        from hospital_lob.tools.metrics_calculator import compute_lob_metrics

        store = get_store()
        now = datetime.now()
        patients = store.get_patients(start_time=now - timedelta(hours=time_window_hours))
        capacities = store.get_stage_capacities()
        metrics = compute_lob_metrics(patients, capacities, time_window_hours)

        chart_data = build_lob_chart_data(metrics)
        fig = create_lob_chart(chart_data)
        return fig.to_json()


def build_lob_chart_data(metrics: LOBMetrics) -> LOBChartData:
    """Build chart data from LOB metrics."""
    stages = []
    target_tp = []
    actual_tp = []
    cum_target = []
    cum_actual = []
    running_target = 0
    running_actual = 0

    for stage in PATIENT_FLOW_STAGES:
        sm = metrics.stage_metrics.get(stage)
        if sm:
            stages.append(STAGE_DISPLAY_NAMES.get(stage, stage.value))
            target_tp.append(sm.target_throughput_per_hour)
            actual_tp.append(sm.actual_throughput_per_hour)
            running_target += sm.target_throughput_per_hour
            running_actual += sm.actual_throughput_per_hour
            cum_target.append(running_target)
            cum_actual.append(running_actual)

    return LOBChartData(
        stages=stages,
        target_throughput=target_tp,
        actual_throughput=actual_tp,
        cumulative_target=cum_target,
        cumulative_actual=cum_actual,
        timestamp=metrics.timestamp,
    )


def create_lob_chart(data: LOBChartData) -> go.Figure:
    """Create the primary LOB bar chart."""
    fig = go.Figure()

    # Target throughput bars
    fig.add_trace(go.Bar(
        name="Target Throughput",
        x=data.stages,
        y=data.target_throughput,
        marker_color="#2196F3",
        opacity=0.7,
    ))

    # Actual throughput bars
    fig.add_trace(go.Bar(
        name="Actual Throughput",
        x=data.stages,
        y=data.actual_throughput,
        marker_color="#4CAF50",
    ))

    # Target line
    fig.add_trace(go.Scatter(
        name="Target Rate",
        x=data.stages,
        y=data.target_throughput,
        mode="lines+markers",
        line=dict(color="#F44336", width=3, dash="dash"),
        marker=dict(size=8),
    ))

    fig.update_layout(
        title="Hospital Line of Balance: Throughput by Stage",
        xaxis_title="Patient Flow Stage",
        yaxis_title="Throughput (patients/hour)",
        barmode="group",
        template="plotly_white",
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def create_cumulative_lob_chart(data: LOBChartData) -> go.Figure:
    """Create cumulative LOB chart showing planned vs actual progression."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        name="Planned (Target)",
        x=data.stages,
        y=data.cumulative_target,
        mode="lines+markers",
        line=dict(color="#2196F3", width=3),
        marker=dict(size=10),
        fill="tozeroy",
        fillcolor="rgba(33, 150, 243, 0.1)",
    ))

    fig.add_trace(go.Scatter(
        name="Actual",
        x=data.stages,
        y=data.cumulative_actual,
        mode="lines+markers",
        line=dict(color="#FF9800", width=3),
        marker=dict(size=10),
        fill="tozeroy",
        fillcolor="rgba(255, 152, 0, 0.1)",
    ))

    fig.update_layout(
        title="Cumulative Line of Balance: Planned vs Actual",
        xaxis_title="Patient Flow Stage",
        yaxis_title="Cumulative Throughput (patients/hour)",
        template="plotly_white",
        height=450,
    )

    return fig


def create_wip_chart(wip_by_stage: dict[StageEnum, int]) -> go.Figure:
    """Create WIP (Work In Progress) chart by stage."""
    stages = [STAGE_DISPLAY_NAMES.get(s, s.value) for s in PATIENT_FLOW_STAGES if s in wip_by_stage]
    wip_values = [wip_by_stage[s] for s in PATIENT_FLOW_STAGES if s in wip_by_stage]

    colors = ["#F44336" if v > 10 else "#FF9800" if v > 5 else "#4CAF50" for v in wip_values]

    fig = go.Figure(go.Bar(
        x=stages,
        y=wip_values,
        marker_color=colors,
        text=wip_values,
        textposition="auto",
    ))

    fig.update_layout(
        title="Work In Progress (WIP) by Stage",
        xaxis_title="Stage",
        yaxis_title="Patients in Queue",
        template="plotly_white",
        height=400,
    )

    return fig
