"""Pharmacy LOB Analysis Crew."""

from crewai import Agent, Crew, Process, Task

from hospital_lob.tools.data_query_tool import DataQueryTool
from hospital_lob.tools.pharmacy_metrics import PharmacyMetricsTool


def create_pharmacy_crew(time_window_hours: int = 24) -> Crew:
    """Create the pharmacy LOB analysis crew."""

    data_query = DataQueryTool()
    pharmacy_metrics = PharmacyMetricsTool()

    data_collector = Agent(
        role="Pharmacy Data Specialist",
        goal="Gather medication order pipeline data for LOB analysis",
        backstory="Expert in hospital pharmacy informatics and medication order workflows.",
        tools=[data_query],
        verbose=True,
    )

    pharmacy_analyst = Agent(
        role="Hospital Pharmacy Operations Analyst",
        goal="Analyze the pharmacy dispensing pipeline and identify MTAT bottlenecks",
        backstory=(
            "Specialist in pharmacy operations who understands that MTAT is a patient "
            "safety metric. Analyzes the full pipeline from order to administration."
        ),
        tools=[pharmacy_metrics],
        verbose=True,
    )

    recommender = Agent(
        role="Pharmacy Operations Improvement Advisor",
        goal="Recommend optimizations for the pharmacy medication turnaround pipeline",
        backstory=(
            "Consultant experienced in pharmacy automation, ADC deployment, and "
            "pharmacist workflow redesign. Knows that fixing dispensing without fixing "
            "verification just shifts the constraint."
        ),
        tools=[],
        verbose=True,
    )

    collect_data = Task(
        description=(
            f"Query the pharmacy order data for the last {time_window_hours} hours. "
            f"Get total orders, completion rates, and queue status."
        ),
        expected_output="Pharmacy data summary with order counts, completion rates, and queue depths.",
        agent=data_collector,
    )

    analyze_pharmacy = Task(
        description=(
            "Compute pharmacy LOB metrics: MTAT, verification wait times, compounding "
            "times, queue depths per stage, and throughput per stage. Identify the "
            "pharmacy bottleneck stage."
        ),
        expected_output=(
            "Pharmacy metrics with MTAT, per-stage performance, bottleneck identification, "
            "and comparison to target turnaround times."
        ),
        agent=pharmacy_analyst,
        context=[collect_data],
    )

    recommend = Task(
        description=(
            "Based on pharmacy LOB analysis, recommend 2-3 specific improvements. "
            "Consider: automated dispensing cabinets, pharmacist capacity rebalancing, "
            "IV compounding workflow optimization, and stat order fast-tracking."
        ),
        expected_output=(
            "Prioritized pharmacy improvement recommendations with expected MTAT reduction."
        ),
        agent=recommender,
        context=[analyze_pharmacy],
    )

    return Crew(
        agents=[data_collector, pharmacy_analyst, recommender],
        tasks=[collect_data, analyze_pharmacy, recommend],
        process=Process.sequential,
        verbose=True,
    )
