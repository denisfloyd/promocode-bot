"""
One-time Telegram authentication setup.

Run this script once to authenticate with Telegram.
It will ask for your phone number and a verification code.
After that, the session is saved and the app can use it automatically.

Usage:
    python scripts/telegram_setup.py
"""

import asyncio

from app.config import settings


async def main():
    if not settings.telegram_api_id or not settings.telegram_api_hash:
        print("ERROR: Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env first")
        return

    from telethon import TelegramClient

    client = TelegramClient("promocode_bot", settings.telegram_api_id, settings.telegram_api_hash)
    await client.start()

    me = await client.get_me()
    print(f"\nAuthenticated as: {me.first_name} ({me.phone})")

    # Test configured channels
    channels = [c.strip() for c in settings.telegram_channels.split(",") if c.strip()]
    print(f"\nTesting {len(channels)} configured channels:")

    for channel_name in channels:
        try:
            channel = await client.get_entity(channel_name)
            # Get last 3 messages as preview
            messages = []
            async for msg in client.iter_messages(channel, limit=3):
                if msg.text:
                    messages.append(msg.text[:80])
            print(f"  @{channel_name} - OK ({len(messages)} recent messages)")
            for m in messages:
                print(f"    -> {m}")
        except Exception as e:
            print(f"  @{channel_name} - FAILED: {e}")

    await client.disconnect()
    print("\nSession saved to 'promocode_bot.session'. The app can now use Telegram.")


if __name__ == "__main__":
    asyncio.run(main())
