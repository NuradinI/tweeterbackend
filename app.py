from flask import Flask, request, Response
import mariadb 
import dbcreds
import json
from flask_cors import CORS
import random
import string

def CreateloginToken(size=50, chars=string.ascii_uppercase + string.digits):
     return ''.join(random.choice(chars) for _ in range(size))

app = Flask(__name__)
CORS(app)

@app.route('/api/users', methods = ['GET', "POST", "PATCH", 'DELETE'])
def users():
    if request.method == 'GET':
        #same tuple error
        conn = None
        cursor = None
        users = None
        user = None
        user_id = request.args.get('userId')
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, port=dbcreds.port, database=dbcreds.database, user=dbcreds.user) 
            cursor = conn.cursor()
            if (user_id != None):
                cursor.execute('SELECT user id, email, username, bio, birthdate WHERE id=?', [user_id])
            else:
                cursor.execute("SELECT email, username, bio, birthdate FROM User")
            users = cursor.fetchall()
        except Exception as error:
            print('Could not grab users')
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(users != None):
                all_users = []
                for user in users:
                    user_data = {
                        "userId" : user[0],
                        "email" : user[1],
                        "username": user[2],
                        "bio": user[3],
                        "birthdate": user[4]
                    }
                    all_users.append(user_data)
                return Response(json.dumps(users, default=str), mimetype='application/json', status=200)
            else:
                return Response('Something went wrong...', mimetype='text/html', status=500)
    
    elif request.method == 'POST':
        conn = None
        cursor = None
        user = None
        rows = None
        email = request.json.get('email')
        username = request.json.get('username')
        bio = request.json.get('bio')
        birthdate = request.json.get('birthdate')
        password = request.json.get('password')
        
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, port=dbcreds.port, database=dbcreds.database, user=dbcreds.user) 
            cursor = conn.cursor()
            cursor.execute('INSERT INTO User(email, username, bio, birthdate, password) VALUES (?,?,?,?,?)', [email, username, bio, birthdate, password,])
            rows = cursor.rowcount
            if (rows == 1):
                loginToken = CreateloginToken()
                userId = cursor.lastrowid
                cursor.execute('INSERT INTO login(logintoken, id) VALUES(?,?)', [loginToken, userId])
                conn.commit()
                rows = cursor.amount
        except Exception as error:
            print('Something went wrong')
            print(error)

        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if( rows == 1):
                users_post = {
                    #am i suppose to put the userId and loginToken in here?
                    "email" : email,
                    "username": username,
                    "bio" : bio,
                    "birthdate" : birthdate,
                    
                }
                return Response(json.dumps(users_post, default=str), mimetype='application/json', status=201)
            else:
                return Response('User not made....', mimetype='text/html', status=500)

    elif request.method == 'PATCH':
        conn = None
        cursor = None
        logintoken = request.json.get('loginToken')
        bio = request.json.get('bio')
        rows= None
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, port=dbcreds.port, database=dbcreds.database, user=dbcreds.user) 
            cursor = conn.cursor()
            cursor.execute('SELECT `user-fk` FROM login WHERE logintoken=?',)
            logged_in = cursor.fetchone()
            if logged_in:
                if bio != '' and bio != None:
                    cursor.execute('UPDATE User SET bio=? WHERE id=?', [bio, user_id])
                conn.commit()
                rows = cursor.rowcount
                cursor.execute('SELECT * FROM User WHERE id=?', [logged_in[0],])
                user = cursor.fetchall()
        except Exception as error:
            print('Something went wrong...')
            print(error)
        
        finally:
            if (cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if (rows != None):
                user_data = {
                    "userId": logged_in[0],
                    "bio": bio
                }
                return Response(json.dumps(user_data, default=str), mimetype='application/json', status=204)
            else:
                return Response('Failed Update...', mimetype='text/html', status=500)

    elif request.method == 'DELETE':
        conn = None
        cursor = None
        logintoken = request.json.get('loginToken')
        password = request.json.get('password')
        rows= None
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, port=dbcreds.port, database=dbcreds.database, user=dbcreds.user) 
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM login WHERE logintoken=?', [logintoken])
            user = cursor.fetchall()
            if user[0][1] == logintoken:
                cursor.execute('DELETE FROM User WHERE id=? AND password=?', [user[0][2], password])
                conn.commit()
                rows = cursor.rowcount

        except Exception as error:
            print('Something went wrong')
            print(error)

        finally:
            if (cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(rows == 1):
                return Response('Successfull Delete!', mimetype='text/html', status=204 )
            else:
                return Response('Failed Delete...', mimetype='text/html', status=500)

@app.route('/api/login', methods = ['POST', "DELETE"])
def login():
    if request.method == 'POST':
        conn = None
        cursor = None
        email = request.json.get('email')
        password = request.json.get('password')
        loginToken = CreateloginToken()
        rows = None
        user = None
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, port=dbcreds.port, database=dbcreds.database, user=dbcreds.user) 
            cursor = conn.cursor()
            cursor.execute('SELECT email, password, id FROM User WHERE email=? AND password=?', [email, password])
            user = cursor.fetchall()
            if(len(user) == 1):
                cursor.execute('INSERT INTO login(logintoken, `user-fk`) VALUES(?,?)', [loginToken, user[0][2]])
                conn.commit()
                rows = cursor.rowcount

        except Exception as error:
            print('Something went wrong')
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(rows == 1):
                
                return Response('Successfull Login!', mimetype='text/html', status=201)
            else:
                return Response('Login Failed..', mimetype='text/html', status=500)

    if request.method == 'DELETE':
        conn = None
        cursor = None
        login_token = request.json.get('loginToken')
        rows = None
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, port=dbcreds.port, database=dbcreds.database, user=dbcreds.user)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM login WHERE logintoken=?', [login_token])
            conn.commit()
            rows = cursor.rowcount
            
        except Exception as error:
                print('Something went wrong!')
                print(error)

        finally: 
                if(cursor != None):
                    cursor.close()
                if(conn != None):
                    conn.rollback()
                    conn.close()
                if(rows == 1):
                    return Response('Logged out!', mimetype='application/json', status=204)
                else:
                    return Response('Failed logout...', mimetype='text/html', status= 500)
