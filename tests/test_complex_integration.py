import pytest

from src.manager import Manager
from src.models import Bill, Parameters


def test_get_apartment_costs_existing_bills_for_month():
    manager = Manager(Parameters())

    total = manager.get_apartment_costs("apart-polanka", 2025, 1)

    assert total == 910.0
    assert isinstance(total, float)


def test_get_apratment_costs_no_bills_in_month_or_wrong_month():
    manager = Manager(Parameters())

    assert manager.get_apartment_costs("apart-polanka", 2025, 2) == 0.0
    assert manager.get_apartment_costs("apart-polanka", 2024, 3) == 0.0


def test_get_apartment_costs_nonexistent_apartment():
    manager = Manager(Parameters())

    with pytest.raises(ValueError):
        manager.get_apartment_costs("aaa", 2025, 1)
