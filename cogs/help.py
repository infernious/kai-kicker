import discord
from discord.ext import commands


class CogButtons(discord.ui.Button):

    def __init__(self, cog: commands.Cog, commands_list: list):
        self.cog_name = getattr(cog, "qualified_name", "No Category")
        super().__init__(style=discord.ButtonStyle.gray, label=self.cog_name)
        self.cog = cog
        self.commands_list = commands_list

    async def callback(self, interaction):
        cog_embed = discord.Embed(title=self.cog_name, color = 0xf8a532)
        cog_embed.add_field(name='Description', value=self.cog.description, inline=False)

        commands_string = ''
        for command in self.commands_list:
            commands_string += f'`k!{command.qualified_name} {command.signature}`\n{command.brief}\n\n'

        cog_embed.add_field(name='Commands', value=commands_string, inline=False)
        cog_embed.set_footer(text='Use "k!help [command]" to get more info on a command.\n'
                                  '[] are option arguments while <> are required.')
        await interaction.response.send_message(embed=cog_embed, ephemeral=True)


class HelpView(discord.ui.View):

    def __init__(self, mapping):
        super().__init__()

        for cog, commands_list in mapping.items():
            if commands_list:
                self.add_item(CogButtons(cog, commands_list))


class InviteLink(discord.ui.View):

    def __init__(self):
        super().__init__()

        url = "https://discord.com/oauth2/authorize?client_id=835274989686095932&scope=bot&permissions=470117574"

        self.add_item(discord.ui.Button(label='Invite Me', url=url, style=discord.ButtonStyle.blurple))


class MyHelp(commands.HelpCommand):

    # k!help
    async def send_bot_help(self, mapping):
        help_embed = discord.Embed(title='Help', color=0xf8a532)

        filtered_dict: dict = {}
        for cog, commands in mapping.items():

            cog_name = getattr(cog, "qualified_name", "No Category")
            filtered = await self.filter_commands(commands)

            if filtered:
                if cog.description:
                    help_embed.add_field(name=cog_name, value=cog.description, inline=False)
                else:
                    help_embed.add_field(name=cog_name, value="None", inline=False)

            cog_dict = {cog: filtered}
            filtered_dict = {**filtered_dict, **cog_dict}

        await self.context.send(embed=help_embed, view=HelpView(filtered_dict))

    async def send_command_help(self, command):

        command_embed = discord.Embed(title=f'k!{command.qualified_name}', color = 0xf8a532)

        if command.signature:
            command_embed.add_field(name='Arguments', value=command.signature)

        command_embed.add_field(name="Description", value=command.description, inline=False)

        if command.aliases:
            command_embed.add_field(name='Aliases', value=", ".join(command.aliases), inline=False)

        command_embed.set_footer(text='[] are option arguments while <> are required.')

        await self.context.send(embed=command_embed)

    async def send_cog_help(self, cog):
        cog_name = getattr(cog, "qualified_name", "No Category")
        cog_embed = discord.Embed(title=cog_name, color=0xf8a532)
        cog_embed.add_field(name='Description', value=cog.description, inline=False)

        commands_string = ''
        for command in cog.get_commands():
            commands_string += f'`k!{command.qualified_name} {command.signature}`\n{command.brief}\n\n'

        cog_embed.add_field(name='Commands', value=commands_string, inline=False)
        cog_embed.set_footer(text='Use "k!help [command]" to get more info on a command.\n'
                                  '[] are option arguments while <> are required.')
        await self.context.send(embed=cog_embed)

    async def send_error_message(self, error):
        error_embed = discord.Embed(title="", color = 0xff0000)
        error_embed.add_field(name='Error!', value=f'```{error}```')
        await self.context.send(embed=error_embed)


class About(commands.Cog):
    """Commands related to me, Kai Kicker"""
    def __init__(self, bot):
        self.default_help_command = bot.help_command
        bot.help_command = MyHelp()
        bot.help_command.cog = self
        self.bot = self

    @commands.command()
    async def about(self, ctx):
        about_embed = discord.Embed(title='', color=0xf8a532)
        about_embed.add_field(name='About Me', value='Features: kick kai, ban kai, mute kai, increase/decrease chances for each of these and manually change, manually change and randomize multiplier, send dms anonymously, receive and log dms, modmail, change nickname, kick/ban/mute kai with shop, defeat bosses or enemies, tax people, kai kicker economy, bully kai, steal kai\'s kids, arrest kai, frame kai, sue kai, beat kai in court, beat kai in the bed, etc, ')

        await ctx.send(embed=about_embed, view=InviteLink())

async def setup(bot):
    await bot.add_cog(About(bot))
