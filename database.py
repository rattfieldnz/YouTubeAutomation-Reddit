from tinydb import TinyDB
db = TinyDB('./Database/database.json')

def load_database():
    db = TinyDB('./Database/database.json')
    return db

