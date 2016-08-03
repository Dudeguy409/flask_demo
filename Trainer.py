class Trainer:

    def __init__(self, trainerID, displayName):
        self.trainerID = trainerID
        self.displayName = displayName

    def __str__(self):
        return "Trainer - ID: "+self.trainerID+", Name: "+self.displayName+";"

    def __repr__(self):
        return str(self)