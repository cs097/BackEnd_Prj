import jwt

from flask	import request, jsonify, current_app, Response, g
from flask.json	import JSONEncoder
from functools	import wraps

#Need to Custom Encoder for converting set to list
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)

        return JSONEncoder.default(self, obj)

################################################################
#       Decorators
################################################################

#Login Decorator function
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        access_token = request.headers.get('Authorization')
        if access_token is not None:
            try:
                payload = jwt.decode(access_token, current_app.config['JWT_SECRET_KEY'], 'HS256')
            except jwt.InvalidTokenError:
                payload = None

            if payload is None: return Response(status=401)

            user_id	= payload['user_id']
            g.user_id	= user_id
            g.user	= get_user(user_id) if user_id else None

        else:
            return Response(status=401)

        return f(*args, **kwargs)
    return decorated_function


def create_endpoints(app, services):
    app.json_encoder = CustomJSONEncoder

    user_service = services.user_service
    tweet_service = services.tweet_service

    @app.route("/ping", methods=['GET'])
    def ping():
        return "pong"

    @app.route("/sign-up", methods=['POST'])
    def sign_up():
        new_user	= request.json
        new_user	= user_serivce.create_new_user(new_user)

        return jsonify(new_user)

    @app.route("/login", methods=['POST'])
    def login():
        credential = request.json
        authorized = user_service.login(credential)

        if authorized:
            user_credential	= user_service.get_user_id_and_password(credential['email'])
            user_id		= user_credential['id']
            token		= user_service.generate_access_token(user_id)

            return jsonify({
                'user_id'	: user_id,
                'access_token'	: token
            })
        else:
            return '', 401

    @app.route("/tweet", methods=['POST'])
    @login_reqiured
    def tweet():
        user_tweet	= request.json
        tweet		= user_tweet['tweet']
        user_id		= g.user_id

        result = tweet_service.tweet(user_id, tweet)
        if result is None:
            return 'Exceeded 300 Bytes!', 400

        return '', 200

    @app.route("/follow", methods=['POST'])
    @login_required
    def follow():
        paylaod		= request.json
        user_id		= g.user_id
        follow_id	= payload['follow']

        user_service.follow(user_id, follow_id)

        return '', 200

    @app.route("/unfollow", methods=['POST'])
    @login_required
    def unfollow():
        paylaod		= request.json
        user_id		= g.user_id
        unfollow_id	= payload['unfollow']

        user_service.unfollow(user_id, unfollow_id)

        return '', 200

    @app.route("/timeline/<int:user_id>", methods=['GET'])
    def timeline(user_id):
        timeline = tweet_service.get_timeline(user_id)

        return jsonify({
            'user_id' : user_id,
            'timeline': timeline
        })

    @app.route("/timeline", methods=['GET'])
    @login_required
    def user_timeline():
        timeline = tweet_service.get_timeline(g.user_id)

        return  jsonify({
            'user_id' : user_id,
            'timeline': timeline
        })
