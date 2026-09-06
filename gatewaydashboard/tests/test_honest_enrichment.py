"""Tests for honest scanner enrichment.

Enforces:
1. When there is no VCP structure (no valid pivot or stop), no fake trade plan is
   invented. tp1, tp2, rr_ratio, pot_risk, pot_gain must be None, rr_ratio_fmt must be 'N/A'.
2. When a valid pivot and stop exist, rr_ratio is computed dynamically from the
   levels (tp1 - pivot) / (pivot - stop), not hardcoded to 2.4.
3. No fabricated numbers: win_probability (73) and confidence_score must not be
   invented constants.
"""

from __future__ import annotations

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scanner


def test_no_vcp_structure_produces_no_trade_plan():
    raw_record = {
        "symbol": "TCS",
        "exchange": "NSE",
        "country": "India",
        "verdict": "no_setup",
        "status": "no_vcp",
        "close": {"value": 3500.0},
        "plan": {
            "available": False,
            "reason": "CALCULATION_UNAVAILABLE: no contraction wave to price",
        },
    }

    enriched = scanner._enrich_record(raw_record)

    assert enriched["tp1"] is None, "tp1 must not be invented when no VCP structure"
    assert enriched["tp2"] is None, "tp2 must not be invented when no VCP structure"
    assert enriched["rr_ratio"] is None
    assert enriched["rr_ratio_fmt"] == "N/A"
    assert enriched["potential_risk_val"] is None
    assert enriched["potential_gain_val"] is None
    assert enriched["trade_plan_available"] is False
    assert enriched["confidence_score"] is None, "confidence_score must not be an invented constant"
    assert enriched["win_probability"] is None, "win_probability must not be an invented constant"
    assert "No trade plan available" in enriched["ai_take"]


def test_valid_vcp_structure_computes_levels_and_honest_rr_ratio():
    pivot = 1000.0
    stop = 950.0
    risk = pivot - stop  # 50.0
    expected_tp1 = 1000.0 + 2.0 * 50.0  # 1100.0
    expected_tp2 = 1000.0 + 3.0 * 50.0  # 1150.0
    expected_rr = round((expected_tp1 - pivot) / risk, 2)  # 2.0

    raw_record = {
        "symbol": "RELIANCE",
        "exchange": "NSE",
        "country": "India",
        "verdict": "valid_setup",
        "status": "ready",
        "close": {"value": 995.0},
        "plan": {
            "available": True,
            "pivot": {"value": pivot},
            "stop": {"value": stop},
        },
    }

    enriched = scanner._enrich_record(raw_record)

    assert enriched["tp1"] == expected_tp1
    assert enriched["tp2"] == expected_tp2
    assert enriched["rr_ratio"] == expected_rr
    assert enriched["rr_ratio_fmt"] == "2 : 1" or enriched["rr_ratio_fmt"] == "2.0 : 1"
    assert enriched["potential_risk_val"] == 5000.0  # 100 * 50.0
    assert enriched["potential_gain_val"] == 15000.0  # 100 * (1150 - 1000)
    assert enriched["trade_plan_available"] is True
    assert enriched["confidence_score"] is None
    assert enriched["win_probability"] is None
    assert "trade offers a" in enriched["ai_take"]
    assert "2:1" in enriched["ai_take"] or "2 : 1" in enriched["ai_take"]


def test_invalid_stop_greater_than_pivot_does_not_invent_plan():
    raw_record = {
        "symbol": "INFY",
        "exchange": "NSE",
        "country": "India",
        "verdict": "no_setup",
        "close": {"value": 1500.0},
        "plan": {
            "available": False,
            "pivot": {"value": 1400.0},
            "stop": {"value": 1450.0},  # inverted
            "reason": "stop is above pivot",
        },
    }

    enriched = scanner._enrich_record(raw_record)

    assert enriched["tp1"] is None
    assert enriched["tp2"] is None
    assert enriched["rr_ratio"] is None
    assert enriched["trade_plan_available"] is False
