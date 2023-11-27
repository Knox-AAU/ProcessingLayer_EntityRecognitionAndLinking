from components import *
from components.EntityLinker import entitylinkerFunc
import json, os
from lib.Exceptions.UndetectedLanguageException import (
    UndetectedLanguageException,
)
from lib.DirectoryWatcher import DirectoryWatcher
from langdetect import detect
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="public")
app = FastAPI(title="API")

DIRECTORY_TO_WATCH = "data_from_A/"
DB_PATH = "./Database/DB.db"

async def newFileCreated(file_path: str):
    await processInput(file_path)



dirWatcher = DirectoryWatcher(directory=DIRECTORY_TO_WATCH, async_callback=newFileCreated)


@app.on_event("startup")
async def startEvent():
    dirWatcher.start_watching()

    await Db.InitializeIndexDB(
        DB_PATH
    )  # makes the DB containing the entities of KG
    


@app.on_event("shutdown")
def shutdown_event():
    dirWatcher.stop_watching()


app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


@app.get('/')
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request}
    )

@app.get("/entitymentions/all")
async def get_all_json():
    if not os.path.exists("entity_mentions.json"):
        raise HTTPException(status_code=404, detail="mentions not found")
    
    mentions = await Db.Read(DB_PATH, "entitymention")
    print(mentions)

    with open("entity_mentions.json", "r") as entity_json:
        entity_mentions = json.load(entity_json)
        return entity_mentions

@app.get("/entitymentions")
async def get_json(article: str = Query(..., title="Article Filename")):
    path = DIRECTORY_TO_WATCH + article
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Article not found")
    
    newFile = await processInput(path)
    return newFile

@app.post("/detectlanguage")
async def checklang(request: Request):
    data = await request.body()
    stringdata = str(data)
    print(len(stringdata))
    if len(stringdata) < 4:
        raise HTTPException(status_code=400, detail="Text is too short")

    language = detect(stringdata)

    return language


async def processInput(file_path: str = "Artikel.txt"):
    #await Db.Read(DB_PATH, "entitymention", "filename = ")

    text = GetSpacyData.GetText(
        file_path
    )  # Takes in title of article. Gets article text in string format
    doc = GetSpacyData.GetTokens(
        text
    )  # finds entities in text, returns entities in doc object

    text = GetSpacyData.GetText(
        file_path
    )  # Takes in title of article. Gets article text in string format

    try:
        doc = GetSpacyData.GetTokens(
            text
        )  # finds entities in text, returns entities in doc object
    except UndetectedLanguageException:
        raise HTTPException(status_code=400, detail="Undetected language")

    ents = GetSpacyData.GetEntities(
        doc
    )  # construct entities from text

    entLinks = await entitylinkerFunc(
        ents
    )  # Returns JSON object containing an array of entity links

    entsJSON = GetSpacyData.BuildJSONFromEntities(
        entLinks,
        doc,
        file_path
    )

    with open("entity_mentions.json", "w", encoding="utf8") as entityJson:
        json.dump(entsJSON.allFiles, entityJson, ensure_ascii=False, indent=4)

    return entsJSON.newFile