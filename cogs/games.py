import discord
from discord.ext import commands

import os
import random
import pydealer
import asyncio

from typing import List
from cogs.economy import create_embed
import motor.motor_asyncio as motor

database_password = os.environ.get("DATABASE_PASSWORD")
db_client = motor.AsyncIOMotorClient(database_password)
db = db_client["kai-kicker"]
user_config = db["user_config"]

enemy_list = ["Discord Mods", "Discord Trolls", "me lon", "Discord Creeps"]
enemy_dict = {
    "Discord Mods": "❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ",
    "Discord Trolls": "❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ",
    "me lon": "❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ❤️ ",
    "Discord Creeps": "❤️ ❤️ ❤️ ❤️ ❤️ ",
}

BLACKJACK_RANK = {
    "Ace": 11,
    "King": 10,
    "Queen": 10,
    "Jack": 10,
    "10": 10,
    "9": 9,
    "8": 8,
    "7": 7,
    "6": 6,
    "5": 5,
    "4": 4,
    "3": 3,
    "2": 2,
    "1": 1
}


async def get_user_config(user_id):
    config_from_db = await user_config.find_one({"user_id": user_id})

    if config_from_db is None:
        config = {
            "user_id": user_id,
            "points": 0,
            "nikkah": 0
        }
        await user_config.insert_one(config)

    config = {
        user_id: config_from_db
    }

    return config


async def update_user_config(user_id, new_config):
    old_config = await user_config.find_one({"user_id": user_id})
    _id = old_config['_id']

    await user_config.replace_one({"_id": _id}, new_config[user_id])


def get_hand_value(hand: pydealer.Stack):
    value = 0
    num_of_ace = 0
    list_of_cards = []

    for card in hand.cards:
        list_of_cards.append(f'`{card.value} of {card.suit}`')

        if card.value != "Ace":
            value += BLACKJACK_RANK[card.value]
        else:
            num_of_ace += 1

    for ace in range(num_of_ace):
        value += 11
        if value > 21:
            value -= 10

    hand_dict = {
        "cards_list": list_of_cards,
        "cards_string": "\n".join(list_of_cards),
        "value": value
    }

    return hand_dict


class Enemy(discord.ui.View):

    def __init__(self, embed: discord.Embed, enemy: str, summoner: discord.Member, bot):
        super().__init__()
        global enemy_dict
        self.embed = embed
        self.embed_value = enemy_dict[enemy]
        self.enemy = enemy
        self.summoner = summoner
        self.temp_config = {}
        self.bot = bot

    @discord.ui.button(label='Attack!', emoji='⚔️', style=discord.ButtonStyle.red)
    async def callback(self, button, interaction):

        if '❤️' in self.embed_value:
            self.embed_value = self.embed_value[3:]

        if self.embed_value == '':
            self.embed_value = 'Boss defeated!'
            self.embed.colour = 0x0fff50

            button.style = discord.ButtonStyle.green
            button.label = 'Defeated!'
            button.emoji = '✅'
            button.disabled = True
            boss_log = create_embed("default", f"{self.enemy} defeated in {self.summoner.guild.name} ({self.summoner.guild.id})",
                                    f"Summoner: {self.summoner.name}#{self.summoner.discriminator} ({self.summoner.id})")
            embed_value = ''

            for key in self.temp_config:
                config = await get_user_config(key)
                config[key]['points'] += self.temp_config[key]['points']
                await update_user_config(key, config)

                member = interaction.guild.get_member(key)
                embed_value += f'{member.name}#{member.discriminator} ({member.id}): {self.temp_config[key]["points"]} points\n'

            boss_log.add_field(name='Points Breakdown', value=embed_value, inline=False)

            fs = self.bot.get_guild(725749745338941451)
            bot_log = fs.get_channel(730864382065770518)

            await bot_log.send(embed=boss_log)

            self.stop()

        if self.embed_value == "Boss defeated!":
            button.disabled = True

        self.embed.clear_fields()
        self.embed.add_field(name=f'Oh no! {self.summoner.name} summoned {self.enemy}!',
                             value=self.embed_value)

        await interaction.response.edit_message(embed=self.embed, view=self)

        try:
            self.temp_config[interaction.user.id]['points'] = self.temp_config[interaction.user.id]['points'] + 5
        except KeyError:
            new_config = {
                interaction.user.id:
                    {
                        'points': 5
                    }
            }

            self.temp_config = {**self.temp_config, **new_config}


