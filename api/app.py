from flask import Flask, request, jsonify, current_app
from flask.json.provider import DefaultJSONProvider
from sqlalchemy import create_engine, text

class CustomJSONProvider(DefaultJSONProvider):
   def default(self, obj):
       if isinstance(obj, set):
           return list(obj)
       return super().default(obj)

def insert_user(user):
   with current_app.database.connect() as conn:
       result = conn.execute(text("""
           INSERT INTO users (
               name,
               email,
               profile,
               hashed_password
           ) VALUES (
               :name,
               :email,
               :profile,
               :password
           )
       """), user)
       conn.commit()
       return result.lastrowid

def get_user(user_id):
   with current_app.database.connect() as conn:
       user = conn.execute(text("""
           SELECT
               id,
               name,
               email,
               profile
           FROM users
           WHERE id = :user_id
       """), {'user_id': user_id}).fetchone()

   return {
       'id'      : user[0],
       'name'    : user[1],
       'email'   : user[2],
       'profile' : user[3]
   } if user else None

def create_app(test_config=None):
   app = Flask(__name__)
   app.json_provider_class = CustomJSONProvider
   app.json = CustomJSONProvider(app)

   if test_config is None:
       app.config.from_pyfile("config.py")
   else:
       app.config.update(test_config)

   database = create_engine(app.config['DB_URL'], max_overflow=0)
   app.database = database

   # 메모리 기반 데이터 (3단계에서 DB로 교체 예정)
   app.tweets = []

   @app.route("/ping", methods=['GET'])
   def ping():
       return "pong"

   @app.route("/sign-up", methods=['POST'])
   def sign_up():
       new_user = request.json
       new_user_id = insert_user(new_user)
       new_user = get_user(new_user_id)
       return jsonify(new_user)

   @app.route('/tweet', methods=['POST'])
   def tweet():
       payload = request.json
       user_id = int(payload['id'])
       tweet = payload['tweet']

       if user_id not in app.users:
           return '사용자가 존재하지 않습니다.', 400
       if len(tweet) > 300:
           return '300자를 초과했습니다.', 400

       app.tweets.append({
           'user_id': user_id,
           'tweet': tweet
       })
       return '', 200

   @app.route('/follow', methods=['POST'])
   def follow():
       payload = request.json
       user_id = int(payload['id'])
       user_id_to_follow = int(payload['follow'])

       if user_id not in app.users or user_id_to_follow not in app.users:
           return '사용자가 존재하지 않습니다.', 400

       user = app.users[user_id]
       user.setdefault('follow', set()).add(user_id_to_follow)
       return jsonify(user)

   @app.route('/unfollow', methods=['POST'])
   def unfollow():
       payload = request.json
       user_id = int(payload['id'])
       user_id_to_follow = int(payload['unfollow'])

       if user_id not in app.users or user_id_to_follow not in app.users:
           return '사용자가 존재하지 않습니다.', 400

       user = app.users[user_id]
       user.setdefault('follow', set()).discard(user_id_to_follow)
       return jsonify(user)

   @app.route('/timeline/<int:user_id>', methods=['GET'])
   def timeline(user_id):
       if user_id not in app.users:
           return '사용자가 존재하지 않습니다.', 400

       follow_list = app.users[user_id].get('follow', set())
       follow_list.add(user_id)
       timeline = [t for t in app.tweets if t['user_id'] in follow_list]

       return jsonify({
           'user_id': user_id,
           'timeline': timeline
       })

   return app
