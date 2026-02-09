from __future__ import annotations

import asyncio

from telethon import TelegramClient


async def send_messages(
    api_id: int,
    api_hash: str,
    session_file: str,
    contacts: list[str],
    message: str,
) -> None:
    async with TelegramClient(session_file, api_id, api_hash) as client:
        for contact in contacts:
            await client.send_message(contact, message)


def send_notifications(
    api_id: int,
    api_hash: str,
    session_file: str,
    contacts: list[str],
    message: str,
) -> None:
    asyncio.run(send_messages(api_id, api_hash, session_file, contacts, message))
