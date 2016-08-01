#Test cookies
'''self.clearDatabase()
        expiryDate = (datetime.date.fromordinal(datetime.date.today().toordinal() - 15)).strftime("%Y-%m-%d")
        self.redisDB.sadd("Date:" + expiryDate + ":Cookies", "abc123")
        self.redisDB.set("Trainer:" + "14" + ":Cookie", "abc123")
        self.redisDB.set("Cookie:" + "abc123" + ":TrainerID", 14)
        self.redisDB.set("Cookie:" + "abc123" + ":Date", expiryDate)

        print(self.redisDB.smembers("Date:" + expiryDate + ":Cookies"))
        print(self.redisDB.get("Trainer:" + "14" + ":Cookie"))
        print(self.redisDB.get("Cookie:" + "abc123" + ":TrainerID"))
        print(self.redisDB.get("Cookie:" + "abc123" + ":Date"))
        self.deleteAgedCookies()

        print(self.redisDB.smembers("Date:" + expiryDate + ":Cookies"))
        print( self.redisDB.get("Trainer:" + "14" + ":Cookie"))
        print(self.redisDB.get("Cookie:" + "abc123" + ":TrainerID"))
        print(self.redisDB.get("Cookie:" + "abc123" + ":Date"))
        return'''