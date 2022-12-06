import discord
from discord.ext import commands

from cogs.games import Enemy, get_user_config, update_user_config
import random
import json

enemy_list = ["Discord Mods", "Discord Trolls", "me lon", "Discord Creeps"]
enemy_dict = {
    "Discord Mods": "❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ",
    "Discord Trolls": "❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ",
    "me lon": "❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ",
    "Discord Creeps": "❤️ ❤️ ❤️ ❤️ ❤️ ",
}


class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_typing(self, channel, user, when):

        # checks if it's FS
        if channel.guild.id == 725749745338941451:
            try:
                target = channel.topic.split()
                target_guild = self.bot.get_guild(int(target[0]))
                target_channel = target_guild.get_channel(int(target[1]))
            except:
                return

            async with target_channel.typing():
                await self.bot.wait_for('message', timeout=10.0)

    @commands.Cog.listener()
    async def on_message(self, message):

        if not message.guild:
            return

        # checks if it's someone other than kai kicker saying something.
        elif not message.author.id == self.bot.user.id:

            # checks if it's FS
            if message.guild.id == 725749745338941451:

                # checks if it's #kai-kicker-global-say
                if message.channel.id == 860935157778743316:

                    target = message.channel.topic.split()
                    target_guild = self.bot.get_guild(int(target[0]))
                    target_channel = target_guild.get_channel(int(target[1]))
                    try:
                        if message.content:
                            await target_channel.send(message.content)
                        if message.attachments:
                            for attachment in message.attachments:
                                await target_channel.send(attachment.proxy_url)
                        await message.add_reaction('✅')
                    except discord.errors.Forbidden:
                        await message.add_reaction('❌')

            else:

                # Random boss spawn
                if 1 == random.randint(1, 250):

                    global enemy_list, enemy_dict
                    enemy_name = enemy_list[random.randint(0, 3)]
                    enemy_hearts = enemy_dict[enemy_name]

                    enemy_embed = discord.Embed(title='', color=0xff0000)
                    enemy_embed.add_field(name=f'Oh no! {message.author.name} summoned {enemy_name}!',
                                          value=f'{enemy_hearts}')

                    view = Enemy(enemy_embed, enemy_name, message.author, self.bot)

                    await message.channel.send(embed=enemy_embed, view=view)

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        if member.guild.id == 725749745338941451 and member.id == 892743093911171123:
            config = await get_user_config(892743093911171123)
            config[892743093911171123]['nickname'] = member.nick
            await update_user_config(892743093911171123, config)

    @commands.Cog.listener()
    async def on_member_join(self, member):

        if member.guild.id == 725749745338941451 and member.id == 892743093911171123:
            config = await get_user_config(892743093911171123)
            await member.edit(nick=config[892743093911171123]['nickname'])


async def setup(bot):
    await bot.add_cog(OnMessage(bot))
