class Trainer:

    def __init__(self, trainerEmail, displayName, pokeList = []):
        self.trainerEmail = trainerEmail
        self.displayName = displayName
        self.pokeList = pokeList

    def __str__(self):
        return 'Trainer - Email: ' + self.trainerEmail + "\tdisplayName: "+self.displayName+"\tPokemon: "+ self.pokeList.__str__()

    def repr(self):
        self.__str__()