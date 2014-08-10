import asyncio

from obrbot import hook
from obrbot.plugin import HookType
from obrbot.util import bucket

TOKENS = 10
RESTORE_RATE = 1
MESSAGE_COST = 4

channel_buckets = {}


@asyncio.coroutine
@hook.sieve
def sieve_suite(event):
    """
    :type event: obrbot.event.Event
    """

    # check permissions
    allowed_permissions = event.hook.permissions
    if allowed_permissions:
        for perm in allowed_permissions:
            if event.has_permission(perm):
                break
        else:  # This executes when 'break' above never does
            event.notice("Sorry, you don't have access to this command.")
            return None

    # check command spam tokens
    if event.hook.type is HookType.command:
        if not event.chan_name in channel_buckets:
            _bucket = bucket.TokenBucket(TOKENS, RESTORE_RATE)
            channel_buckets[event.chan_name] = _bucket
        else:
            _bucket = channel_buckets[event.chan_name]

        if not _bucket.consume(MESSAGE_COST):
            event.notice("Command rate-limited, please try again in a few seconds.")
            return None

    return event
