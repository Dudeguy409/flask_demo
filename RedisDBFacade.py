import string
import random
import redis
import datetime
from ClientException import ClientException
import hashlib
from Trainer import Trainer
from Pokemon import Pokemon

class DatabaseFacade:

#TODO fix enum species
#TODO add pipes AND return stmts to any new code
    def __init__(self):
        self.redisDB = redis.StrictRedis(host='localhost', port=6379)
        return

    def printDB(self):
        print(self.redisDB.keys())
        return

    # Empties the database and resets the ID Counters
    def clearDatabase(self):
        pipe = self.redisDB.pipeline()
        pipe.flushdb()
        pipe.set("Trainer:IDCounter", 0)
        pipe.set("Pokemon:IDCounter", 0)
        pipe.execute()
        return

    # Returns a string of next avail int trainerID
    def popNextTrainerID(self):
        pipe = self.redisDB.pipeline()
        pipe.get("Trainer:IDCounter")
        pipe.incr("Trainer:IDCounter",1)
        rslts = pipe.execute()
        if rslts[0] is None:
            raise Exception("popNextTrainerID failed")
        return rslts[0]

    # Returns a string of next avail int trainerID
    def popNextPokemonID(self):
        pipe = self.redisDB.pipeline()
        pipe.get("Pokemon:IDCounter")
        pipe.incr("Pokemon:IDCounter",1)
        rslts = pipe.execute()
        if rslts[0] is None:
            raise Exception("popNextPokemonID failed")
        return rslts[0]

    #====== AUTHENTICATION METHODS ======#

    def generateRehashedPassword(self, email, givenPassword):
        rehashedPassword = givenPassword + email
        for i in range(0,500):
            rehashedPassword =  hashlib.sha512(rehashedPassword + givenPassword + email).hexdigest()
        return rehashedPassword


    # Takes in a cookie (256-digit string) and an email address (any type).
    # Returns a tuple containing the trainerID (string) and date (string) of the given cookie, or throws an exception
    def validateCookie(self, cookieToCheck, emailToCheck):
        pipeQuery = self.redisDB.pipeline()
        pipeQuery.get("Cookie:" + cookieToCheck + ":TrainerID")
        pipeQuery.get("Cookie:" + cookieToCheck + ":Date")
        queryRslts = pipeQuery.execute()
        trainerID = queryRslts[0]
        date = queryRslts[1]
        if date is None or trainerID is None:
            raise ClientException("The supplied cookied did not have a mapping to a date and/or trainerID.  It appears to not be in the database.  It may have expired and been deleted.")
        expectedTrainerEmail = self.redisDB.get("Trainer:"+trainerID+":email")
        if not expectedTrainerEmail == emailToCheck:
            raise Exception("The email supplied in a cookie did not match the cookie on file.  Could be a rogue client or a design issue.")
        return (trainerID,date)

    # Takes in an email (string) and password (string).
    # Returns a trainerID (string), or throws an exception
    def validateUser(self, trainerEmail, givenPassword):
        trainerID = self.redisDB.get("Email:"+trainerEmail+":TrainerID")
        if trainerID is None:
            raise ClientException("No account exists with the supplied email")
        expectedPassword = self.redisDB.get("Trainer:"+trainerID+":password")

        rehashedPassword = self.generateRehashedPassword(trainerEmail,givenPassword)
        if rehashedPassword != expectedPassword:
            raise ClientException("Incorrect Password")
        return trainerID

    def deleteCookieForTrainerIfExists(self, trainerID):
        cookie = self.redisDB.get("Trainer:" + trainerID + ":Cookie")
        if cookie is not None:
            date = self.redisDB.get("Cookie:" + cookie + ":Date")
            self.deleteCookie(trainerID, cookie, date)
        return

    def deleteCookie(self, trainerID, cookieToDelete, dateToDelete):
        pipe = self.redisDB.pipeline()
        pipe.srem("Date:" + dateToDelete + ":Cookies", cookieToDelete)
        pipe.delete("Cookie:" + cookieToDelete + ":TrainerID")
        pipe.delete("Cookie:" + cookieToDelete + ":Date")
        pipe.delete("Trainer:" + trainerID + ":Cookie")
        pipe.execute()
        return

    def getNewCookie(self, trainerID):
        cookieToReturn = self.generateRandomCookie()
        dateToAdd = datetime.date.today().strftime("%Y-%m-%d")
        pipe = self.redisDB.pipeline()
        pipe.sadd("Date:" + dateToAdd + ":Cookies", cookieToReturn)
        pipe.set("Trainer:" + trainerID + ":Cookie", cookieToReturn)
        pipe.set("Cookie:" + cookieToReturn + ":Date", dateToAdd)
        pipe.set("Cookie:" + cookieToReturn + ":TrainerID", trainerID)
        pipe.execute()
        return cookieToReturn

    def getTrainerName(self, trainerID):
        return self.redisDB.get("Trainer:" + trainerID + ":displayName")

    # Returns a 256-digit string of ascii letters and numbers, for a total of 62 ^ 512 possible combos
    def generateRandomCookie(self):
        return ''.join(random.SystemRandom().choice(string.digits + string.ascii_letters) for _ in range(512))

    def deleteAgedCookies(self):
        # gets the date 15 days ago
        expiryDate = (datetime.date.fromordinal(datetime.date.today().toordinal() - 15)).strftime("%Y-%m-%d")
        cookiesToDelete = self.redisDB.smembers("Date:" + expiryDate + ":Cookies")

        queryPipe = self.redisDB.pipeline()
        for cookieToQuery in cookiesToDelete:
            queryPipe.get("Cookie:" + cookieToQuery + ":TrainerID")
        trainerCookiesToDelete = queryPipe.execute()

        for i in range(0,len(trainerCookiesToDelete)):
            trainerID = trainerCookiesToDelete[i]
            if trainerID is not None:
                # None Check: There is a very minute chance that the cookie was
                # deleted between <<self.redisDB.smembers("Date:" + expiryDate + ":Cookies")>> and
                # <<queryPipe.get("Cookie:" + cookieToQuery + ":TrainerID")>>.
                # This will cause problems here w/o a None check.
                cookie = cookiesToDelete[i]
                self.deleteCookie(trainerID,cookie, expiryDate)
        return


    #====== ADD ITEM METHODS ======#

    def registerTrainer(self, displayName, email, hashedPassword):
        existingID = self.redisDB.get("Email:"+email+":TrainerID")
        if existingID is not None:
            raise ClientException("This email is already associated with an account.  Please pick a different EMail address.")
        trainerID = self.popNextTrainerID()
        rehashedPassword = self.generateRehashedPassword(email, hashedPassword)

        pipe = self.redisDB.pipeline()

        pipe.set("Email:"+email+":TrainerID", trainerID)
        pipe.set("Trainer:"+trainerID+":password", rehashedPassword)
        pipe.set("Trainer:"+trainerID+":email", email)
        pipe.set("Trainer:"+trainerID+":displayName", displayName)
        pipe.sadd("Trainers", trainerID)

        pipe.execute()
        return trainerID

    #TODO create move lists, or cp lists
    def addPokemonToTrainer(self, trainerID, nickname, species, cp):
        pokemonID = self.popNextPokemonID()

        pipe = self.redisDB.pipeline()

        pipe.set("Pokemon:"+pokemonID+":nickname", nickname)
        pipe.set("Pokemon:"+pokemonID+":species", species)
        pipe.set("Pokemon:"+pokemonID+":cp", cp)
        pipe.set("Pokemon:"+pokemonID+":trainerID", trainerID)
        pipe.sadd("Trainer:"+trainerID+":Pokemon", pokemonID)
        pipe.zadd("Pokemon-By-CP",cp,pokemonID)
        pipe.zadd("Species:"+species+":Pokemon", cp, pokemonID)
        
        pipe.execute()
        return

    #====== SCAN, QUERY, and GET METHODS ======#

    def getGeneralPokemon(self, min=None, max=None, start=None, num=None):
        if min is None:
            min = "-inf"
        if max is None:
            max = "+inf"
        if start is None:
            start = 0
        if num is None:
            num = 100
        ids = self.redisDB.zrangebyscore("Pokemon-By-CP", min, max, start, num)
        return self.getPokemonFromIDs(ids)

    def getSpeciesPokemon(self, species, min=None, max=None, start=None, num=None):
        if min is None:
            min = "-inf"
        if max is None:
            max = "+inf"
        if start is None or num is None:
            start = 0
            num = 100
        ids = self.redisDB.zrangebyscore("Species:"+species+":Pokemon", min, max, start, num)
        return self.getPokemonFromIDs(ids)

    def getAllTrainers(self):
        trainerIDs = list(self.redisDB.smembers("Trainers"))
        pipe = self.redisDB.pipeline()
        for trainerID in trainerIDs:
            pipe.get("Trainer:"+trainerID+":displayName")
        trainerNames = pipe.execute()
        trainers = []
        for i in range(0,len(trainerIDs)):
            trainers.append(Trainer(trainerIDs[i], trainerNames[i]))
        return trainers

    #TODO consider replacing with fuzzy search
    def getTrainersByStrictNameMatch(self, name):
        trainersToFilter= self.getAllTrainers()
        trainersToReturn = []
        for trainer in trainersToFilter:
            if trainer.displayName==name:
                trainersToReturn.append(trainer)
        return trainersToReturn


    #TODO check and check what happens if pokemon doesn't exist
    def getPokemonForTrainer(self, trainerID):
        pokemonToRetreive = list(self.redisDB.smembers("Trainer:"+trainerID+":Pokemon"))
        trainerName = self.redisDB.get("Trainer:" + trainerID + ":displayName")
        pipe = self.redisDB.pipeline()
        for pokemonID in pokemonToRetreive:
            pipe.get("Pokemon:" + pokemonID + ":nickname")
            pipe.get("Pokemon:" + pokemonID + ":species")
            pipe.get("Pokemon:" + pokemonID + ":cp")
        rslts = pipe.execute()
        pokemonToParse = [rslts[x:x + 3] for x in range(0, len(rslts), 3)]
        pokemonToReturn = []
        for i in range(0, len(pokemonToParse)):
            pokemon = pokemonToParse[i]
            pokemonID = pokemonToRetreive[i]
            name = pokemon[0]
            species = pokemon[1]
            cp = pokemon[2]
            pokemonToReturn.append(Pokemon(pokemonID, name, species, cp, trainerID, trainerName))
        return pokemonToReturn

    def getPokemonFromIDs(self, pokemonToRetreive):
        if not isinstance(pokemonToRetreive, list):
            pokemonToRetreive = list(pokemonToRetreive)
        pipe = self.redisDB.pipeline()
        for pokemonID in pokemonToRetreive:
            pipe.get("Pokemon:" + pokemonID + ":nickname")
            pipe.get("Pokemon:" + pokemonID + ":species")
            pipe.get("Pokemon:" + pokemonID + ":cp")
            pipe.get("Pokemon:" + pokemonID + ":trainerID")
        rslts = pipe.execute()
        pokemonToParse = [rslts[x:x + 4] for x in range(0, len(rslts), 4)]
        trainerPipe = self.redisDB.pipeline()
        for pokemon in pokemonToParse:
            trainerID = pokemon[3]
            trainerPipe.get("Trainer:" + trainerID + ":displayName")
        trainerNames = trainerPipe.execute()
        pokemonToReturn = []
        for i in range(0,len(pokemonToParse)):
            pokemon = pokemonToParse[i]
            pokemonID = pokemonToRetreive[i]
            name = pokemon[0]
            species = pokemon[1]
            cp = pokemon[2]
            trainerID=pokemon[3]
            trainerName = trainerNames[i]
            pokemonToReturn.append(Pokemon(pokemonID, name, species, cp, trainerID, trainerName))
        return pokemonToReturn.reverse()

    #====== DELETE ITEM METHODS ======#

    def deleteSpecificPokemon(self, pokemonID, trainerID):
        species = self.redisDB.get("Pokemon:" + pokemonID + ":species")
        pipe = self.redisDB.pipeline()
        pipe.delete("Pokemon:" + pokemonID + ":nickname")
        pipe.delete("Pokemon:" + pokemonID + ":species")
        pipe.delete("Pokemon:" + pokemonID + ":cp")
        pipe.delete("Pokemon:" + pokemonID + ":trainerID")
        pipe.srem("Trainer:" + trainerID + ":Pokemon", pokemonID)
        pipe.zrem("Pokemon-By-CP", pokemonID)
        pipe.zrem("Species:"+species+":Pokemon",pokemonID)
        pipe.execute()
        return

    def removeTrainer(self, trainerID):
        self.deleteCookieForTrainerIfExists(trainerID)
        queryPipe = self.redisDB.pipeline()
        queryPipe.smembers("Trainer:" + trainerID + ":Pokemon")
        queryPipe.get("Trainer:" + trainerID + ":email")
        rslts = queryPipe.execute()
        pokelist = rslts[0]
        email = rslts[1]
        for pokemonID in pokelist:
            self.removePokemonFromTrainer()
        pipe = self.redisDB.pipeline()
        pipe.delete("Email:" + email + ":TrainerID", trainerID)
        pipe.delete("Trainer:" + trainerID + ":password")
        pipe.delete("Trainer:" + trainerID + ":email")
        pipe.delete("Trainer:" + trainerID + ":displayName")
        pipe.delete("Trainer:" + trainerID + ":Pokemon")
        pipe.srem("Trainers", trainerID)
        pipe.execute()
        return