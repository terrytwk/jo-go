import imp
from os import access
import sqlite3
import datetime
import json

from authentication import ADFGVX

JOGO_DB_LOCATION = '/var/jail/home/team7/db/jogo.db'

def change_item_count(item_name, item_count, action):
    """
    Adds or Removes user's items by item_count

    Parameters:
    * item_name (str): name of the item we are changing
    * item_count (int): amount we are changing items by (negative := returning; positive := borrowing)

    Returns:
        success or fail (if borrowed amount is more than max limit) message and user's total number borrowed of that item
    """
    # add the transaction to history table
    # get id from swipe table
    # edit the items table
    # return the total number of items

    conn = sqlite3.connect(JOGO_DB_LOCATION)
    c = conn.cursor()

    encoded_id = c.execute('''SELECT id from swipe ORDER BY time DESC LIMIT 1''').fetchone()[0]
    item_limit = c.execute('''SELECT max_limit from item_limits WHERE item_name=?''', (item_name, )).fetchone()[0]

    if int(item_count) > item_limit:
        conn.commit()
        conn.close()
        return json.dumps({"status": 400, "message": f'''Transaction failed. User with id {encoded_id} removed > than {item_count} of {item_name}s.'''})
    
    c.execute(
        '''INSERT INTO items (id, item, item_count) VALUES (?,?,?);''',
          (encoded_id, item_name, int(item_count))
    )

    # TODO: verify action column
    c.execute(
        '''INSERT INTO history (id, item, action) VALUES (?,?,?);''',
          (encoded_id, item_name, action)
    )

    conn.commit()
    conn.close()

    # TODO where to get totals from?

    return json.dumps(
        {
        "status": 200, 
        "message": f'''User with id {encoded_id} successfully removed {item_count} {item_name}s.''',
        "action": 0 if action == "borrow" else 1, "count": int(item_count)
        }
    )
    

def get_items(id):
    """
    Gets user's items data

    Parameters:
    * id (int): user's ID number

    Returns:
        item_name:item_count pairs (dict)
    """
    # encrypt the id
    # get all the items and their counts from items table

    user_items = {"status": 200, "message": "GET request successful."}
    conn = sqlite3.connect(JOGO_DB_LOCATION)
    c = conn.cursor()

    user_item_db_info = c.execute(
        '''SELECT * FROM items WHERE id=?''', (id)
    ).fetchall()

    for id, item, item_count in user_item_db_info:
        user_items[item] = item_count

    conn.commit()
    conn.close()

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

    conn = sqlite3.connect(JOGO_DB_LOCATION)
    c = conn.cursor()
    access_level = c.execute(
        '''SELECT user_type FROM users WHERE id=?''', (id, )
    ).fetchone()

    if access_level[0] != "staff":
        return json.dumps({"code": "400", "message": "Error. User cannot set item limits."})
    
    item_exists = c.execute('''SELECT * FROM item_limits WHERE item_name=?''', (item_name, )).fetchone()

    if item_exists:
        c.execute(
            '''UPDATE item_limits SET max_limit=? WHERE item=?''', (item_limit, item_name)
        )
        action = "added"
    else:
        c.execute(
            '''INSERT INTO item_limits (item_name, max_limit) VALUES (?, ?)''',
            (item_name, item_limit)
        )
        action = "updated"
        
    
    conn.commit()
    conn.close()

    return json.dumps({"status": 200, "message": f'''User successfully {action} item limits.'''})
        