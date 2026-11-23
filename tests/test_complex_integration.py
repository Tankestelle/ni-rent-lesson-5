import pytest

from src.manager import Manager
from src.models import (
    Apartment,
    ApartmentSettlement,
    Bill,
    Parameters,
    Room,
    TenantSettlement,
)


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

    assert manager.get_apartment_costs("aaa", 2025, 1) is None


def test_apartment_costs_with_optional_parameters():
    manager = Manager(Parameters())
    manager.bills.append(
        Bill(
            apartment="apart-polanka",
            date_due="2025-03-15",
            settlement_year=2025,
            settlement_month=2,
            amount_pln=1250.0,
            type="rent",
        )
    )

    manager.bills.append(
        Bill(
            apartment="apart-polanka",
            date_due="2024-03-15",
            settlement_year=2024,
            settlement_month=2,
            amount_pln=1150.0,
            type="rent",
        )
    )

    manager.bills.append(
        Bill(
            apartment="apart-polanka",
            date_due="2024-02-02",
            settlement_year=2024,
            settlement_month=1,
            amount_pln=222.0,
            type="electricity",
        )
    )

    costs = manager.get_apartment_costs("apartment-1", 2024, 1)
    assert costs is None

    costs = manager.get_apartment_costs("apart-polanka", 2024, 3)
    assert costs == 0.0

    costs = manager.get_apartment_costs("apart-polanka", 2024, 1)
    assert costs == 222.0

    costs = manager.get_apartment_costs("apart-polanka", 2025, 1)
    assert costs == 910.0

    costs = manager.get_apartment_costs("apart-polanka", 2024)
    assert costs == 1372.0

    costs = manager.get_apartment_costs("apart-polanka")
    assert costs == 3532.0


def test_create_apartment_settlement_with_and_without_bills():
    manager = Manager(Parameters())

    settlement_with_bills = manager.create_apartment_settlement(
        "apart-polanka", 2025, 1
    )
    assert isinstance(settlement_with_bills, ApartmentSettlement)
    assert settlement_with_bills.apartment == "apart-polanka"
    assert settlement_with_bills.year == 2025
    assert settlement_with_bills.month == 1
    assert settlement_with_bills.total_rent_pln == 4200.0
    assert settlement_with_bills.total_bills_pln == 910.0
    assert settlement_with_bills.total_due_pln == -910.0

    settlement_no_bills = manager.create_apartment_settlement("apart-polanka", 2025, 2)
    assert isinstance(settlement_no_bills, ApartmentSettlement)
    assert settlement_no_bills.apartment == "apart-polanka"
    assert settlement_no_bills.year == 2025
    assert settlement_no_bills.month == 2
    assert settlement_no_bills.total_rent_pln == 4200.0
    assert settlement_no_bills.total_bills_pln == 0.0
    assert settlement_no_bills.total_due_pln == 0.0

    assert (
        manager.create_apartment_settlement("non-existent-apartment", 2025, 1) is None
    )


def test_create_tenant_settlements_for_apartment_settlement():
    manager = Manager(Parameters())

    settlement_multi = manager.create_apartment_settlement("apart-polanka", 2025, 1)
    assert settlement_multi is not None

    tenant_settlements_multi = manager.create_tenant_settlements(settlement_multi)
    assert len(tenant_settlements_multi) == 3
    assert all(isinstance(item, TenantSettlement) for item in tenant_settlements_multi)

    by_tenant = {item.tenant: item for item in tenant_settlements_multi}
    expected_share_three = 910.0 / 3

    assert by_tenant["tenant-1"].bills_pln == pytest.approx(expected_share_three)
    assert by_tenant["tenant-1"].rent_pln == 1500.0
    assert by_tenant["tenant-1"].total_due_pln == pytest.approx(
        1500.0 + expected_share_three
    )
    assert by_tenant["tenant-1"].balance_pln == pytest.approx(
        -(1500.0 + expected_share_three)
    )

    assert by_tenant["tenant-2"].bills_pln == pytest.approx(expected_share_three)
    assert by_tenant["tenant-3"].bills_pln == pytest.approx(expected_share_three)

    manager.apartments["apart-single"] = Apartment(
        key="apart-single",
        name="Single",
        location="Single 1",
        area_m2=35.0,
        rooms={"r1": Room(name="Room", area_m2=35.0)},
    )
    manager.tenants["tenant-solo"] = manager.tenants["tenant-1"].model_copy(
        update={"apartment": "apart-single", "rent_pln": 1800.0}
    )
    manager.bills.append(
        manager.bills[0].model_copy(
            update={"apartment": "apart-single", "amount_pln": 400.0}
        )
    )

    settlement_single = manager.create_apartment_settlement("apart-single", 2025, 1)
    assert settlement_single is not None
    tenant_settlements_single = manager.create_tenant_settlements(settlement_single)
    assert len(tenant_settlements_single) == 1
    assert tenant_settlements_single[0].tenant == "tenant-solo"
    assert tenant_settlements_single[0].bills_pln == 400.0
    assert tenant_settlements_single[0].total_due_pln == 2200.0

    manager.apartments["apart-empty"] = Apartment(
        key="apart-empty",
        name="Empty",
        location="Empty 2",
        area_m2=40.0,
        rooms={"r1": Room(name="Room", area_m2=40.0)},
    )
    settlement_empty = manager.create_apartment_settlement("apart-empty", 2025, 1)
    assert settlement_empty is not None
    assert manager.create_tenant_settlements(settlement_empty) == []
