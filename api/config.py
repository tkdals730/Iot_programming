db ={
    'user' : 'root',
    'password' : 'test1234',
    'database': 'miniter',
    'port' : 3306,
    'host' : 'localhost'
}
DB_URL = f"mysql+mysqlconnector://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}?charset=utf8"