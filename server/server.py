import json
import sys
sys.path.append('/var/jail/home/team7/server')

def request_handler(request):
    # importing functions
    from database import create_database
    from authentication import login, signup, tap_in, ADFGVX
    from items import change_item_count, get_items, set_item_limit, get_all_items, get_all_item_limits

    # initialize databases
    create_database()


    # extracting information from request
    method = request["method"] # GET or POST
    body = request.get("form", -1) # only for POST request (dict))
    params = request.get("values", -1) # only for GET request (dict)
    endpoint = body.get("endpoint", -1) if method == "POST" else params.get("endpoint", -1) # endpoint: specifying action

    # routers
    # for web app --------------------------------------------------------------------------------
    if method == "POST" and endpoint == "login":
        # logs user into the website
        kerb = body.get("kerb", None)
        id = body.get("id", None)
        return login(kerb, id)
    elif method == "POST" and endpoint == "signup":
        # create user
        kerb = body.get("kerb", None)
        id = body.get("id", None)
        first_name = body.get("first_name", None)
        last_name = body.get("last_name", None)
        return signup(kerb, id, first_name, last_name) 
    elif method == "POST" and endpoint == "set-item-limit":
        # staff sets the max item limit per item
        encoded_id = body.get("id", None)
        item_name = body.get("item_name", None)
        item_limit = body.get('item_limit', None)
        return set_item_limit(encoded_id, item_name, item_limit)
    elif method == "GET" and endpoint == "all-items":
        encoded_id = params.get("id", None)
        return get_all_items(encoded_id)
    elif method == "GET" and endpoint == "items-limits":
        encoded_id = params.get("id", None)
        return get_all_item_limits(encoded_id)
    elif method == "GET" and endpoint == "history":
        # get user's history
        pass
    # for arduino --------------------------------------------------------------------------------
    elif method == "POST" and endpoint == "items":
        # change user's items data & add to history
        item_name = body.get("item_name", None)
        item_count = body.get('item_count', None)
        return change_item_count(item_name, item_count)
    elif method == "POST" and endpoint == "tap-in":
        # taps user in with id
        id = body.get("id", None)
        return tap_in(id)
    elif method == "GET" and endpoint == "items":
        # get user's item data
        id = params.get("id", None)
        item = params.get("item", None)
        return get_items(id, item)
    # for testing ---------------------------------------------------------------------------------
    elif method == "POST" and endpoint == "test":
       return json.dumps({'status': 200, 'message': f"POST request received. \n Request: {request}"}) 
    elif method == "GET" and endpoint == "test":
       return json.dumps({'status': 200, 'message': f"GET request received. \n Request: {request}"}) 
    else:
        return json.dumps({'status': 404, 'message': f"Request: {request} \n The endpoint does not exist."})