@app.route('/api/follows', methods= ['GET', 'POST', 'DELETE'])
def follows():
    if request.method == 'GET': 
        #works
        conn = None
        cursor = None
        user_id = request.args.get('id')
        followers = None
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, port=dbcreds.port, database=dbcreds.database, user=dbcreds.user)
            cursor = conn.cursor()
            cursor.execute('SELECT follows.id, User.email, User.username, User.bio, User.birthdate FROM follows INNER JOIN User On User.id = follows.id WHERE follows.`follows-fk`=?', [user_id])
            followers = cursor.fetchall()
            print(followers)
        except Exception as error:
            print('Something went wrong!')
            print(error)
        finally:
            if(cursor!= None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(followers!= None):
                followers_data = []
                for follower in followers:
                    follower_info = {
                        'userId': follower[0],
                        'email': follower[1],
                        'username': follower[2],
                        'bio': follower[3],
                        'birthdate': follower[4]
                    }
                    followers_data.append(follower_info)
                return Response(json.dumps(followers_data, default=str), mimetype='application/json', status=200)
            else:
                return Response('Something went wrong...', mimetype='text/html', status=500)
    if request.method == 'POST':
        #works, MAKE SURE TO PASS THE FK KEY NOT THE PK 
        conn = None
        cursor = None
        follow_id = request.json.get('followId')
        loginToken =  request.json.get('loginToken')
        rows = None
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, port=dbcreds.port, database=dbcreds.database, user=dbcreds.user)
            cursor = conn.cursor()
            cursor.execute('SELECT `user-fk` from login WHERE logintoken=?', [loginToken])
            userId = cursor.fetchall()
            if userId[0][0] != follow_id:
                cursor.execute('INSERT INTO follows(`follows-fk`, `user-fk` ) VALUES(?,?)', [follow_id, userId[0][0],])
                conn.commit()
                rows = cursor.rowcount
        except Exception as error:
                print("Something went wrong")
                print(error)
        finally:
                if(cursor != None):
                    cursor.close()
                if(conn != None):
                    conn.rollback()
                    conn.close()
                if (rows == 1):

                    return Response('User has been followed!', mimetype='text/html', status=204)
                else:
                    return Response('failed...', mimetype='text/html', status=500)
    if request.method == 'DELETE':
        
        conn = None
        cursor = None
        rows = None
        loginToken =request.json.get('loginToken')
        followId = request.json.get('followId')
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, port=dbcreds.port, database=dbcreds.database, user=dbcreds.user)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM login WHERE logintoken=?', [loginToken])
            post_follow = cursor.fetchall()
            #this isnt working
            if post_follow[0][2] == loginToken and post_follow[0][1] != followId:
                cursor.execute('DELETE FROM follows WHERE `user-fk`=? AND `follows-fk`=?', [post_follow[0][1], followId])
                conn.commit()
                rows = cursor.rowcount
        except Exception as error:
            print('Something went wrong')
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if( conn!= None):
                conn.rollback()
                conn.close()
            if(rows == 1):
                return Response('deleted!', mimetype='text/html', status=204)
            else:
                return Response('Failed delete...', mimetype='text/html', status=500)
            

   
