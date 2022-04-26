import sqlite3
import datetime
import json

JOGO_DB_LOCATION = '/var/jail/home/team7/db/jogo.db'

def change_item_count(item_name, item_count):
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
    pass

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
    pass

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
    pass