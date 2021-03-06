import asyncio
import re

from obrbot import hook

plugin_info = {
    "plugin_category": "core",
    "command_category_name": "Administration"
}


@asyncio.coroutine
@hook.command("groups", permissions=["permissions.view"], autohelp=False)
def get_permission_groups(conn):
    """- lists all valid groups
    :type conn: obrbot.connection.Connection
    """
    return "Valid groups: {}".format(conn.permissions.get_groups())


@asyncio.coroutine
@hook.command("gperms", permissions=["permissions.view"])
def get_group_permissions(text, conn, notice):
    """<group> - lists permissions given to <group>
    :type text: str
    :type conn: obrbot.connection.Connection
    """
    group = text.strip().lower()
    permission_manager = conn.permissions
    group_users = permission_manager.get_group_users(group)
    group_permissions = permission_manager.get_group_permissions(group)
    if group_permissions:
        return "Group {} has permissions {}".format(group, group_permissions)
    elif group_users:
        return "Group {} exists, but has no permissions".format(group)
    else:
        notice("Unknown group '{}'".format(group))


@asyncio.coroutine
@hook.command("gusers", permissions=["permissions.view"])
def get_group_users(text, conn, notice):
    """<group> - lists users in <group>
    :type text: str
    :type conn: obrbot.connection.Connection
    """
    group = text.strip().lower()
    permission_manager = conn.permissions
    group_users = permission_manager.get_group_users(group)
    group_permissions = permission_manager.get_group_permissions(group)
    if group_users:
        return "Group {} has members: {}".format(group, group_users)
    elif group_permissions:
        return "Group {} exists, but has no members".format(group, group_permissions)
    else:
        notice("Unknown group '{}'".format(group))


@asyncio.coroutine
@hook.command("uperms", autohelp=False, permissions=["permissions.view", "permissions.view.self"])
def get_user_permissions(text, conn, mask, has_permission, notice):
    """[user] - lists all permissions given to [user], or the caller if no user is specified
    :type text: str
    :type conn: obrbot.connection.Connection
    :type mask: str
    """
    if text:
        if not has_permission("permissions.view"):
            notice("Sorry, you are not allowed to use this command on another user.")
            return
        user = text.strip().lower()
    else:
        user = mask.lower()

    permission_manager = conn.permissions

    user_permissions = permission_manager.get_user_permissions(user)
    if user_permissions:
        return "User {} has permissions: {}".format(user, user_permissions)
    else:
        return "User {} has no elevated permissions".format(user)


@asyncio.coroutine
@hook.command("ugroups", autohelp=False, permissions=["permissions.view", "permissions.view.self"])
def get_user_groups(text, conn, mask, has_permission, notice):
    """[user] - lists all permissions given to [user], or the caller if no user is specified
    :type text: str
    :type conn: obrbot.connection.Connection
    :type mask: str
    """
    if text:
        if not has_permission("permissions.view"):
            notice("Sorry, you are not allowed to use this command on another user")
            return
        user = text.strip().lower()
    else:
        user = mask.lower()

    permission_manager = conn.permissions

    user_groups = permission_manager.get_user_groups(user)
    if user_groups:
        return "User {} is in groups: {}".format(user, user_groups)
    else:
        return "User {} is in no permission groups".format(user)


@asyncio.coroutine
@hook.command("deluser", permissions=["permissions.manage"])
def remove_permission_user(text, bot, conn, notice, reply):
    """<user> [group] - removes <user> from [group], or from all groups if no group is specified
    :type text: str
    :type bot: obrbot.bot.ObrBot
    :type conn: obrbot.connection.Connection
    """
    split = text.split()
    if len(split) > 2:
        notice("Too many arguments")
        return
    elif len(split) < 1:
        notice("Not enough arguments")
        return

    if len(split) > 1:
        user = split[0].lower()
        group = split[1].lower()
    else:
        user = split[0].lower()
        group = None

    permission_manager = conn.permissions
    changed = False
    if group is not None:
        if not permission_manager.group_exists(group):
            notice("Unknown group '{}'".format(group))
            return
        changed_masks = permission_manager.remove_group_user(group, user)
        if changed_masks:
            changed = True
        if len(changed_masks) > 1:
            reply("Removed {} and {} from {}".format(", ".join(changed_masks[:-1]), changed_masks[-1], group))
        elif changed_masks:
            reply("Removed {} from {}".format(changed_masks[0], group))
        else:
            reply("No masks in {} matched {}".format(group, user))
    else:
        groups = permission_manager.get_user_groups(user)
        for group in groups:
            changed_masks = permission_manager.remove_group_user(group, user)
            if changed_masks:
                changed = True
            if len(changed_masks) > 1:
                reply("Removed {} and {} from {}".format(", ".join(changed_masks[:-1]), changed_masks[-1], group))
            elif changed_masks:
                reply("Removed {} from {}".format(changed_masks[0], group))
        if not changed:
            reply("No masks with elevated permissions matched {}".format(group, user))

    if changed:
        bot.config.save_config()
        permission_manager.reload()


