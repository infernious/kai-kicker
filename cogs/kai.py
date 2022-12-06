import discord
from discord.ext import tasks, commands
from discord.utils import get

import asyncio
import random
import os

import motor.motor_asyncio as motor

patrick = "<:patrick:737502513875517552>"
cache = {
    "boolean": True
}
message_check = []
multipliers = [0.5, 2, 3]

database_password = os.environ.get("DATABASE_PASSWORD")
db_client = motor.AsyncIOMotorClient(database_password)
db = db_client["kai-kicker"]
server_config = db["server_config"]


async def get_config(guild_id):
    global cache

    try:
        config = {
            guild_id: cache[guild_id]
        }
    except KeyError:

        config_from_db = await server_config.find_one({"server_id": guild_id})
        config = {
            guild_id: config_from_db
        }

        if config_from_db is None:
            config = {
                "server_id": guild_id,
                "ban_chance": 1,
                "kick_chance": 2.5,
                "mute_chance": 0.5,
                "mute_bound": 10,
                "ban_bound": 10,
                "mult_chance": 0.1,
                "config": False,
                "ids": []
            }

            await server_config.insert_one(config)

            config = {guild_id: config}

        cache = {**cache, **config}

    return config


async def update_config(guild_id, new_config):
    global cache
    cache.update({guild_id: new_config[guild_id]})

    old_config = await server_config.find_one({"server_id": guild_id})
    _id = old_config['_id']

    await server_config.replace_one({"_id": _id}, new_config[guild_id])


