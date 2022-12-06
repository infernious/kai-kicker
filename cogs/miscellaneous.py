import discord
from discord.ext import commands

import os
import time
import asyncio
import random
import datetime

import motor.motor_asyncio as motor

from cogs.economy import get_user_config, update_user_config

nikkah_boolean = False
husband = "[placeholder]"
ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])

database_password = os.environ.get("DATABASE_PASSWORD")
db_client = motor.AsyncIOMotorClient(database_password)
db = db_client["kai-kicker"]
user_config = db["user_config"]
bot_config = db["bot_config"]


class Miscellaneous(commands.Cog):
    """Assortment of other commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='Leaves the server you specify.',
                      description='Leaves the server you specify.')
    @commands.has_role(728309144452464731)
    async def leave(self, ctx, id: int):
        guild = self.bot.get_guild(id)
        await ctx.send(f'Left **{guild.name}**.')
        await guild.leave()

    @commands.command(brief='Purges channel messages.',
                      description='Purges channel messages with the limit you specify.')
    @commands.is_owner()
    async def purge(self, ctx, amount: int):
        await ctx.message.channel.purge(limit=amount)

    @commands.command(brief='View leaderboard of kai kicker points',
                      description='View leaderboard of kai kicker points. '
                                  'Use `k!points` to see how many points you have.')
    @commands.has_role(728309144452464731)
    async def alb(self, ctx, page: int = 1):

        if page < 0:
            raise commands.UserInputError('The page number you have selected cannot be negative. Please try again.')

        pipeline = [
            {"$group": {"_id": "$user_id", "points": {"$max": "$points"}}},
            {"$sort": {"points": -1}},
            {"$skip": 10 * (page - 1)},
            {"$limit": 10 * page}
        ]

        lb = ''
        index = (10 * page) - 9
        async with ctx.channel.typing():
            async for doc in user_config.aggregate(pipeline):

                try:
                    lb += f'`#{index}` {self.bot.get_user(doc["_id"]).name}#{self.bot.get_user(doc["_id"]).discriminator}: {doc["points"]} points\n'
                except AttributeError:
                    lb += f'`#{index}` {doc["_id"]}: {doc["points"]} points\n'

                index += 1

                if index > (10 * page):
                    break

        leaderboard_embed = discord.Embed(title='', color=0xf8a532)
        # leaderboard_embed.add_field(name='Your Rank', value='You are rank `#{rank}` with `{points}` points.')
        leaderboard_embed.add_field(name='Leaderboard', value=lb, inline=False)

        try:
            await ctx.send(embed=leaderboard_embed)
        except:
            raise commands.UserInputError(f'Page "{page}" does not exist, please try again with a lower value.')

    @commands.command(aliases=['lb'],
                      brief='View leaderboard of kai kicker points',
                      description='View leaderboard of kai kicker points. '
                                  'Use `k!points` to see how many points you have.')
    async def leaderboard(self, ctx, page: int = 1):

        if page < 0:
            raise commands.UserInputError('The page number you have selected cannot be negative. Please try again.')

        pipeline = [
            {"$group": {"_id": "$user_id", "points": {"$max": "$points"}}},
            {"$sort": {"points": -1}},
            {"$skip": 10 * (page - 1)},
            {"$limit": 10 * page}
        ]

        lb = ''
        index = (10 * page) - 9
        async with ctx.channel.typing():
            async for doc in user_config.aggregate(pipeline):

                try:
                    lb += f'`#{index}` {self.bot.get_user(doc["_id"]).name}: {doc["points"]} points\n'
                except AttributeError:
                    lb += f'`#{index}` {doc["_id"]}: {doc["points"]} points\n'

                index += 1

                if index > (10 * page):
                    break

        leaderboard_embed = discord.Embed(title='', color=0xf8a532)
        # leaderboard_embed.add_field(name='Your Rank', value='You are rank `#{rank}` with `{points}` points.')
        leaderboard_embed.add_field(name='Leaderboard', value=lb, inline=False)

        try:
            await ctx.send(embed=leaderboard_embed)
        except:
            raise commands.UserInputError(f'Page "{page}" does not exist, please try again with a lower value.')

    @commands.cooldown(1, 1800, commands.BucketType.default)
    @commands.command(brief='Marry Kai\'s mom.',
                      description='Marry Kai\'s mom. This command has a global cooldown of 30 minutes.')
    async def nikkah(self, ctx):
        nikkah = discord.Embed(title='', color=0xff0000)

        bot_config_dict = await bot_config.find_one()
        boolean = bot_config_dict["nikkah_boolean"]

        if not boolean:

            nikkah.add_field(name='Error: Command Removed',
                             value=f"```Out of respect for Kai, this command has been removed and has been replaced "
                                   f"with k!boss. However, if Kai decides to make a mom joke, this command will be "
                                   f"temporarily brought back.```")

        elif boolean:

            nikkah.colour = 0xf8a532

            global husband
            husband = f'{ctx.author.name}'

            config = await get_user_config(ctx.author.id)

            config[ctx.author.id]['nikkah'] += 1
            config[ctx.author.id]['points'] += 25
            count = config[ctx.author.id]['nikkah']

            await update_user_config(ctx.author.id, config)

            global ordinal
            nikkah.add_field(name=f"{ctx.author.name} has just finished nikkah with kai's mother!",
                             value=f"Please congratulate them on their {ordinal(count)} marriage! :ring:")

        await ctx.send(embed=nikkah)

    @nikkah.error
    async def nikkah_error(self, ctx, error):
        nikkah_error = discord.Embed(title='', color=0xff0000)

        bot_config_dict = await bot_config.find_one()
        boolean = bot_config_dict["nikkah_boolean"]

        if boolean:
            global husband
            nikkah_error.add_field(name='Error: Already Married',
                                   value=f"```Kai's mother is already married to {husband}, please try again in "
                                         f"{round(error.retry_after / 60, 1)} minutes.```")
            message = await ctx.send(embed=nikkah_error)
            await asyncio.sleep(10)
            await message.delete()

        elif not boolean:
            nikkah_error.add_field(name='Error: Command Removed',
                                   value=f"```Out of respect for Kai, this command has been removed and has been replaced "
                                         f"with k!boss. However, if Kai decides to make a mom joke, this command will be "
                                         f"temporarily brought back.```")
            await ctx.send(embed=nikkah_error)

    @commands.command(aliases=["nc"], brief='View how many times you married Kai\'s mom.',
                      description='See how many times you married Kai\'s mom. '
                                  'Use `k!nikkahleaderboard` (or `k!nlb` for short) to see the leaderboard.')
    async def nikkahcount(self, ctx, user: discord.User = None):

        nikkah = discord.Embed(title='', color=0xf8a532)

        if user is None:
            user = ctx.author

        config = await get_user_config(ctx.author.id)
        count = config[ctx.author.id]['nikkah']

        nikkah.add_field(name='Nikkah Counter', value=f"Kai's Mother has been married to {user.name} {count} time(s)!")

        await ctx.send(embed=nikkah)

    @commands.command(aliases=['nlb'],
                      brief='Leaderboard but for nikkah count.',
                      description='Basically like leaderboard except for nikkah count.')
    async def nikkahleaderboard(self, ctx, page: int = 1):

        if page < 0:
            raise commands.UserInputError('The page number you have selected cannot be negative. Please try again.')

        pipeline = [
            {"$group": {"_id": "$user_id", "nikkah": {"$max": "$nikkah"}}},
            {"$sort": {"nikkah": -1}},
            {"$skip": 10 * (page - 1)},
            {"$limit": 10 * page}
        ]

        lb = ''
        index = 1
        async with ctx.channel.typing():
            async for doc in user_config.aggregate(pipeline):

                try:
                    lb += f'`#{index}` {self.bot.get_user(doc["_id"]).name}#{self.bot.get_user(doc["_id"]).descriminator}: ' \
                          f'{doc["nikkah"]} marriage(s)\n'
                except AttributeError:
                    lb += f'`#{index}` {doc["_id"]}: {doc["nikkah"]} marriage(s)\n'

                index += 1

        leaderboard_embed = discord.Embed(title='', color=0xf8a532)
        # fix below (get ranking to work)
        # leaderboard_embed.add_field(name='Your Rank', value='You are rank `#{rank}` with `{points}` points.')
        leaderboard_embed.add_field(name='Leaderboard', value=lb, inline=False)

        try:
            await ctx.send(embed=leaderboard_embed)
        except:
            raise commands.UserInputError(f'Page "{page}" does not exist, please try again with a lower value.')

    @commands.command(brief='Get info about a server',
                      description='Retrieve info about a server that the bot is in.')
    @commands.has_role(728309144452464731)
    async def serverinfo(self, ctx, id: int):
        guild = self.bot.get_guild(id)
        server_info = discord.Embed(title=f'{guild.name} Information', description=guild.description,
                                    color=discord.Colour.blue())

        server_info.set_thumbnail(url=guild.icon.url)
        server_info.add_field(name='Owner', value=str(guild.owner), inline=False)
        server_info.add_field(name='Server ID', value=guild.id, inline=False)
        server_info.add_field(name='Region', value=guild.region, inline=False)
        server_info.add_field(name='Member Count', value=guild.member_count, inline=False)

        await ctx.send(embed=server_info)

    @commands.command(brief='Send a suggestion.',
                      description='Send a suggestion to FS. This can be used for new features or bug reports.')
    async def suggest(self, ctx, *, suggestion):
        fs = self.bot.get_guild(725749745338941451)
        suggestion_channel = fs.get_channel(845140621853589545)

        suggestion_embed = discord.Embed(title="", color=0xf8a532)
        suggestion_embed.add_field(
            name=f"Suggestion from {ctx.author.name}#{ctx.author.discriminator} (ID:{ctx.author.id})",
            value=suggestion, inline=False)
        suggestion_embed.timestamp = datetime.datetime.utcnow()

        await suggestion_channel.send(embed=suggestion_embed)
        await ctx.send("Suggestion sent!")

    @commands.command(brief='Get ping from API and heartbeat.',
                      description='Returns the API and heartbeat ping. The heartbeat ping is the websocket latency.')
    async def ping(self, ctx):
        ping_embed = discord.Embed(title='', color=0xf8a532)
        ping_embed.add_field(name='Pinging... 🏓', value='\u200b')

        start_time = time.time()
        pingpong = await ctx.send(embed=ping_embed)
        end_time = time.time()

        ping_embed.clear_fields()
        ping_embed.add_field(
            name='Pong! 🏓',
            value=f'Heartbeat: `{round(self.bot.latency * 1000, 1)} ms` '
                  f'\nAPI: `{round(end_time - start_time, 4) * 1000} ms`')

        await pingpong.edit(embed=ping_embed)

    @commands.command(brief='place holder', description='place holder')
    @commands.is_owner()
    async def globaladdrole(self, ctx, guild_id: int, role_id: int, member_id: int):

        target_guild = self.bot.get_guild(guild_id)
        target_role = target_guild.get_role(role_id)
        target_member = target_guild.get_member(member_id)

        await target_member.add_roles(target_role)
        await ctx.send(f'{target_role.name} successfully added to {target_member.name} in {target_guild.name}.')

    @commands.command(brief='place holder', description='place holder')
    @commands.is_owner()
    async def globalremoverole(self, ctx, guild_id: int, role_id: int, member_id: int):

        target_guild = self.bot.get_guild(guild_id)
        target_role = target_guild.get_role(role_id)
        target_member = target_guild.get_member(member_id)

        await target_member.remove_roles(target_role)
        await ctx.send(f'{target_role.name} successfully removed from {target_member.name} in {target_guild.name}.')

    @commands.command(brief='place holder', description='place holder')
    @commands.is_owner()
    async def getservers(self, ctx):

        for guild in self.bot.guilds:

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

            await ctx.send(embed=join_log)

        await ctx.send('Fetched all guilds.')

    @commands.command(brief='place holder', description='place holder')
    @commands.is_owner()
    async def reply(self, ctx, guild_id: int, channel_id: int, msg_id: int, *, response: str):

        target_guild = self.bot.get_guild(guild_id)
        target_channel = target_guild.get_channel(channel_id)
        target_message = await target_channel.fetch_message(msg_id)

        await target_message.reply(response)

        await ctx.send("reply sent!")

    @commands.command(brief='place holder', description='place holder')
    @commands.is_owner()
    async def vcjoin(self, ctx, guild_id: int, voice_channel_id: int):

        target_guild = self.bot.get_guild(guild_id)
        target_channel = target_guild.get_channel(voice_channel_id)

        await target_channel.connect()
        await ctx.send('connected to VC successfully')

    @commands.command(brief='place holder', description='place holder')
    @commands.is_owner()
    async def vcleave(self, ctx, guild_id: int, voice_channel_id: int):

        target_guild = self.bot.get_guild(guild_id)
        target_channel = target_guild.get_channel(voice_channel_id)

        await target_channel.disconnect()
        await ctx.send('disconnected from VC successfully')

    @commands.command(brief='Automatically taxes someone', description='Automatically taxes someone, dum dum heads is required.')
    @commands.has_role(728309144452464731)
    async def tax(self, ctx, user: discord.User):

        tax_percent = random.randint(5, 30)

        config = await get_user_config(user.id)
        points = config[user.id]['points']

        new_points = round(points * (1 - (tax_percent / 100)))
        config[user.id]['points'] = new_points

        await update_user_config(user.id, config)

        tax_embed_two = discord.Embed(title='', color=0xf8a532)
        tax_embed_two.add_field(name=f'You have been taxed a random amount as per '
                                     f'Executive Order 1: The Reduce Inflation Order.',
                                value=f'Applied tax: `{tax_percent}%`\n'
                                      f'Previous balance: `{points}` points\n'
                                      f'New balance: `{new_points}` points')

        sent_message = True

        try:
            await user.send(embed=tax_embed_two)
        except:
            sent_message = False

        tax_embed = discord.Embed(title='', color=0xf8a532)
        tax_embed.add_field(name=f'{user.name}#{user.discriminator} taxed!',
                            value=f'Applied tax: `{tax_percent}%`\n'
                                  f'Previous balance: `{points}` points\n'
                                  f'New balance: `{new_points}` points')
        tax_embed.timestamp = datetime.datetime.utcnow()

        if not sent_message:
            tax_embed.set_footer(text='Could not DM tax message.')

        await ctx.send(embed=tax_embed)

        fs = self.bot.get_guild(725749745338941451)
        bot_log = fs.get_channel(730864382065770518)

        await bot_log.send(embed=tax_embed)

    @commands.command(brief='Gets an invite to the server specified', description='Gets an invite to the server specified')
    @commands.has_role(728309144452464731)
    async def getinvite(self, ctx, guild_id: int, channel_id: int):

        target_guild = self.bot.get_guild(guild_id)
        target_channel = target_guild.get_channel(channel_id)

        invite_link = await target_channel.create_invite()

        await ctx.send(invite_link)


async def setup(bot):
    await bot.add_cog(Miscellaneous(bot))