@asyncio.coroutine
@hook.command("adduser", permissions=["permissions.manage"])
def add_permissions_user(text, conn, bot, notice, reply):
    """<user> <group> - adds <user> to <group>
    :type text: str
    :type conn: obrbot.connection.Connection
    :type bot: obrbot.bot.ObrBot
    """
    split = text.split()
    if len(split) > 2:
        notice("Too many arguments")
        return
    elif len(split) < 2:
        notice("Not enough arguments")
        return

    user = split[0].lower()
    group = split[1].lower()

    if not re.search('.+!.+@.+', user):
        # TODO: When we have presence tracking, check if there are any users in the channel with the nick given
        notice("The user must be in the format 'nick!user@host'")
        return

    permission_manager = conn.permissions

    group_exists = permission_manager.group_exists(group)

    changed = permission_manager.add_user_to_group(user, group)

    if not changed:
        reply("User {} is already matched in group {}".format(user, group))
    elif group_exists:
        reply("User {} added to group {}".format(user, group))
    else:
        reply("Group {} created with user {}".format(group, user))

    if changed:
        bot.config.save_config()
        permission_manager.reload()


@asyncio.coroutine
@hook.command("stop", permissions=["bot.manage"], autohelp=False)
def stop(text, bot):
    """[reason] - stops me with [reason] as its quit message.
    :type text: str
    :type bot: obrbot.bot.ObrBot
    """
    if text:
        yield from bot.stop(reason=text)
    else:
        yield from bot.stop()


@asyncio.coroutine
@hook.command(permissions=["bot.manage"], autohelp=False)
def restart(text, bot):
    """[reason] - restarts me with [reason] as its quit message.
    :type text: str
    :type bot: obrbot.bot.ObrBot
    """
    if text:
        yield from bot.restart(reason=text)
    else:
        yield from bot.restart()


@asyncio.coroutine
@hook.command(permissions=["bot.manage"])
def join(text, conn, notice):
    """<channel> - joins <channel>
    :type text: str
    :type conn: obrbot.connection.Connection
    """
    for target in text.split():
        if not target.startswith("#"):
            target = "#{}".format(target)
        notice("Attempting to join {}...".format(target))
        conn.join(target)


@asyncio.coroutine
@hook.command(permissions=["bot.manage"], autohelp=False)
def part(text, conn, chan_name, notice):
    """[#channel] - parts [#channel], or the caller's channel if no channel is specified
    :type text: str
    :type conn: obrbot.connection.Connection
    :type chan_name: str
    """
    if text:
        targets = text
    else:
        targets = chan_name
    for target in targets.split():
        if not target.startswith("#"):
            target = "#{}".format(target)
        notice("Leaving {}.".format(target))
        conn.part(target)


@asyncio.coroutine
@hook.command(autohelp=False, permissions=["bot.manage"])
def cycle(text, conn, chan_name, notice):
    """[#channel] - cycles [#channel], or the caller's channel if no channel is specified
    :type text: str
    :type conn: obrbot.connection.Connection
    :type chan_name: str
    """
    if text:
        targets = text
    else:
        targets = chan_name
    for target in targets.split():
        if not target.startswith("#"):
            target = "#{}".format(target)
        notice("Cycling {}.".format(target))
        conn.part(target)
        conn.join(target)


@asyncio.coroutine
@hook.command(permissions=["bot.manage"])
def nick(text, conn, notice):
    """<nick> - changes my nickname to <nick>
    :type text: str
    :type conn: obrbot.connection.Connection
    """
    if not re.match("^[a-z0-9_|.-\]\[]*$", text.lower()):
        notice("Invalid username '{}'".format(text))
        return
    notice("Changing nick to '{}'.".format(text))
    conn.set_nick(text)


@asyncio.coroutine
@hook.command(permissions=["bot.manage"])
def raw(text, conn, notice):
    """<command> - sends <command> as a raw IRC command
    :type text: str
    :type conn: obrbot.clients.irc.IrcConnection
    """
    notice("Sending raw command.")
    conn.send(text)


@asyncio.coroutine
@hook.command(permissions=["bot.control"])
def say(text, conn, chan_name):
    """[#channel] <message> - says <message> to [#channel], or to the caller's channel if no channel is specified
    :type text: str
    :type conn: obrbot.connection.Connection
    :type chan_name: str
    """
    text = text.strip()
    if text.startswith("#"):
        split = text.split(None, 1)
        channel = split[0]
        text = split[1]
    else:
        channel = chan_name
        text = text
    conn.message(channel, text)


@asyncio.coroutine
@hook.command("message", permissions=["bot.control"])
def message(text, conn):
    """<name> <message> - says <message> to <name>
    :type text: str
    :type conn: obrbot.connection.Connection
    """
    split = text.split(None, 1)
    channel = split[0]
    text = split[1]
    conn.message(channel, text)


@asyncio.coroutine
@hook.command("act", permissions=["bot.control"])
def me(text, conn, chan_name):
    """[#channel] <action> - acts out <action> in a [#channel], or in the current channel of none is specified
    :type text: str
    :type conn: obrbot.connection.Connection
    :type chan_name: str
    """
    text = text.strip()
    if text.startswith("#"):
        split = text.split(None, 1)
        channel = split[0]
        text = split[1]
    else:
        channel = chan_name
        text = text
    conn.action(channel, text)


@asyncio.coroutine
@hook.command("eval", permissions=["bot.manage"])
def eval_command(bot, conn, event, text):
    return str(eval(text, globals(), {"bot": bot, "conn": conn, "event": event}))
