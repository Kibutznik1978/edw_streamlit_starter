"""
Database Module - Production-Ready Supabase Integration
========================================================

This module provides all database operations for the Aero Crew Data application.

Key Features:
- Singleton Supabase client with @lru_cache
- Validation for all data types
- Bulk insert with batching (1000-row limit)
- Query operations with pagination
- Streamlit caching for performance
- Comprehensive error handling
- Audit logging support

Usage:
    from database import get_supabase_client, save_bid_period, save_pairings

    # Get client
    supabase = get_supabase_client()

    # Save bid period
    bid_period_id = save_bid_period({
        'period': '2507',
        'domicile': 'ONT',
        'aircraft': '757',
        'seat': 'CA',
        'start_date': '2025-01-01',
        'end_date': '2025-01-31'
    })

    # Save pairings
    count = save_pairings(bid_period_id, pairings_df)

Version: 1.0
Date: 2025-10-28
"""

import os
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
load_dotenv()

# =====================================================================
# SUPABASE CLIENT (SINGLETON)
# =====================================================================


@lru_cache(maxsize=1)
def _get_base_client() -> Client:
    """
    Get base Supabase client (internal use only).

    This is the cached singleton client instance.
    Use get_supabase_client() instead to get a properly authenticated client.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError(
            "Missing Supabase credentials. " "Set SUPABASE_URL and SUPABASE_ANON_KEY in .env file."
        )

    return create_client(url, key)


def get_supabase_client(debug: bool = False) -> Client:
    """
    Get authenticated Supabase client.

    This function returns the singleton client instance and automatically
    sets the user's JWT session if one exists in st.session_state.

    This ensures that all database operations use the authenticated user's
    JWT token, which is required for Row Level Security (RLS) policies.

    Args:
        debug: If True, print debug information about JWT session

    Returns:
        Client: Supabase client instance with JWT session set (if authenticated)

    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_ANON_KEY are not set
    """
    # Get the base client (singleton)
    client = _get_base_client()

    # Set JWT session if user is authenticated
    # This is critical for RLS policies to work correctly
    if hasattr(st, "session_state") and "supabase_session" in st.session_state:
        session = st.session_state["supabase_session"]
        if session and hasattr(session, "access_token"):
            if debug:
                print(f"DEBUG: Setting JWT session for user")
                print(f"DEBUG: Access token exists: {bool(session.access_token)}")
                print(f"DEBUG: Refresh token exists: {bool(session.refresh_token)}")

            client.auth.set_session(session.access_token, session.refresh_token)
        elif debug:
            print("DEBUG: Session exists but missing tokens")
    elif debug:
        print("DEBUG: No session found in st.session_state")

    return client


# =====================================================================
# DEBUG FUNCTIONS
# =====================================================================


def debug_jwt_claims() -> Dict[str, Any]:
    """
    Debug function to check JWT claims.

    This function decodes the JWT token and returns the claims.
    Useful for troubleshooting RLS policy issues.

    Returns:
        Dictionary with JWT claims and debug info
    """
    import jwt

    result: Dict[str, Any] = {
        "has_session": False,
        "has_access_token": False,
        "claims": None,
        "error": None,
    }

    try:
        if hasattr(st, "session_state") and "supabase_session" in st.session_state:
            session = st.session_state["supabase_session"]
            result["has_session"] = True

            if session and hasattr(session, "access_token"):
                result["has_access_token"] = True

                # Decode JWT without verification (just to see claims)
                # Note: We're not verifying because we trust the token from Supabase
                decoded = jwt.decode(session.access_token, options={"verify_signature": False})
                result["claims"] = decoded

                # Check for app_role claim
                if "app_role" in decoded:
                    result["app_role"] = decoded["app_role"]
                else:
                    result["app_role"] = "NOT FOUND - RLS policies will fail!"

    except Exception as e:
        result["error"] = str(e)

    return result


# =====================================================================
# VALIDATION FUNCTIONS
# =====================================================================


def validate_bid_period_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate bid period data before insert.

    Args:
        data: Dictionary with bid period fields

    Returns:
        List of error messages (empty if valid)

    Example:
        errors = validate_bid_period_data({
            'period': '2507',
            'domicile': 'ONT',
            'aircraft': '757',
            'seat': 'CA',
            'start_date': '2025-01-01',
            'end_date': '2025-01-31'
        })
        if errors:
            print(f"Validation failed: {errors}")
    """
    errors = []

    # Required fields
    required_fields = ["period", "domicile", "aircraft", "seat", "start_date", "end_date"]
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")

    # Validate seat
    if "seat" in data and data["seat"] not in ["CA", "FO"]:
        errors.append(f"Invalid seat: {data['seat']} (must be 'CA' or 'FO')")

    # Validate dates
    if "start_date" in data and "end_date" in data:
        try:
            if isinstance(data["start_date"], str):
                start = datetime.fromisoformat(data["start_date"])
            else:
                start = data["start_date"]

            if isinstance(data["end_date"], str):
                end = datetime.fromisoformat(data["end_date"])
            else:
                end = data["end_date"]

            if end <= start:
                errors.append("end_date must be after start_date")
        except (ValueError, AttributeError) as e:
            errors.append(f"Invalid date format: {str(e)}")

    return errors


