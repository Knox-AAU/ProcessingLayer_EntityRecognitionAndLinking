from components import *
from components.EntityLinker import entitylinkerFunc
import sys, json
from multiprocessing import Process
from lib.FileWatcher import FileWatcher

from fastapi import FastAPI

app = FastAPI()


@app.on_event("startup")
async def startEvent():
    await main()


@app.get("/entitymentions")
async def getJson():
    await main()
    with open("entity_mentions.json", "r") as entityJson:
        entityMentions = json.load(entityJson)
        return entityMentions


async def main():
    # FileWatcher(filename = "Artikel.txt", interval = 5.0, callback=lambda :print("whatever")).start() #Starts fileWatcher

    text = GetSpacyData.GetText(
        "Artikel.txt"
    )  # Takes in title of article. Gets article text in string format
    doc = GetSpacyData.GetTokens(
        text
    )  # finds entities in text, returns entities in doc object
    ents = GetSpacyData.GetEntities(doc, "Artikel.txt")  # appends entities in list

    text = GetSpacyData.GetText("Artikel.txt") #Takes in title of article. Gets article text in string format
    doc = GetSpacyData.GetTokens(text) #finds entities in text, returns entities in doc object
    entsJSON = GetSpacyData.GetEntities(doc, "Artikel.txt") #appends entities in list
    #To prevent appending challenges, the final JSON is created in GetEntities()
    #entMentions= GetSpacyData.entityMentionJson(ents)  #Returns JSON object containing an array of entity mentions

    await Db.InitializeIndexDB(
        "./Database/DB.db"
    )  # makes the DB containing the entities of KG

    #entLinks = await entitylinkerFunc(ents) #Returns JSON object containing an array of entity links
    #entLinks = entitylinkerFunc(entsJSON) #Returns JSON object containing an array of entity links

    with open("entity_mentions.json", "w", encoding="utf8") as entityJson:
        json.dump(entsJSON, entityJson, ensure_ascii=False, indent = 4)
