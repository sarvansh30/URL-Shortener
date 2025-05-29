from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import Optional
from fastapi.responses import RedirectResponse
from pymongo.errors import PyMongoError
import re

app = FastAPI()
load_dotenv()
Backend_URL = os.getenv("Backend_URL")
#Database connection
client = AsyncIOMotorClient(Backend_URL)
db = client.get_database("URL-shortener")
shortLinksDB = db["shortLinks"]
counterDB = db["counter"]

async def generateID():
    try:
        count = await counterDB.find_one_and_update(
            {"use":"counter"},{"$inc":{"count":1}},
            return_document=True,
            upsert=True
        )
    except PyMongoError as e:
        raise HTTPException(status_code=500,detail="erroring generating random slug, Try again!")
    
    return count["count"]

def base62Converter(slug):
    base62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    num=len(base62)
    createdSlug=[]
    if slug==0:
        return base62[0]
    while slug>0:
        rem=slug%num
        slug=slug//num
        createdSlug.append(base62[rem])
    
    return "".join(createdSlug)

async def generateSlug(linkData,customInput):
    if customInput==None:
        slug = await generateID()
        genSlug=base62Converter(slug)
        # print(genSlug)
        try:
            await shortLinksDB.insert_one({"slug":genSlug,"link":linkData })
        except PyMongoError as e:
            raise HTTPException(status_code=500,detail="Error occurred inserting the shortLink, Try Again!!")
        
        return genSlug
    else:
        try:
            res = await shortLinksDB.find_one({"slug":customInput})
            if res==None:
                shortLinksDB.insert_one({"slug":customInput,"link":linkData})
                return customInput
            else:
                raise HTTPException(status_code=409,detail="This custom shortlink is already in use. Try another.")
        except PyMongoError as e:
            raise HTTPException(status_code=500,detail="Error occurred finding or inserting the shortLink, Try Again!!")


@app.post("/createShortLink")
async def creatingShortLink(link:str,customInput:Optional[str]=None ):
    
    if customInput and not re.match(r'^[A-Za-z0-9]{1,30}$',customInput):
        raise HTTPException(status_code=400,detail="Use valid symbols for custom link with length ranging from 1 to 30 characters")
    link = link.rstrip("/")
    # print(link)
    flag=link.find("https://")
    if flag==-1:
        link = "https://"+link

    try:
        resp = await shortLinksDB.find_one({"link":link})
    except PyMongoError as e:
        raise HTTPException(status_code=409,detail="Server Error occurred trying to create short-link")
    if resp:
        return {"msg":"Shortlink already exists",
                "stLink":f"smol/r/{resp["slug"]}"}
    result = await generateSlug(link,customInput)
    if result == -1:
        raise HTTPException(status_code=400,detail="This link already in use try another custom link")
    return {"stLink":f"smol/r/{result}"}



@app.get("/r/{slug}")
async def redirectUser(slug:str):
    try:
        resp = await shortLinksDB.find_one({"slug":slug})
    except PyMongoError as e:
        raise HTTPException(status_code=500,detail="Error occurred in redirecting. Try Again!")

    if resp:
        return RedirectResponse(url=resp["link"])
    else:
        raise HTTPException(status_code=404,detail="Shortlink not found")