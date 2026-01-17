import pymongo

# --- CONFIGURATION ---

# Dhyan se dekho, link ke dono taraf " " (quotes) hain
MONGO_URL = "mongodb+srv://muioma:Om9942660451@cluster0.obzctfp.mongodb.net/?appName=Cluster0"

# Baaki code same rahega...
client = pymongo.MongoClient(MONGO_URL)
db = client['ReactionBotData']
