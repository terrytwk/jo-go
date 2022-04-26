import json
import sys
sys.path.append('/var/jail/home/team7/server')

def request_handler(request):
    # importing functions
    from database import create_database
    from authentication import login, signup, ADFGVX
    from items import change_item_count, get_items, set_item_limit

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
        id = body.get("id", None)
        item_name = body.get("item_name", None)
        item_limit = body.get('item_limit', None)
        return set_item_limit(id, item_name, item_limit)
    elif method == "GET" and endpoint == "items":
        # get user's item data
        id = params.get("id", None)
        return get_items(id)
    elif method == "GET" and endpoint == "history":
        # get user's history
        pass
    # for arduino --------------------------------------------------------------------------------
    elif method == "POST" and endpoint == "items":
        # change user's items data & add to history
        item_name = body.get("item_name", None)
        item_count = body.get('item_count', None)
        action = body.get('action', None)
        return change_item_count(item_name, item_count, action)
        pass
    elif method == "POST" and endpoint == "tap-in":
        # taps user in with id
        pass
    # for testing ---------------------------------------------------------------------------------
    elif method == "POST" and endpoint == "test":
       return json.dumps({'status': 200, 'message': f"POST request received. \n Request: {request}"}) 
    elif method == "GET" and endpoint == "test":
       return json.dumps({'status': 200, 'message': f"GET request received. \n Request: {request}"}) 
    else:
        return json.dumps({'status': 404, 'message': f"Request: {request} \n The endpoint does not exist."})


