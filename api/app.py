from flask import Flask, request, jsonify, current_app
from flask.json.provider import DefaultJSONProvider
from sqlalchemy import create_engine, text

# JSON으로 변환할 때 set을 list로 바꿔주는 설정
# 솔직히 이해 못했어 그냥 외우 그렇데
class CustomJSONProvider(DefaultJSONProvider):
   def default(self, obj):
       if isinstance(obj, set):
           return list(obj)
       return super().default(obj)

# 데이터베이스에 연결하고 유저 저장
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

# 유저 정보 변경  이름이랑 프로필
def update_user(user):
   with current_app.database.connect() as conn:
       result = conn.execute(text("""
           UPDATE users 
           SET name = :name, profile = :profile 
           WHERE id = :user_id
       """), user)
       conn.commit()
       return result.rowcount

   
# 데이터베이스에 연결하고 유저 조회
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

# 트윗 글남기고 저장
def insert_tweet(user_tweet):
   with current_app.database.connect() as conn:
       result = conn.execute(text("""
           INSERT INTO tweets (
               user_id,
               tweet
           ) VALUES (
               :id,
               :tweet
           )
       """), user_tweet)
       conn.commit()
       return result.rowcount

# 팔로우하는 기능
def insert_follow(user_follow):
   with current_app.database.connect() as conn:
       result = conn.execute(text("""
           INSERT INTO users_follow_list (
               user_id,
               follow_user_id
           ) VALUES (
               :id,
               :follow
           )
       """), user_follow)
       conn.commit()
       return result.rowcount
# 트윗삭제
def delete_tweet(tweet_id):
   with current_app.database.begin() as conn:
       result = conn.execute(text("""
           DELETE FROM tweets
           WHERE id = :tweet_id
       """), {'tweet_id': tweet_id})
       return result.rowcount


# 언팔기능
def insert_unfollow(user_unfollow):
   with current_app.database.connect() as conn:
       result = conn.execute(text("""
           DELETE FROM users_follow_list
           WHERE user_id = :id
           AND follow_user_id = :unfollow
       """), user_unfollow)
       conn.commit()
       return result.rowcount
# 전체 유저 조회 기능
def get_all_users():
   with current_app.database.connect() as conn:
       users = conn.execute(text("""
           SELECT
               id,
               name,
               email,
               profile
           FROM users
       """)).fetchall()

   return [{
       'id'      : user[0],
       'name'    : user[1],
       'email'   : user[2],
       'profile' : user[3]
   } for user in users]

# 이건 모르겠다.
# Flask 서버를 만드는 공장 함수
# 1. Flask 객체 생성
# 2. JSON 설정
# 3. config 불러오기
# 4. DB 연결
# 5. URL 라우트 등록
# 6. app 반환
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

    # 어떤요청이오는지 
    # 오는 요청에따라서 해결할 로직
    @app.route("/ping", methods=['GET'])
    def ping():
        return "pong"

    # 회원가입 로직
    @app.route("/sign-up", methods=['POST'])
    def sign_up():
        new_user = request.json
        new_user_id = insert_user(new_user)
        new_user = get_user(new_user_id)
        return jsonify(new_user)
    

    # 트윗글 로직
    @app.route('/tweet', methods=['POST'])
    def tweet():
        user_tweet = request.json
        tweet = user_tweet['tweet']

        if len(tweet) > 300:
            return '300자를 초과했습니다.', 400

        insert_tweet(user_tweet)
        return '', 200

    # 팔로우 로직
    @app.route('/follow', methods=['POST'])
    def follow():
        payload = request.json
        insert_follow(payload)
        return '', 200
    
    # 유저 조회 라우트
    @app.route('/user/<int:user_id>', methods=['GET'])
    def get_user_info(user_id):
        user = get_user(user_id)
        if user is None:
            return '사용자가 존재하지 않습니다.', 404
        return jsonify(user)
    
    @app.route('/user/<int:user_id>', methods=['PUT'])
    def update_user_info(user_id):
        data = request.json
        data['user_id'] = user_id  

        rows = update_user(data)

        if rows == 0:
            return '사용자가 존재하지 않습니다.', 404

        return jsonify(get_user(user_id))

    # 트윗삭제 라우트
    @app.route('/tweet/<int:tweet_id>', methods=['DELETE'])
    def delete_tweet_endpoint(tweet_id):
        rows = delete_tweet(tweet_id)
        if rows == 0:
            return '트윗이 존재하지 않습니다.', 404
        return '', 200


    # 언팔 로직
    @app.route('/unfollow', methods=['POST'])
    def unfollow():
        payload = request.json
        insert_unfollow(payload)
        return '', 200
    # 전체 유저 조회 
    @app.route('/users', methods=['GET'])
    def user_list():
        return jsonify(get_all_users())

    # 타임라인 로직
    @app.route('/timeline/<int:user_id>', methods=['GET'])
    def timeline(user_id):
        return jsonify({
            'user_id'  : user_id,
            'timeline' : get_timeline(user_id)
        })

    return app


# 타임라인 가져오는 함수
def get_timeline(user_id):
    with current_app.database.connect() as conn:
        timeline = conn.execute(text("""
           SELECT
               t.user_id,
               t.tweet
           FROM tweets t
           LEFT JOIN users_follow_list ufl ON ufl.user_id = :user_id
           WHERE t.user_id = :user_id
           OR t.user_id = ufl.follow_user_id
       """), {'user_id': user_id}).fetchall()

    return [{
       'user_id' : tweet[0],
       'tweet'   : tweet[1]
    } for tweet in timeline]
