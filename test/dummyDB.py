import string
import random

class DatabaseFacade:

    #Takes in a request that hopefully contains a 256-digit session token.  It returns a user id and maybe a new cookie? or throws an exception
    def validateCookie(self):
        pass
    def validateUser(self):
        pass
    def generateRandomCookie(self):
        return ''.join(random.SystemRandom().choice(string.digits + string.ascii_letters) for _ in range(512)) # 62 ^ 512 possible strings
    def registerTrainer(self, displayName, email, encryptedPassword):
        pass
    def addPokemonToTrainer(self,):
        pass
    def removePokemonFromTrainer(self):
        pass
    def movePokemonFromTo(self, pokemonID, trainerID1, trainerID2):
        pass
    def tradePokemon(self,pokemonID1, pokemonID2):
        pass
    def getPokemonForTrainer(self, trainerID):
        pass
    def getAllPokemon(self):
        pass
    def getAllTrainers(self):
        pass
    def getPokemon(self, pokemonID):
        pass
    def getTrainer(self, trainerID):
        pass