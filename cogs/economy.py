import discord
from discord.ext import commands

import os
import random
import asyncio

import motor.motor_asyncio as motor

shop_dict = {
    "1": 500,
    "2": 250,
    "3": 100
}

kai_shop = [892743093911171123, 790448330915840000, 282618575410167818]
shop_reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "❌"]
immune = False

database_password = os.environ.get("DATABASE_PASSWORD")
db_client = motor.AsyncIOMotorClient(database_password)
db = db_client["kai-kicker"]
user_config = db["user_config"]
bot_config = db["bot_config"]


async def get_user_config(user_id):
    config_from_db = await user_config.find_one({"user_id": user_id})

    if config_from_db is None:
        config_from_db = {
            "user_id": user_id,
            "points": 0,
            "nikkah": 0
        }
        await user_config.insert_one(config_from_db)

    config_from_db = {
        user_id: config_from_db
    }

    return config_from_db


async def update_user_config(user_id, new_config):
    old_config = await user_config.find_one({"user_id": user_id})

    if old_config is None:
        config = {
            "user_id": user_id,
            "points": 0,
            "nikkah": 0
        }
        old_config = await user_config.insert_one(config)

    _id = old_config['_id']
    await user_config.replace_one({"_id": _id}, new_config[user_id])


async def get_fs_general_id():
    bot_config_dict = await bot_config.find_one()
    fs_general_id = bot_config_dict["fs_general"]
    print(fs_general_id)
    print(type(fs_general_id))
    return fs_general_id


async def update_fs_general_id(channel_id):
    old_config = await bot_config.find_one()
    old_channel_id = old_config["fs_general"]
    old_config["fs_general"] = channel_id
    await bot_config.replace_one({"fs_general": old_channel_id}, old_config)


def create_shop_log(option: int, cost: int, purchaser: discord.Member, kai: bool = None):
    if kai is None:
        kai = False

    shop_log_embed = discord.Embed(title='', color=0xf8a532)
    embed_value = ''

    if not kai:
        if option == 1:
            embed_value = f'{purchaser.name}#{purchaser.discriminator} bought a ban for Kai for {cost} points.'

        elif option == 2:
            embed_value = f'{purchaser.name}#{purchaser.discriminator} bought a mute for Kai for {cost} points.'

        elif option == 3:
            embed_value = f'{purchaser.name}#{purchaser.discriminator} bought a kick for Kai for {cost} points.'

        elif option == 4:
            embed_value = f'{purchaser.name}#{purchaser.discriminator} bought a nickname change for Kai for {cost} points.'

        elif option == 5:
            embed_value = f'{purchaser.name}#{purchaser.discriminator} bought a spam ping for Kai for {cost} points.'

    else:
        if option == 1:
            embed_value = f'{purchaser.name}#{purchaser.discriminator} bought temporary immunity for {cost} points.'

        elif option == 2:
            embed_value = f'{purchaser.name}#{purchaser.discriminator} bought an unban for {cost} points.'

        elif option == 3:
            embed_value = f'{purchaser.name}#{purchaser.discriminator} bought an unmute for {cost} points.'

        elif option == 4:
            embed_value = f'{purchaser.name}#{purchaser.discriminator} bought an invite reset for {cost} points.'

        elif option == 5:
            embed_value = f'{purchaser.name}#{purchaser.discriminator} bought a nickname reset for {cost} points.'

    shop_log_embed.add_field(name='Shop Log', value=embed_value)
    shop_log_embed.set_footer(text=f'ID: {purchaser.id}')

    return shop_log_embed


def create_embed(color, name, value):
    embed_var = discord.Embed(title='')

    if color == "default":
        embed_var.colour = 0xf8a532
    elif color == "red":
        embed_var.colour = 0xff0000
    elif color == "orange":
        embed_var.colour = 0xff8000
    elif color == "yellow":
        embed_var.colour = 0xffff00
    elif color == "dark green":
        embed_var.colour = 0x228b22
    elif color == "green":
        embed_var.colour = 0x40ff00
    elif color == "cyan":
        embed_var.colour = 0x00ffff
    elif color == "blue":
        embed_var.colour = 0x0040ff
    elif color == "purple":
        embed_var.colour = 0x8000ff
    elif color == "pink":
        embed_var.colour = 0xff69b4

    embed_var.add_field(name=name, value=value)

    return embed_var


