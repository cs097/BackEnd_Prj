import pytest
import json
import bcrypt
import config

from sqlalchemy import create_engine, text
from app import create_app

database = create_engine(config.test_config['DB_URL'], encoding='utf-8', max_overflow=0)

@pytest.fixture
def api():
    app = create_app(config.test_config)
    app.config['TEST'] = True
    api = app.test_client()

    return api

## Before Test
def setup_function():
    ##Create a test user
    hashed_password = bcrypt.hashpw(
        b"test password",
        bcrypt.gensalt()
    )

    new_users = [
        {
            'id'		: 1,
            'name'		: 'Test_1',
            'email'		: 'Test_1@gmail.com',
            'profile'		: 'test_1 profile',
            'hashed_password'	: hashed_password
        }, {
            'id'		: 2,
            'name'		: 'Test_2',
            'email'		: 'Test_2@gmail.com',
            'profile'		: 'test_2 profile',
            'hashed_password'	: hashed_password
        }
    ]
    database.execute(text("""
        INSERT INTO users (
            id,
            name,
            email,
            profile,
            hashed_password
        ) VALUES (
            :id,
            :name,
            :email,
            :profile,
            :hashed_password
        )
    """), new_users)

    ## Test_2's Tweet
    database.execute(text("""
        INSERT INTO tweets (
            user_id,
            tweet
        ) VALUES (
            2,
            "Hello, Testing Tweet"
        )
    """))

## After Test
def teardown_function():
    database.execute(text("set foreign_key_checks=0"))
    database.execute(text("delete from users"))
    database.execute(text("delete from tweets"))
    database.execute(text("delete from users_follow_list"))
    database.execute(text("set foreign_key_checks=1"))


def test_ping(api):
    resp = api.get('/ping')
    assert b'pong' in resp.data

def test_login(api):
    resp = api.post('/login',
        data		= json.dumps({'email':'Test_1@gmail.com', 'password':'test password'}),
        content_type	= 'application/json'
    )
    assert b'access_token' in resp.data

def test_unauthorized(api):
    resp = api.post('tweet',
        data		= json.dumps({'tweet':'Test_Unauthorized'}),
        content_type	= 'application/json'
    )
    assert resp.status_code == 401

    resp = api.post('follow',
        data		= json.dumps({'follow':2}),
        content_type	= 'application/json'
    )
    assert resp.status_code == 401

    resp = api.post('unfollow',
        data		= json.dumps({'unfollow':2}),
        content_type	= 'application/json'
    )
    assert resp.status_code == 401

def test_tweet(api):
    ## Login
    resp = api.post('/login',
        data		= json.dumps({'email':'test_1@gmail.com', 'password':'test password'}),
        content_type	= 'application/json'
    )
    resp_json	= json.loads(resp.data.decode('utf-8'))
    access_token= resp_json['access_token']

    ## Tweet
    resp = api.post('/tweet',
        data 		= json.dumps({'tweet':"API Test using Pytest"}),
        content_type	= 'application/json',
        headers		= {'Authorization':access_token}
    )
    assert resp.status_code == 200

    ## Checking Tweet
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets	== {
        'user_id' : 1,
        'timeline' : [
            {
                'user_id' : 1,
                'tweet'   : "API Test using Pytest"
            }
        ]
    }

def test_follow(api):
    ## Login
    resp = api.post(
        '/login',
        data		= json.dumps({'email':'test_1@gmail.com', 'password':'test password'}),
        content_type	= 'application/json'
    )
    resp_json	= json.loads(resp.data.decode('utf-8'))
    access_token= resp_json['access_token']

    ## Check the Test_1's tweet is empty
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id' : 1,
        'timeline': [ ]
    }

    ## follow Test_2
    resp = api.post('/follow',
        data		= json.dumps({'follow':2}),
        content_type	= 'application/json',
        headers		= {'Authorization':access_token}
    )
    assert resp.status_code == 200

    ## Check the Test_1's tweet is not empty
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id' : 1,
        'timeline': [
            {
                'user_id' : 2,
                'tweet'   : "Hello, Testing Tweet"
            }
        ]
    }

def test_unfollow(api):
    ## Login
    resp = api.post(
        '/login',
        data		= json.dumps({'email':'Test_1@gmail.com', 'password':'test password'}),
        content_type	= 'application/json'
    )
    resp_json	= json.loads(resp.data.decode('utf-8'))
    access_token= resp_json['access_token']

    ## follow Test_2
    resp = api.post('/follow',
        data		= json.dumps({'follow':2}),
        content_type	= 'application/json',
        headers		= {'Authorization':access_token}
    )
    assert resp.status_code == 200

    ## Check the Test_1's tweet is not empty
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id' : 1,
        'timeline': [
            {
                'user_id' : 2,
                'tweet'   : "Hello, Testing Tweet"
            }
        ]
    }

    ## unfollow Test_2
    resp = api.post('/unfollow',
        data		= json.dumps({'unfollow':2}),
        content_type	= 'application/json',
        headers		= {'Authorization':access_token}
    )
    assert resp.status_code == 200

    ## Check the Test_1's tweet is empty
    resp = api.get(f'/timeline/1')
    tweets = json.loads(resp.data.decode('utf-8'))

    assert resp.status_code == 200
    assert tweets == {
        'user_id' : 1,
        'timeline': [ ]
    }
