import discord
from discord.ext import commands
from discord.utils import get

import asyncio
import datetime

patrick = "<:patrick:737502513875517552>"

time_convert = {"s": 1, "m": 60, "h": 3600, "d": 86400}


async def convert_time_to_seconds(time):
    try:
        return float(time[:-1]) * time_convert[time[-1]]
    except:
        return time * 60


class BannedMember(commands.Converter):
    async def convert(self, ctx, argument):
        if argument.isdigit():
            member_id = int(argument, base=10)
            try:
                return await ctx.guild.fetch_ban(discord.Object(id=member_id))
            except discord.NotFound:
                raise commands.BadArgument('Member is already unbanned.') from None

        ban_list = await ctx.guild.bans()
        entity = discord.utils.find(lambda u: str(u.user) == argument, ban_list)

        if entity is None:
            raise commands.BadArgument('This member has not been banned before.')
        return entity


class Moderation(commands.Cog):
    """Things to assist in moderation"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='Kicks the given user.', description='Kicks the given user.')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason='None'):

        sent_kick_message = True

        await member.kick(reason=reason)

        try:
            kickMessage = discord.Embed(title="", color=0xffff00)
            kickMessage.add_field(name=f'You have been kicked from {member.guild.name}!', value=f'Reason: {reason}',
                                  inline=False)
            kickMessage.timestamp = datetime.datetime.utcnow()
            await member.send(embed=kickMessage)
        except:
            print('Could not DM message.')
            sent_kick_message = False

        kickLog = discord.Embed(title=f'{member.name}#{member.discriminator} kicked from {member.guild.name}',
                                color=0xffff00)
        kickLog.add_field(name='ID:', value=member.id)
        kickLog.add_field(name='Reason:', value=reason, inline=False)
        kickLog.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=kickLog)

        kickLog.add_field(name='Responsible Moderator:',
                          value=f'{ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id})', inline=False)
        if not sent_kick_message:
            kickLog.set_footer(text='Could not DM kick message.')
        modlog = self.bot.get_channel(747588359425228922)
        await modlog.send(embed=kickLog)

    @commands.command(brief='Temporarily mutes the given user.', description='Temporarily mutes the given user.')
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration=None, *, reason='None'):

        if duration is None:
            duration = "5m"

        duration_in_sec = await convert_time_to_seconds(duration)
        time_until = datetime.timedelta(seconds=duration_in_sec)

        await member.timeout(time_until, reason=reason)
        sent_mute_message = True

        try:
            muteMessage = discord.Embed(title="", color=0xffa500)
            muteMessage.add_field(name=f'You have been muted on {member.guild.name}!',
                                  value=f'Reason: {reason} \nDuration:{duration}', inline=False)
            muteMessage.timestamp = datetime.datetime.utcnow()
            await member.send(embed=muteMessage)
        except:
            print('Could not DM message.')
            sent_mute_message = False

        muteLog = discord.Embed(title=f'{member.name}#{member.discriminator} muted on {member.guild.name}',
                                color=0xffa500)
        muteLog.add_field(name='ID:', value=member.id)
        muteLog.add_field(name='Duration:', value=duration)
        muteLog.add_field(name='Reason:', value=reason, inline=False)
        muteLog.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=muteLog)

        muteLog.add_field(name='Responsible Moderator:',
                          value=f'{ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id})', inline=False)
        if not sent_mute_message:
            muteLog.set_footer(text='Could not DM mute message.')

        modlog = self.bot.get_channel(747588359425228922)
        await modlog.send(embed=muteLog)

        duration_sec = await convert_time_to_seconds(duration)
        await asyncio.sleep(duration_sec)

    @commands.command(brief='Unmutes the given user.', description='Unmutes the given user.')
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member, reason='None'):

        if member.is_timed_out():

            await member.timeout(None, reason=reason)
            sent_unmute_message = False

            try:
                unmute_message = discord.Embed(title="", color=0xaaff00)
                unmute_message.add_field(name=f'You have been unmuted on {member.guild.name}!',
                                         value=f'Reason: {reason}', inline=False)
                unmute_message.timestamp = datetime.datetime.utcnow()
                await member.send(embed=unmute_message)
            except:
                print('Could not DM message.')
                sent_unmute_message = False

            unmute_log = discord.Embed(title=f'{member.name}#{member.discriminator} unmuted on {member.guild.name}',
                                       color=0xaaff00)
            unmute_log.add_field(name='ID:', value=member.id)
            unmute_log.add_field(name='Reason:', value=reason, inline=False)
            unmute_log.timestamp = datetime.datetime.utcnow()
            await ctx.send(embed=unmute_log)

            unmute_log.add_field(name='Responsible Moderator:',
                                 value=f'{ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id})',
                                 inline=False)
            if not sent_unmute_message:
                unmute_log.set_footer(text='Could not DM unmute message.')

            modlog = self.bot.get_channel(747588359425228922)
            await modlog.send(embed=unmute_log)

        else:
            unmute_message = discord.Embed(title="", color=0xff0000)
            unmute_message.add_field(name='Error: Member Not Muted',
                                     value='The member you have specified is not muted.')
            await ctx.send(embed=unmute_message)

    @commands.command(brief='Bans the given user.', description='Bans the given user.')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason='None'):

        sent_ban_message = True
        await member.ban(reason=reason, delete_message_days=0)

        try:
            ban_message = discord.Embed(title="", color=0xff0000)
            ban_message.add_field(name=f'You have been banned from {member.guild.name}!', value=f'Reason: {reason}',
                                  inline=False)
            ban_message.timestamp = datetime.datetime.utcnow()
            await member.send(embed=ban_message)
        except:
            print('Could not DM message.')
            sent_ban_message = False

        ban_log = discord.Embed(title=f'{member.name}#{member.discriminator} banned from {member.guild.name}',
                                color=0xff0000)
        ban_log.add_field(name='ID:', value=member.id)
        ban_log.add_field(name='Reason:', value=reason, inline=False)
        ban_log.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=ban_log)

        ban_log.add_field(name='Responsible Moderator:',
                          value=f'{ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id})', inline=False)
        if not sent_ban_message:
            ban_log.set_footer(text='Could not DM mute message.')
        modlog = self.bot.get_channel(747588359425228922)
        await modlog.send(embed=ban_log)

    @commands.command(brief='Temporarily bans the given user.', description='Temporarily bans the given user.')
    @commands.has_permissions(ban_members=True)
    async def tempban(self, ctx, member: discord.Member, duration, *, reason='None'):

        sent_ban_message = True
        await member.ban(reason=reason, delete_message_days=0)

        try:
            ban_message = discord.Embed(title="", color=0xff0000)
            ban_message.add_field(name=f'You have been banned from {member.guild.name}!',
                                 value=f'Reason: {reason} \nDuration: {duration}', inline=False)
            ban_message.timestamp = datetime.datetime.utcnow()
            await member.send(embed=ban_message)
        except:
            print('Could not DM message.')
            sent_ban_message = False

        ban_log = discord.Embed(title=f'{member.name}#{member.discriminator} banned from {member.guild.name}',
                                color=0xff0000)
        ban_log.add_field(name='ID:', value=member.id)
        ban_log.add_field(name='Duration:', value=duration)
        ban_log.add_field(name='Reason:', value=reason, inline=False)
        ban_log.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=ban_log)

        ban_log.add_field(name='Responsible Moderator:',
                          value=f'{ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id})', inline=False)
        if not sent_ban_message:
            ban_log.set_footer(text='Could not DM mute message.')
        modlog = self.bot.get_channel(747588359425228922)
        await modlog.send(embed=ban_log)

        duration_sec = await convert_time_to_seconds(duration)
        await asyncio.sleep(duration_sec)
        await member.unban(reason="Ban duration reached.")

    @commands.command(brief='Unbans the given user.', description='Unbans the given user.')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, member: BannedMember, *, reason='None'):

        await ctx.guild.unban(member.user, reason=reason)

        unbanLog = discord.Embed(title=f'{member.user}#{member.user.discriminator} unbanned from {ctx.guild}',
                                 color=0x0fff50)
        unbanLog.add_field(name='ID:', value=member.user.id, inline=False)
        unbanLog.add_field(name='Reason:', value=reason)
        unbanLog.add_field(name='Previously Banned For:', value=member.reason)
        unbanLog.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=unbanLog)

        unbanLog.add_field(name='Responsible Moderator:',
                           value=f'{ctx.author.name}#{ctx.author.discriminator} (ID: {ctx.author.id})', inline=False)
        modlog = self.bot.get_channel(747588359425228922)
        await modlog.send(embed=unbanLog)

    @commands.command(brief='Unbans the given user from the server specified.',
                      description='Unbans the given user from the server specified.')
    @commands.has_role(728309144452464731)
    async def globalunban(self, ctx, user: discord.User, server_id: int):
        server = self.bot.get_guild(server_id)
        await server.unban(user)
        await ctx.send(f'{user.name} is unbanned from {server.name}.')

    @commands.command(brief='Bans the given user from the server specified.',
                      description='Bans the given user from the server specified.')
    @commands.has_role(728309144452464731)
    async def globalban(self, ctx, member_id: int, server_id: int):
        server = self.bot.get_guild(server_id)
        member = server.get_member(member_id)
        await server.ban(member, delete_message_days=0)
        await ctx.send(f'{member.name} is banned from {server.name}.')


async def setup(bot):
    await bot.add_cog(Moderation(bot))
