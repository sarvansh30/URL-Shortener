from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
from typing import Optional
from fastapi.responses import RedirectResponse

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
    i=0
    while True:
        yield i
        i+=1
gen = generateID()
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
        slug = next(gen)
        genSlug=base62Converter(slug)
        # print(genSlug)
        await shortLinksDB.insert_one({"slug":genSlug,"link":linkData })
        return genSlug
    else:
        res = await shortLinksDB.find_one({"slug":customInput})
        if res==None:
            shortLinksDB.insert_one({"slug":customInput,"link":linkData})
            return customInput
        else:
            return -1

@app.post("/createShortLink")
async def creatingShortLink(link:str,customInput:Optional[str]=None ):
    
    flag=link.find("https://")
    if flag==-1:
        link = "https://"+link

    resp = await shortLinksDB.find_one({"link":link})
    if resp:
        return {"msg":"Shortlink already exists",
                "stLink":f"smol/r/{resp["slug"]}"}
    result = await generateSlug(link,customInput)
    if result == -1:
        return {"Msg":"This is alsready in use try another"}
    return {"stLink":f"smol/r/{result}"}


@app.get("/r/{slug}")
async def redirectUser(slug:str):
    resp = await shortLinksDB.find_one({"slug":slug})

    if resp:
        return RedirectResponse(url=resp["link"])
    else:
        raise HTTPException(status_code=404,detail="Shortlink not found")