import discord
from discord.ext import commands

import datetime

patrick = "<:patrick:737502513875517552>"


class Modmail(commands.Cog):
    """Send messages to other users"""
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author != self.bot.user:

            if message.guild:
                return

            embedVar = discord.Embed(title="", color=0xf8a532)
            embedVar.add_field(
                name=f"Message from {message.author.display_name}#{message.author.discriminator}"
                     f" (ID:{message.author.id})", value=f'{message.content} \u200b', inline=False)
            embedVar.timestamp = datetime.datetime.utcnow()
            modmail = self.bot.get_channel(747588359425228922)

            if message.attachments:
                embedVar.set_image(url=message.attachments[0].proxy_url)

            await modmail.send(embed=embedVar)

    @commands.command(brief='Send messages to users that share a server with the bot.',
                      description='Be able to send messages to other users that share a server with the bot. '
                                  'Note that it cannot send messages if the user does not share a server.')
    @commands.has_role(823366721779269642)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def send(self, ctx, user: discord.User, *, arg):
        await user.send(arg)
        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                await user.send(attachment.proxy_url)
        await ctx.send(f'DM sent to {user.name}! {patrick}')

    @commands.command(brief='Send messages to Kai.',
                      description='Send messages specifically to Kai. The default argument is ' 
                                  '"<@892743093911171123> Please use my DMs for serious bot inquiries only. '
                                  'Do not spam my DMs either. For general discussion, please move to #general." ')
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.has_role(823366721779269642)
    async def kaisend(self, ctx, *, arg = None):

        if arg is None:
            arg = '<@892743093911171123> Please use my DMs for serious bot inquiries only. Do not spam my DMs '
            'either. For general discussion, please move to #general.'

        kai = self.bot.get_user(892743093911171123)

        try:
            await kai.send(arg)
            if ctx.message.attachments:
                for attachment in ctx.message.attachments:
                    await kai.send(attachment.proxy_url)
            await ctx.send(f'DM sent! {patrick}')
        except:
            await ctx.send("Could not DM Kai.")


async def setup(bot):
    await bot.add_cog(Modmail(bot))
