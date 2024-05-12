import random

from discord.ext import commands

from mgylabs.i18n import __

from .utils.MGCert import Level, MGCertificate
from .utils.MsgFormat import MsgFormatter


@commands.command()
@MGCertificate.verify(level=Level.TRUSTED_USERS)
async def yacht(ctx: commands.Context):
    """
    Play simplified version of Yacht Dice!
    """
    dices = [
        ":zero:",
        "1⃣",
        "2⃣",
        "3⃣",
        "4⃣",
        "5⃣",
        ":six:",
    ]
    rolledDice = []

    # run dice
    for i in range(5):
        rand = random.randint(1, 6)
        rolledDice.append(dices[rand])

    botmsg = await ctx.send(
        embed=MsgFormatter.get(
            ctx,
            __("Yacht Dice!"),
            rolledDice.toString(),
        )
    )

    for i in range(5):
        await botmsg.add_reaction(rolledDice[i])
    await botmsg.add_reaction("✅")

    class Game(user1, user2):
        # dice pick.. let's make that later

        def playGame():
            # run n times of turns, and throw dices 3 times (nested loop)
            # end of dice throw, calculate Points -> shoot to GUI
            # end of point selection, calculate bonus point -> total point -> to GUI
            # end of point selection, renew actual point (use Point class)
            # if stopGame is called, stop the game
            pass

        totalPoints = 0
        dices = list()

        def stopGame():
            # 강제 게임 종료
            pass

        def throwDice(self, numberOfDices=5):  # for later dice picking
            # run dice
            for i in range(numberOfDices):
                rand = random.randint(1, 6)
                self.dices.append(dices[rand])
            self.dices.sort()

        # for later..
        # def pickDice(args):
        #    return pickedDice

        def winner():
            pass

    class Points:
        def __init__(self, pickedDice):
            self.run()
            self.ones = 0
            self.twos = 0
            self.threes = 0
            self.fours = 0
            self.fives = 0
            self.sixes = 0
            self.choice = 0
            self.fourOfAKind = 0
            self.fullHouse = 0
            self.sStraight = 0
            self.lStraight = 0
            self.yacht = 0

        # private?
        def sum(pickedDice):
            sum = 0
            for dice in pickedDice:
                sum += dice
            return sum

        def run(self, pickedDice):
            # run all calculations
            self.calcSingles(pickedDice)
            self.calcChoice(pickedDice)
            self.calcFourOfAKind(pickedDice)
            self.calcFullHouse(pickedDice)
            self.calcsStraight(pickedDice)
            self.calclStraight(pickedDice)
            self.calcYacht(pickedDice)

        def calcSingles(self, pickedDice):
            # edit pointDict
            face = 0
            for dice in pickedDice:
                if dice == 1:
                    self.ones += 1
                elif dice == 2:
                    self.twos += 2
                elif dice == 3:
                    self.threes += 3
                elif dice == 4:
                    self.fours += 4
                elif dice == 5:
                    self.fives += 5
                elif dice == 6:
                    self.sixes += 6

        def calcChoice(self, pickedDice):
            self.choice = (
                pickedDice[0]
                + pickedDice[1]
                + pickedDice[2]
                + pickedDice[3]
                + pickedDice[4]
            )

        def calcFourOfAKind(self, pickedDice):
            # 3 3 3 3 1
            if pickedDice[0] == pickedDice[1]:
                if pickedDice[2] == pickedDice[3]:
                    self.fourOfAKind = self.sum(pickedDice)
            elif pickedDice[4] == [3]:
                if pickedDice[1] == [2]:
                    self.fourOfAKind = self.sum(pickedDice)

        def calcFullHouse(self, pickedDice):
            # 2 2 3 3 3
            if pickedDice[0] == pickedDice[1] and pickedDice[3] == pickedDice[4]:
                if pickedDice[2] == pickedDice[1] or pickedDice[2] == pickedDice[3]:
                    self.fullHouse = sum(pickedDice)

        # if not full house, value is already 0

        def calcsStraight(self, pickedDice):
            # 1 2 3 4 / 2 3 4 5 / 3 4 5 6
            if (
                pickedDice[0] + 3
                == pickedDice[1] + 2
                == pickedDice[2] + 1
                == pickedDice[3]
            ):
                self.sStraight = 15
            if (
                pickedDice[1] + 3
                == pickedDice[2] + 2
                == pickedDice[3] + 1
                == pickedDice[4]
            ):
                self.sStraight = 15

        def calclStraight(self, pickedDice):
            # 1 2 3 4 5 / 2 3 4 5 6
            if (
                pickedDice[0] + 4
                == pickedDice[1] + 3
                == pickedDice[2] + 2
                == pickedDice[3] + 1
                == pickedDice[4]
            ):
                self.lStraight = 30

        def calcYacht(self, pickedDice):
            # 6 6 6 6 6
            if (
                pickedDice[0]
                == pickedDice[1]
                == pickedDice[2]
                == pickedDice[3]
                == pickedDice[4]
            ):
                self.yacht = 50

    class GUI:
        # use discord panels
        pass


async def setup(bot: commands.Bot):
    bot.add_command(yacht)
