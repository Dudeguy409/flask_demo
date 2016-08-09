
class Species():

    def __init__(self):
        self.nameToNumMap = {}
        self.numToNameMap = {}
        self.speciesList = []
        self.addSpecies("Bulbasaur", 1)
        self.addSpecies("Ivysaur", 2)
        self.addSpecies("Venusaur", 3)
        self.addSpecies("Charmander", 4)
        self.addSpecies("Charmeleon", 5)
        self.addSpecies("Charizard", 6)
        self.addSpecies("Squirtle", 7)
        self.addSpecies("Wartortle", 8)
        self.addSpecies("Blastoise", 9)
        return

    def addSpecies(self, name, num):
        self.nameToNumMap[name] = num
        self.numToNameMap[num] = name
        self.speciesList.append((name, num))
        return

    def getSpeciesByNum(self, num):
        return self.numToNameMap[num]

    def getSpeciesByName(self, name):
        return self.nameToNumMap[name]

    def getAllSpecies(self):
        return self.speciesList

