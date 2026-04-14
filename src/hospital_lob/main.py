"""Main entry point for Hospital LOB AI Framework."""

import sys

from dotenv import load_dotenv

load_dotenv()


def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "server":
            import uvicorn
            uvicorn.run(
                "hospital_lob.api.main:app",
                host="0.0.0.0",
                port=8000,
                reload=True,
            )

        elif command == "dashboard":
            import subprocess
            subprocess.run([
                sys.executable, "-m", "streamlit", "run",
                "src/hospital_lob/dashboard/app.py",
                "--server.headless", "true",
            ])

        elif command == "analyze":
            from hospital_lob.crews.lob_analysis_crew import create_lob_analysis_crew
            crew = create_lob_analysis_crew()
            result = crew.kickoff()
            print(result)

        elif command == "simulate":
            from hospital_lob.tools.simulation_engine import run_simulation
            import json
            result = run_simulation()
            print(json.dumps(result, indent=2))

        elif command == "generate-data":
            from hospital_lob.data.store import get_store
            store = get_store()
            patients = store.get_patients()
            print(f"Generated {len(patients)} patients")
            orders = store.get_pharmacy_orders()
            print(f"Generated {len(orders)} pharmacy orders")

        else:
            _print_usage()
    else:
        _print_usage()


def _print_usage():
    print("Hospital LOB AI Framework")
    print("=" * 40)
    print()
    print("Usage:")
    print("  python -m hospital_lob server         - Launch FastAPI backend (port 8000)")
    print("  python -m hospital_lob dashboard      - Launch Streamlit dashboard (legacy)")
    print("  python -m hospital_lob analyze        - Run LOB analysis crew")
    print("  python -m hospital_lob simulate       - Run patient flow simulation")
    print("  python -m hospital_lob generate-data  - Generate mock data")
    print()
    print("For the React frontend, also run:")
    print("  cd frontend && npm run dev")


if __name__ == "__main__":
    main()
