#!/usr/bin/env python3
"""
Johnny Forsyth Daily Audit — Telegram Feed Scraper
Pulls all messages from Johnny's Telegram channels for a given date,
merges chronologically, and outputs a structured report for analysis.

Usage:
    python3 johnny-audit.py                  # today
    python3 johnny-audit.py 2026-04-07       # specific date
    python3 johnny-audit.py --auth           # first-time auth only
"""

import sys
import os
import json
import asyncio
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

# --- Config ---
API_ID = 34436027
API_HASH = "6b951a5c409fac6bfbbd859f889bc2b7"
SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "johnny-audit-session")

# Channel chat IDs (from system-context.md)
CHANNELS = {
    "Email Feed":     -5033788441,
    "Calendar Feed":  -5181102673,
    "Teams Feed":     -5244367510,
    "Transcripts":    -5141490093,
    "Johnny Alerts":  -1003883592748,
    "Ops Log":        -5205161230,
}

# Johnny DM is discovered at runtime (DM with @johnny_forsyth_bot)
JOHNNY_BOT_USERNAME = "johnny_forsyth_bot"

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audits")


async def discover_johnny_dm(client):
    """Find the DM chat with Johnny's bot."""
    try:
        entity = await client.get_entity(JOHNNY_BOT_USERNAME)
        return entity.id, entity
    except Exception as e:
        print(f"  [!] Could not find DM with @{JOHNNY_BOT_USERNAME}: {e}")
        return None, None


async def pull_messages(client, chat_id, chat_name, start_dt, end_dt):
    """Pull all messages from a chat within the date range."""
    messages = []
    try:
        async for msg in client.iter_messages(
            chat_id,
            offset_date=end_dt,
            reverse=False,
        ):
            if msg.date < start_dt:
                break
            if msg.date >= end_dt:
                continue

            sender_name = "Unknown"
            if msg.sender:
                if hasattr(msg.sender, 'first_name'):
                    sender_name = msg.sender.first_name or ""
                    if msg.sender.last_name:
                        sender_name += f" {msg.sender.last_name}"
                elif hasattr(msg.sender, 'title'):
                    sender_name = msg.sender.title
                if hasattr(msg.sender, 'username') and msg.sender.username:
                    sender_name += f" (@{msg.sender.username})"
            elif msg.sender_id:
                sender_name = f"User {msg.sender_id}"

            media_info = None
            if msg.media:
                if isinstance(msg.media, MessageMediaPhoto):
                    media_info = "[Photo]"
                elif isinstance(msg.media, MessageMediaDocument):
                    doc = msg.media.document
                    filename = None
                    if doc and doc.attributes:
                        for attr in doc.attributes:
                            if hasattr(attr, 'file_name'):
                                filename = attr.file_name
                                break
                    media_info = f"[File: {filename}]" if filename else "[Document]"
                else:
                    media_info = "[Media]"

            messages.append({
                "timestamp": msg.date.isoformat(),
                "timestamp_ct": msg.date.astimezone(timezone(timedelta(hours=-5))).strftime("%I:%M:%S %p CT"),
                "channel": chat_name,
                "sender": sender_name.strip(),
                "message_id": msg.id,
                "text": msg.text or "",
                "media": media_info,
                "reply_to": msg.reply_to.reply_to_msg_id if msg.reply_to else None,
                "edit_date": msg.edit_date.isoformat() if msg.edit_date else None,
            })

        print(f"  {chat_name}: {len(messages)} messages")
    except Exception as e:
        print(f"  {chat_name}: ERROR — {e}")

    return messages


async def main():
    # Parse args
    auth_only = "--auth" in sys.argv
    date_str = None
    for arg in sys.argv[1:]:
        if arg != "--auth" and not arg.startswith("-"):
            date_str = arg

    if date_str:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        target_date = datetime.now()

    date_label = target_date.strftime("%Y-%m-%d")

    # CT timezone (UTC-5 for CDT, but using -5 as approximation)
    ct = timezone(timedelta(hours=-5))
    start_dt = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=ct)
    end_dt = start_dt + timedelta(days=1)

    # Connect
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    await client.start()

    if auth_only:
        print("Auth successful. Session saved.")
        await client.disconnect()
        return

    print(f"\n{'='*60}")
    print(f"  JOHNNY FORSYTH DAILY AUDIT — {date_label}")
    print(f"{'='*60}\n")
    print("Pulling messages...\n")

    all_messages = []

    # Pull from known channels
    for name, chat_id in CHANNELS.items():
        msgs = await pull_messages(client, chat_id, name, start_dt, end_dt)
        all_messages.extend(msgs)

    # Discover and pull Johnny DM
    dm_id, dm_entity = await discover_johnny_dm(client)
    if dm_id:
        msgs = await pull_messages(client, dm_entity, "Johnny DM", start_dt, end_dt)
        all_messages.extend(msgs)
    else:
        print("  Johnny DM: SKIPPED (not found)")

    # Sort chronologically
    all_messages.sort(key=lambda m: m["timestamp"])

    print(f"\n  TOTAL: {len(all_messages)} messages across all channels\n")

    # Write JSON output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    json_path = os.path.join(OUTPUT_DIR, f"audit-{date_label}.json")
    with open(json_path, "w") as f:
        json.dump({
            "date": date_label,
            "generated_at": datetime.now().isoformat(),
            "total_messages": len(all_messages),
            "channels": {name: sum(1 for m in all_messages if m["channel"] == name) for name in list(CHANNELS.keys()) + ["Johnny DM"]},
            "messages": all_messages,
        }, f, indent=2)
    print(f"  JSON saved: {json_path}")

    # Write human-readable timeline
    txt_path = os.path.join(OUTPUT_DIR, f"audit-{date_label}.txt")
    with open(txt_path, "w") as f:
        f.write(f"JOHNNY FORSYTH DAILY AUDIT — {date_label}\n")
        f.write(f"{'='*60}\n")
        f.write(f"Total messages: {len(all_messages)}\n")
        for name in list(CHANNELS.keys()) + ["Johnny DM"]:
            count = sum(1 for m in all_messages if m["channel"] == name)
            if count > 0:
                f.write(f"  {name}: {count}\n")
        f.write(f"{'='*60}\n\n")

        current_channel = None
        for msg in all_messages:
            # Channel header when it changes
            if msg["channel"] != current_channel:
                current_channel = msg["channel"]

            line = f"[{msg['timestamp_ct']}] [{msg['channel']}] {msg['sender']}"
            if msg["reply_to"]:
                line += f" (reply to #{msg['reply_to']})"
            if msg["edit_date"]:
                edit_ct = datetime.fromisoformat(msg["edit_date"]).astimezone(ct).strftime("%I:%M %p")
                line += f" (edited {edit_ct})"
            f.write(f"{line}\n")

            if msg["text"]:
                # Indent message text
                for text_line in msg["text"].split("\n"):
                    f.write(f"    {text_line}\n")
            if msg["media"]:
                f.write(f"    {msg['media']}\n")
            f.write("\n")

    print(f"  Timeline saved: {txt_path}")

    await client.disconnect()

    print(f"\n{'='*60}")
    print(f"  Audit complete. Files in {OUTPUT_DIR}/")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
