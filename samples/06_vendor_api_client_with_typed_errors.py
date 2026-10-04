"""Fronting a third party HTTP API so failures are typed, not silent.

From a service that fronts a telephony vendor's API and republishes
conversations, messages, call summaries and voicemails as one structured
endpoint, so internal tooling and GPT based workflows never talk to the vendor
directly.
"""

from typing import Any, Dict, Optional

import requests
from fastapi import HTTPException

from config import (
    HTTP_TIMEOUT_SECONDS,
    MAX_CONVERSATIONS,
    PHONE_NUMBER_ID,
    VENDOR_API_KEY,
    VENDOR_BASE_URL,
)

HTTP_SESSION = requests.Session()


def vendor_get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The single place the vendor is called, so auth, timeouts and error shape are consistent."""
    response = HTTP_SESSION.get(
        f"{VENDOR_BASE_URL}{path}",
        headers={"Authorization": VENDOR_API_KEY},
        params=params,
        timeout=HTTP_TIMEOUT_SECONDS,
    )

    if response.status_code >= 400:
        # The vendor's own error body is the useful part of the failure, so it is
        # carried through to the caller instead of being flattened into a generic 502.
        raise HTTPException(
            status_code=response.status_code,
            detail={
                "url": response.url,
                "vendor_error": response.text,
            },
        )

    return response.json()


def fetch_latest_conversations(max_results: int = MAX_CONVERSATIONS) -> list[Dict[str, Any]]:
    return vendor_get(
        "/v1/conversations",
        params={
            "phoneNumberId": PHONE_NUMBER_ID,
            "maxResults": max_results,
        },
    ).get("data", [])


def fetch_calls_for_participant(participant_number: str, max_results: int = 10) -> list[Dict[str, Any]]:
    return vendor_get(
        "/v1/calls",
        params={
            "phoneNumberId": PHONE_NUMBER_ID,
            "participants": participant_number,
            "maxResults": max_results,
        },
    ).get("data", [])


def fetch_call_summary(activity_id: str) -> Optional[Dict[str, Any]]:
    """Some calls legitimately have no summary. That is a None, not an error."""
    try:
        return vendor_get(f"/v1/call-summaries/{activity_id}").get("data", {})
    except HTTPException as exc:
        error_text = str(exc.detail)
        if "not found" in error_text.lower():
            return None
        print(f"summary error for {activity_id}: {exc.detail}")
        return None
