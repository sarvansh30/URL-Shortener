from fastapi import FastAPI
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os

app = FastAPI()
load_dotenv()
Backend_URL = os.getenv("Backend_URL")
#Database connection
client = AsyncIOMotorClient(Backend_URL)
db = client.get_database("URL-shortener")
shortLinksDB = db["shortLinks"]

@app.get("/")
def getHome():
    return {"msg":"HEllow"}

def generateID():
    for i in range(1000000,10000000):
        yield i

def base62Converter(slug):
    base62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    


async def generateSlug(linkData,customInput=""):
    if len(customInput)==0:
        slug = next(generateID())
        genSlug=base62Converter(slug)
        return True
    else:
        res = await shortLinksDB.find_one({"slug":customInput})
        if res==None:
            shortLinksDB.insert_one({"slug":customInput,"link":linkData})
            return True
        else:
            return False
