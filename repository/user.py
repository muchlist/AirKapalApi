from db import mongo
from utils.my_bcrypt import bcrypt


class UserRepo(object):
    def isUserExist(self, username):
        result = mongo.db.users.find_one(
            {"username": username}, {"username": 1})
        if result:
            return True
        return False

    #Mereturn [result, code, error]
    def register(self,
                 username,
                 password,
                 email,
                 name,
                 isAdmin,
                 isAgent,
                 isTally,
                 isForeman,
                 branch
                 ):

        data_insert = {
            "username": username.upper(),
            "password": password,
            "email": email,
            "name": name.upper(),
            "isAdmin": isAdmin,
            "isForeman": isForeman,
            "isTally": isTally,
            "isAgent": isAgent,
            "branch": branch.upper()
        }
        try:
            mongo.db.users.insert_one(data_insert)
        except:
            return [None, 500, "galat insert register"]

        return ["data berhasil disimpan", 200, None,]
