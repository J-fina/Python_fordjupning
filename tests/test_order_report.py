"""Tester för order_report.py.

Körs från projektets rotmapp med:

    python -m pytest
"""

import pandas as pd
import pytest

from order_report import (
    REQUIRED_COLUMNS,
    OrderDataError,
    ReportConfig,
    add_order_values,
    build_overview,
    build_reports,
    build_returns_report,
    build_sales_report,
    clean_orders,
    load_orders,
    run_report,
    summarize_orders,
    validate_orders,
)


@pytest.fixture
def raw_orders() -> pd.DataFrame:
    """Ett litet dataset med samma typer av "smutsig" data som orders.csv.

    Radernas värden efter tvätt:

    * O1: 2 * 100 * (1 - 0.0) = 200
    * O2: 1 * 200 * (1 - 0.5) = 100
    * O3: 3 * 100 * (1 - 0.1) = 270
    * O4: quantity saknas (blir 1), discount är ogiltig (blir 0) -> 50
    * O5: unit_price saknas och ersätts med medianen 100 -> 200
    """
    return pd.DataFrame(
        {
            "order_id": ["O1", "O2", "O3", "O4", "O5"],
            "order_date": [
                "2026-01-01",
                "2026-01-02",
                "2026-01-03",
                "2026-01-04",
                "2026-01-05",
            ],
            "customer_id": ["C1", "C2", "C3", "C4", "C5"],
            "region": [" north ", "North", "South", None, "South"],
            "product_category": [
                "electronics ",
                "Electronics",
                "Books",
                "Books",
                "Books",
            ],
            "quantity": [2.0, 1.0, 3.0, None, 2.0],
            "unit_price": [100.0, 200.0, 100.0, 50.0, None],
            "discount": [0.0, 0.5, 0.1, "unknown", 0.0],
            "returned": ["false", "true", "Yes", None, "no"],
        }
    )


@pytest.fixture
def orders(raw_orders: pd.DataFrame) -> pd.DataFrame:
    """Samma dataset, tvättat och med ordervärden uträknade."""
    return add_order_values(clean_orders(raw_orders))


# --------------------------------------------------------------------------
# Beräkningar
# --------------------------------------------------------------------------


def test_order_value_is_quantity_times_unit_price():
    data = pd.DataFrame(
        {"quantity": [2, 3], "unit_price": [100.0, 50.0], "discount": [0.0, 0.0]}
    )

    result = add_order_values(data)

    assert result["order_value"].tolist() == [200.0, 150.0]


def test_discounted_value_uses_discount():
    data = pd.DataFrame(
        {"quantity": [2, 1], "unit_price": [100.0, 200.0], "discount": [0.25, 0.5]}
    )

    result = add_order_values(data)

    assert result["discounted_value"].tolist() == [150.0, 100.0]


def test_discounted_value_equals_order_value_without_discount():
    data = pd.DataFrame({"quantity": [4], "unit_price": [25.0], "discount": [0.0]})

    result = add_order_values(data)

    assert result.loc[0, "discounted_value"] == result.loc[0, "order_value"] == 100.0


def test_total_sales_and_counts(orders):
    summary = summarize_orders(orders)

    assert summary.total_sales == 820.0
    assert summary.order_count == 5
    assert summary.return_count == 2


def test_order_count_counts_unique_order_ids():
    data = pd.DataFrame(
        {
            "order_id": ["O1", "O1", "O2"],
            "discounted_value": [100.0, 100.0, 50.0],
            "returned": [False, False, True],
        }
    )

    summary = summarize_orders(data)

    assert summary.order_count == 2
    assert summary.total_sales == 250.0
    assert summary.return_count == 1


def test_total_sales_is_rounded_to_two_decimals():
    data = pd.DataFrame(
        {
            "order_id": ["O1", "O2"],
            "discounted_value": [10.005, 20.001],
            "returned": [False, False],
        }
    )

    assert summarize_orders(data).total_sales == 30.01


# --------------------------------------------------------------------------
# Tvätt av data
# --------------------------------------------------------------------------


def test_text_columns_are_normalized(raw_orders):
    cleaned = clean_orders(raw_orders)

    assert cleaned["region"].tolist() == ["North", "North", "South", "Unknown", "South"]
    assert cleaned["product_category"].tolist() == [
        "Electronics",
        "Electronics",
        "Books",
        "Books",
        "Books",
    ]


def test_missing_quantity_becomes_one(raw_orders):
    assert clean_orders(raw_orders).loc[3, "quantity"] == 1


def test_invalid_discount_becomes_zero(raw_orders):
    # Rad O4 har texten "unknown" i discount.
    assert clean_orders(raw_orders).loc[3, "discount"] == 0


def test_missing_unit_price_is_filled_with_median(raw_orders):
    # Giltiga priser är 100, 200, 100 och 50, vilket ger medianen 100.
    assert clean_orders(raw_orders).loc[4, "unit_price"] == 100.0


def test_unit_price_is_left_empty_when_no_valid_values_exist():
    data = pd.DataFrame(
        {
            "region": ["North"],
            "product_category": ["Books"],
            "quantity": [2],
            "unit_price": ["saknas"],
            "discount": [0.0],
            "returned": ["false"],
        }
    )

    assert pd.isna(clean_orders(data).loc[0, "unit_price"])


