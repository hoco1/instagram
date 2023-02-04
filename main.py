import uvicorn
from fastapi import FastAPI,Body,Depends
from app.model import InstagramSchema,UserLoginSchema,UserSchema
# database
from app.db import conn
from app.schemas import serializeDict,serializeList
# scraping
import requests
from datetime import datetime
import json

app = FastAPI()
# GET - introduction
@app.get('/',tags=['main'])
def introduction():
    return {"Instagram Scraping"}

# save (user , pass) , cookies
@app.post('/instagram',tags=['instagram'])
def add_user(instagram:InstagramSchema):
    
    url = 'https://www.instagram.com/data/shared_data/'
    login_url = 'https://www.instagram.com/accounts/login/ajax/'

    time = int(datetime.now().timestamp())

    session = requests.Session()
    response = session.get(url)

    csrf = json.loads(response.text)['config']['csrf_token']

    username = instagram.instagramID
    password = instagram.instagramPass

    payload = {
        'username': username,
        'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{time}:{password}',
        'optIntoOneTap': 'false',
    }

    login_header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'X-CSRFToken':csrf,
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        "Referer": "https://www.instagram.com/accounts/login/",
    }
    
    response = requests.post(login_url,data=payload,headers=login_header)
    cookie = response.cookies.get_dict()
    
    conn.local.accounts.insert_one({'usr':username,'pwd':password})
    conn.local.cookies.insert_one(dict(cookie))
    
    return {'cookie':cookie}

# get followers list
app.get("/instagram/{usr}",tags=['instagram'])
def list_followers(usr:str):
    pass

