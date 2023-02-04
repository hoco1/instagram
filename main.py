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

    username = 'fpepby'
    password = '58598311mM'

    payload = {
        'username': username,
        'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{time}:{password}',
        'queryParams': {},
        'optIntoOneTap': 'false'
    }

    login_header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.instagram.com/accounts/login/",
        "x-csrftoken": csrf
    }
    
    response = requests.post(login_url,data=payload,headers=login_header)
    print(response.status_code)
    cookie = response.cookies.get_dict()
    
    conn.local.accounts.insert_one({'usr':username,'pwd':password})
    conn.local.cookies.insert_one(cookie)
    
    return {'cookie':cookie}

# get followers list
app.get("/instagram/{usr}",tags=['instagram'])
def list_followers(usr:str):
    pass

