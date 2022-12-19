import random


class Hangman:
    def __init__(self) -> None:
        self.word = ""
        self.hiddenLetters = []
        self.usedLetters = ""
        self.VALID_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.lives = 0
        self.debug = False
        self.send = None

    def render(self, builder: list, sep="\n"):
        return sep.join(builder)

    def initialiseVariables(self):
        # get the word
        self.word = self.getWordFromFile()
        # initialise hiddenLetters to be underscores equal to the length of word
        self.hiddenLetters = []
        for i in range(len(self.word)):
            if self.word[i] == "-":
                self.hiddenLetters.append("-")
            else:
                self.hiddenLetters.append("_")
        # initialise usedLetters to be an empty string
        self.usedLetters = ""
        # set lives to zero
        self.lives = 0
        # initialise number of vowels

    def getWordFromFile(self):
        from .constants.nouns import nouns

        # Select the word from wordList
        word = random.choice(nouns)
        word = word.replace(" ", "-")
        # Convert the word to uppercase and return the word
        word = word.upper()
        return word

    def displayScreen(self):
        builder = []
        # give some space above
        builder.append("")
        builder.append("")
        # display the cartoon
        builder.append(self.displayCartoon())
        # display a list of used letters
        builder.append("")
        builder.append(self.displayUsedCharacters())
        # enter debug mode
        if self.debug:
            builder.append("Debugging mode")
            builder.append(self.word)

        return self.render(builder)

    def displayCartoon(self):
        builder = []

        cartoon = [[] for i in range(12)]
        cartoon[0] = [
            "           ",
            "           ",
            "           ",
            "           ",
            "           ",
            "           ",
            "           ",
            "           ",
        ]
        cartoon[1] = [
            "           ",
            "           ",
            "           ",
            "           ",
            "           ",
            "           ",
            "           ",
            "___________",
        ]
        cartoon[2] = [
            "    |      ",
            "    |      ",
            "    |      ",
            "    |      ",
            "    |      ",
            "    |      ",
            "    |      ",
            "____|______",
        ]
        cartoon[3] = [
            "    |----  ",
            "    |      ",
            "    |      ",
            "    |      ",
            "    |      ",
            "    |      ",
            "    |      ",
            "____|______",
        ]
        cartoon[4] = [
            "    |----  ",
            "    | /    ",
            "    |/     ",
            "    |      ",
            "    |      ",
            "    |      ",
            "    |      ",
            "____|______",
        ]
        cartoon[5] = [
            "    |----  ",
            "    | / |  ",
            "    |/     ",
            "    |      ",
            "    |      ",
            "    |      ",
            "    |      ",
            "____|______",
        ]
        cartoon[6] = [
            "    |----  ",
            "    | / |  ",
            "    |/  O  ",
            "    |      ",
            "    |      ",
            "    |      ",
            "    |      ",
            "____|______",
        ]
        cartoon[7] = [
            "    |----  ",
            "    | / |  ",
            "    |/  O  ",
            "    |   |  ",
            "    |      ",
            "    |      ",
            "    |      ",
            "____|______",
        ]
        cartoon[8] = [
            "    |----  ",
            "    | / |  ",
            "    |/  O  ",
            "    |   |- ",
            "    |      ",
            "    |      ",
            "    |      ",
            "____|______",
        ]
        cartoon[9] = [
            "    |----  ",
            "    | / |  ",
            "    |/  O  ",
            "    |  -|- ",
            "    |      ",
            "    |      ",
            "    |      ",
            "____|______",
        ]
        cartoon[10] = [
            "    |----  ",
            "    | / |  ",
            "    |/  O  ",
            "    |  -|- ",
            "    |    \\ ",
            "    |      ",
            "    |      ",
            "____|______",
        ]
        cartoon[11] = [
            "    |----  ",
            "    | / |  ",
            "    |/  O  ",
            "    |  -|- ",
            "    |  / \\ ",
            "    |      ",
            "    |      ",
            "____|______",
        ]

        # Loop through all 8 lines
        for i in range(8):
            # if it is line 3
            if i == 3:
                # Print the line based on the lives lost
                # Print the hidden word
                builder.append(
                    cartoon[self.lives][i] + "      " + self.displayHiddenWord()
                )
            # prevent line getting over number of array.
            elif self.lives >= 12:
                break
            # else it is another line
            else:
                # Print the line based on the lives lost
                builder.append(cartoon[self.lives][i])

        return self.render(builder)

    def displayHiddenWord(self):
        builder = []
        # Loop through all of the hiddenLetters
        sub_builder = []
        for i in range(len(self.hiddenLetters)):
            # Display the letter
            sub_builder.append(self.hiddenLetters[i])
            # Display a space
        builder.append(self.render(sub_builder, " "))
        # builder.append("")
        # print a new line
        return self.render(builder)

    def displayUsedCharacters(self):
        builder = []
        # Loop through all of the usedLetters
        sub_builder = []
        for i in range(len(self.usedLetters)):
            # Display the letter
            sub_builder.append(self.usedLetters[i])
            # Display a space

        builder.append(self.render(sub_builder, "  "))
        # print a new line
        builder.append("")

        return self.render(builder)

    def displayGameResult(self, gState):
        builder = []
        # if the gameState is lost
        if gState == "LOST":
            # Print out a consolation message
            builder.append("YOU HAVE LOST. THE WORD WAS " + self.word)
        # if the gameState is won
        if gState == "WON":
            # Print out a message of congratulations
            builder.append("YOU WON!")

        return self.render(builder)

    def checkLetter(self, letter):
        if letter not in self.VALID_LETTERS:
            letter_state = "UNKNOWN"
        # if the letter is in the set of hiddenLeters set the state to already selected
        elif letter in self.hiddenLetters:
            letter_state = "ALREADY SELECTED"
            # else if the letter is in the set of usedLeters set the state to already selected
        elif letter in self.usedLetters:
            letter_state = "ALREADY SELECTED"
        # else if the letter is in the word set the state to found
        elif letter in self.word:
            letter_state = "FOUND"
        # else if the letter is in the list of valid letters word set the state to missed
        elif letter in self.VALID_LETTERS:
            letter_state = "MISSED"
        else:
            letter_state = "UNKNOWN"
        # return the letter state
        return letter_state

    def respondToLetter(self, letter, state):
        # if the letterState is missed
        if state == "MISSED":
            # increase the lives lost by one
            self.lives += 1
            # Add the letter to the usedLetters array
            self.usedLetters += letter
        # if the state is found
        if state == "FOUND":
            # Step through each letter in word
            for i in range(len(self.word)):
                # if the letter matches
                if letter == self.word[i]:
                    # set the character in hidden letters to the letter
                    self.hiddenLetters[i] = letter

    def checkGameState(self):
        gamestate = "PLAYING"

        # if the lives lost is 11 or more
        if self.lives >= 11:
            # set the game state to lost
            gamestate = "LOST"
        # else if no underscore canbe found in hiddenLetters
        elif "_" not in self.hiddenLetters:
            # set the game state to won
            gamestate = "WON"
        # return the game state
        return gamestate
