import sqlite3
import datetime
import json
from itertools import product

# from ADFGVX import ADFGVX

JOGO_DB_LOCATION = '/var/jail/home/team7/db/jogo.db'
ROLES = {'instructor': 0, 'assistant': 1, 'student': 2}
ACTIONS = ["borrowed", "returned"]
ADMINS = ["jodalyst"]
HARD_CODED_ITEM_COUNT = 3

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



def create_DB(db_location):
    c = db_location.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS users (id text, username text, role int, account_created timestamp, last_swiped timestamp);''')
    c.execute(
        '''CREATE TABLE IF NOT EXISTS items (id text, username text, item text, item_count int);'''
    )
    c.execute(
        '''CREATE TABLE IF NOT EXISTS history (id text, item_name text, action text);'''
    )
    c.execute(
        '''CREATE TABLE IF NOT EXISTS swipe_history (id text, username text, action text, time timestamp);'''
    )
    return


def request_handler(request):
    JOGO_DB = sqlite3.connect(JOGO_DB_LOCATION)
    create_DB(JOGO_DB)

    if request["method"] == "GET":
        conn = sqlite3.connect(JOGO_DB_LOCATION)
        c = conn.cursor()

        if "id" in request["values"] and "item" in request["values"]:
            db_html = "<ul>"
            id, item = request["values"]["id"], request["values"]["item"]
            adfgvx = ADFGVX()
            encoded_id = adfgvx.encrypt(id)[0]
            user_item_info = c.execute('''SELECT id, item_count FROM items WHERE id=? AND item=?''', (encoded_id, item)).fetchone()

            conn.commit()
            conn.close()

            return json.dumps({"count": int(user_item_info[1])})

        if 'swipe_history' in request['values']:
            db_html = "<ul>"
            all_swipe_history = c.execute('''SELECT * FROM swipe_history;''').fetchall()

            for hist_row in all_swipe_history:
                db_html += f"\n<li>{hist_row}</li>"

            conn.commit()
            conn.close()

        return db_html +"<ul>"

        

    elif request["method"] == "POST":
        db_html = "<ul>"
        ## the "/receiveID" request
        if 'id' in request['form'] and 'username' in request['form']:
            id, username = request['form']['id'], request['form']['username']
            adfgvx = ADFGVX()
            encoded_id = adfgvx.encrypt(id)[0]
            conn = sqlite3.connect(JOGO_DB_LOCATION)
            c = conn.cursor()

            if id and username:
                user_exists = c.execute('''SELECT id FROM USERS where id=?;''', (encoded_id, )).fetchone()
                current_time = datetime.datetime.now()

                if not user_exists:
                    c.execute('''INSERT INTO users (id, username, role, account_created, last_swiped) VALUES (?,?,?,?,?);''', (
                        encoded_id, username,
                        "admin" if username in ADMINS else "student",
                        current_time, current_time))
                else:
                    c.execute('''UPDATE users SET last_swiped=? WHERE id=?''', (datetime.datetime.now(), encoded_id))
                
                if 'action' in request['form']:
                    action = request['form']['action']
                    c.execute('''INSERT INTO swipe_history (id, username, action, time) VALUES (?,?,?,?)''',
                                (encoded_id, username, action, current_time)
                            )

            all_users = c.execute('''SELECT * FROM users''').fetchall()

            for user in all_users:
                db_html += f"\n<li>{user}</li>"

            conn.commit()
            conn.close()
            return db_html + "</ul>"
            
        ## the '/itemcount' and '/history' requests
        if 'id' in request['form'] and 'item' in request['form']:
            id, item = request['form']['id'], request['form']['item']
            adfgvx = ADFGVX()
            encoded_id = adfgvx.encrypt(id)[0]
            conn = sqlite3.connect(JOGO_DB_LOCATION)
            c = conn.cursor()

            username = c.execute('''SELECT username FROM USERS where id=?;''', (encoded_id, )).fetchone()[0]

            if 'count' in request['form']:
                count = request['form']['count']

                if int(count) > HARD_CODED_ITEM_COUNT:
                    conn.commit()
                    conn.close()
                    return json.dumps({"error": "More than the maximum amount of the item has been taken."})

                c.execute(
                    '''INSERT INTO items (id, username, item, item_count) VALUES (?,?,?,?);''',
                    (encoded_id, username, item, int(count))
                )

                all_items = c.execute('''SELECT * FROM items''').fetchall()

                for item in all_items:
                    db_html += f"\n<li>{item}</li>"

                conn.commit()
                conn.close()

                return db_html + "</ul>"
            
            if 'action' in request['form']:
                action = request['form']['action']

                if action not in ACTIONS:
                    conn.commit()
                    conn.close()
                    return json.dumps({"error": "Invalid action POSTed"})

                c.execute(
                    '''INSERT INTO history (id, item_name, action) VALUES (?,?,?);''',
                    (encoded_id, item, action)
                )

                all_history = c.execute('''SELECT * FROM history;''').fetchall()

                for hist_row in all_history:
                    db_html += f"\n<li>{hist_row}</li>"

                conn.commit()
                conn.close()


                return db_html + "</ul>"

            else:
                return "Error in POST request"
    else:
        pass

