import sqlite3

DATABASE_NAME = 'instastalk.db'

def createTable():
    '''
        Create table - users
    '''
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users 
                  (email NVARCHAR(64),
                   cookie NVARCHAR(1028),
                   last_login INT)''')
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        conn.close()

def insert(email, cookie, last_login):
    '''
        insert row 
    '''  
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        c = conn.cursor()
        c.execute('''INSERT INTO users VALUES(
                  '{email}', '{cookie}', {last_login})
                  '''.format(email=email,
                             cookie=cookie, 
                             last_login=last_login))
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        conn.close()

def update(email, cookie, last_login):
    '''
        update row (logout or re-login to update token)
    '''
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        c = conn.cursor()
        c.execute('''Update users
                  SET cookie = '{cookie}', last_login = {last_login}
                  WHERE email = '{email}'
                  '''.format(cookie=cookie,
                             last_login=last_login,
                             email=email))
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        conn.close()

def delete(email):
    '''
        delete row - for logout
    '''
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        c = conn.cursor()
        c.execute(''' DELETE FROM users WHERE email='{email}'
                  '''.format(email=email))
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        conn.close()

def getUser(email):
    '''
        get row data by email
    '''
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        c = conn.cursor()
        c.execute(''' SELECT * FROM users WHERE email='{email}'
                  '''.format(email=email))
        row = c.fetchone()
    except Exception as e:
        print(e)
        row = None 
    finally:
        conn.close()
        return row

def getAll():
    '''
        get row data 
    '''
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        c = conn.cursor()
        c.execute(''' SELECT * FROM users ''')
        rows = c.fetchall()
    except Exception as e:
        print(e)
        rows = None
    finally:
        conn.close()
    return rows