@pytest.mark.parametrize(
    "value, expected",
    [
        ("true", True),
        ("TRUE", True),
        ("Yes", True),
        ("ja", True),
        ("1", True),
        ("false", False),
        ("no", False),
        (None, False),
        ("", False),
    ],
)
def test_returned_is_converted_to_boolean(value, expected):
    data = pd.DataFrame(
        {
            "region": ["North"],
            "product_category": ["Books"],
            "quantity": [1],
            "unit_price": [100.0],
            "discount": [0.0],
            "returned": [value],
        }
    )

    assert bool(clean_orders(data).loc[0, "returned"]) is expected


def test_clean_orders_does_not_change_input(raw_orders):
    before = raw_orders.copy()

    clean_orders(raw_orders)

    pd.testing.assert_frame_equal(raw_orders, before)


# --------------------------------------------------------------------------
# Rapporter
# --------------------------------------------------------------------------


def test_sales_by_category(orders):
    report = build_sales_report(orders, "product_category")

    # Books har högst försäljning (270 + 50 + 200) och ska ligga först.
    assert report["product_category"].tolist() == ["Books", "Electronics"]
    assert report["total_sales"].tolist() == [520.0, 300.0]
    assert report["order_count"].tolist() == [3, 2]
    assert report["returns"].tolist() == [1, 1]


def test_sales_by_region(orders):
    report = build_sales_report(orders, "region")

    assert report["region"].tolist() == ["South", "North", "Unknown"]
    assert report["total_sales"].tolist() == [470.0, 300.0, 50.0]
    assert report["order_count"].tolist() == [2, 2, 1]


def test_return_rate_is_returns_divided_by_orders(orders):
    report = build_sales_report(orders, "product_category")

    # Books har 1 retur av 3 orders.
    assert report.set_index("product_category").loc["Books", "return_rate"] == 0.333


def test_returns_by_category_is_sorted_by_return_rate(orders):
    report = build_returns_report(orders, "product_category")

    assert report["product_category"].tolist() == ["Electronics", "Books"]
    assert report["return_rate"].tolist() == [0.5, 0.333]
    assert list(report.columns) == [
        "product_category",
        "order_count",
        "returns",
        "return_rate",
    ]


def test_return_rate_is_zero_when_nothing_is_returned():
    data = pd.DataFrame(
        {
            "order_id": ["O1", "O2"],
            "product_category": ["Books", "Books"],
            "discounted_value": [100.0, 50.0],
            "returned": [False, False],
        }
    )

    report = build_returns_report(data, "product_category")

    assert report.loc[0, "returns"] == 0
    assert report.loc[0, "return_rate"] == 0.0


def test_overview_report(orders):
    report = build_overview(summarize_orders(orders))

    assert report["metric"].tolist() == ["total_sales", "order_count", "return_count"]
    assert report["value"].tolist() == [820.0, 5, 2]


def test_build_reports_creates_all_four_reports(orders):
    reports = build_reports(orders, summarize_orders(orders))

    assert sorted(reports) == [
        "overview.csv",
        "returns_by_category.csv",
        "sales_by_category.csv",
        "sales_by_region.csv",
    ]


# --------------------------------------------------------------------------
# Validering och felfall
# --------------------------------------------------------------------------


def test_valid_data_passes_validation(raw_orders):
    # Ska inte höja något fel.
    validate_orders(raw_orders)


def test_missing_required_column_raises_error(raw_orders):
    with pytest.raises(OrderDataError) as error:
        validate_orders(raw_orders.drop(columns=["discount"]))

    assert "discount" in str(error.value)


def test_empty_dataframe_raises_error():
    empty = pd.DataFrame(columns=list(REQUIRED_COLUMNS))

    with pytest.raises(OrderDataError) as error:
        validate_orders(empty)

    assert "inga rader" in str(error.value)


def test_missing_file_raises_error(tmp_path):
    with pytest.raises(OrderDataError) as error:
        load_orders(ReportConfig(input_file=tmp_path / "finns_inte.csv"))

    assert "finns_inte.csv" in str(error.value)


def test_load_orders_reads_csv_file(tmp_path, raw_orders):
    csv_path = tmp_path / "orders.csv"
    raw_orders.to_csv(csv_path, index=False)

    data = load_orders(ReportConfig(input_file=csv_path))

    assert len(data) == len(raw_orders)


def test_load_orders_rejects_file_without_required_columns(tmp_path):
    csv_path = tmp_path / "orders.csv"
    csv_path.write_text("order_id,quantity\nO1,2\n", encoding="utf-8")

    with pytest.raises(OrderDataError) as error:
        load_orders(ReportConfig(input_file=csv_path))

    assert "unit_price" in str(error.value)


# --------------------------------------------------------------------------
# Hela flödet
# --------------------------------------------------------------------------


def test_run_report_writes_all_files(tmp_path, raw_orders):
    csv_path = tmp_path / "orders.csv"
    raw_orders.to_csv(csv_path, index=False)
    config = ReportConfig(input_file=csv_path, output_folder=tmp_path / "output")

    summary = run_report(config)

    assert summary.total_sales == 820.0
    for filename in (
        "overview.csv",
        "sales_by_category.csv",
        "sales_by_region.csv",
        "returns_by_category.csv",
    ):
        assert config.output_path(filename).is_file()

    by_region = pd.read_csv(config.output_path("sales_by_region.csv"))
    assert by_region.loc[0, "region"] == "South"