@app.route('/api/tweets', methods = ['GET', 'POST', 'PATCH', 'DELETE'])
def tweets():
    if request.method == 'GET':
        conn = None
        cursor = None
        user_tweets = None
        user_id = request.json.get('userId')
        rows = None
        row = None
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, port=dbcreds.port, database=dbcreds.database, user=dbcreds.user)
            cursor = conn.cursor()
            if (user_id != None):
                cursor.execute('SELECT tweet.content, tweet.id, tweet.`user-fk`, tweet.created_at, User.username FROM tweet INNER JOIN User ON tweet.`user-fk` = User.id WHERE User.id = ?', [user_id])
            else:
                cursor.execute('SELECT tweet.content, tweet.id, tweet.`user-fk`, tweet.created_at, User.username FROM tweet INNER JOIN User ON tweet.`user-fk` = User.id',)
            rows = cursor.fetchall()
        except Exception as error:
            print('Opps Something went wrong')
            print(error)
        except mariadb.ProgrammingError as error:
            print(error)
            print('Programmer Error')
        except mariadb.DatabaseError as error:
            print(error)
            print('Failed Database connection')
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(rows != None):
                all_thy_tweets = []
                for row in rows:
                    user_tweets = {
                        "content": row[0],
                        "tweetId": row[1],
                        "userId": row[2],
                        "createdAt": row[3],
                        "username": row[4]
                    }
                    all_thy_tweets.append(user_tweets)
                return Response(json.dumps(all_thy_tweets, default=str), mimetype='application/json', status=200)
            else:
                return Response('Oops some went wrong', mimetype='text/html', status=500)


    if request.method == 'POST':
        conn = None
        cursor = None
        content = request.json.get('content')
        loginToken = request.json.get('loginToken')
        tweetId = None
        created_at = request.json.get('createdAt')
        rows = None
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, port=dbcreds.port, database=dbcreds.database, user=dbcreds.user)
            cursor = conn.cursor()
            cursor.execute('SELECT login.`user-fk`, User.username FROM login INNER JOIN User ON login.`user-fk` = User.id WHERE login.logintoken=?', [loginToken])
            user = cursor.fetchall()
            tweet_len = len(content)
            if tweet_len <= 250 and len(user) == 1:
                cursor.execute('INSERT INTO tweet(content, `user-fk`, created_at) VALUES(?,?,?)', [content, user[0][0], created_at])
                conn.commit()
                tweetId = cursor.lastrowid
                
        except Exception as error:
            print(error)
            print('Something went wrong...')
        except mariadb.ProgrammingError as error:
            print(error)
            print('Programmer error')
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(tweetId != None):
                tweet_posts = {
                    "tweetId": tweetId ,
                    "userId": user[0][0],
                    "username": user[0][1],
                    "content": content,
                    "createdAt": created_at
                }
               
                return Response(json.dumps(tweet_posts, default=str), mimetype='application/json', status=201)
            else:
                return Response('Error...', mimetype='text/html', status=500)
    
    elif request.method == "PATCH":
        
        conn = None
        cursor = None
        rows = None
        patched_tweet_data = None
        loginToken = request.json.get('loginToken')
        tweetId = request.json.get('tweetId')
        content = request.json.get('content')
        
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, port=dbcreds.port, database=dbcreds.database, user=dbcreds.user)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM login WHERE logintoken=?', [loginToken])
            user = cursor.fetchall()
            if user[0][1] ==loginToken:
                cursor.execute('UPDATE tweet SET content=? WHERE id=?', [content, tweetId])
                conn.commit()
            rows = cursor.rowcount
            cursor.execute('SELECT * FROM tweet WHERE id=?', [tweetId])
            patched_tweet = cursor.fetchall()
        except Exception as error:
            print(error)
            print('Something went wrong')
        finally:
            if (cursor != None):
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if rows == 1:
                patched_tweet_data = {
                    "tweetId": patched_tweet[0][1],
                    "content": content
                }
                return Response(json.dumps(patched_tweet_data, default=str), mimetype='application/json', status=201)
            else:
                return Response('Something went wrong', mimetype='text/html', status=500)

    if request.method == "DELETE":
        conn = None
        cursor = None
        loginToken = request.json.get('loginToken')
        tweetId = request.json.get('tweetId')
        rows = None
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, port=dbcreds.port, database=dbcreds.database, user=dbcreds.user)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM login WHERE logintoken=?', [loginToken])
            user = cursor.fetchall()
            cursor.execute('DELETE FROM tweet WHERE id=? AND `user-fk`=?', [tweetId, user[0][1]])
            conn.commit()
            rows = cursor.rowcount

        except Exception as error:
            print('Something went wrong')
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if rows == 1:
                return Response('Successful delete!', mimetype='text/html', status=204)
            else:
                return Response('Delete failed...', mimetype='text/html', status=500)

