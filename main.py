from components import *
from components.EntityLinker import entitylinkerFunc
import json, os, time, string
from lib.Exceptions.UndetectedLanguageException import (
    UndetectedLanguageException,
)
from lib.DirectoryWatcher import DirectoryWatcher
from langdetect import detect
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
from dotenv import load_dotenv
templates = Jinja2Templates(directory="public")
app = FastAPI(title="API")

load_dotenv()

DIRECTORY_TO_WATCH = str(os.getenv("DIRECTORY_TO_WATCH"))
PIPELINE_C_URL = str(os.getenv("PIPELINE_C_URL"))
PIPELINE_C_AUTHORIZATION = str(os.getenv("PIPELINE_C_AUTHORIZATION"))
ACCESS_API_AUTHORIZATION = str(os.getenv("ACCESS_API_AUTHORIZATION"))

async def newFileCreated(file_path: str):
    time.sleep(1)
    await modifyTxt(file_path)
    outputJSON = await processInput(file_path)

    Headers = { "Authorization" : PIPELINE_C_AUTHORIZATION, "Access-Authorization": ACCESS_API_AUTHORIZATION }
    status = requests.post(PIPELINE_C_URL, json=outputJSON, headers=Headers)
    print(status.text)


dirWatcher = dirWatcher = DirectoryWatcher(
    directory=DIRECTORY_TO_WATCH, async_callback=newFileCreated
)


@app.on_event("startup")
async def startEvent():
    if not os.path.exists(DIRECTORY_TO_WATCH):
        os.mkdir(DIRECTORY_TO_WATCH)

    dirWatcher = DirectoryWatcher(
        directory=DIRECTORY_TO_WATCH, async_callback=newFileCreated
    )
    if os.path.exists(DIRECTORY_TO_WATCH):
        dirWatcher.start_watching()


@app.on_event("shutdown")
def shutdown_event():
    if os.path.exists(DIRECTORY_TO_WATCH):
        dirWatcher.stop_watching()


app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/entitymentions/all")
async def get_all_json():
    if not os.path.exists("entity_mentions.json"):
        raise HTTPException(status_code=404, detail="mentions not found")

    with open("entity_mentions.json", "r") as entity_json:
        entity_mentions = json.load(entity_json)
        return entity_mentions


@app.get("/entitymentions")
async def get_json(article: str = Query(..., title="Article Filename")):
    path = DIRECTORY_TO_WATCH + article
    print(path)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Article not found")
    try:
        newFile = await processInput(path)
    except Exception as e:
        #Server does not need to freeze everytime an exeption is thrown
        print(f"An exception occurred: {str(e)}")
        return {"error": str(e)}
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


async def modifyTxt(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            if not content:
                print("The file is empty.")
            lines = content.split('\n\n')
            # List comprehension that adds '. ' to lines not ending with punctuation, else adds a space.
            modified_lines = [line + '. ' if not line.endswith(tuple(string.punctuation)) else line + ' ' for line in lines]
            file.close()
        with open(file_path, 'w') as file:
            file.write(' '.join(modified_lines))
            file.close()
    except FileNotFoundError:
        print(f"The file at {file_path} could not be found.")
    except Exception as e:
        print(f"An error occurred: {e}")


async def processInput(file_path: str = "Artikel.txt"):
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

    ents = GetSpacyData.GetEntities(doc)  # construct entities from text

    await Db.InitializeIndexDB(
        "./Database/DB.db"
    )  # makes the DB containing the entities of KG
    # Returns JSON object containing an array of entity links

    entLinks = await entitylinkerFunc(
        ents
    )  # Returns JSON object containing an array of entity links

    entsJSON = GetSpacyData.BuildJSONFromEntities(entLinks, doc, file_path)

    with open("entity_mentions.json", "w", encoding="utf8") as entityJson:
        json.dump(entsJSON.allFiles, entityJson, ensure_ascii=False, indent=4)

    return entsJSON.newFile
