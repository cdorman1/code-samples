"""An idempotent sync loop.

Condensed from a scheduled job that pulls vendor activity into local storage.
The property that matters: running it twice does not duplicate anything, and it
returns a count of what it actually did, so a silent no-op and a silent failure
cannot look the same in the logs.
"""

import sqlite3
from typing import Any, Dict

from db import (
    existing_ids,
    get_last_sync,
    save_conversation,
    save_message,
    save_summary,
    save_voicemail,
    set_last_sync,
    utc_now,
)
from vendor_client import (
    fetch_calls_for_participant,
    fetch_latest_conversations,
    fetch_messages_for_phone,
)


def sync_latest_activity(conn: sqlite3.Connection) -> Dict[str, Any]:
    conversations = fetch_latest_conversations(max_results=10)

    counts = {
        "conversations_seen": 0,
        "messages_saved": 0,
        "summaries_saved": 0,
        "voicemails_saved": 0,
        "skipped_existing_messages": 0,
        "skipped_existing_summaries": 0,
    }

    for conversation in conversations:
        counts["conversations_seen"] += 1

        participant_number = extract_participant_number(conversation)
        last_activity_id = conversation.get("lastActivityId")
        last_activity_at = conversation.get("lastActivityAt")

        if not participant_number or participant_number == "Unknown":
            continue

        save_conversation(conn, last_activity_id, last_activity_at, conversation)

        calls = fetch_calls_for_participant(participant_number, max_results=10)
        call_ids = [call["id"] for call in calls if call.get("id")]

        # Look up what is already stored once, then decide per item, instead of
        # querying inside the loop.
        existing_summary_ids = existing_ids(conn, "summaries", "call_id", call_ids)
        existing_voicemail_ids = existing_ids(conn, "voicemails", "call_id", call_ids)

        messages = fetch_messages_for_phone(participant_number, max_results=10)
        message_ids = [message["id"] for message in messages if message.get("id")]
        existing_message_ids = existing_ids(conn, "messages", "message_id", message_ids)

        for message in messages:
            message_id = message.get("id")
            if message_id in existing_message_ids:
                counts["skipped_existing_messages"] += 1
                continue

            if save_message(conn, participant_number, message):
                counts["messages_saved"] += 1
                existing_message_ids.add(message_id)

        for call in calls:
            call_id = call.get("id")
            if not call_id:
                continue

            if call_id not in existing_summary_ids:
                summary_data = fetch_call_summary(call_id)
                if summary_data and save_summary(conn, call, participant_number, summary_data):
                    counts["summaries_saved"] += 1
                    existing_summary_ids.add(call_id)
            else:
                counts["skipped_existing_summaries"] += 1

            if call_id not in existing_voicemail_ids:
                voicemail = fetch_call_voicemail(call_id)
                if voicemail and save_voicemail(conn, call, voicemail):
                    counts["voicemails_saved"] += 1
                    existing_voicemail_ids.add(call_id)

    # Advance the watermark only after the work has been committed.
    conn.commit()
    set_last_sync(conn, utc_now())
    conn.commit()

    return {"status": "ok", **counts}