class AcceptDeny(discord.ui.View):

    def __init__(self, requester: discord.Member, requestee: discord.Member, cost: int, sec_view: discord.ui.View):
        super().__init__(timeout=60)
        self.requester = requester
        self.requestee = requestee
        self.cost = cost
        self.sec_view = sec_view

    @discord.ui.button(label='Accept', style=discord.ButtonStyle.green)
    async def accept(self, button, interaction):
        if interaction.user != self.requestee:
            return
        else:

            config_requestee = await get_user_config(self.requestee.id)
            points_requestee = config_requestee[self.requestee.id]['points']

            if points_requestee >= self.cost:

                accepted = create_embed("green", "Challenge accepted!",
                                        f"{interaction.user.name} is now playing with {self.requester.name}!")
                self.sec_view.message = await interaction.response.edit_message(embed=accepted, view=self.sec_view)

            else:
                error = create_embed("red", "Could not continue challenge!",
                                     f"{self.requestee.name} does not have enough to bet {self.cost} points!")
                self.clear_items()
                await interaction.response.edit_message(embed=error, view=self)

    @discord.ui.button(label='Reject', style=discord.ButtonStyle.red)
    async def reject(self, button, interaction):
        if interaction.user != self.requestee:
            return
        else:
            self.clear_items()
            rejected = create_embed("red", "Challenge denied!",
                                    f"{interaction.user.name} has decided to not play with {self.requester.name}!")
            await interaction.response.edit_message(embed=rejected, view=self)

    async def on_timeout(self) -> None:
        timeout = create_embed("red", "Timed out!", "Request has timed out! Please be quicker next time.")
        self.clear_items()
        try:
            await self.message.edit(embed=timeout, view=self)
        except:
            return


class TicTacToeButton(discord.ui.Button['TicTacToe']):
    def __init__(self, x: int, y: int, challenger: discord.Member, opponent: discord.Member, bet: int, bot):
        super().__init__(style=discord.ButtonStyle.secondary, label='\u200b', row=y)
        self.x = x
        self.y = y
        self.challenger = challenger
        self.opponent = opponent
        self.bet = bet
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: TicTacToe = self.view
        state = view.board[self.y][self.x]
        if state in (view.X, view.O):
            return

        if view.current_player == view.X:
            if interaction.user != self.challenger:
                return
            self.style = discord.ButtonStyle.danger
            self.label = 'X'
            self.disabled = True
            view.board[self.y][self.x] = view.X
            view.current_player = view.O
            content = f"It is now {self.opponent.name}'s turn"
        else:
            if interaction.user != self.opponent:
                return
            self.style = discord.ButtonStyle.success
            self.label = 'O'
            self.disabled = True
            view.board[self.y][self.x] = view.O
            view.current_player = view.X
            content = f"It is now {self.challenger.name}'s turn"

        winner = view.check_board_winner()
        if winner is not None:
            if winner == view.X:
                content = f'{self.challenger.name} won the challenge!'

                challenger_config = await get_user_config(self.challenger.id)
                challenger_config[self.challenger.id]['points'] += self.bet
                await update_user_config(self.challenger.id, challenger_config)

                opponent_config = await get_user_config(self.opponent.id)
                opponent_config[self.opponent.id]['points'] -= self.bet
                await update_user_config(self.opponent.id, opponent_config)
                embed_value = f'Winner: {self.challenger.name}#{self.challenger.discriminator}\n' \
                              f'Loser: {self.opponent.name}#{self.opponent.discriminator}\n\n' \
                              f'Challenger: {self.challenger.name}#{self.challenger.discriminator} ({self.challenger.id})\n' \
                              f'Opponent: {self.opponent.name}#{self.opponent.discriminator} ({self.opponent.id})\n\n' \
                              f'Bet: {self.bet} points'

            elif winner == view.O:
                content = f'{self.opponent.name} won the challenge!'

                opponent_config = await get_user_config(self.opponent.id)
                opponent_config[self.opponent.id]['points'] += self.bet
                await update_user_config(self.opponent.id, opponent_config)

                challenger_config = await get_user_config(self.challenger.id)
                challenger_config[self.challenger.id]['points'] -= self.bet
                await update_user_config(self.challenger.id, challenger_config)

                embed_value = f'Winner: {self.opponent.name}#{self.opponent.discriminator}\n' \
                              f'Loser: {self.challenger.name}#{self.challenger.discriminator}\n\n' \
                              f'Challenger: {self.challenger.name}#{self.challenger.discriminator} ({self.challenger.id})\n' \
                              f'Opponent: {self.opponent.name}#{self.opponent.discriminator} ({self.opponent.id})\n\n' \
                              f'Bet: {self.bet} points'

            else:
                content = "It's a tie!"
                embed_value = f'Tie between {self.opponent.name}#{self.opponent.discriminator} ' \
                              f'and {self.challenger.name}#{self.challenger.discriminator}\n\n' \
                              f'Challenger: {self.challenger.name}#{self.challenger.discriminator} ({self.challenger.id})\n' \
                              f'Opponent: {self.opponent.name}#{self.opponent.discriminator} ({self.opponent.id})\n\n' \
                              f'Bet: {self.bet} points'

            for child in view.children:
                child.disabled = True

            tictactoe_log = discord.Embed(title='', color=0xf8a532)
            tictactoe_log.add_field(name='Tic-Tac-Toe Log', value=embed_value)

            fs = self.bot.get_guild(725749745338941451)
            bot_log = fs.get_channel(730864382065770518)

            await bot_log.send(embed=tictactoe_log)

            view.stop()

        await interaction.response.edit_message(content=content, view=view)


