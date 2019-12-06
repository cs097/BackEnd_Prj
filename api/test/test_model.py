import bcrypt
import pytest
import config

from model	import UserDao, TweetDao
from sqlalchemy	import create_engine, text

database = create_engine(config.test_config['DB_URL'], encoding='utf-8', max_overflow=0)

@pytest.fixture
def user_dao():
    return UserDao(database)

@pytest.fixture
def tweet_dao():
    return TweetDao(database)

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

## Test insert_user Method
def test_insert_user(user_dao):
    new_user = {
        'name'		: 'LCS',
        'email'		: 'CS@test.com',
        'profile'	: 'TEST',
        'password'	: 'testtest'
    }

    new_user_id = user_dao.insert_user(new_user)
    user	= get_user(new_user_id)

    assert user == {
        'id'		: new_user_id,
        'name'		: new_user['name'],
        'email'		: new_user['email'],
        'profile'	: new_user['profile']
    }

## Test get_user_id_and_password Method
def test_get_user_id_and_password(user_dao):
    user_credential = user_dao.get_user_id_and_password(email = 'Test_1@gmail.com')

    assert user_credential['id'] == 1

    assert bcrypt.checkpw('test password'.encode('UTF-8'), user_credential['hashed_password'].encode('UTF-8'))

## Test insert_follow Method
def test_insert_follow(user_dao):
    user_dao.insert_follow(user_id=1, follow_id=2)

    follow_list = get_follow_list(1)

    assert follow_list == [2]

## Test insert_unfollow Method
def test_insert_unfollow(user_dao):
    user_dao.insert_follow(user_id=1, follow_id=2)
    user_dao.insert_unfollow(user_id=1, unfollow_id=2)

    follow_list = get_follow_list(1)

    assert follow_list == []

## Test insert_tweet Method
def test_insert_tweet(tweet_dao):
    tweet_dao.insert_tweet(1, "Tweet Test")
    timeline = tweet_dao.get_timeline(1)

    assert timeline == [
        {
            'user_id' : 1,
            'tweet'   : 'Tweet Test'
        }
    ]

## Test timeline Method
def test_timeline(user_dao, tweet_dao):
    tweet_dao.insert_tweet(1, "Tweet Test")
    tweet_dao.insert_tweet(2, "Tweet Test 2")
    user_dao.insert_follow(1,2)

    timeline = tweet_dao.get_timeline(1)

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
