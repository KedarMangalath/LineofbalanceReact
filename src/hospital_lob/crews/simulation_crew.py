"""Simulation Crew for what-if scenario analysis."""

import json

from crewai import Agent, Crew, Process, Task

from hospital_lob.tools.metrics_calculator import MetricsCalculatorTool
from hospital_lob.tools.simulation_engine import SimulationEngineTool


def create_simulation_crew(
    duration_hours: int = 168,
    arrival_rate: float = 8.0,
    capacity_overrides: dict | None = None,
    service_time_multipliers: dict | None = None,
) -> Crew:
    """Create the simulation crew for what-if analysis."""

    sim_engine = SimulationEngineTool()
    metrics_calc = MetricsCalculatorTool()

    simulator = Agent(
        role="Discrete-Event Simulation Specialist",
        goal="Run patient flow simulations and predict impact of capacity changes",
        backstory=(
            "Operations research PhD who models hospital systems using discrete-event "
            "simulation. Designs scenarios and presents actionable comparisons."
        ),
        tools=[sim_engine],
        verbose=True,
    )

    analyst = Agent(
        role="Simulation Results Analyst",
        goal="Compare simulation results against baseline and quantify improvements",
        backstory=(
            "Healthcare operations analyst who interprets simulation outputs and "
            "translates them into business impact metrics."
        ),
        tools=[metrics_calc],
        verbose=True,
    )

    cap_json = json.dumps(capacity_overrides or {})
    mult_json = json.dumps(service_time_multipliers or {})

    run_sim = Task(
        description=(
            f"Run a discrete-event simulation of hospital patient flow for {duration_hours} hours "
            f"with arrival rate {arrival_rate} pts/hr. Apply capacity overrides: {cap_json} "
            f"and service time multipliers: {mult_json}. Report projected throughput, "
            f"wait times, and predicted bottleneck."
        ),
        expected_output=(
            "Simulation results with projected throughput per stage, ALOS, "
            "predicted bottleneck, and comparison to baseline."
        ),
        agent=simulator,
    )

    analyze = Task(
        description=(
            "Compare simulation results against current baseline metrics. "
            "Calculate the current baseline metrics first, then compare each KPI. "
            "Quantify the improvement or degradation for each metric."
        ),
        expected_output=(
            "Comparison table: baseline vs projected for each KPI. "
            "Summary of which improvements are significant and which are marginal."
        ),
        agent=analyst,
        context=[run_sim],
    )

    return Crew(
        agents=[simulator, analyst],
        tasks=[run_sim, analyze],
        process=Process.sequential,
        verbose=True,
    )