class TicTacToe(discord.ui.View):
    children: List[TicTacToeButton]
    X = -1
    O = 1
    Tie = 2

    def __init__(self, challenger: discord.Member, opponent: discord.Member, bet: int, bot):
        super().__init__(timeout=60)
        self.current_player = self.X
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        self.challenger = challenger
        self.opponent = opponent
        self.bet = bet

        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y, challenger, opponent, bet, bot))

    def check_board_winner(self):
        for across in self.board:
            value = sum(across)
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        for line in range(3):
            value = self.board[0][line] + self.board[1][line] + self.board[2][line]
            if value == 3:
                return self.O
            elif value == -3:
                return self.X

        diag = self.board[0][2] + self.board[1][1] + self.board[2][0]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        diag = self.board[0][0] + self.board[1][1] + self.board[2][2]
        if diag == 3:
            return self.O
        elif diag == -3:
            return self.X

        if all(i != 0 for row in self.board for i in row):
            return self.Tie

        return None

    async def on_timeout(self) -> None:

        timeout = create_embed("red", "Timed out!", "Game has timed out! Please be quicker next time.")
        self.clear_items()

        try:
            await self.message.edit(embed=timeout, view=self)
        except:
            return


class Blackjack(discord.ui.View):

    def __init__(self, player_hand: pydealer.Stack, dealer_hand: pydealer.Stack, deck: pydealer.Deck, bet: int,
                 player: discord.Member, bot):
        super().__init__(timeout=60)
        self.player = player
        self.player_hand = player_hand
        self.dealer_draw = True
        self.dealer_hand = dealer_hand
        self.deck = deck
        self.bet = bet
        self.bot = bot

    @discord.ui.button(label='Hit', style=discord.ButtonStyle.red)
    async def hit_callback(self, button, interaction):

        if interaction.user != self.player:
            return

        self.player_hand += self.deck.deal(1)
        player_dict = get_hand_value(self.player_hand)
        dealer_dict = get_hand_value(self.dealer_hand)

        player_value = player_dict['value']
        dealer_value = dealer_dict['value']

        blackjack_embed = create_embed("default", "Your Cards:", f'{player_dict["cards_string"]}\n\n'
                                                                 f'**Total:** `{player_dict["value"]}`\n')
        blackjack_embed.add_field(name='Dealer Cards:', value=f'{dealer_dict["cards_string"]}')

        if player_value > 21:
            blackjack_embed.add_field(name=f'Lost {self.bet} points.',
                                      value=f'Oh no! You got more than 21 points, you lost your bet!', inline=False)

            config = await get_user_config(self.player.id)
            config[self.player.id]["points"] -= self.bet
            config[self.player.id]['game_in_progress'] = False
            await update_user_config(self.player.id, config)

            blackjack_log = discord.Embed(title='', color=0xf8a532)
            embed_value = f'Result: Lost (busted)\nBet: {self.bet}'
            blackjack_log.add_field(name=f'Blackjack game with {self.player.name}#{self.player.discriminator}',
                                    value=embed_value)
            blackjack_log.set_footer(text=f'User ID: {self.player.id}')

            fs = self.bot.get_guild(725749745338941451)
            bot_log = fs.get_channel(730864382065770518)

            await bot_log.send(embed=blackjack_log)

            self.clear_items()
            self.stop()

        elif player_value == 21:
            blackjack_embed.add_field(name='Congrats!', value='You get exactly 21 points, you win the bet!',
                                      inline=False)

            config = await get_user_config(self.player.id)
            config[self.player.id]["points"] += self.bet
            config[self.player.id]['game_in_progress'] = False
            await update_user_config(self.player.id, config)

            blackjack_log = discord.Embed(title='', color=0xf8a532)
            embed_value = f'Result: Won (exactly 21)\nBet: {self.bet}'
            blackjack_log.add_field(name=f'Blackjack game with {self.player.name}#{self.player.discriminator}',
                                    value=embed_value)
            blackjack_log.set_footer(text=f'User ID: {self.player.id}')

            fs = self.bot.get_guild(725749745338941451)
            bot_log = fs.get_channel(730864382065770518)

            await bot_log.send(embed=blackjack_log)

            self.clear_items()
            self.stop()

        await interaction.response.edit_message(embed=blackjack_embed, view=self)

    @discord.ui.button(label='Stand', style=discord.ButtonStyle.blurple)
    async def stay_callback(self, button, interaction):

        if interaction.user != self.player:
            return

        self.hit_callback.disabled = True
        button.label = 'Stand'

        self.dealer_hand += self.deck.deal(1)

        player_dict = get_hand_value(self.player_hand)
        dealer_dict = get_hand_value(self.dealer_hand)

        player_value = player_dict['value']
        dealer_value = dealer_dict['value']

        blackjack_embed = create_embed("default", "Your Cards:", f'{player_dict["cards_string"]}\n\n'
                                                                 f'**Total:** `{player_dict["value"]}`\n')
        blackjack_embed.add_field(name='Dealer Cards:', value=f'{dealer_dict["cards_string"]}\n\n'
                                                              f'**Total:** `{dealer_dict["value"]}`\n')

        if dealer_value > 21:
            blackjack_embed.add_field(name='Congrats!', value='The dealer busted, you win the bet!',
                                      inline=False)

            config = await get_user_config(self.player.id)
            config[self.player.id]["points"] += self.bet
            config[self.player.id]['game_in_progress'] = False
            await update_user_config(self.player.id, config)

            blackjack_log = discord.Embed(title='', color=0xf8a532)
            embed_value = f'Result: Won (dealer busted)\nBet: {self.bet}'
            blackjack_log.add_field(name=f'Blackjack game with {self.player.name}#{self.player.discriminator}',
                                    value=embed_value)
            blackjack_log.set_footer(text=f'User ID: {self.player.id}')

            fs = self.bot.get_guild(725749745338941451)
            bot_log = fs.get_channel(730864382065770518)

            await bot_log.send(embed=blackjack_log)

            self.clear_items()
            self.stop()

        elif dealer_value < 17:
            blackjack_embed.add_field(name='Dealer drawing another card...', value='The dealer drew less than 17!',
                                      inline=False)
            button.label = "Continue..."

        else:
            if dealer_value > player_value:

                blackjack_embed.add_field(name=f'Lost {self.bet} points.',
                                          value=f'Oh no! The dealer got more than you, you lost your bet!',
                                          inline=False)

                config = await get_user_config(self.player.id)
                config[self.player.id]["points"] -= self.bet
                config[self.player.id]['game_in_progress'] = False
                await update_user_config(self.player.id, config)

                blackjack_log = discord.Embed(title='', color=0xf8a532)
                embed_value = f'Result: Lost (dealer more points)\nBet: {self.bet}'
                blackjack_log.add_field(name=f'Blackjack game with {self.player.name}#{self.player.discriminator}',
                                        value=embed_value)
                blackjack_log.set_footer(text=f'User ID: {self.player.id}')

                fs = self.bot.get_guild(725749745338941451)
                bot_log = fs.get_channel(730864382065770518)

                await bot_log.send(embed=blackjack_log)

                self.clear_items()
                self.stop()

            elif dealer_value == player_value:

                blackjack_embed.add_field(name=f'Draw!.',
                                          value=f'Oh no! You got the same amount of points, you keep your bet!',
                                          inline=False)

                config = await get_user_config(self.player.id)
                config[self.player.id]['game_in_progress'] = False
                await update_user_config(self.player.id, config)

                blackjack_log = discord.Embed(title='', color=0xf8a532)
                embed_value = f'Result: Tie (same points)\nBet: {self.bet}'
                blackjack_log.add_field(name=f'Blackjack game with {self.player.name}#{self.player.discriminator}',
                                        value=embed_value)
                blackjack_log.set_footer(text=f'User ID: {self.player.id}')

                fs = self.bot.get_guild(725749745338941451)
                bot_log = fs.get_channel(730864382065770518)

                await bot_log.send(embed=blackjack_log)

                self.clear_items()
                self.stop()

            else:
                blackjack_embed.add_field(name='Congrats!',
                                          value='You got more than the dealer, you win the bet!',
                                          inline=False)

                config = await get_user_config(self.player.id)
                config[self.player.id]["points"] += self.bet
                config[self.player.id]['game_in_progress'] = False
                await update_user_config(self.player.id, config)

                blackjack_log = discord.Embed(title='', color=0xf8a532)
                embed_value = f'Result: Won (points more than dealer)\nBet: {self.bet}'
                blackjack_log.add_field(name=f'Blackjack game with {self.player.name}#{self.player.discriminator}',
                                        value=embed_value)
                blackjack_log.set_footer(text=f'User ID: {self.player.id}')

                fs = self.bot.get_guild(725749745338941451)
                bot_log = fs.get_channel(730864382065770518)

                await bot_log.send(embed=blackjack_log)

                self.clear_items()
                self.stop()

        await interaction.response.edit_message(embed=blackjack_embed, view=self)

    async def on_timeout(self) -> None:

        timeout = create_embed("red", "Timed out!", "Game has timed out! Please be quicker next time.")
        self.clear_items()

        config = await get_user_config(self.player.id)
        config[self.player.id]['game_in_progress'] = False
        await update_user_config(self.player.id, config)

        try:
            await self.message.edit(embed=timeout, view=self)
        except:
            return