@app.route('/api/comments', methods = ['GET', 'POST', 'PATCH', 'DELETE'])
def comments():
    if request.method == 'GET':
        conn = None
        cursor = None
        comment_data = None
        tweetId = request.args.get('tweetId')
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, port=dbcreds.port, database=dbcreds.database, user=dbcreds.user)
            cursor = conn.cursor()
            if tweetId != None and tweetId != '':
                cursor.execute('SELECT comments.*, User.username FROM comments INNER JOIN User ON comments.`user-fk` = User.id WHERE comments.tweetId=?', [tweetId])
                comment_data = cursor.fetchall()
            else:
                cursor.execute('SELECT * FROM comments')
                comment_data = cursor.fetchall()
        except Exception as error:
            print(error)
            print('Something went wrong!')
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(comment_data != None):
                user_data = []
                for comment in comment_data:
                    user_comment = {
                        "commentId": comment[2],
                        "tweetId": comment[1],
                        "userId": comment[3],
                        "username": comment[1],
                        "content": comment[0],
                        "createdAt": comment[4]
                    }
                    user_data.append(user_comment)
                return Response(json.dumps(user_data, default=str), mimetype='application/json', status=200)
            else:
                return Response('Something went wrong...', mimetype='text/html', status=500)
    
    if request.method == 'POST':
        conn = None
        cursor = None
        rows = None
        user_comment = None
        last_comment = None
        loginToken = request.json.get('loginToken')
        tweetId = request.json.get('tweetId')
        content = request.json.get('content')
        created_at = request.json.get('created_at')
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, port=dbcreds.port, database=dbcreds.database, user=dbcreds.user)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM login WHERE logintoken=?', [loginToken])
            creating_comment = cursor.fetchall()
            comment_len = len(content)
            rows = cursor.rowcount
            if comment_len <=200:
                cursor.execute('INSERT INTO comments(content, tweetId, `user-fk`, created_at) VALUES(?,?,?,?)', [content, tweetId, creating_comment[0][1], created_at])
                last_comment = cursor.lastrowid
                conn.commit()
                rows = cursor.rowcount
                cursor.execute('SELECT comments.*, User.username FROM comments INNER JOIN User ON User.id = comments.`user-fk` WHERE comments.id=?', [last_comment])
                user_comment = cursor.fetchall()
        except Exception as error:
                print(error)
                print('Something went wrong')
        finally:
                if(cursor != None):
                    cursor.close()
                if(conn != None):
                    conn.rollback()
                    conn.close()
                if(rows == 1):
                    comment_data = {
                        "commentId": last_comment,
                        "tweetId": tweetId,
                        "userId": creating_comment[0][2],
                        "username": user_comment[0][1],
                        "content": content,
                        "createdAt": created_at
                    }
                    return Response(json.dumps(comment_data, default=str), mimetype='application/json', status=201)
                else:
                    return Response('Something went wrong!', mimetype='text/html', status=500)
    
    if request.method == 'PATCH':
        conn = None
        cursor = None
        rows = None
        content = request.json.get("content")
        commentId = request.json.get("commentId")
        loginToken = request.json.get("loginToken")
        created_at = request.json.get('created_at')
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM login WHERE logintoken = ?", [loginToken,])
            updating_comment = cursor.fetchall()
            cursor.execute("UPDATE comments SET content = ? WHERE id = ? AND `user-fk`=?", [content, commentId, updating_comment[0][1]])
            conn.commit()
            rows = cursor.rowcount
            if rows != None:
                cursor.execute("SELECT comments.*, User.username FROM User INNER JOIN comments ON User.id = comments.`user-fk` WHERE comments.id = ?", [commentId,])
                the_user_comment = cursor.fetchall()
    
        except Exception as error:
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if (rows == 1):
                comment_data = {
                    "commentId": commentId,
                    "tweetId": the_user_comment[0][3],
                    "userId": the_user_comment[0][4],
                    "username": the_user_comment[0][5],
                    "content": content,
                    "createdAt": created_at
                }
                return Response(json.dumps(comment_data, default = str), mimetype = "application/json", status = 200)
            else:
                return Response("Something went wrong...please try again.", mimetype = "text/html", status = 500)

    if request.method == 'DELETE':
        conn = None
        cursor = None
        rows = None
        loginToken = request.json.get("loginToken")
        commentId = request.json.get("commentId")
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM login WHERE logintoken = ?", [loginToken,])
            deleting_comment = cursor.fetchall()
            cursor.execute("SELECT `user-fk` FROM comments WHERE id =?", [commentId,])
            users_comment = cursor.fetchall()
            if deleting_comment[0][1] == loginToken and deleting_comment[0][2] == users_comment[0][0]:
                cursor.execute("DELETE FROM comments WHERE id = ?", [commentId,])
                conn.commit()
                rows = cursor.rowcount
        except Exception as error:
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if (rows != None):
                return Response("Comment deleted!", mimetype="text/html", status = 204)
            else:
                return Response("Something went wrong", mimetype = "text/html", status = 500)

