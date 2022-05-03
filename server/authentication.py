from email import message
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

    # first check if the user logged in is a staff --> return authorization error
    # user authorization
    # access_level = c.execute(
    #     '''SELECT user_type FROM users WHERE id=?''', (encoded_id, )
    # ).fetchone()
    # if access_level[0] != "staff":
    #     return json.dumps({"status": "400", "message": "Error. User cannot set item limits."})

    if kerb is None or id is None or first_name is None or last_name is None or kerb == "" or id == "" or first_name == "" or last_name == "":
        return json.dumps({'status': 400, 'message': 'Must provode all required information.'}) 

    try:
        adfgvx = ADFGVX()
        encoded_id = adfgvx.encrypt(id)[0] 
    except Exception as error:
        return json.dumps({'status': 401, 'message': "Signup Unsuccessful", "error": error})

    conn = sqlite3.connect(JOGO_DB_LOCATION)
    c = conn.cursor()

    # get tapped in user's token
    tapped_in_token = c.execute('''SELECT * FROM swipe''').fetchone()

    # no user is tapped in
    if not tapped_in_token:
        return json.dumps({'status': 400, "message": "Student must tap the student ID before signing up"})

    # complete user's sign up by filling up all the user's information
    c.execute(
            '''UPDATE users SET id=?, kerb=?, first_name=?, last_name=? WHERE token=?''', (encoded_id, kerb, first_name, last_name, tapped_in_token[0])
    )

    conn.commit()
    conn.close()

    return json.dumps({'status': 200, "message": "Signup Successful", 'id': encoded_id, 'staff': False})


def tapped_in_user():
    """
    Checks if a user is currently tapped in or not.

    Returns:
        boolean representing if a user is tapped in
    """
    conn = sqlite3.connect(JOGO_DB_LOCATION)
    c = conn.cursor()

    # check the swipe table 
    tapped_in_token = c.execute('''SELECT * FROM swipe''').fetchone()

    conn.commit()
    conn.close()

    # user is tapped in
    if tapped_in_token:
        return json.dumps({'status': 200, "message": "A user is tapped in", "is_user_tapped_in": True, "user": tapped_in_token})
    else: 
        return json.dumps({'status': 200, "message": "A user is NOT tapped in", "is_user_tapped_in": False}) 



def tap_in(token):
    """
    Taps user in. Creates user account if it does not exist already.

    Parameters:
    * token (string): user's token from the student ID card

    Returns:
        token (int) encrypted student id 
    """
    conn = sqlite3.connect(JOGO_DB_LOCATION)
    c = conn.cursor()

    if token:
        user_exists = c.execute('''SELECT token FROM USERS where token=?;''', (token, )).fetchone()
        current_time = datetime.datetime.now()

        if not user_exists:
            c.execute('''INSERT INTO users (token, user_type, created_at) VALUES (?,?,?);''', (
                token,
                "student",
                current_time))
        

        # Get if there are any users in the table - if there are any reject it
        card_currently_swiped = c.execute('''SELECT * FROM swipe where token=?;''', (token,)).fetchone()

        if card_currently_swiped:
            if card_currently_swiped[0] != token:
                return json.dumps({"code": 400, "message": "error, another student is already tapped in"})
        else:
            ## add them to the currently swiped table
            # 
            c.execute('''INSERT INTO swipe (token) VALUES (?);''', (token, ))

    conn.commit()
    conn.close()
    return json.dumps({"code": 200, "message": f'''student with token {token} successfully signed in''', "token": token})

def tap_out(token):
    """
    Taps user out. Removes them from the `swipe` table

    Parameters:
    * token (string): user's token from the student ID card

    Returns:
        token (int) encrypted student id 
    """
    conn = sqlite3.connect(JOGO_DB_LOCATION)
    c = conn.cursor()

    if token:
        user_exists = c.execute('''SELECT token FROM USERS where token=?;''', (token, )).fetchone()

        if not user_exists:
            return json.dumps({"code": 400, "message": "error, user to be tapped out does not exist"})
        
        # Get if there are any users in the table
        card_currently_swiped = c.execute('''SELECT * FROM swipe where token=?;''', (token,)).fetchone()

        if card_currently_swiped:
            c.execute('''DELETE FROM swipe''')     
        else:
            return json.dumps({"code": 400, "message": "error, there is no tapped in user."})

    conn.commit()
    conn.close()
    return json.dumps({"code": 200, "message": f'''student with token {token} successfully signed out''', "token": token})


def get_all_users():
    conn = sqlite3.connect(JOGO_DB_LOCATION)
    c = conn.cursor()

    all_users = c.execute('''SELECT * FROM users;''').fetchall()

    conn.commit()
    conn.close()
    return json.dumps(all_users) 