class Games(commands.Cog):
    """Various mini-games that you can play by yourself or with others"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief='Summon a boss to fight.',
                      description='Summon a boss to fight. Each damage you do gives you 5 points. '
                                  'Summoning a boss gives you 15. Bosses can only be summoned every 30 minutes.')
    @commands.cooldown(1, 1800, commands.BucketType.default)
    async def boss(self, ctx):
        config = await get_user_config(ctx.author.id)
        config[ctx.author.id]['points'] = config[ctx.author.id]['points'] + 15
        await update_user_config(ctx.author.id, config)

        global enemy_dict

        boss_embed = discord.Embed(title='', color=0xff0000)
        boss_embed.add_field(name=f'Oh no! {ctx.author.name} summoned Discord Mods!',
                             value=f'{enemy_dict["Discord Mods"]}')

        view = Enemy(boss_embed, "Discord Mods", ctx.author, self.bot)

        await ctx.send(embed=boss_embed, view=view)

    @boss.error
    async def boss_error(self, ctx, error):
        boss_error = discord.Embed(title='', color=0xff0000)
        boss_error.add_field(name='Error: Already Summoned',
                             value=f"```A boss has already been recently summoned, please try again"
                                   f" in {round(error.retry_after / 60, 1)} minutes.```")
        message = await ctx.send(embed=boss_error)
        await asyncio.sleep(10)
        await message.delete()

    @commands.command(brief='Summons a random type of enemy.',
                      description='Summons a random type of enemy for you. '
                                  'Note that bosses cannot be spawned with this, nor do you get points for summoning. '
                                  'This command has a per-user cooldown of 10-minutes.')
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def summon(self, ctx):

        global enemy_list, enemy_dict
        enemy_name = enemy_list[random.randint(1, 3)]
        enemy_hearts = enemy_dict[enemy_name]

        enemy_embed = discord.Embed(title='', color=0xff0000)
        enemy_embed.add_field(name=f'Oh no! {ctx.author.name} summoned {enemy_name}!',
                              value=f'{enemy_hearts}')

        view = Enemy(enemy_embed, enemy_name, ctx.author, self.bot)

        await ctx.send(embed=enemy_embed, view=view)

    @commands.command(brief='Challenge someone to play tic-tac-toe.',
                      description='Challenge and bet someone to play tic-tac-toe. Default bet value is 0. '
                                  'Both users will have to bet the same amount. Winner takes all.')
    async def tictactoe(self, ctx, opponent: discord.Member, bet: int = 0):

        if opponent == ctx.author:
            raise commands.UserInputError("You cannot challenge yourself!")

        else:

            config = await get_user_config(ctx.author.id)
            points = config[ctx.author.id]['points']

            if bet < 0:
                raise commands.UserInputError('You cannot bet with a negative amount of points.')

            elif points >= bet:
                initial_embed = create_embed("default", "Duel!",
                                             f"{ctx.author.mention} challenges you ({opponent.mention}) "
                                             f"to a round of tic-tac-toe. Do you accept?\n"
                                             f"Bet: {bet}")

                tictactoe_view = TicTacToe(ctx.author, opponent, bet, self.bot)
                request_view = AcceptDeny(ctx.author, opponent, bet, tictactoe_view)

                request_view.message = await ctx.send(embed=initial_embed, view=request_view)

            else:
                raise commands.UserInputError(f"You do not have enough to bet {bet} points.")

    @commands.command(brief='Play blackjack with the bot.',
                      description='Bet to play blackjack against the bot with a minimum bet value of 20.'
                                  ' Maximum bet value is 100, winner takes all.',
                      aliases=['bj'])
    async def blackjack(self, ctx, bet: int = 20):

        config = await get_user_config(ctx.author.id)
        points = config[ctx.author.id]['points']

        try:
            game_in_progress = config[ctx.author.id]['game_in_progress']
        except:
            game_in_progress = False

        if game_in_progress:
            raise commands.UserInputError(f'You cannot have two games running at once! '
                                          f'Please use k!unlock if this is an error.')

        elif bet < 20:
            raise commands.UserInputError(f"You need to bet more than 20 points.")

        elif bet > 5000:
            raise commands.UserInputError(f"You cannot bet over 5000 points.")

        elif points >= bet:

            config[ctx.author.id]['game_in_progress'] = True
            await update_user_config(ctx.author.id, config)

            deck = pydealer.Deck(joker=False)
            deck.shuffle()

            player_hand = pydealer.Stack(ranks=BLACKJACK_RANK)
            player_hand = deck.deal(2)

            dealer_hand = pydealer.Stack(ranks=BLACKJACK_RANK)
            dealer_hand += deck.deal(1)

            player_dict = get_hand_value(player_hand)
            dealer_dict = get_hand_value(dealer_hand)

            blackjack_embed = create_embed("default", "Your Cards:", f'{player_dict["cards_string"]}\n\n'
                                                                     f'**Total:** `{player_dict["value"]}`')
            blackjack_embed.add_field(name='Dealer Cards:', value=f'{dealer_dict["cards_string"]}')

            if player_dict["value"] == 21:

                blackjack_embed.add_field(name='Congrats!',
                                          value='You get exactly 21 points, you win twice of the bet!',
                                          inline=False)
                await ctx.send(embed=blackjack_embed)

                config = await get_user_config(ctx.author.id)
                config[ctx.author.id]["points"] += 2 * bet
                config[ctx.author.id]['game_in_progress'] = False
                await update_user_config(ctx.author.id, config)

                blackjack_log = discord.Embed(title='', color=0xf8a532)
                embed_value = f'Result: Won (21 first try)\nBet: {bet}'
                blackjack_log.add_field(name=f'Blackjack game with {ctx.author.name}#{ctx.author.discriminator}',
                                        value=embed_value)
                blackjack_log.set_footer(text=f'User ID: {ctx.author.id}')

                fs = self.bot.get_guild(725749745338941451)
                bot_log = fs.get_channel(730864382065770518)

                await bot_log.send(embed=blackjack_log)

            else:
                blackjack_view = Blackjack(player_hand=player_hand, dealer_hand=dealer_hand, deck=deck, bet=bet,
                                           player=ctx.author, bot=self.bot)
                blackjack_view.message = await ctx.send(embed=blackjack_embed, view=blackjack_view)

        else:
            raise commands.UserInputError(f"You do not have enough to bet {bet} points.")

    @commands.command(brief='Unlocks you from playing more than one game.',
                      description='Unlocks you from playing more than one game. Per-user cooldown of 10-minutes. '
                                  'Meant to be used if you cannot play blackjack due to the more than one game error, '
                                  'even if you are playing just one game.')
    @commands.cooldown(1, 18000, commands.BucketType.user)
    async def unlock(self, ctx):

        config = await get_user_config(ctx.author.id)
        config[ctx.author.id]['game_in_progress'] = False
        await update_user_config(ctx.author.id, config)

        await ctx.send('Unlocked!')


async def setup(bot):
    await bot.add_cog(Games(bot))