def validate_pairings_dataframe(df: pd.DataFrame) -> List[str]:
    """
    Validate pairings DataFrame before bulk insert.

    Args:
        df: DataFrame with pairing records

    Returns:
        List of error messages (empty if valid)

    Example:
        errors = validate_pairings_dataframe(pairings_df)
        if errors:
            raise ValueError(f"Validation failed: {'; '.join(errors)}")
    """
    errors = []

    # Required columns
    required_cols = ["trip_id", "is_edw", "tafb_hours", "num_duty_days"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        errors.append(f"Missing columns: {', '.join(missing)}")
        return errors  # Can't proceed without required columns

    # Check for nulls in required columns
    for col in required_cols:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            errors.append(f"Found {null_count} null values in column '{col}'")

    # Validate numeric ranges
    if "tafb_hours" in df.columns:
        invalid = df[(df["tafb_hours"] < 0) | (df["tafb_hours"] > 9999)]
        if not invalid.empty:
            errors.append(
                f"Found {len(invalid)} rows with invalid tafb_hours "
                f"(must be between 0 and 9999)"
            )

    if "total_credit_time" in df.columns:
        invalid = df[(df["total_credit_time"] < 0) | (df["total_credit_time"] > 9999)]
        if not invalid.empty:
            errors.append(
                f"Found {len(invalid)} rows with invalid total_credit_time "
                f"(must be between 0 and 9999)"
            )

    if "num_duty_days" in df.columns:
        invalid = df[(df["num_duty_days"] < 0) | (df["num_duty_days"] > 31)]
        if not invalid.empty:
            errors.append(
                f"Found {len(invalid)} rows with invalid num_duty_days "
                f"(must be between 0 and 31)"
            )

    if "num_legs" in df.columns:
        invalid = df[(df["num_legs"] < 0) | (df["num_legs"] > 20)]
        if not invalid.empty:
            errors.append(
                f"Found {len(invalid)} rows with invalid num_legs " f"(must be between 0 and 20)"
            )

    return errors


def validate_bid_lines_dataframe(df: pd.DataFrame) -> List[str]:
    """
    Validate bid lines DataFrame before bulk insert.

    Args:
        df: DataFrame with bid line records

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Required columns
    required_cols = ["line_number", "total_ct", "total_bt", "total_do", "total_dd"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        errors.append(f"Missing columns: {', '.join(missing)}")
        return errors

    # Check for nulls
    for col in required_cols:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            errors.append(f"Found {null_count} null values in column '{col}'")

    # Validate ranges
    if "total_ct" in df.columns:
        invalid = df[(df["total_ct"] < 0) | (df["total_ct"] > 200)]
        if not invalid.empty:
            errors.append(
                f"Found {len(invalid)} rows with invalid total_ct " f"(must be between 0 and 200)"
            )

    if "total_bt" in df.columns:
        invalid = df[(df["total_bt"] < 0) | (df["total_bt"] > 200)]
        if not invalid.empty:
            errors.append(
                f"Found {len(invalid)} rows with invalid total_bt " f"(must be between 0 and 200)"
            )

    if "total_do" in df.columns:
        invalid = df[(df["total_do"] < 0) | (df["total_do"] > 31)]
        if not invalid.empty:
            errors.append(
                f"Found {len(invalid)} rows with invalid total_do " f"(must be between 0 and 31)"
            )

    if "total_dd" in df.columns:
        invalid = df[(df["total_dd"] < 0) | (df["total_dd"] > 31)]
        if not invalid.empty:
            errors.append(
                f"Found {len(invalid)} rows with invalid total_dd " f"(must be between 0 and 31)"
            )

    # Validate DO + DD <= 31
    if "total_do" in df.columns and "total_dd" in df.columns:
        invalid = df[(df["total_do"] + df["total_dd"]) > 31]
        if not invalid.empty:
            errors.append(
                f"Found {len(invalid)} rows where total_do + total_dd > 31 "
                f"(sum cannot exceed 31 days)"
            )

    # Validate VTO fields if present
    if "vto_type" in df.columns:
        invalid_vto = df[(~df["vto_type"].isin(["VTO", "VTOR", "VOR"])) & (df["vto_type"].notna())]
        if not invalid_vto.empty:
            errors.append(
                f"Found {len(invalid_vto)} rows with invalid vto_type "
                f"(must be 'VTO', 'VTOR', 'VOR', or NULL)"
            )

    if "vto_period" in df.columns:
        invalid_period = df[(~df["vto_period"].isin([1, 2])) & (df["vto_period"].notna())]
        if not invalid_period.empty:
            errors.append(
                f"Found {len(invalid_period)} rows with invalid vto_period "
                f"(must be 1, 2, or NULL)"
            )

    return errors


# =====================================================================
# BID PERIOD OPERATIONS
# =====================================================================


@st.cache_data(ttl=timedelta(minutes=5))
def get_bid_periods(
    domicile: Optional[str] = None,
    aircraft: Optional[str] = None,
    seat: Optional[str] = None,
    include_deleted: bool = False,
) -> pd.DataFrame:
    """
    Get bid periods with optional filters (cached 5 minutes).

    Args:
        domicile: Filter by domicile (e.g., 'ONT', 'LAX')
        aircraft: Filter by aircraft (e.g., '757', 'A320')
        seat: Filter by seat ('CA' or 'FO')
        include_deleted: Include soft-deleted records

    Returns:
        DataFrame with bid period records

    Example:
        # Get all CA bid periods for ONT 757
        df = get_bid_periods(domicile='ONT', aircraft='757', seat='CA')
    """
    supabase = get_supabase_client()

    query = supabase.table("bid_periods").select("*").order("start_date", desc=True)

    if domicile:
        query = query.eq("domicile", domicile)
    if aircraft:
        query = query.eq("aircraft", aircraft)
    if seat:
        query = query.eq("seat", seat)
    if not include_deleted:
        query = query.is_("deleted_at", "null")

    response = query.execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()


def check_duplicate_bid_period(
    period: str, domicile: str, aircraft: str, seat: str
) -> Optional[Dict[str, Any]]:
    """
    Check if bid period already exists.

    Args:
        period: Bid period (e.g., '2507')
        domicile: Domicile code
        aircraft: Aircraft type
        seat: Seat position ('CA' or 'FO')

    Returns:
        Existing bid period record or None

    Example:
        existing = check_duplicate_bid_period('2507', 'ONT', '757', 'CA')
        if existing:
            print(f"Already exists: ID {existing['id']}")
    """
    supabase = get_supabase_client()

    try:
        response = (
            supabase.table("bid_periods")
            .select("*")
            .match({"period": period, "domicile": domicile, "aircraft": aircraft, "seat": seat})
            .is_("deleted_at", "null")
            .execute()
        )

        # Return first record if found, None otherwise
        if response and response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception:
        # If query fails, assume no duplicate exists
        return None


def save_bid_period(data: Dict[str, Any]) -> str:
    """
    Save bid period to database.

    Args:
        data: Dictionary with bid period fields

    Returns:
        Bid period ID (UUID string)

    Raises:
        ValueError: If validation fails or duplicate exists

    Example:
        bid_period_id = save_bid_period({
            'period': '2507',
            'domicile': 'ONT',
            'aircraft': '757',
            'seat': 'CA',
            'start_date': '2025-01-01',
            'end_date': '2025-01-31'
        })
    """
    # Validate data
    errors = validate_bid_period_data(data)
    if errors:
        raise ValueError(f"Validation failed: {'; '.join(errors)}")

    # Check for duplicates
    existing = check_duplicate_bid_period(
        data["period"], data["domicile"], data["aircraft"], data["seat"]
    )

    if existing:
        raise ValueError(
            f"Bid period {data['period']} {data['domicile']} {data['aircraft']} "
            f"{data['seat']} already exists (ID: {existing['id']})"
        )

    # Insert record
    supabase = get_supabase_client()
    response = supabase.table("bid_periods").insert(data).execute()

    # Clear cache
    get_bid_periods.clear()

    return response.data[0]["id"]


# =====================================================================
# PAIRING OPERATIONS
# =====================================================================


def save_pairings(bid_period_id: str, pairings_df: pd.DataFrame) -> int:
    """
    Bulk insert pairings with batching (Supabase limit: 1000 rows).

    Args:
        bid_period_id: Bid period UUID
        pairings_df: DataFrame with pairing records

    Returns:
        Number of records inserted

    Raises:
        ValueError: If validation fails
        Exception: If database insert fails

    Example:
        count = save_pairings(bid_period_id, pairings_df)
        print(f"Inserted {count} pairings")
    """
    # Validate DataFrame
    errors = validate_pairings_dataframe(pairings_df)
    if errors:
        raise ValueError(f"Validation failed: {'; '.join(errors)}")

    # Remove duplicates based on trip_id (keep first occurrence)
    # Parser now stops at "Trips to Flight Report" section
    # so duplicates should not occur
    original_count = len(pairings_df)
    pairings_df = pairings_df.drop_duplicates(subset=["trip_id"], keep="first")
    deduped_count = len(pairings_df)

    if original_count != deduped_count:
        import streamlit as st

        st.warning(
            f"⚠️ Removed {original_count - deduped_count} duplicate trip(s). "
            f"Inserting {deduped_count} unique pairings."
        )

    # Convert to list of dicts
    records = pairings_df.to_dict("records")

    # Get current user ID for audit fields
    user_id = None
    if hasattr(st, "session_state") and "user" in st.session_state:
        user = st.session_state["user"]
        user_id = user.id if hasattr(user, "id") else None

    # Add bid_period_id and audit fields to each record
    for record in records:
        record["bid_period_id"] = bid_period_id
        if user_id:
            record["created_by"] = user_id
            record["updated_by"] = user_id

    # Bulk insert with batching
    BATCH_SIZE = 1000
    inserted_count = 0
    supabase = get_supabase_client()

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]

        try:
            response = supabase.table("pairings").insert(batch).execute()
            inserted_count += len(response.data)
        except Exception as e:
            raise Exception(
                f"Failed to insert batch {i // BATCH_SIZE + 1} "
                f"(rows {i}-{i + len(batch)}): {str(e)}"
            )

    return inserted_count


def check_pairings_exist(bid_period_id: str) -> bool:
    """
    Check if pairings exist for a bid period.

    Args:
        bid_period_id: Bid period UUID

    Returns:
        True if pairings exist, False otherwise

    Example:
        if check_pairings_exist(bid_period_id):
            print("Pairings already exist for this bid period")
    """
    supabase = get_supabase_client()

    try:
        response = (
            supabase.table("pairings")
            .select("id")
            .eq("bid_period_id", bid_period_id)
            .limit(1)
            .execute()
        )

        return len(response.data) > 0 if response.data else False
    except Exception:
        return False


def delete_pairings(bid_period_id: str) -> int:
    """
    Delete all pairings for a bid period.

    Args:
        bid_period_id: Bid period UUID

    Returns:
        Number of records deleted

    Raises:
        Exception: If delete operation fails

    Example:
        count = delete_pairings(bid_period_id)
        print(f"Deleted {count} pairings")
    """
    supabase = get_supabase_client()

    try:
        response = supabase.table("pairings").delete().eq("bid_period_id", bid_period_id).execute()

        return len(response.data) if response.data else 0
    except Exception as e:
        raise Exception(f"Failed to delete pairings: {str(e)}")


# =====================================================================
# BID LINE OPERATIONS
# =====================================================================


def save_bid_lines(bid_period_id: str, bid_lines_df: pd.DataFrame) -> int:
    """
    Bulk insert bid lines with batching (Supabase limit: 1000 rows).

    Args:
        bid_period_id: Bid period UUID
        bid_lines_df: DataFrame with bid line records

    Returns:
        Number of records inserted

    Raises:
        ValueError: If validation fails
        Exception: If database insert fails

    Example:
        count = save_bid_lines(bid_period_id, bid_lines_df)
        print(f"Inserted {count} bid lines")
    """
    # Validate DataFrame
    errors = validate_bid_lines_dataframe(bid_lines_df)
    if errors:
        raise ValueError(f"Validation failed: {'; '.join(errors)}")

    # Remove duplicates based on line_number (keep first occurrence)
    # This prevents unique constraint violations
    original_count = len(bid_lines_df)
    bid_lines_df = bid_lines_df.drop_duplicates(subset=["line_number"], keep="first")
    deduped_count = len(bid_lines_df)

    if original_count != deduped_count:
        import streamlit as st

        st.warning(
            f"⚠️ Removed {original_count - deduped_count} duplicate line(s). "
            f"Inserting {deduped_count} unique bid lines."
        )

    # Convert to list of dicts
    records = bid_lines_df.to_dict("records")

    # Get current user ID for audit fields
    user_id = None
    if hasattr(st, "session_state") and "user" in st.session_state:
        user = st.session_state["user"]
        user_id = user.id if hasattr(user, "id") else None

    # Add bid_period_id and audit fields to each record
    for record in records:
        record["bid_period_id"] = bid_period_id
        if user_id:
            record["created_by"] = user_id
            record["updated_by"] = user_id

    # Bulk insert with batching
    BATCH_SIZE = 1000
    inserted_count = 0
    supabase = get_supabase_client()

    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i : i + BATCH_SIZE]

        try:
            response = supabase.table("bid_lines").insert(batch).execute()
            inserted_count += len(response.data)
        except Exception as e:
            raise Exception(
                f"Failed to insert batch {i // BATCH_SIZE + 1} "
                f"(rows {i}-{i + len(batch)}): {str(e)}"
            )

    return inserted_count


def check_bid_lines_exist(bid_period_id: str) -> bool:
    """
    Check if bid lines exist for a bid period.

    Args:
        bid_period_id: Bid period UUID

    Returns:
        True if bid lines exist, False otherwise

    Example:
        if check_bid_lines_exist(bid_period_id):
            print("Bid lines already exist for this bid period")
    """
    supabase = get_supabase_client()

    try:
        response = (
            supabase.table("bid_lines")
            .select("id")
            .eq("bid_period_id", bid_period_id)
            .limit(1)
            .execute()
        )

        return len(response.data) > 0 if response.data else False
    except Exception:
        return False


def delete_bid_lines(bid_period_id: str) -> int:
    """
    Delete all bid lines for a bid period.

    Args:
        bid_period_id: Bid period UUID

    Returns:
        Number of records deleted

    Raises:
        Exception: If delete operation fails

    Example:
        count = delete_bid_lines(bid_period_id)
        print(f"Deleted {count} bid lines")
    """
    supabase = get_supabase_client()

    try:
        response = supabase.table("bid_lines").delete().eq("bid_period_id", bid_period_id).execute()

        return len(response.data) if response.data else 0
    except Exception as e:
        raise Exception(f"Failed to delete bid lines: {str(e)}")


# =====================================================================
# QUERY OPERATIONS
# =====================================================================


def query_pairings(
    filters: Dict[str, Any], limit: int = 1000, offset: int = 0
) -> Tuple[pd.DataFrame, int]:
    """
    Query pairings with filters and pagination.

    Args:
        filters: Dictionary with filter criteria
            - bid_period_id: UUID string
            - is_edw: boolean
            - min_credit_time: float
            - max_credit_time: float
            - min_tafb: float
            - max_tafb: float
        limit: Maximum records to return (default 1000)
        offset: Number of records to skip (for pagination)

    Returns:
        Tuple of (dataframe, total_count)

    Example:
        df, total = query_pairings({
            'bid_period_id': 'uuid-here',
            'is_edw': True,
            'min_credit_time': 5.0
        }, limit=100)
        print(f"Showing {len(df)} of {total} records")
    """
    supabase = get_supabase_client()

    query = supabase.table("pairings").select("*", count="exact")

    # Apply filters
    if "bid_period_id" in filters:
        query = query.eq("bid_period_id", filters["bid_period_id"])

    if "is_edw" in filters:
        query = query.eq("is_edw", filters["is_edw"])

    if "min_credit_time" in filters:
        query = query.gte("total_credit_time", filters["min_credit_time"])

    if "max_credit_time" in filters:
        query = query.lte("total_credit_time", filters["max_credit_time"])

    if "min_tafb" in filters:
        query = query.gte("tafb_hours", filters["min_tafb"])

    if "max_tafb" in filters:
        query = query.lte("tafb_hours", filters["max_tafb"])

    # Pagination
    query = query.range(offset, offset + limit - 1)

    response = query.execute()

    df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
    total_count = response.count if response.count else 0

    return df, total_count


def query_bid_lines(
    filters: Dict[str, Any], limit: int = 1000, offset: int = 0
) -> Tuple[pd.DataFrame, int]:
    """
    Query bid lines with filters and pagination.

    Args:
        filters: Dictionary with filter criteria
            - bid_period_id: UUID string
            - min_ct: float
            - max_ct: float
            - min_bt: float
            - max_bt: float
            - is_reserve: boolean
        limit: Maximum records to return
        offset: Number of records to skip

    Returns:
        Tuple of (dataframe, total_count)
    """
    supabase = get_supabase_client()

    query = supabase.table("bid_lines").select("*", count="exact")

    # Apply filters
    if "bid_period_id" in filters:
        query = query.eq("bid_period_id", filters["bid_period_id"])

    if "min_ct" in filters:
        query = query.gte("total_ct", filters["min_ct"])

    if "max_ct" in filters:
        query = query.lte("total_ct", filters["max_ct"])

    if "min_bt" in filters:
        query = query.gte("total_bt", filters["min_bt"])

    if "max_bt" in filters:
        query = query.lte("total_bt", filters["max_bt"])

    if "is_reserve" in filters:
        query = query.eq("is_reserve", filters["is_reserve"])

    # Pagination
    query = query.range(offset, offset + limit - 1)

    response = query.execute()

    df = pd.DataFrame(response.data) if response.data else pd.DataFrame()
    total_count = response.count if response.count else 0

    return df, total_count


# =====================================================================
# TREND ANALYSIS
# =====================================================================


@st.cache_data(ttl=timedelta(hours=1))
def get_historical_trends(
    metric: Optional[str] = None,
    domicile: Optional[str] = None,
    aircraft: Optional[str] = None,
    seat: Optional[str] = None,
) -> pd.DataFrame:
    """
    Get historical trend data from materialized view (cached 1 hour).

    Args:
        metric: Not used (kept for compatibility)
        domicile: Filter by domicile
        aircraft: Filter by aircraft
        seat: Filter by seat

    Returns:
        DataFrame with trend data

    Example:
        trends = get_historical_trends(domicile='ONT', aircraft='757')
    """
    supabase = get_supabase_client()

    query = supabase.table("bid_period_trends").select("*").order("start_date")

    if domicile:
        query = query.eq("domicile", domicile)
    if aircraft:
        query = query.eq("aircraft", aircraft)
    if seat:
        query = query.eq("seat", seat)

    response = query.execute()
    return pd.DataFrame(response.data) if response.data else pd.DataFrame()


def refresh_trends() -> None:
    """
    Refresh materialized view after data changes.

    Call this after saving bid periods, pairings, or bid lines
    to update the pre-computed trend aggregations.

    Note: This may fail if the materialized view needs a unique index.
    The failure is non-fatal as the view will be refreshed eventually.

    Example:
        save_pairings(bid_period_id, df)
        refresh_trends()  # Update trend statistics
    """
    supabase = get_supabase_client()

    try:
        supabase.rpc("refresh_trends").execute()
        # Clear cache on success
        get_historical_trends.clear()
    except Exception:
        # Non-fatal: materialized view refresh can fail if unique index is missing
        # Data is still saved successfully, view will be refreshed eventually
        pass


# =====================================================================
# UTILITY FUNCTIONS
# =====================================================================


def test_connection() -> bool:
    """
    Test Supabase connection and verify schema.

    Returns:
        True if connection successful, False otherwise

    Example:
        if test_connection():
            print("✅ Connected to Supabase")
        else:
            print("❌ Connection failed")
    """
    try:
        supabase = get_supabase_client()

        # Test by querying bid_periods table
        response = supabase.table("bid_periods").select("*", count="exact").limit(1).execute()

        print(f"✅ Connection successful!")
        print(f"   Found {response.count} bid periods in database")

        return True

    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False
