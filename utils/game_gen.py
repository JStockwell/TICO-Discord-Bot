import json
import requests

base_url = "https://www.speedrun.com/api/v1/"

db = {
    "ico": {
        "id": "o1yrkr6q"
    },
    "sotc": {
        "id": "9j1l8v6g"
    },
    "sotc(2018)": {
        "id": "y6545p8d"
    },
    "tlg": {
        "id": "j1nvyx6p"
    },
    "ce": {
        "id": "y6547l0d"
    }
}

exceptions = {
    # ICO
    "ps2_ntsc-u": "ntsc-u",
    # SotC
    "individual_normal_time_attack": "nta",
    "individual_hard_time_attack": "hta",
    "any%_queen's_sword": "queens_sword",
    "ps3_remaster": "ps3",
    "ps2_original": "ps2",
}

def gen_db(path):
    for game in db:
        if game != "ce":
            db[game]["categories"] = create_db(db[game])

    json_object = json.dumps(db, indent=3)

    with open(path, "w") as outfile:
        outfile.write(json_object)

def create_db(game):
    categories = requests.get(f"{base_url}games/{game['id']}/categories").json()["data"]

    result = {
        "fg": {},
        "il": {}
    }

    for category in categories:
        cat = {}
        cat["id"] = category["id"]
        
        variables = requests.get(f"{base_url}categories/{cat['id']}/variables").json()["data"]

        name = category["name"].lower().replace(" ","_")

        if name in exceptions.keys():
            name = exceptions[name]

        if category["type"] == "per-game":
            result["fg"][name] = cat
        else:
            result["il"][name] = cat

        vars = []
        for variable in variables:
            var = {
                "var_id": variable["id"]
            }

            values = {}
            for value in variable["values"]["values"]:
                var_name = variable["values"]["values"][value]["label"].lower().replace(" ","_")

                if var_name in exceptions.keys():
                    var_name = exceptions[var_name]
                    
                values[var_name] = value

            var["values"] = values

            vars.append(var)

        cat["variables"] = vars


    return result