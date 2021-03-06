import asyncio
import logging

from obrbot import hook

plugin_info = {
    "plugin_category": "core"
}

logger = logging.getLogger('obrbot')

# Identify to NickServ (or other service)
@asyncio.coroutine
@hook.irc_raw('004')
def onjoin(conn):
    """
    :type conn: obrbot.clients.irc.IrcConnection
    """
    nickserv = conn.config.get('nickserv')
    if nickserv and nickserv.get('enabled', True):
        nickserv_password = nickserv.get('nickserv_password', '')
        nickserv_name = nickserv.get('nickserv_name', 'nickserv')
        nickserv_account_name = nickserv.get('nickserv_user', '')
        nickserv_command = nickserv.get('nickserv_command', 'IDENTIFY')
        if nickserv_password:
            if nickserv_account_name:
                conn.message(nickserv_name,
                             "{} {} {}".format(nickserv_command, nickserv_account_name, nickserv_password),
                             log_hide=nickserv_password)
            else:
                conn.message(nickserv_name, "{} {}".format(nickserv_command, nickserv_password),
                             log_hide=nickserv_password)
            yield from asyncio.sleep(1)

    # Set bot modes
    mode = conn.config.get('mode')
    if mode:
        logger.info("Setting bot mode: '{}'".format(mode))
        conn.cmd('MODE', conn.bot_nick, mode)

    # Join config-defined channels
    logger.info("Joining channels.")
    for channel in conn.config.get('channels', []):
        conn.join(channel)
        yield from asyncio.sleep(0.5)

    logger.info("Startup complete.")


@asyncio.coroutine
@hook.irc_raw('004')
def keep_alive(conn):
    """
    :type conn: obrbot.clients.irc.IrcConnection
    """

    if not conn.config.get('keep_alive', False):
        return

    while True:
        conn.cmd('PING', conn.bot_nick)
        yield from asyncio.sleep(60)
