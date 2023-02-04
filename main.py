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
@app.get("/instagram/{usr}",tags=['instagram'])
def list_followers(usr:str):
    cookie = serializeList(conn.local.cookies.find().sort('_id',-1).limit(1))[0]
    del cookie['_id']
    
    cookies = {
        'ig_did': cookie['ig_did'],
        'mid': cookie['mid'],
        'rur': cookie['rur'],
        'csrftoken': cookie['csrftoken'],
        'ds_user_id': cookie['ds_user_id'],
        'sessionid': cookie['sessionid'],
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'X-CSRFToken': cookie['csrftoken'],
        # Static, and I don't know what it is yet (X-IG-App-ID,X-ASBD-ID)
        'X-IG-App-ID': '936619743392459',
        'X-ASBD-ID': '198387',
        #'X-IG-WWW-Claim': 'hmac.AR2t23cd-PLsVw8GByCHBcLMYfsKEk5T9x80YB-dnKMcZOPw',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
        'Referer': f'https://www.instagram.com/{usr}/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-GPC': '1',
        'TE': 'trailers',
    }

    params_info = (
        ('username', usr),
    )

    response = requests.get('https://www.instagram.com/api/v1/users/web_profile_info/', headers=headers, params=params_info, cookies=cookies)
    
    print(response)
    
    data = json.loads(response.text)
    usr_id = data['data']['user']['id']
    print(usr_id)
    
    headers['Referer'] = f'https://www.instagram.com/{usr}/followers/'
    
    params_follower = {
    'max_id': '100',
    'search_surface': 'follow_list_page',
    }
    
    for i in range(3):
        response = requests.get(f'https://www.instagram.com/api/v1/friendships/{usr_id}/followers/', headers=headers, params=params_follower, cookies=cookies)
        print('follower : ',response)
        follower_data = json.loads(response.text)
        for user in follower_data['users']:
            conn.local.followers.insert_one({'userName':user['username'],'full_name':user['full_name'],'is_private':user['is_private'],'which_account':usr})      
    return serializeList(conn.local.followers.find().sort('_id',-1).limit(15))
    
    
    

