import imp
from os import access
import sqlite3
import datetime
import json

from authentication import ADFGVX

JOGO_DB_LOCATION = '/var/jail/home/team7/db/jogo.db'

def change_item_count(item_name, item_count):
    """
    Adds or Removes user's items by item_count

    Parameters:
    * item_name (str): name of the item we are changing
    * item_count (int): current amount of items owned by user

    Returns:
        success or fail (if borrowed amount is more than max limit) message and user's total number borrowed of that item
    """
    # add the transaction to history table
    # get id from swipe table
    # edit the items table
    # return the total number of items

    conn = sqlite3.connect(JOGO_DB_LOCATION)
    c = conn.cursor()
    status = 200

    encoded_id = c.execute('''SELECT id from swipe ORDER BY time DESC LIMIT 1''').fetchone()[0]
    item_limit = c.execute('''SELECT max_limit from item_limits WHERE item_name=?''', (item_name, )).fetchone()
    prev_items = c.execute('''SELECT item_count from items WHERE id=? AND item_name=?''', (encoded_id, item_name)).fetchone()

    if not prev_items:
        prev_items = 0
        c.execute(
        '''INSERT INTO items (id, item_name, item_count) VALUES (?,?,?);''',
          (encoded_id, item_name, int(item_count))
    )
    else:
        prev_items = prev_items[0]
        c.execute(
            '''UPDATE items SET item_count=? WHERE id=? AND item_name=?''',
            (int(item_count), encoded_id, item_name)
        )
    
    diff = int(item_count) - prev_items

    if item_limit and abs(diff) > item_limit[0]:
       status = 400
    
    action = "returned" if diff < 0 else "borrowed"

    c.execute(
        '''INSERT INTO history (id, item_name, action) VALUES (?,?,?);''',
          (encoded_id, item_name, action)
    )

    conn.commit()
    conn.close()

    return json.dumps(
        {
        "status": status, 
        "message": f'''User with id {encoded_id} {action} {abs(diff)} {item_name}s and currently has {item_count} {item_name}s.''',
        "item_count": int(item_count)
        }
    )
    

def get_items(id=None, item=None):
    """
    Gets user's items data

    Parameters:
    * id (int): user's ID number

    Returns:
        item_name:item_count pairs (dict)
    """
    # encrypt the id
    # get all the items and their counts from items table
    cipher = ADFGVX()

    user_items = {"status": 200, "message": "GET request successful."}
    conn = sqlite3.connect(JOGO_DB_LOCATION)
    c = conn.cursor()

    # If ID is defined, encrypt it and use it, otherwise simply get from the swipe history table
    if id != None:
        encoded_id = cipher.encrypt(id)
    else:
        encoded_id = c.execute('''SELECT id from swipe ORDER BY time DESC LIMIT 1''').fetchone()[0]
    
    user_item_db_info = c.execute(
        '''SELECT * FROM items WHERE id=?''', [encoded_id]
    ).fetchall()


    if not user_item_db_info:
        c.execute(
        '''INSERT INTO items (id, item_name, item_count) VALUES (?,?,?);''',
          (encoded_id, item, 0)
        )
        user_items[item] = 0
          
    else:
        for id, item, item_count in user_item_db_info:
            user_items[item] = item_count
    
    conn.commit()
    conn.close()

    if item != None:
        return json.dumps({"status": 200,  "message": "GET request successful.", item: user_items[item]})

    return json.dumps(user_items)


def set_item_limit(id, item_name, item_limit):
    """
    Changes the maximum number of items a student can take

    Parameters:
    * id (int): staff's ID number (must be staff's to authorize; NOT student's)
    * item_name (str): name of the item we are changing the limit of
    * item_limit (int): the new maximum number students can take

    Returns:
        item_name and item_limit
    """
    # check if the id is staff's
    # change item_limits table
    cipher = ADFGVX()
    encoded_id = cipher.encrypt(id)[0]
    
    conn = sqlite3.connect(JOGO_DB_LOCATION)
    c = conn.cursor()
    access_level = c.execute(
        '''SELECT user_type FROM users WHERE id=?''', (encoded_id, )
    ).fetchone()

    if access_level[0] != "staff":
        return json.dumps({"status": "400", "message": "Error. User cannot set item limits."})
    
    item_exists = c.execute('''SELECT * FROM item_limits WHERE item_name=?''', (item_name, )).fetchone()

    if item_exists:
        c.execute(
            '''UPDATE item_limits SET max_limit=? WHERE item_name=?''', (item_limit, item_name)
        )
        action = "updated"
    else:
        c.execute(
            '''INSERT INTO item_limits (item_name, max_limit) VALUES (?, ?)''',
            (item_name, item_limit)
        )
        action = "added"
        
    
    conn.commit()
    conn.close()

    return json.dumps({"status": 200, "message": f'''User successfully {action} item limits.'''})
        