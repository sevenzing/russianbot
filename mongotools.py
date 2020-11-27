import pymongo

variable_names = ['game_in_process', 'current_q', 'count', 'name', 'score', 'questions', 'realname']


def create_new_user(db, id, username, realname):
    try:
        new_user = {'user_id': id,
                    'game_in_process': 0,
                    'current_q': '()',
                    'count': 0,
                    'name': username,
                    'score': 0,
                    'questions': 0,
                    'realname': realname}
        db.save(new_user)
        return True
    except:
        return False


def get_user(db, user_id):
    try:
        user = None
        for i in db.find({'user_id': user_id}):
            user = i
            break
    except:
        raise

    return user


def update_user(db, user_id, game_in_process=None, current_q=None, count=None,
                name=None, score=None, questions=None, realname=None):
    new_user_options = {}

    for i, option in enumerate([game_in_process, current_q, count, name, score, questions, realname]):
        if option is not None:
            new_user_options[variable_names[i]] = option
    try:
        db.update({'user_id': user_id}, {'$set': new_user_options})
    except Exception as e:
        raise

    return True


def user_in_database(db, user_id):
    if get_user(db, user_id) is None:
        return False
    return True


def get_top_users(db, amount=5):
    users = []
    for i, user in enumerate(sorted(db.find({'score': {'$gt': 0}}), key=lambda x: x['score'], reverse=True)):
        if i >= amount:
            break
        users.append(user)

    return users


if __name__ == '__main__':
    MONGO_DB_LOGIN = 'user1'
    MONGO_DB_PASSWORD = '6CFcThxQRy33Zwf'
    client = pymongo.MongoClient(get_url_mongo(MONGO_DB_LOGIN, MONGO_DB_PASSWORD))
    pymongo.MongoClient()
    print(dir(client))
    print(client.database_names)
    db = client.russian_db.collections1
    #create_new_user(db, 3, 'third', 'lol lovna')
    #update_user(db, 3, score=3)
    print(get_user(db, 3))
