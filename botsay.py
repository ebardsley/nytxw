#!/usr/bin/env pipenv-shebang
import asyncio
import os
import sys
import urllib.parse

import aiohttp
import discord


async def rpc(endpoint, json):
    async with aiohttp.ClientSession() as session:
        try:
            response = await session.post(endpoint, json=json)
        except aiohttp.ClientError as e:
            raise

        if not response.ok:
            print("failed:", await response.text())


def discord_message(token, channels, message):
    client = discord.Client()

    @client.event
    async def on_ready():
        print(f"Logged into Discord as {client.user}")
        for channel_id in channels:
            channel = client.get_channel(channel_id)
            print("Channel", channel.id if channel else None, channel)
            if channel:
                await channel.send(message)
        await client.close()

    @client.event
    async def on_error(event):
        await client.close()
        raise

    client.run(token)


def webhook(url, message):
    hook = discord.SyncWebhook.from_url(url)
    hook.send(
        content=message,
        # suppress_embeds=True,
    )


def main(argv):
    if len(argv) < 3:
        print(f"usage: {argv[0]} <channel id|webhook> <message>", file=sys.stderr)
        sys.exit(1)

    message = " ".join(argv[2:])
    return say(argv[1], message)


def say(target, message):
    if target.startswith("https:"):
        print("Webhook:", message)
        webhook(target, message)

    elif target.startswith("http:"):  # TODO: https-ify?
        parsed = urllib.parse.urlparse(target)
        json = dict(urllib.parse.parse_qsl(parsed.query), msg=message)
        parsed = parsed._replace(query=None)
        endpoint = urllib.parse.urlunparse(parsed)
        print("RPC", endpoint, json)
        asyncio.run(rpc(endpoint, json))

    else:
        import env

        token = env.require_env("NYTXW_BOT")
        channels = [int(c) for c in target.split(",") if c]
        print("Message:", message)
        discord_message(token, channels, message)


if __name__ == "__main__":
    main(sys.argv)
