"""Main LOB Analysis Crew: data collection → metrics → bottleneck → recommendations."""

from crewai import Agent, Crew, Process, Task

from hospital_lob.tools.bottleneck_analyzer import BottleneckAnalyzerTool
from hospital_lob.tools.data_query_tool import DataQueryTool
from hospital_lob.tools.lob_chart_generator import LOBChartGeneratorTool
from hospital_lob.tools.metrics_calculator import MetricsCalculatorTool


def create_lob_analysis_crew(time_window_hours: int = 24) -> Crew:
    """Create the LOB analysis crew with sequential task flow."""

    # Tools
    data_query = DataQueryTool()
    metrics_calc = MetricsCalculatorTool()
    chart_gen = LOBChartGeneratorTool()
    bottleneck = BottleneckAnalyzerTool()

    # Agents
    data_collector = Agent(
        role="Hospital Data Acquisition Specialist",
        goal="Gather and validate patient flow data across all LOB stages",
        backstory=(
            "Expert health informatics analyst who understands EHR data structures "
            "and hospital workflows. Specializes in extracting clean, validated data."
        ),
        tools=[data_query],
        verbose=True,
    )

    lob_analyst = Agent(
        role="Line of Balance Performance Analyst",
        goal="Compute all LOB metrics and detect flow imbalances between stages",
        backstory=(
            "Industrial engineer specializing in healthcare operations with deep "
            "knowledge of takt time, flow balancing, and lean methodology."
        ),
        tools=[metrics_calc, chart_gen],
        verbose=True,
    )

    bottleneck_detector = Agent(
        role="Constraint Identification Specialist",
        goal="Identify the binding constraint in the patient flow pipeline",
        backstory=(
            "Six Sigma Black Belt with hospital operations experience. Applies "
            "Theory of Constraints drum-buffer-rope thinking to healthcare."
        ),
        tools=[bottleneck, data_query],
        verbose=True,
    )

    recommender = Agent(
        role="Healthcare Operations Improvement Advisor",
        goal="Generate actionable recommendations to resolve bottlenecks and rebalance the LOB",
        backstory=(
            "Hospital COO consultant who has led dozens of Lean/Six Sigma "
            "transformations. Translates analysis into concrete corrective actions."
        ),
        tools=[],
        verbose=True,
    )

    # Tasks (sequential flow)
    collect_data = Task(
        description=(
            f"Gather current patient flow data across all hospital LOB stages for the "
            f"last {time_window_hours} hours. Query the data store for a summary of "
            f"patient census by stage, priority, and department. Validate data quality."
        ),
        expected_output=(
            "Structured summary with total patients, active patients, "
            "patients by stage, patients by priority, and data quality flags."
        ),
        agent=data_collector,
    )

    compute_metrics = Task(
        description=(
            "Using the patient flow data, compute all Line of Balance metrics: "
            "takt time per stage, ALOS, bed turnover rate, ED door-to-provider time, "
            "OR utilization. Generate LOB chart data showing planned vs actual throughput."
        ),
        expected_output=(
            "Complete LOB metrics snapshot with per-stage metrics, overall KPIs, "
            "and LOB chart data. Highlight stages significantly below target."
        ),
        agent=lob_analyst,
        context=[collect_data],
    )

    find_bottlenecks = Task(
        description=(
            "Analyze the LOB metrics to identify primary and secondary bottleneck "
            "stages using Theory of Constraints. Consider throughput deviation, WIP "
            "accumulation, and utilization. Explain the cascade effect."
        ),
        expected_output=(
            "Bottleneck analysis report with: primary constraint, secondary constraint, "
            "constraint scores, and narrative explaining impact on hospital throughput."
        ),
        agent=bottleneck_detector,
        context=[collect_data, compute_metrics],
    )

    generate_recommendations = Task(
        description=(
            "Based on bottleneck analysis and LOB metrics, generate a prioritized list "
            "of 3-5 corrective actions. Consider: adding capacity, staff redeployment, "
            "care pathway redesign, discharge improvement. Estimate expected impact."
        ),
        expected_output=(
            "Prioritized corrective actions with: description, target stage, expected "
            "throughput improvement, implementation complexity, and timeline."
        ),
        agent=recommender,
        context=[compute_metrics, find_bottlenecks],
    )

    return Crew(
        agents=[data_collector, lob_analyst, bottleneck_detector, recommender],
        tasks=[collect_data, compute_metrics, find_bottlenecks, generate_recommendations],
        process=Process.sequential,
        verbose=True,
    )
