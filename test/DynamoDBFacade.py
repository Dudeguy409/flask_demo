from __future__ import print_function # Python 2/3 compatibility
import string
import random
import boto3
import sys
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from Trainer import Trainer
from Pokemon import Pokemon

class DatabaseFacade:
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2', endpoint_url="http://localhost:8000")
    TABLE_NAMES=["Trainers","Pokemon"]

    #====== INIT METHOD ======#

    def initDB(self):
        self.checkTables()
        #self.registerTrainer("Andrew Davidson","davidsac@rose-hulman.edu","poop")
        trainer = self.getSpecificTrainer("davidsac@rose-hulman.edu")
        print(trainer)
        '''self.deleteAllTables()
        self.createAllTables()
        self.checkTables()'''
        return

    #====== CREATE TABLE METHODS ======#

    def createAllTables(self):
        self.createPokemonTable()
        self.createTrainerTable()
        return

    def createPokemonTable(self):
        table = self.dynamodb.create_table(
            TableName='Pokemon',
            KeySchema=[
                {
                    'AttributeName': 'trainerEmail',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'pokemonID',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'trainerEmail',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'pokemonID',
                    'AttributeType': 'N'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        return

    def createTrainerTable(self):
        table = self.dynamodb.create_table(
            TableName='Trainers',
            KeySchema=[
                {
                    'AttributeName': 'trainerEmail',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'trainerEmail',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        return

    #====== DELETE TABLE METHODS ======#

    def deleteAllTables(self):
        for name in self.TABLE_NAMES:
            self.deleteTableIfExists(name)
        return

    def deleteTableIfExists(self, name):
        try:
            self.dynamodb.Table(name).delete()
        except:
            print("failed deleting table ", name, " : ", sys.exc_info()[0])
        return

    #====== CHECK TABLE METHODS ======#

    def checkTables(self):
        for name in self.TABLE_NAMES:
            self.checkTableStatus(name)
        return

    def checkTableStatus(self, name):
        try:
            print(name, " : ", self.dynamodb.Table(name).table_status)
        except:
            print(name, " : ", "DNE")
        return

    #====== VALIDATION METHODS ======#

    #TODO
    #Takes in a request that hopefully contains a 256-digit session token.  It returns a user id and maybe a new cookie? or throws an exception
    def validateCookie(self, cookie):
        pass

    #TODO
    def validateUser(self, trainerEmail, encryptedPassword):
        pass

    def generateRandomCookie(self):
        return ''.join(random.SystemRandom().choice(string.digits + string.ascii_letters) for _ in range(512)) # 62 ^ 512 possible strings

    #====== ADD ITEM METHODS ======#

    #TODO check
    def registerTrainer(self, displayName, email, encryptedPassword):
        response = self.dynamodb.Table('Trainers').put_item(
            Item={
                'trainerEmail': email,
                'displayName': displayName,
                'password': encryptedPassword
            })
        #print("Result of insert:",response)
        return

    #TODO parse the list of pokemon for trainer to get next pokemonID, based on largest id found
    #TODO throw error if same id?
    def addPokemonToTrainer(self, trainerEmail, nickname, species, cp):
        pokemonID = random.randint(0,4000)
        response = self.dynamodb.Table('Pokemon').put_item(
            Item={
                'trainerEmail': trainerEmail,
                'pokemonID': pokemonID,
                'nickname': nickname,
                'species': species,
                'cp':cp
            })
        print("Result of insert:",response)
        return

    #====== SCAN, QUERY, and GET METHODS ======#

    #TODO check that this works.  May need to repeat if more rslts
    def getAllPokemon(self):
        table = self.dynamodb.Table('Pokemon')
        response = table.scan()
        for i in response['Items']:
            print(i)


    #TODO check that this works.  May need to repeat if more rslts
    def getAllTrainers(self):
        response = self.dynamodb.Table('Trainers').scan()
        for i in response['Items']:
            print(i)

    #TODO fix format of response
    def getPokemonForTrainer(self, trainerEmail):
        response = self.dynamodb.Table('Pokemon').query(KeyConditionExpression = Key('trainerEmail').eq(trainerEmail))
        print(response)
        return

    #TODO check that this works
    def getSpecificPokemon(self, trainerEmail, pokemonID):
        table = self.dynamodb.Table('Pokemon')
        try:
            response = table.get_item(
                Key={
                    'trainerEmail': trainerEmail,
                    'pokemonID': pokemonID
                }
            )
        except ClientError as e:
            print(e.response['Error']['Message'])
        else:
            item = response['Item']
            print("GetItem succeeded:")
            return item

    #TODO check that it works
    def getSpecificTrainer(self, trainerEmail):
        table = self.dynamodb.Table('Trainers')
        try:
            response = table.get_item(
                Key={
                    'trainerEmail': trainerEmail
                }
            )
        except ClientError as e:
            print("Error while getting specific trainer : ", e.response['Error']['Message'])
        else:
            item = response['Item']
            trainer = Trainer(item['trainerEmail'],item['displayName'])
            return trainer

    #====== TRADE METHODS ======#

    # TODO unimportant
    def movePokemonFromTo(self, pokemonID, trainerEmail1, trainerEmail2):
        pass

    # TODO unimportant
    def tradePokemon(self, pokemonID1, pokemonID2):
        pass

    #====== DELETE ITEM METHODS ======#

    #TODO unimportant
    #TODO shift all ids of that trainer's pokemon?
    def removePokemonFromTrainer(self):
        pass

    #TODO delete trainer