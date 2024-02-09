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
        rolledDice = []
        pickedDice = []
        def playGame():
            #run n times of turns, and throw dices 3 times (nested loop)
            #initialize points and send calculated points to GUI in the loop
            pointDict = {ones: null, twos: null, threes: null} #continued.. search net
            #send pointDict each time to Points class, 
            #then if user chooses the point, send to actual pointDict
            #if stopGame is called, stop the game
            pass 
        totalPoints = 0
        def stopGame():
            #강제 게임 종료
            pass 
        def organizeDice():
            #organize dice by faces
            pass
        def throwDice (numberOfDices):
            #run dice
            for i in range(numberOfDices):
                rand = random.randint(1, 6)
                self.rolledDice.append(dices[rand])
            return self.rolledDice
        #search up how to use args
        def pickDice(args):
            return pickedDice
        def winner():
            pass
        
    class Points(originPointDict):
        pointDict = dict()
        def __init__():
            run()
        #private?
        def sum(pickedDice):
            sum = 0
            for dice in pickedDice:
                sum += dice
            return sum

        def run(pickedDice):
            #run all calculations that are not finalized
            while key in originPointDict.keys(): #is it key?
                if key != null:
                    pass
                    #run.. ? 널이 아니면 특정 함수를 실행시키는 방법이 있을까? 리스트 생성?
            return pointDict

        def calcSingles(pickedDice, singles):
            #edit pointDict
            for dice in pickedDice:
                if dice == 1:
                    pointDict[singles]+=1
        
        def calcFullHouse(pickedDice):
            if pickedDice[0] == pickedDice[1] and pickedDice[3]==pickedDice[4]:
                if pickedDice[2]==pickedDice[1] or pickedDice[2]==pickedDice[3]:
                    pointDict["fullHouse"] = sum(pickedDice)
            #if not full house, value is already 0
        
        def calcFourOfAKind(pickedDice):
            if pickedDice[0]==pickedDice[1]:
                if pickedDice[2]==pickedDice[3]:
                    pointDict["fourOfAKind"] = self.sum(pickedDice)
            elif pickedDice[4]==[3]:
                if pickedDice[1]==[2]:
                    pointDict["fourOfAKind"] = self.sum(pickedDice)
        
        #todo: how to differentiate null state of points and 0 
        #need to display 0 at times to display what points can be inputted.
        #option 1: use 0s as results in Points dictionary, and use null in playGame dict


        
    class GUI():
        #use discord panels
        pass


async def setup(bot: commands.Bot):
    bot.add_command(yacht)
