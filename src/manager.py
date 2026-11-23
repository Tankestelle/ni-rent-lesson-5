from src.models import (
    Apartment,
    ApartmentSettlement,
    Bill,
    Parameters,
    Tenant,
    TenantSettlement,
    Transfer,
)


class Manager:
    def __init__(self, parameters: Parameters):
        self.parameters = parameters

        self.apartments = {}
        self.tenants = {}
        self.transfers = []
        self.bills = []

        self.load_data()

    def load_data(self):
        self.apartments = Apartment.from_json_file(self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)

    def check_tenants_apartment_keys(self) -> bool:
        for tenant in self.tenants.values():
            if tenant.apartment not in self.apartments:
                return False
        return True

    def get_apartment_costs(
        self, apartment_key: str, year: int | None = None, month: int | None = None
    ) -> float | None:
        if apartment_key not in self.apartments:
            return None

        if month is not None and not (1 <= month <= 12):
            raise ValueError(
                f"Invalid month '{month}'. Expected value between 1 and 12."
            )

        total = 0.0
        for bill in self.bills:
            if bill.apartment != apartment_key:
                continue
            if year is not None and bill.settlement_year != year:
                continue
            if month is not None and bill.settlement_month != month:
                continue
            total += bill.amount_pln

        return float(total)

    def create_apartment_settlement(
        self, apartment_key: str, year: int, month: int
    ) -> ApartmentSettlement | None:
        if apartment_key not in self.apartments:
            return None

        total_rent = float(
            sum(
                tenant.rent_pln
                for tenant in self.tenants.values()
                if tenant.apartment == apartment_key
            )
        )

        total_bills = self.get_apartment_costs(apartment_key, year, month)
        if total_bills is None:
            return None

        total_transfers = 0.0
        balance = total_transfers - total_bills

        return ApartmentSettlement(
            apartment=apartment_key,
            month=month,
            year=year,
            total_rent_pln=total_rent,
            total_bills_pln=total_bills,
            total_due_pln=balance,
        )

    def create_tenant_settlements(
        self,
        apartment_settlement: ApartmentSettlement,
    ) -> list[TenantSettlement]:
        matching_tenants = [
            (tenant_key, tenant)
            for tenant_key, tenant in self.tenants.items()
            if tenant.apartment == apartment_settlement.apartment
        ]

        if not matching_tenants:
            return []

        bill_share = apartment_settlement.total_bills_pln / len(matching_tenants)
        settlement_ref = (
            f"{apartment_settlement.apartment}-"
            f"{apartment_settlement.year}-"
            f"{apartment_settlement.month}"
        )

        result: list[TenantSettlement] = []
        for tenant_key, tenant in matching_tenants:
            total_due = tenant.rent_pln + bill_share
            transfers_sum = 0.0
            balance = transfers_sum - total_due

            result.append(
                TenantSettlement(
                    tenant=tenant_key,
                    apartment_settlement=settlement_ref,
                    month=apartment_settlement.month,
                    year=apartment_settlement.year,
                    rent_pln=tenant.rent_pln,
                    bills_pln=bill_share,
                    total_due_pln=total_due,
                    balance_pln=balance,
                )
            )

        return result