class Economy(commands.Cog):
    """Directly related to kai kicker points"""

    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command(brief='View or buy shop items to bully Kai.',
                      description='Click on the buttons to buy shop items that can bully Kai (he deserves it). '
                                  'Nothing will happen if you do not have the amount of points to buy something.')
    async def shop(self, ctx):

        global immune

        bot_config_dict = await bot_config.find_one()
        blacklist = bot_config_dict["shop_blacklist"]
        fs_general = bot_config_dict["fs_general"]

        if ctx.author.id in blacklist:
            raise commands.BadArgument("You are blacklisted from using shop commands.") from None

        elif ctx.author.id in kai_shop:

            config = await get_user_config(ctx.author.id)
            points = config[ctx.author.id]['points']

            shop_embed = discord.Embed(title='Kai Shop', color=0xf8a532)
            shop_embed.add_field(name='Current Balance:', value=f'{points} points', inline=False)
            shop_embed.add_field(name='Options:',
                                 value=f'`1` Random temporary immunity to all purchases — 500 points\n'
                                       f'`2` Unban from FS — 250 points\n'
                                       f'`3` Unmute in FS — 100 points\n'
                                       f'`4` Invite link to FS — 100 points\n'
                                       f'`5` Change username to default — 50 points',
                                 inline=False)
            shop_embed.set_footer(text='React to select an option from above.')

            shop_msg = await ctx.send(embed=shop_embed)

            for reaction in shop_reactions:
                await shop_msg.add_reaction(reaction)

            def check(reaction, user):
                return user == ctx.author

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=15.0, check=check)
                selection = str(reaction.emoji)
            except asyncio.TimeoutError:
                selection = "❌"

            fs = self.bot.get_guild(725749745338941451)
            gen = fs.get_channel(fs_general)
            bot_log = fs.get_channel(730864382065770518)
            kai_user = self.bot.get_user(ctx.author.id)
            kai_member = fs.get_member(ctx.author.id)
            success_embed = discord.Embed(title='', color=0x0fff50)

            if selection == "1️⃣":

                if points < 500:
                    await shop_msg.delete()
                    raise commands.UserInputError(
                        'You currently do not have enough points to buy this, please try again later.') from None

                else:
                    immune = True

                    config[ctx.author.id]['points'] = config[ctx.author.id]['points'] - 500
                    await update_user_config(ctx.author.id, config)

                    immunity_time = random.randint(15, 45)

                    success_embed.add_field(name='Congrats!',
                                            value=f'You have been temporarily granted immunity'
                                                  f' for {immunity_time} minutes!')
                    await ctx.send(embed=success_embed)
                    await shop_msg.delete()

                    success_embed.clear_fields()
                    success_embed.colour = 0xff0000
                    success_embed.add_field(name='Awwwwww!',
                                            value=f'{ctx.author.name}#{ctx.author.discriminator} has bought temporary immunity for {immunity_time} minutes!')
                    await gen.send(embed=success_embed)

                    await asyncio.sleep(immunity_time * 60)
                    immune = False

                    shop_log_embed = create_shop_log(1, 500, ctx.author, True)
                    await bot_log.send(embed=shop_log_embed)

            elif selection == "2️⃣":

                if points < 250:
                    await shop_msg.delete()
                    raise commands.UserInputError(
                        'You currently do not have enough points to buy this, please try again later.') from None

                else:

                    config[ctx.author.id]['points'] = config[ctx.author.id]['points'] - 250
                    await update_user_config(ctx.author.id, config)

                    await fs.unban(kai_user, reason='k!shop moment')

                    success_embed.add_field(name='Congrats!', value='You have successfully unbanned from FS!')
                    await ctx.send(embed=success_embed)
                    await shop_msg.delete()

                    success_embed.clear_fields()
                    success_embed.colour = 0xff0000
                    success_embed.add_field(name='Awwwwww!',
                                            value=f'{ctx.author.name}#{ctx.author.discriminator} has bought an unban!')
                    await gen.send(embed=success_embed)

                    shop_log_embed = create_shop_log(2, 250, ctx.author, True)
                    await bot_log.send(embed=shop_log_embed)

            elif selection == "3️⃣":

                if points < 100:
                    await shop_msg.delete()
                    raise commands.UserInputError(
                        'You currently do not have enough points to buy this, please try again later.') from None

                else:
                    config[ctx.author.id]['points'] = config[ctx.author.id]['points'] - 100
                    await update_user_config(ctx.author.id, config)

                    success_embed.add_field(name='Congrats!', value='You are successfully unmuted on FS!')
                    await ctx.send(embed=success_embed)
                    await shop_msg.delete()

                    success_embed.clear_fields()
                    success_embed.colour = 0xff0000
                    success_embed.add_field(name='Awwwwww!',
                                            value=f'{ctx.author.name}#{ctx.author.discriminator} has bought an unmute!')
                    await gen.send(embed=success_embed)

                    await kai_member.timeout(duration=None, reason="k!shop moment (Kai)")

                    shop_log_embed = create_shop_log(3, 100, ctx.author, True)
                    await bot_log.send(embed=shop_log_embed)

            elif selection == "4️⃣":

                if points < 100:
                    await shop_msg.delete()
                    raise commands.UserInputError(
                        'You currently do not have enough points to buy this, please try again later.') from None

                else:

                    config[ctx.author.id]['points'] = config[ctx.author.id]['points'] - 100
                    await update_user_config(ctx.author.id, config)

                    invite_link = await gen.create_invite(max_uses=3, reason='k!shop moment (Kai)')

                    success_embed.add_field(name='Congrats!',
                                            value=f'You have successfully created an invite link to FS!\n'
                                                  f'Here it is: {invite_link}')
                    await kai_user.send(embed=success_embed)
                    await shop_msg.delete()

                    success_embed.clear_fields()
                    success_embed.colour = 0xff0000
                    success_embed.add_field(name='Awwwwww!',
                                            value=f'{ctx.author.name}#{ctx.author.discriminator} has bought an invite!')

                    await gen.send(embed=success_embed)

                    shop_log_embed = create_shop_log(4, 100, ctx.author, True)
                    await bot_log.send(embed=shop_log_embed)

            elif selection == "5️⃣":

                if points < 50:
                    await shop_msg.delete()
                    raise commands.UserInputError(
                        'You currently do not have enough points to buy this, please try again later.') from None

                else:

                    config[ctx.author.id]['points'] = config[ctx.author.id]['points'] - 50
                    await update_user_config(ctx.author.id, config)

                    await kai_member.edit(nick=kai_user.name)

                    success_embed.add_field(name='Congrats!',
                                            value=f'You have successfully changed your nickname to your'
                                                  f' default username in FS!')
                    await ctx.send(embed=success_embed)
                    await shop_msg.delete()

                    success_embed.clear_fields()
                    success_embed.colour = 0xff0000
                    success_embed.add_field(name='Awwwwww!',
                                            value=f'{ctx.author.name}#{ctx.author.discriminator} has bought a nickname reset!')
                    await gen.send(embed=success_embed)

                    shop_log_embed = create_shop_log(5, 50, ctx.author, True)
                    await bot_log.send(embed=shop_log_embed)

            elif selection == "❌":
                await shop_msg.delete()

        else:

            config = await get_user_config(ctx.author.id)
            points = config[ctx.author.id]['points']

            shop_embed = discord.Embed(title='Shop', color=0xf8a532)
            shop_embed.add_field(name='Current Balance:', value=f'{points} points', inline=False)
            shop_embed.add_field(name='Options:',
                                 value=f'`1` Ban Kai from FS for 15 minutes — 500 points\n'
                                       f'`2` Mute Kai in FS for 10 minutes — 250 points\n'
                                       f'`3` Kick Kai from FS — 100 points\n'
                                       f'`4` Change Kai\'s username in FS — 50 points\n'
                                       f'`5` Spam ping & DM Kai 15 times — 25 points',
                                 inline=False)
            shop_embed.set_footer(text='React to select an option from above.')

            shop_msg = await ctx.send(embed=shop_embed)

            for reaction in shop_reactions:
                await shop_msg.add_reaction(reaction)

            def check(reaction, user):
                global shop_dict
                return user == ctx.author

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=15.0, check=check)
                selection = str(reaction.emoji)
            except asyncio.TimeoutError:
                selection = "❌"

            fs = self.bot.get_guild(725749745338941451)
            gen = fs.get_channel(fs_general)
            kai = fs.get_member(892743093911171123)
            success_embed = discord.Embed(title='', color=0x0fff50)

            if kai is None or immune:
                await shop_msg.delete()
                raise commands.UserInputError(
                    'Kai is currently not in FS right now, or he has purchased temporary immunity. Please try again '
                    'later.')

            elif selection == "1️⃣":

                if points < 500:
                    await shop_msg.delete()
                    raise commands.UserInputError(
                        'You currently do not have enough points to buy this, please try again later.') from None

                else:

                    config[ctx.author.id]['points'] = config[ctx.author.id]['points'] - 500
                    await update_user_config(ctx.author.id, config)

                    if not ctx.channel == gen:
                        success_embed.add_field(name='Congrats!', value='You have successfully banned Kai from FS!')
                        await ctx.send(embed=success_embed)

                    await shop_msg.delete()

                    success_embed.clear_fields()
                    success_embed.colour = 0xff0000
                    success_embed.add_field(name='Awwwwww!', value='A 15 minute ban has been bought for you!')

                    try:
                        await kai.send(embed=success_embed)
                    except:
                        success_embed.set_footer(text='Could not DM Kai.')

                    await fs.ban(user=kai, reason='k!shop moment', delete_message_days=0)

                    success_embed.clear_fields()
                    success_embed.colour = 0x0fff50
                    success_embed.add_field(name='Congrats!',
                                            value=f'{ctx.author.name} has bought a 15 minute ban for Kai!')
                    await gen.send(embed=success_embed)

                    await asyncio.sleep(900)
                    try:
                        await fs.unban(kai, reason='k!shop moment')
                    except:
                        pass

                    shop_log_embed = create_shop_log(1, 500, ctx.author)

                    fs = self.bot.get_guild(725749745338941451)
                    bot_log = fs.get_channel(730864382065770518)

                    await bot_log.send(embed=shop_log_embed)

            elif selection == "2️⃣":

                if points < 250:
                    await shop_msg.delete()
                    raise commands.UserInputError(
                        'You currently do not have enough points to buy this, please try again later.') from None

                else:

                    await kai.timeout(duration=600, reason="k!shop moment")

                    config[ctx.author.id]['points'] = config[ctx.author.id]['points'] - 250
                    await update_user_config(ctx.author.id, config)

                    if not ctx.channel == gen:
                        success_embed.add_field(name='Congrats!', value='You have successfully muted Kai on FS!')
                        await ctx.send(embed=success_embed)
                    await shop_msg.delete()

                    success_embed.clear_fields()
                    success_embed.colour = 0xff0000
                    success_embed.add_field(name='Awwwwww!', value='A 10 minute mute has been bought for you!')

                    try:
                        await kai.send(embed=success_embed)
                    except:
                        success_embed.set_footer(text='Could not DM Kai.')

                    success_embed.clear_fields()
                    success_embed.colour = 0x0fff50
                    success_embed.add_field(name='Congrats!',
                                            value=f'{ctx.author.name} has bought a 10 minute mute for Kai!')
                    await gen.send(embed=success_embed)

                    shop_log_embed = create_shop_log(2, 250, ctx.author)

                    fs = self.bot.get_guild(725749745338941451)
                    bot_log = fs.get_channel(730864382065770518)

                    await bot_log.send(embed=shop_log_embed)

            elif selection == "3️⃣":

                if points < 100:
                    await shop_msg.delete()
                    raise commands.UserInputError(
                        'You currently do not have enough points to buy this, please try again later.') from None

                else:
                    config[ctx.author.id]['points'] = config[ctx.author.id]['points'] - 100
                    await update_user_config(ctx.author.id, config)

                    if not ctx.channel == gen:
                        success_embed.add_field(name='Congrats!', value='You have successfully kicked Kai from FS!')
                        await ctx.send(embed=success_embed)
                    await shop_msg.delete()

                    success_embed.clear_fields()
                    success_embed.colour = 0xff0000
                    success_embed.add_field(name='Awwwwww!', value='A kick has been bought for you!')

                    try:
                        await kai.send(embed=success_embed)
                    except:
                        success_embed.set_footer(text='Could not DM Kai.')

                    await kai.kick(reason='k!shop moment')

                    success_embed.clear_fields()
                    success_embed.colour = 0x0fff50
                    success_embed.add_field(name='Congrats!', value=f'{ctx.author.name} has bought a kick for Kai!')
                    await gen.send(embed=success_embed)

                    shop_log_embed = create_shop_log(3, 100, ctx.author)

                    fs = self.bot.get_guild(725749745338941451)
                    bot_log = fs.get_channel(730864382065770518)

                    await bot_log.send(embed=shop_log_embed)

            elif selection == "4️⃣":

                if points < 50:
                    await shop_msg.delete()
                    raise commands.UserInputError(
                        'You currently do not have enough points to buy this, please try again later.') from None

                else:

                    shop_embed.clear_fields()
                    shop_embed.add_field(name='Nickname Selection',
                                         value='Please enter the nickname you\'d like to choose for Kai. Please make '
                                               'sure that it is less than 32 characters.')
                    await shop_msg.edit(embed=shop_embed)

                    def nick_check(message):
                        return message.author == ctx.author and len(message.content) <= 32

                    msg = await self.bot.wait_for('message', check=nick_check)

                    await kai.edit(nick=msg.content)

                    config[ctx.author.id]['points'] = config[ctx.author.id]['points'] - 50
                    await update_user_config(ctx.author.id, config)

                    if not ctx.channel == gen:
                        success_embed.add_field(name='Congrats!',
                                                value=f'You have successfully changed Kai\'s username to {msg.content} in '
                                                      f'FS!')
                        await ctx.send(embed=success_embed)
                    await shop_msg.delete()

                    success_embed.clear_fields()
                    success_embed.colour = 0xff0000
                    success_embed.add_field(name='Awwwwww!',
                                            value=f'A nickname change has been bought for you! Your'
                                                  f' nickname is now {msg.content}.')

                    try:
                        await kai.send(embed=success_embed)
                    except:
                        success_embed.set_footer(text='Could not DM Kai.')

                    success_embed.clear_fields()
                    success_embed.colour = 0x0fff50
                    success_embed.add_field(name='Congrats!',
                                            value=f'{ctx.author.name} has bought a nickname change for Kai! His '
                                                  f'nickname is now {msg.content}.')
                    await gen.send(embed=success_embed)

                    shop_log_embed = create_shop_log(4, 50, ctx.author)

                    fs = self.bot.get_guild(725749745338941451)
                    bot_log = fs.get_channel(730864382065770518)

                    await bot_log.send(embed=shop_log_embed)

            elif selection == "5️⃣":

                if points < 25:
                    await shop_msg.delete()
                    raise commands.UserInputError(
                        'You currently do not have enough points to buy this, please try again later.') from None

                else:

                    config[ctx.author.id]['points'] = config[ctx.author.id]['points'] - 25
                    await update_user_config(ctx.author.id, config)

                    if not ctx.channel == gen:
                        success_embed.add_field(name='Congrats!',
                                                value='You have successfully spam pinged Kai in multiple servers!')
                        await ctx.send(embed=success_embed)
                    await shop_msg.delete()

                    success_embed.clear_fields()
                    success_embed.colour = 0xff0000
                    success_embed.add_field(name='Awwwwww!', value='A spam ping has been bought for you!')

                    try:
                        await kai.send(embed=success_embed)
                    except:
                        success_embed.set_footer(text='Could not DM Kai.')

                    success_embed.clear_fields()
                    success_embed.colour = 0x0fff50
                    success_embed.add_field(name='Congrats!',
                                            value=f'{ctx.author.name} has bought a spam ping for Kai!')
                    await gen.send(embed=success_embed)

                    shop_log_embed = create_shop_log(5, 25, ctx.author)

                    fs = self.bot.get_guild(725749745338941451)
                    bot_log = fs.get_channel(730864382065770518)

                    await bot_log.send(embed=shop_log_embed)

                    for i in range(5):
                        await ctx.send(kai.mention)
                        await asyncio.sleep(0.1)

                        await gen.send(kai.mention)
                        await asyncio.sleep(0.1)

                        try:
                            await kai.send(kai.mention)
                            await asyncio.sleep(0.1)
                        except:
                            print('Kai has bot blocked')

            elif selection == "❌":
                await shop_msg.delete()

    @commands.command(aliases=['wallet', 'wal', 'balance', 'bal'],
                      brief='View your current amount of points.',
                      description='View your current amount of points. '
                                  'You can use these points through `k!shop` or through the minigames.')
    async def points(self, ctx, user: discord.User = None):
        if user is None:
            user = ctx.author

        config = await get_user_config(user.id)
        balance_embed = create_embed("green", "Balance:", f"{user.name} currently has "
                                                          f"`{config[user.id]['points']} points`.")
        await ctx.send(embed=balance_embed)

    @commands.command(aliases=['pay'],
                      brief='Pay other users.',
                      description='Pay other users the amount you specify. '
                                  'Note that you cannot pay a negative or zero amount of points.')
    async def give(self, ctx, receiver: discord.User, amount: int):
        if receiver == ctx.author:
            raise commands.UserInputError('You cannot give yourself money!')

        sender_config = await get_user_config(ctx.author.id)
        receiver_config = await get_user_config(receiver.id)

        points = sender_config[ctx.author.id]['points']

        if amount > points:
            raise commands.UserInputError('You do not have enough points to send. '
                                          'Please try again with a different amount.')

        elif amount <= 0:
            raise commands.UserInputError('You cannot give a negative or zero amount of points.')

        else:

            sender_config[ctx.author.id]['points'] -= amount
            receiver_config[receiver.id]['points'] += amount

            await update_user_config(ctx.author.id, sender_config)
            await update_user_config(receiver.id, receiver_config)

            payment_embed = create_embed('green', 'Successfully paid!', f'You have successfully paid '
                                                                        f'{receiver.name} `{amount} points.`')
            await ctx.send(embed=payment_embed)

            log_embed = create_embed('default', 'Transaction', f'`{ctx.author.name}#{ctx.author.discriminator}` paid '
                                                               f'`{receiver.name}#{receiver.discriminator}` {amount} points.')
            log_embed.set_footer(text=f'Sender ID: {ctx.author.id}\nReceiver ID: {receiver.id}')

            fs = self.bot.get_guild(725749745338941451)
            bot_log = fs.get_channel(730864382065770518)

            await bot_log.send(embed=log_embed)

    @commands.command(aliases=['sp', 'setbalance', 'sb'],
                      brief='Set the points of other users',
                      description='Set points of other users with the specified value')
    @commands.has_role(728309144452464731)
    async def setpoints(self, ctx, user: discord.User, amount: int):

        if ctx.author == user:
            raise commands.UserInputError("You cannot set the amount of points for yourself.")

        else:
            user_config = await get_user_config(user.id)
            user_config[user.id]['points'] = amount
            await update_user_config(user.id, user_config)

            await ctx.send(f'Successfully set {user.name}#{user.discriminator} balance to {amount} points.')

    @commands.command(aliases=['fsgen', 'gen'],
                      brief='Update FS general channel',
                      description='Update the channel for k!shop messages whenever someone buys something.')
    @commands.has_role(728309144452464731)
    async def fsgeneral(self, ctx, channel:discord.TextChannel):

        await update_fs_general_id(channel.id)
        update_embed = create_embed("green", "Sucessfully Updated", f'FS general channel updated to {channel.mention}.')
        await ctx.send(embed=update_embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))
