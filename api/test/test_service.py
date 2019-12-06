import jwt
import bcrypt
import pytest
import config

from model	import UserDao, TweetDao
from service	import UserService, TweetService
from sqlalchemy	import create_engine, text

database = create_engine(config.test_config['DB_URL'], encoding='utf-8', max_overflow=0)

@pytest.fixture
def user_service():
    return UserService(UserDao(database), config)

@pytest.fixture
def tweet_service():
    return TweetService(TweetDao(database))

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

def get_user(user_id):
    row = database.execute(text("""
        SELECT
            id,
            name,
            email,
            profile
        FROM users
        WHERE id = :user_id
    """), {
        'user_id' : user_id
    }).fetchone()

    return {
        'id'		: row['id'],
        'name'		: row['name'],
        'email'		: row['email'],
        'profile'	: row['profile']
    } if row else None

def get_follow_list(user_id):
    rows = database.execute(text("""
        SELECT follow_user_id as id
        FROM users_follow_list
        WHERE user_id = :user_id
    """), {
        'user_id' : user_id
    }).fetchall()

    return [int(row['id']) for row in rows]

## Test create_new_user Method
def test_create_new_user(user_service):
    new_user = {
        'name'		: 'LCS',
        'email'		: 'CS@test.com',
        'profile'	: 'TEST',
        'password'	: 'testtest'
    }

    new_user_id = user_service.create_new_user(new_user)
    created_user = get_user(new_user_id)

    assert created_user == {
        'id'		: new_user_id,
        'name'		: new_user['name'],
        'profile'	: new_user['profile'],
        'email'		: new_user['email']
    }

## Test login Method
def test_login(user_service):
    assert user_service.login({
        'email'		: 'Test_1@gmail.com',
        'password'	: 'test password'
    })

    assert not user_service.login({
        'email'		: 'Test_1@gmail.com',
        'password'	: 'wrong password'
    })

## Test generate_access_token Method
def test_generate_access_token(user_service):
    token = user_service.generate_access_token(1)
    payload = jwt.decode(token, config.JWT_SECRET_KEY, 'HS256')

    assert payload['user_id'] == 1

## Test follow Method
def test_follow(user_service):
    user_service.follow(1, 2)
    follow_list = get_follow_list(1)

    assert follow_list == [2]

## Test unfollow Method
def test_unfollow(user_service):
    user_service.follow(1,2)
    user_service.unfollow(1,2)

    follow_list = get_follow_list(1)

    assert follow_list == [ ]

## Test tweet Method
def test_tweet(tweet_service):
    tweet_service.tweet(1, "Tweet Test")
    timeline = tweet_service.get_timeline(1)

    assert timeline == [
        {
            'user_id' : 1,
            'tweet'   : 'Tweet Test'
        }
    ]

## Test timeline Method
def test_timeline(user_service, tweet_service):
    tweet_service.tweet(1, "Tweet Test")
    tweet_service.tweet(2, "Tweet Test 2")
    user_service.follow(1, 2)

    timeline = tweet_service.get_timeline(1)

    assert timeline == [
        {
            'user_id' : 2,
            'tweet'   : 'Hello, Testing Tweet'
        },
        {
            'user_id' : 1,
            'tweet'   : 'Tweet Test'
        },
        {
            'user_id' : 2,
            'tweet'   : 'Tweet Test 2'
        }
    ]
