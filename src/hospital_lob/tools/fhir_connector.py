"""FHIR connector stub for future EHR integration."""

from hospital_lob.tools._compat import BaseTool
from pydantic import BaseModel, Field


class FHIRInput(BaseModel):
    resource_type: str = Field(description="FHIR R4 resource type: Patient, Encounter, Procedure, MedicationRequest")
    query_params: str = Field(default="{}", description="JSON query parameters")


class FHIRConnectorTool(BaseTool):
    name: str = "fhir_connector"
    description: str = (
        "Connects to a FHIR R4 compliant EHR system to retrieve patient, encounter, "
        "procedure, and medication data. Currently returns mock data. "
        "Will connect to real EHR APIs in production."
    )
    args_schema: type[BaseModel] = FHIRInput

    def _run(self, resource_type: str = "Patient", query_params: str = "{}") -> str:
        # Stub: returns a message indicating future integration
        return (
            f"FHIR Connector Stub: Would query {resource_type} resources with params {query_params}. "
            f"This is a placeholder for future EHR integration via HL7 FHIR R4. "
            f"Supported resources: Patient, Encounter, Procedure, MedicationRequest, Observation. "
            f"Currently using mock data from the in-memory store."
        )
