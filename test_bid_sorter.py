import pandas as pd

from bid_sorter import (
    build_line_trip_links,
    summarize_line_trip_metrics,
    unmatched_trip_tokens,
)
from line_schedule import line_day_records_to_df, map_line_to_trip_tokens
from bid_parser import _parse_comment_schedule


def _sample_day_records():
    return [
        {
            "Line": 101,
            "PayPeriod": 1,
            "PayPeriodCode": "2510",
            "DayIndex": 1,
            "Value": "209",
            "ValueType": "trip",
        },
        {
            "Line": 101,
            "PayPeriod": 1,
            "PayPeriodCode": "2510",
            "DayIndex": 2,
            "Value": "OFF",
            "ValueType": "off",
        },
        {
            "Line": 101,
            "PayPeriod": 1,
            "PayPeriodCode": "2510",
            "DayIndex": 3,
            "Value": "211",
            "ValueType": "trip",
        },
        {
            "Line": 102,
            "PayPeriod": 1,
            "PayPeriodCode": "2510",
            "DayIndex": 1,
            "Value": "VAC",
            "ValueType": "off",
        },
    ]


def test_line_day_records_to_df_orders_and_types():
    df = line_day_records_to_df(_sample_day_records())
    assert list(df.columns) == [
        "Line",
        "PayPeriod",
        "PayPeriodCode",
        "DayIndex",
        "Value",
        "ValueType",
    ]
    assert df.loc[0, "Line"] == 101
    assert df.loc[0, "ValueType"] == "trip"
    assert df.loc[1, "ValueType"] == "off"


def test_map_line_to_trip_tokens():
    df = line_day_records_to_df(_sample_day_records())
    mapping = map_line_to_trip_tokens(df)
    assert mapping[101] == ["209", "211"]
    assert 102 not in mapping  # No trip entries


def test_build_line_trip_links_matches_catalog():
    records = _sample_day_records()
    trip_catalog = pd.DataFrame({"Trip ID": [209, 211]})
    links, summary = build_line_trip_links(records, trip_catalog)

    assert len(links) == 2
    assert links["Match"].all()
    assert summary.iloc[0]["UnmatchedTokens"] == 0


def test_build_line_trip_links_with_missing_trip():
    records = _sample_day_records()
    trip_catalog = pd.DataFrame({"Trip ID": [209]})  # 211 missing
    links, summary = build_line_trip_links(records, trip_catalog)

    missing = unmatched_trip_tokens(links)
    assert missing == {101: ["211"]}
    assert summary.iloc[0]["UnmatchedTokens"] == 1


def test_parse_comment_schedule_from_block_text():
    block_text = """
ONT 3 Sun Mon Tue Wed Thu Fri Sat Sun Mon Tue Wed Thu Fri Sat Sun Mon Tue Wed Thu Fri Sat Sun Mon Tue Wed Thu Fri Sat - Mon
1/1/0/ 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 1 2 3 4 - 6
BL PP1 (2510) 188 188 188 198 186 186 186 199 187 187 187 188 188 188 198 186 186 186 199 187 187 187
CT: 66:00
Sun Mon Tue Wed Thu Fri Sat Sun Mon Tue Wed Thu Fri Sat Sun Mon Tue Wed Thu Fri Sat Sun Mon Tue Wed Thu Fri Sat - Mon
5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 1 - 3
BL 188 188 188 198 186 186 186 199 187 187 187 PP2 (2511) 188 188 188 198 186 186 186 199 187 187 187
CT: 66:00
"""

    day_records = _parse_comment_schedule(3, block_text)
    assert len(day_records) == 44
    pp1 = [rec for rec in day_records if rec["PayPeriod"] == 1]
    pp2 = [rec for rec in day_records if rec["PayPeriod"] == 2]
    assert len(pp1) == 22
    assert len(pp2) == 22
    assert pp1[0]["Value"] == "188"
    assert pp2[-1]["ValueType"] == "trip"


def test_summarize_line_trip_metrics():
    records = _sample_day_records()
    trip_catalog = pd.DataFrame(
        {
            "Trip ID": [209, 211],
            "EDW": [True, False],
            "Hot Standby": [False, True],
            "TAFB Hours": [10.0, 20.5],
            "Duty Days": [2, 3],
            "Trip Parsed": [
                {
                    "duty_days": [
                        {
                            "flights": [
                                {"depart": "(08)08:00", "block": "2h00"},
                                {"depart": "(09)10:00", "block": "1h30"},
                            ]
                        }
                    ]
                },
                {
                    "duty_days": [
                        {
                            "flights": [
                                {"depart": "(23)23:30", "block": "3h00"},
                                {"depart": "(01)01:00", "block": "2h00"},
                            ]
                        }
                    ]
                },
            ],
        }
    )
    links, _ = build_line_trip_links(records, trip_catalog)
    metrics = summarize_line_trip_metrics(links, trip_catalog, day_start=6, day_end=23)

    assert len(metrics) == 1
    row = metrics.iloc[0]
    assert row["Line"] == 101
    assert row["MatchedUniqueTrips"] == 2
    assert row["EDWTrips"] == 1
    assert row["HotStandbyTrips"] == 1
    assert abs(row["TotalTAFBHours"] - 30.5) < 1e-6
    assert abs(row["DayBlockHours"] - 3.5) < 1e-6
    assert abs(row["NightBlockHours"] - 5.0) < 1e-6
    assert row["TripIDs"] == [209, 211]
