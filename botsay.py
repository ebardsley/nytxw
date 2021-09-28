#!/usr/bin/env pipenv-shebang

import os
import sys

import env
import discord


BOT_TOKEN = env.require_env('NYTXW_BOT')


def say(token, channels, message):
  client = discord.Client()

  @client.event
  async def on_ready():
    print('Logged into Discord as {0.user}'.format(client))
    for channel_id in channels:
      channel = client.get_channel(channel_id)
      print('Channel', channel.id if channel else None, channel)
      if channel:
        await channel.send(message)
    await client.close()

  @client.event
  async def on_error(event):
    await client.close()
    raise

  client.run(BOT_TOKEN)

  return


def main(argv):
  if len(argv) < 3:
    print(f'usage: {argv[0]} <channel id> <message>', file=sys.stderr)
    sys.exit(1)

  channels = [int(argv[1])]
  message = ' '.join(argv[2:])

  print('Message:', message)
  say(BOT_TOKEN, channels, message)


if __name__ == '__main__':
  main(sys.argv)
