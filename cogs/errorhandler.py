import discord
from discord.ext import commands

import asyncio


class ErrorHandler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        if hasattr(ctx.command, 'on_error'):
            return

        error_message = discord.Embed(title="", color=0xff0000)

        if isinstance(error, commands.CommandNotFound):
            return

        elif isinstance(error, commands.BadArgument):
            error_message.add_field(name='Error: Bad Argument', value=f'```\n{error}\n```', inline=False)

        elif isinstance(error, commands.UserInputError):
            if ctx.command.name == "shop":
                error_message.add_field(name='Error: Member Not Found',
                                        value=f'```Kai is currently not in FS right now, please try again later.```',
                                        inline=False)
            else:
                error_message.add_field(name='Error: Input Error', value=f'```\n{error}\n```', inline=False)

        elif isinstance(error, commands.MissingRequiredArgument):
            error_message.add_field(name='Error: Missing Argument', value=f'```\n{error}\n```', inline=False)

        elif isinstance(error, commands.TooManyArguments):
            error_message.add_field(name='Error: Too Many Arguments', value=f'```\n{error}\n```', inline=False)

        elif isinstance(error, commands.MemberNotFound):
            if ctx.command.name == "shop":
                error = f'Kai is currently not in FS right now, please try again later.'

            error_message.add_field(name='Error: Member Not Found', value=f'```\n{error}\n```', inline=False)

        elif isinstance(error, commands.MissingPermissions):
            error_message.add_field(name='Error: Missing Perms', value=f'```\n{error}\n```', inline=False)

        elif isinstance(error, commands.BotMissingPermissions):
            error_message.add_field(name='Error: Bot Missing Perms', value=f'```\n{error}\n```', inline=False)

        elif isinstance(error, commands.MissingRole):
            error_message.add_field(name='Error: Missing Role', value=f'```\n{error}\n```', inline=False)

        elif isinstance(error, commands.CommandOnCooldown):
            error_message.add_field(name='Error: Cooldown', value=f'```\n{error}\n```', inline=False)

        elif isinstance(error, asyncio.TimeoutError):
            if ctx.command.name == 'shop':
                error_message.add_field(name='Error: Timeout',
                                        value='```Selection has timed out. Please be quicker next time.```')

            else:
                error_message.add_field(name='Error: Invoke Error', value=f'```{error}```')

        elif isinstance(error, KeyError):
            if ctx.command.name == 'shop':
                return

            else:
                error_message.add_field(name='Error: Key Error', value=f'```{error}```')

        elif str(error) == 'Member is already unbanned.':
            error_message.add_field(name='Error: Member Already unbanned', value=f'```\n{error}\n```', inline=False)

        else:
            error_message.add_field(name='Error!',
                                    value=f'Something went wrong with the command. Please double check perms and '
                                          f'command input and try again.')
            error_message.add_field(name='Error Message:', value=f'```\n{error}\n```', inline=False)

        msg = await ctx.send(embed=error_message)

        if isinstance(error, commands.CommandOnCooldown):
            await asyncio.sleep(error.retry_after)
            await msg.delete()


async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