class Kai(commands.Cog):
    """Commands related to the \"auto-mod\" feature.
    This feature is off by default. Using `k!config enable` to enable it."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):

        if not message.guild:
            return

        else:

            config = await get_config(message.guild.id)

            if message.guild.id not in message_check:
                message_check.append(message.guild.id)

            elif not config[message.guild.id]["config"]:
                return

            elif message.author.id in config[message.guild.id]['ids']:

                if random.randint(1, 1000) <= config[message.guild.id]['ban_chance'] * 10:

                    ban_time = random.randint(1, config[message.guild.id]['ban_bound'])

                    try:
                        await message.author.send(
                            f'You have been **banned** from {message.guild.name} for some amount of time! {patrick}')
                    except:
                        print('Could not DM user.')

                    await message.guild.ban(message.author, delete_message_days=0)

                    await message.channel.send(
                        f'**{message.author.mention} has been banned for {ban_time} minute(s)!** {patrick}')

                    await asyncio.sleep(ban_time * 60)
                    try:
                        await message.guild.unban(message.author)
                        await message.channel.send(f'**{message.author.mention} has been unbanned!** {patrick}')
                    except:
                        pass

                elif random.randint(1, 1000) <= config[message.guild.id]['kick_chance'] * 10:

                    try:
                        await message.author.send(f'You have been **kicked** from {message.guild.name}! {patrick}')
                    except:
                        print('Could not DM user.')

                    await message.guild.kick(message.author)

                    await message.channel.send(f'**{message.author.mention} has been kicked!** {patrick}')

                elif random.randint(1, 1000) <= config[message.guild.id]['mute_chance'] * 10:

                    mute_time = random.randint(1, config[message.guild.id]['mute_bound'])
                    await message.author.timeout(duration=mute_time * 60)

                    try:
                        await message.author.send(f'You have been **muted** on {message.guild.name} '
                                                  f'for **{mute_time} minute(s)**!')
                    except:
                        print('Could not DM user.')

                    await message.channel.send(
                        f'**{message.author.mention} has been muted for {mute_time} minute(s)!** {patrick}')

            elif random.randint(1, 1000) <= (config[message.guild.id]['mult_chance'] * 10) and message.guild:

                # "punishment" decides whether it's a mute/kick/ban getting affected
                # 1 = mute, 2 = kick, 3 = ban
                punishment = random.randint(1, 3)
                # decides which multiplier to choose
                global multipliers
                mult = multipliers[random.randint(0, 2)]

                if punishment == 1:
                    config[message.guild.id]['mute_chance'] = mult * config[message.guild.id]['mute_chance']
                    await message.channel.send(
                        f"Multiplier is `{mult}` \nMute Percent changed to `{config[message.guild.id]['mute_chance']}%` {patrick}")
                elif punishment == 2:
                    config[message.guild.id]['kick_chance'] = mult * config[message.guild.id]['kick_chance']
                    await message.channel.send(
                        f"Multiplier is `{mult}` \nKick Percent changed to `{config[message.guild.id]['kick_chance']}%` {patrick}")
                elif punishment == 3:
                    config[message.guild.id]['ban_chance'] = mult * config[message.guild.id]['ban_chance']
                    await message.channel.send(
                        f"Multiplier is `{mult}` \nBan Percent changed to `{config[message.guild.id]['ban_chance']}%` {patrick}")

                await update_config(message.guild.id, config)

    @tasks.loop(minutes=15.0)
    async def cache_eviction(self):

        global message_check
        global cache

        async for guild in self.bot.fetch_guilds(limit=150):
            if guild.id not in message_check:
                try:
                    cache.pop(guild.id)
                finally:
                    print('Not in cache')

        fs = self.bot.get_guild(725749745338941451)
        bot_log = fs.get_channel(730864382065770518)

        cache_log = discord.Embed(title='', color=0xf8a532)
        cache_log.add_field(name="\u200b", value='Cache cleaned.')

        await bot_log.send(embed=cache_log)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):

        await get_config(guild.id)

        fs = self.bot.get_guild(725749745338941451)
        bot_log = fs.get_channel(730864382065770518)

        join_log = discord.Embed(title='', color=0xf8a532)
        join_log.add_field(name="Joined Server", value=f'Joined {guild.name} (ID: {guild.id}).')
        try:
            join_log.set_thumbnail(url=guild.icon.url)
        except:
            pass
        join_log.add_field(name='Owner', value=str(guild.owner), inline=False)
        join_log.add_field(name='Server ID', value=guild.id, inline=False)
        join_log.add_field(name='Region', value=guild.region, inline=False)
        join_log.add_field(name='Member Count', value=guild.member_count, inline=False)

        await bot_log.send(embed=join_log)

        if guild.id == 835338794323542037:
            await guild.leave()
            await bot_log.send(f'Left {guild.name}')

    @commands.command(brief='View or edit config.',
                      description='Control and edit the configuration for the "auto-mod" feature, including chances.'
                                  'Use `k!config view` to view current settings or `k!config args` to see possible arguments.')
    @commands.has_permissions(ban_members=True)
    async def config(self, ctx, arg, arg2=""):

        arg = arg.lower()

        config = await get_config(ctx.guild.id)

        n = 0

        if arg == "mute":
            config[ctx.guild.id]['mute_chance'] = float(arg2)

        elif arg == "kick":
            config[ctx.guild.id]['kick_chance'] = float(arg2)

        elif arg == "ban":
            config[ctx.guild.id]['ban_chance'] = float(arg2)

        elif arg == "mutebound":
            config[ctx.guild.id]['mute_bound'] = float(arg2)
            await ctx.send(f'Mute time upper bound changed to **{arg2} minutes**!')
            n = 1

        elif arg == "banbound":
            config[ctx.guild.id]['ban_bound'] = float(arg2)
            await ctx.send(f'Ban time upper bound changed to **{arg2} minutes**!')
            n = 1

        elif arg == "mult":
            config[ctx.guild.id]['mult_chance'] = float(arg2)
            await ctx.send(f'Multiplier chance changed to **{arg2}%**!')
            n = 1

        elif arg == "view":
            config_view = discord.Embed(title="Current Config Settings", color=0xf8a532)
            config_view.description = f"Mute Chance: `{config[ctx.guild.id]['mute_chance']}%` \n" \
                                      f"Kick Chance: `{config[ctx.guild.id]['kick_chance']}%` \n" \
                                      f"Ban Chance: `{config[ctx.guild.id]['ban_chance']}%` \n\n " \
                                      f"Mute Time Bound: `{config[ctx.guild.id]['mute_bound']}` \n " \
                                      f"Ban Time Bound: `{config[ctx.guild.id]['ban_bound']}` \n\n " \
                                      f"Multiplier Chance: `{config[ctx.guild.id]['mult_chance']}%`"
            await ctx.send(embed=config_view)
            n = 1

        elif arg == "reset":

            await ctx.send("Config has been reset!")
            config[ctx.guild.id]['mute_chance'] = 1
            config[ctx.guild.id]['kick_chance'] = 2.5
            config[ctx.guild.id]['ban_chance'] = 0.5
            config[ctx.guild.id]['mute_bound'] = 10.0
            config[ctx.guild.id]['ban_bound'] = 10.0
            config[ctx.guild.id]['mult_chance'] = 0.1

            n = 1

        elif arg == "random":

            config[ctx.guild.id]['mute_chance'] = float(random.randint(1, 25))
            config[ctx.guild.id]['kick_chance'] = float(random.randint(1, 25))
            config[ctx.guild.id]['ban_chance'] = float(random.randint(1, 25))
            config[ctx.guild.id]['mute_bound'] = float(random.randint(5, 30))
            config[ctx.guild.id]['ban_bound'] = float(random.randint(5, 30))
            config[ctx.guild.id]['mult_chance'] = float(random.randint(1, 25))

            n = 1

            await ctx.send('Config has been randomized!')

        elif arg == "enable":
            config[ctx.guild.id]['config'] = True
            await ctx.send("Config enabled. People added to the list can now be randomly kicked, banned or muted.")
            n = 1

        elif arg == "disable":
            config[ctx.guild.id]['config'] = False
            await ctx.send("Config diabled. People added to the list cannot be randomly kicked, banned or muted.")
            n = 1

        elif arg == "args":

            args_embed = discord.Embed(title='Arguments for k!config:', color=0xf8a532)
            args_embed.add_field(name='mute/kick/ban [chance]',
                                 value='Controls the kick, mute, or ban chance.',
                                 inline=False)
            args_embed.add_field(name='mutebound/banbound [chance]',
                                 value='Controls the amount of time someone automodded is muted or banned.',
                                 inline=False)
            args_embed.add_field(name='mult [chance]',
                                 value='Controls the multiplier chance of the current config settings for the chances to be changed.',
                                 inline=False)
            args_embed.add_field(name='view',
                                 value='View current config settings.',
                                 inline=False)
            args_embed.add_field(name='reset',
                                 value='Resets config settings to default values.',
                                 inline=False)
            args_embed.add_field(name='random',
                                 value='Changes config settings to random values.',
                                 inline=False)
            args_embed.add_field(name='enable/disable',
                                 value='Enables/Disables the "auto-mod" feature (disabled by default).',
                                 inline=False)

            await ctx.send(embed=args_embed)

            n = 1

        else:
            return

        if n == 0:
            await ctx.send(f'{arg.title()} percent changed to **{arg2}%**! {patrick}')

        await update_config(ctx.guild.id, config)

    @commands.command(brief='Add people to get auto-modded.',
                      description='Add people to a list of users for them to get auto-modded.')
    @commands.has_permissions(ban_members=True)
    async def add(self, ctx, member: discord.Member):

        config = await get_config(ctx.guild.id)

        if member.id not in config[ctx.guild.id]['ids']:
            config[ctx.guild.id]['ids'].append(member.id)
        else:
            raise commands.UserInputError("Member is already present in the list.")

        await update_config(ctx.guild.id, config)
        await ctx.send(str(member) + " added. <:patrick:737502513875517552>")

    @commands.command(brief='Remove people from auto-moderation.',
                      description='Remove people from the list of users to get auto-modded.')
    @commands.has_permissions(ban_members=True)
    async def remove(self, ctx, member: discord.Member):

        config = await get_config(ctx.guild.id)

        if member.id in config[ctx.guild.id]['ids']:
            config[ctx.guild.id]['ids'].remove(member.id)

        else:
            raise commands.UserInputError("Member is not present in the list.")

        await update_config(ctx.guild.id, config)
        await ctx.send(str(member) + " removed. <:patrick:737502513875517552>")

    @commands.command(brief='View the current list of people to get "auto-modded."',
                      description='View the current list of people who can get auto-modded. '
                                  'You can edit this list by using `k!add` or `k!remove`.')
    async def names(self, ctx):

        names_embed = discord.Embed(title="Current List of People", color=0xf8a532)
        name_list = []

        config = await get_config(ctx.guild.id)

        for id in config[ctx.guild.id]['ids']:
            name_list.append(f"<@{str(id)}>")

        names_embed.description = '\n'.join(map(str, name_list))
        await ctx.send(embed=names_embed)


async def setup(bot):
    await bot.add_cog(Kai(bot))