@app.route('/api/followers', methods = ['GET'])
def getFollowers():
    if request.method == 'GET':
        conn = None
        cursor = None
        follower_content = None
        userId = request.args.get("userId")
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute('SELECT follows.`user-fk`, User.email, User.username, User.bio, User.birthdate FROM follows INNER JOIN User ON User.id = follows.`user-fk` WHERE follows.`follows-fk`= ?', [userId,])
            followers = cursor.fetchall()
        except Exception as error:
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if (followers != None):
                follower_data = []
                for follower in followers: 
                    follower_content = {
                        "userId": follower[5],
                        "email": follower[0],
                        "username": follower[1],
                        "bio": follower[2],
                        "birthdate": follower[3]
                    }
                    follower_data.append(follower_content) 
                return Response(json.dumps(follower_data, default = str), mimetype = "application/json", status = 200)
            else:
                return Response("Something went wrong...please try again.", mimetype="text/html", status = 500)

@app.route('/api/tweet-likes', methods=['GET', 'POST', 'DELETE'])
def getTweetLikes():
    if request.method == 'GET':
        conn = None
        cursor = None
        likes = None
        likes_content = None
        tweetId = request.args.get("tweetId")
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT tweetlikes.`like-id`, tweetlikes.`user-fk`, User.username FROM tweetlikes INNER JOIN User ON User.id = tweetlikes.`user-fk` WHERE tweetlikes.`like-id` = ?", [tweetId,])
            likes = cursor.fetchall()
        except Exception as error:
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if (likes != None):
                user_data = []
                for like in likes: 
                    likes_content = {
                        "tweetId": like[0],
                        "userId": like[2],
                        "username": like[1]
                    }
                    user_data.append(likes_content) 
                return Response(json.dumps(user_data, default = str), mimetype = "application/json", status = 200)
            else:
                return Response("Something went wrong...please try again.", mimetype="text/html", status=500)
    
    if request.method == 'POST':
        conn = None
        cursor = None
        rows = None
        loginToken = request.json.get("loginToken")
        tweetId = request.json.get("tweetId")
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM login WHERE logintoken = ?", [loginToken,])
            creating_like = cursor.fetchall()
            cursor.execute("INSERT INTO tweetlikes(`like-id`, `user-fk`) VALUES(?, ?)", [tweetId, creating_like[0][1],])
            conn.commit()
            rows = cursor.rowcount
        except Exception as error:
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if (rows != None):
                return Response("Tweet Liked!", mimetype="text/html", status = 204)
            else:
                return Response("Something went wrong...please try again.", mimetype = "text/html", status = 500)

    if request.method == 'DELETE':
        conn = None
        cursor = None
        rows = None
        loginToken = request.json.get("loginToken")
        tweetId = request.json.get("tweetId")
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM login WHERE logintoken = ?", [loginToken,])
            unlike = cursor.fetchall()
            cursor.execute("DELETE FROM tweetlikes WHERE `like-id`=? AND `user-fk` = ?", [tweetId, unlike[0][1],])
            conn.commit()
            rows = cursor.rowcount
        except Exception as error:
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if (rows != None):
                return Response("unliked", mimetype="text/html", status = 204)
            else:
                return Response("Something went wrong", mimetype = "text/html", status = 500)

