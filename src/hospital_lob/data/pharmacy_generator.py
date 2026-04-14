"""Synthetic pharmacy order data generator."""

import random
import uuid
from datetime import datetime, timedelta

import numpy as np

from hospital_lob.config.settings import PharmacyOrderType, PharmacyStageEnum


def generate_pharmacy_orders(
    num_days: int = 3,
    orders_per_shift: int = 80,
    start_date: datetime | None = None,
) -> list[dict]:
    """Generate synthetic pharmacy medication orders.

    Returns list of dicts (not PharmacyOrder models to avoid circular imports).
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=num_days)

    medications = [
        "Metoprolol 25mg", "Amoxicillin 500mg", "Heparin 5000U",
        "Vancomycin 1g IV", "Morphine 4mg IV", "Ceftriaxone 1g IV",
        "Pantoprazole 40mg", "Insulin Lispro", "Furosemide 20mg",
        "Norepinephrine drip", "TPN Solution", "Amphotericin B IV",
    ]

    orders = []

    for day in range(num_days):
        for shift in range(3):  # 3 shifts per day
            shift_start = start_date + timedelta(days=day, hours=shift * 8)
            n_orders = np.random.poisson(orders_per_shift)

            for _ in range(n_orders):
                order_time = shift_start + timedelta(minutes=random.uniform(0, 480))
                order_type = random.choices(
                    [PharmacyOrderType.STANDARD, PharmacyOrderType.STAT, PharmacyOrderType.IV_COMPOUND],
                    weights=[0.55, 0.25, 0.20],
                )[0]

                # Verification time
                if order_type == PharmacyOrderType.STAT:
                    verify_delay = max(3, np.random.exponential(8))
                else:
                    verify_delay = max(5, np.random.exponential(20))
                verification_time = order_time + timedelta(minutes=verify_delay)

                # Compounding (only for IV compounds)
                compounding_start = None
                compounding_end = None
                if order_type == PharmacyOrderType.IV_COMPOUND:
                    compounding_start = verification_time + timedelta(minutes=random.uniform(2, 10))
                    compound_duration = max(15, np.random.exponential(30))
                    compounding_end = compounding_start + timedelta(minutes=compound_duration)
                    post_compound = compounding_end
                else:
                    post_compound = verification_time

                # Dispensing
                dispense_delay = max(2, np.random.exponential(10))
                dispensed_time = post_compound + timedelta(minutes=dispense_delay)

                # Administration
                admin_delay = max(5, np.random.exponential(15))
                administered_time = dispensed_time + timedelta(minutes=admin_delay)

                # Some recent orders still in progress
                time_since = (datetime.now() - order_time).total_seconds() / 3600
                is_complete = True
                current_stage = PharmacyStageEnum.ADMINISTRATION

                if time_since < 2:
                    cutoff = random.random()
                    if cutoff < 0.2:
                        verification_time = None
                        compounding_start = None
                        compounding_end = None
                        dispensed_time = None
                        administered_time = None
                        is_complete = False
                        current_stage = PharmacyStageEnum.ORDER_RECEIPT
                    elif cutoff < 0.4:
                        compounding_start = None
                        compounding_end = None
                        dispensed_time = None
                        administered_time = None
                        is_complete = False
                        current_stage = PharmacyStageEnum.VERIFICATION
                    elif cutoff < 0.6 and order_type == PharmacyOrderType.IV_COMPOUND:
                        dispensed_time = None
                        administered_time = None
                        is_complete = False
                        current_stage = PharmacyStageEnum.COMPOUNDING
                    elif cutoff < 0.8:
                        administered_time = None
                        is_complete = False
                        current_stage = PharmacyStageEnum.LABELLING

                orders.append({
                    "order_id": str(uuid.uuid4())[:8],
                    "patient_id": str(uuid.uuid4())[:8],
                    "medication": random.choice(medications),
                    "order_type": order_type,
                    "order_time": order_time,
                    "verification_time": verification_time,
                    "compounding_start": compounding_start,
                    "compounding_end": compounding_end,
                    "dispensed_time": dispensed_time,
                    "administered_time": administered_time,
                    "current_stage": current_stage,
                    "is_complete": is_complete,
                })

    return orders
