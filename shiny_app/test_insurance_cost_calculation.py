from app import calculate_annual_cost_health_insurance, calculate_annual_cost_insurance
import pytest

def test_health_insurance_cost_calculation():
    assert calculate_annual_cost_health_insurance(treatment_costs_during_year=0, premium_per_month=10, deductible_amount=300) == 12 * 10, (
            "No treatment costs should result in just the premium cost."
            )
    assert calculate_annual_cost_health_insurance(treatment_costs_during_year=1452.2, premium_per_month=7.1, deductible_amount=1500) == pytest.approx(12 * 7.1 + 1452.2), (
            "Treatment costs below deductible should result in premium plus treatment costs."
            )
    assert calculate_annual_cost_health_insurance(treatment_costs_during_year=1000, premium_per_month=5, deductible_amount=300) == 12 * 5 + 300 + 0.10 * 700, (
            "Treatment costs slightly above deductible should result in premium plus deductible plus 10% of remaining costs."
            )
    assert calculate_annual_cost_health_insurance(treatment_costs_during_year=20000, premium_per_month=11.2, deductible_amount=2000) == pytest.approx(12 * 11.2 + 2000 + 700), (
            "Extremely huge treatment costs should result in premium plus deductible plus 700 (max out of pocket)."
            )
    
def test_insurance_cost_calculation():
    assert calculate_annual_cost_insurance(treatment_costs_during_year=0, premium_per_month=4.31, deductible_amount=250, percentage_covered=60, max_amount_insurance_pays=500) == 12 * 4.31, (
            "No treatment costs should result in just the premium cost."
            )
    assert calculate_annual_cost_insurance(treatment_costs_during_year=250, premium_per_month=15.3, deductible_amount=250, percentage_covered=90, max_amount_insurance_pays=1000) == pytest.approx(12 * 15.3 +  250), (
            "Treatment costs below deductible should result in premium plus treatment costs."
            )
    assert calculate_annual_cost_insurance(treatment_costs_during_year=1000, premium_per_month=21.0, deductible_amount=0, percentage_covered=90, max_amount_insurance_pays=900) == pytest.approx(12 * 21 + (1 - 0.9) * 1000), (
            "Treatment costs above deductible, but not too high, will be covered by percentage_covered of the insurance."
            )
    assert calculate_annual_cost_insurance(treatment_costs_during_year=1250, premium_per_month=5.9, deductible_amount=0, percentage_covered=90, max_amount_insurance_pays=100) == pytest.approx(12 * 5.9 + (1250 - 100)), (
            "Treatment costs (without deductible) that are way too high will only be reduced by max_amount_insurance_pays"
            )
    assert calculate_annual_cost_insurance(treatment_costs_during_year=2000, premium_per_month=10.0, deductible_amount=500, percentage_covered=50, max_amount_insurance_pays=749) == pytest.approx(12 * 10.0 + 500 + 751), (
            "Treatment costs (with deductible) that are way too high will only be reduced by max_amount_insurance_pays"
            )