@app.route('/api/comment-likes', methods= ['GET', 'POST', "DELETE"])
def commentLikes():
    if request.method == 'GET':
        conn = None
        cursor = None
        likes = None
        likes_content = None
        commentId = request.args.get("commentId")
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT commentlikes.`comment-like-id`, commentlikes.`user-fk`, User.username FROM commentlikes INNER JOIN User ON User.id = commentlikes.`user-fk` WHERE commentlikes.`comment-like-id` = ?", [commentId,])
            likes = cursor.fetchall()
        except Exception as error:
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if (likes != None):
                user_data = []
                for like in likes: 
                    likes_content = {
                        "commentId": like[0],
                        "userId": like[1],
                        "username": like[2]
                    }
                    user_data.append(likes_content) 
                return Response(json.dumps(user_data, default = str), mimetype = "application/json", status = 200)
            else:
                return Response("Something went wrong", mimetype="text/html", status=500)

    if request.method == 'POST':
        conn = None
        cursor = None
        rows = None
        loginToken = request.json.get("loginToken")
        commentId = request.json.get("commentId")
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM login WHERE logintoken = ?", [loginToken,])
            making_like = cursor.fetchall()
            cursor.execute("INSERT INTO commentlikes(`comment-like-id`, `user-fk`) VALUES(?,?)", [commentId, making_like[0][1],])
            conn.commit()
            rows = cursor.rowcount
            cursor.execute("SELECT commentlikes.*, User.username FROM commentlikes INNER JOIN User ON User.id = commentlikes.`user-fk` WHERE commentlikes.`comment-like-id` = ?", [commentId,])
            likes = cursor.fetchall()
        except Exception as error:
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if (rows != None):
                return Response("Comment liked", mimetype="text/html", status = 204)
            else:
                return Response("Something went wrong", mimetype = "text/html", status = 500)

    if request.method == 'DELETE':
        conn = None
        cursor = None
        rows = None
        loginToken = request.json.get("loginToken")
        commentId = request.json.get("commentId")
        try:
            conn = mariadb.connect(host = dbcreds.host, password = dbcreds.password, user = dbcreds.user, port = dbcreds.port, database = dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM login WHERE logintoken = ?", [loginToken,])
            unlike = cursor.fetchall()
            cursor.execute("SELECT `user-fk` FROM commentlikes WHERE `comment-like-id` = ?", [commentId,])
            cursor.execute("DELETE FROM commentlikes WHERE `comment-like-id` = ? AND `user-fk` = ?", [commentId, unlike[0][1]])
            conn.commit()
            rows = cursor.rowcount
        except Exception as error:
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if (rows != None):
                return Response("unliked", mimetype="text/html", status = 204)
            else:
                return Response("Something went wrong", mimetype = "text/html", status = 500)