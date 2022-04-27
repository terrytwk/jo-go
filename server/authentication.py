import sqlite3
import json
import datetime
from itertools import product

JOGO_DB_LOCATION = '/var/jail/home/team7/db/jogo.db'


ROLES = {'instructor': 0, 'assistant': 1, 'student': 2}
ACTIONS = ["borrowed", "returned"]
ADMINS = ["jodalyst"]
HARD_CODED_ITEM_COUNT = 3

# For ADFGVX encryption
class ADFGVX:
    polybius = list("ADFGVX")
    alphabet = list("N13ACH8TBMO2E5RWPD4F67GI9J0QLKSUZYVX")

    def __init__(self) -> None:
        text_pairings = [p[0] + p[1] for p in product(self.polybius, self.polybius)]
        self.encode = dict(zip(self.alphabet, text_pairings))
        self.decode = dict((val, key) for (key, val) in self.encode.items())
        self.key = "custodial"  # could be randomly generated with get_non_repeating_key_of_length(9)
        self.key_length = len(self.key)
    
    def encrypt(self, message:str):
        key_table = {}
        coded_msg = ''.join([self.encode[c] for c in message.upper() if c in self.alphabet])
        print(coded_msg)

        for i in range(len(self.key)):
            key_table[self.key[i]] = coded_msg[i: len(coded_msg): self.key_length]
                
        sorted_chars = sorted(list(key_table.keys()))
        

        return " ".join(key_table[sorted_chars[i]] for i in range(len(sorted_chars))), self.key

    def decrypt(self, encrypted_message):
        enc_list = encrypted_message.split(" ")
        sort_key = sorted(list(self.key))
        
        if len(enc_list) != len(self.key) != 0:
            raise KeyError

        key_table = dict(zip(sort_key, enc_list))
        column_height = max([len(key_table[word]) for word in key_table])    
        intermediate_msg = ""

        for i in range(column_height):
            for j in range(len(self.key)):
                if i > len(key_table[self.key[j]]) - 1:
                    break
                intermediate_msg += key_table[self.key[j]][i]
        print(intermediate_msg)
        
        enc_message_array = [intermediate_msg[i:i+2] for i in range(0, len(intermediate_msg), 2)]
        return ''.join([self.decode[char] for char in enc_message_array])


def login(kerb, id):
    """
    Logs user in.

    Parameters:
    * kerb (str): user's kerberos
    * id (int): user's student id

    Returns:
        token (int) encrypted student id for authentication & first_name (str)
    """

    if kerb is None or id is None or kerb == "" or id == "":
        return json.dumps({'status': 400, 'message': 'Must provode both kerberos and ID.'})

    try: 
        adfgvx = ADFGVX()
        token = adfgvx.encrypt(id)[0] 
    except: 
        return json.dumps({'status': 401, 'message': "Login Unsuccessful"})

    conn = sqlite3.connect(JOGO_DB_LOCATION)
    c = conn.cursor()
    user_token_name = c.execute(
        '''SELECT id, first_name, user_type from users WHERE kerb=?;''', (kerb,)).fetchone()
    conn.commit()
    conn.close()

    # no user found
    if user_token_name is None:
        return json.dumps({'status': 401, 'message': "Login Unsuccessful"})


    if user_token_name[0] == token:
        return json.dumps({'status': 200, "message": "Login Successful", 'token': user_token_name[0], 'name': user_token_name[1], "is_staff": user_token_name[2] == "staff"})
    else: # user's id doesn't match
        return json.dumps({'status': 401, 'message': "Login Unsuccessful"})


def signup(kerb, id, first_name, last_name):
    """
    Signs user up

    Parameters:
    * kerb (str): user's kerberos
    * id (int): user's student id

    Returns:
        token (int) encrypted student id 
    """

    if kerb is None or id is None or first_name is None or last_name is None or kerb == "" or id == "" or first_name == "" or last_name == "":
        return json.dumps({'status': 400, 'message': 'Must provode all required information.'}) 

    try:
        adfgvx = ADFGVX()
        token = adfgvx.encrypt(id)[0] 
    except Exception as error:
        return json.dumps({'status': 401, 'message': "Signup Unsuccessful", "error": error})

    conn = sqlite3.connect(JOGO_DB_LOCATION)
    c = conn.cursor()
    c.execute(
        '''INSERT INTO users (id, kerb, first_name, last_name, user_type, created_at) VALUES (?, ?, ?, ?, ?, ?);''', (token, kerb, first_name, last_name, "student", datetime.datetime.now()))
    conn.commit()
    conn.close()

    return json.dumps({'status': 200, "message": "Signup Successful", 'id': token, 'staff': False})


def tap_in(id):
    """
    Taps user in. Creates user account if it does not exist already.

    Parameters:
    * id (int): user's student id

    Returns:
        token (int) encrypted student id 
    """
    adfgvx = ADFGVX()
    encoded_id = adfgvx.encrypt(id)[0]
    conn = sqlite3.connect(JOGO_DB_LOCATION)
    c = conn.cursor()

    if id:
        user_exists = c.execute('''SELECT id FROM USERS where id=?;''', (encoded_id, )).fetchone()
        current_time = datetime.datetime.now()

        if not user_exists:
            c.execute('''INSERT INTO users (id, user_type, created_at) VALUES (?,?,?);''', (
                encoded_id,
                "student",
                current_time))
        else:
            c.execute('''UPDATE users SET last_swiped=? WHERE id=?''', (datetime.datetime.now(), encoded_id))
        
        
        c.execute('''INSERT INTO swipe (id, time) VALUES (?,?)''',
                        (encoded_id, current_time))

    conn.commit()
    conn.close()
    return json.dumps({"code": 200, "message": f'''student with id {encoded_id} successfully signed in''', "id": encoded_id})