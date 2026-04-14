"""In-memory data store with abstract interface for future DB/FHIR swap."""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional

from hospital_lob.config.settings import StageEnum
from hospital_lob.data.mock_generator import generate_patients, generate_stage_capacities
from hospital_lob.data.pharmacy_generator import generate_pharmacy_orders
from hospital_lob.models.patient import Patient, StageCapacity
from hospital_lob.models.pharmacy import PharmacyOrder


class DataStore(ABC):
    """Abstract data store interface."""

    @abstractmethod
    def get_patients(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        stage: Optional[StageEnum] = None,
        active_only: bool = False,
    ) -> list[Patient]:
        ...

    @abstractmethod
    def get_stage_capacities(self) -> dict[StageEnum, StageCapacity]:
        ...

    @abstractmethod
    def get_pharmacy_orders(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[PharmacyOrder]:
        ...

    @abstractmethod
    def refresh(self) -> None:
        ...


class InMemoryStore(DataStore):
    """In-memory data store populated from mock generators."""

    def __init__(self, num_days: int = 3, bottleneck_factor: float = 1.5):
        self._num_days = num_days
        self._bottleneck_factor = bottleneck_factor
        self._patients: list[Patient] = []
        self._capacities: dict[StageEnum, StageCapacity] = {}
        self._pharmacy_orders: list[PharmacyOrder] = []
        self.refresh()

    def refresh(self) -> None:
        """Regenerate all mock data."""
        self._patients = generate_patients(
            num_days=self._num_days,
            bottleneck_factor=self._bottleneck_factor,
        )
        self._capacities = generate_stage_capacities()
        self._update_capacity_occupancy()

        raw_orders = generate_pharmacy_orders(num_days=self._num_days)
        self._pharmacy_orders = [PharmacyOrder(**o) for o in raw_orders]

    def _update_capacity_occupancy(self) -> None:
        """Update current occupancy from active patients."""
        for cap in self._capacities.values():
            cap.current_occupancy = 0

        for patient in self._patients:
            if patient.is_active and patient.current_stage in self._capacities:
                self._capacities[patient.current_stage].current_occupancy += 1

    def get_patients(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        stage: Optional[StageEnum] = None,
        active_only: bool = False,
    ) -> list[Patient]:
        result = self._patients

        if start_time:
            result = [p for p in result if p.admission_time >= start_time]
        if end_time:
            result = [p for p in result if p.admission_time <= end_time]
        if stage:
            result = [p for p in result if p.current_stage == stage]
        if active_only:
            result = [p for p in result if p.is_active]

        return result

    def get_stage_capacities(self) -> dict[StageEnum, StageCapacity]:
        return self._capacities.copy()

    def get_pharmacy_orders(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[PharmacyOrder]:
        result = self._pharmacy_orders
        if start_time:
            result = [o for o in result if o.order_time >= start_time]
        if end_time:
            result = [o for o in result if o.order_time <= end_time]
        return result


# Singleton store instance
_store: Optional[InMemoryStore] = None


def get_store() -> InMemoryStore:
    """Get or create the global data store."""
    global _store
    if _store is None:
        _store = InMemoryStore()
    return _store
