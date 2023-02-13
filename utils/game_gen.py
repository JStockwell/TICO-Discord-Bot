# Created by JStockwell on GitHub
import json
import requests

from utils.switch import switch, case
from utils.messages import post

base_url = "https://www.speedrun.com/api/v1/"

db = {
    "ico": {
        "id": "o1yrkr6q",
        "twitch": '8839',
        "role": '412463087874998274',
        "name": "ICO"
    },
    "sotc": {
        "id": "9j1l8v6g",
        "twitch": '5975',
        "role": '412463535327805440',
        "name": "Shadow of the Colossus"
    },
    "sotc(2018)": {
        "id": "y6545p8d",
        "twitch": '5975',
        "role": '412463535327805440',
        "name": "Shadow of the Colossus (2018)"
    },
    "tlg": {
        "id": "j1nvyx6p",
        "twitch": '23961',
        "role": '412463802722811904',
        "name": "The Last Guardian"
    },
    "ce": {
        "id": "y6547l0d",
        'twitch': None,
        'role': None,
        "name": "Category Extensions"
    }
}

exceptions = json.load(open("json/exceptions.json", 'r'))

def gen_db(path):
    for game in db:
        if game == "ce":
            db[game]["categories"] = create_ce_db(db[game])
        else:
            db[game]["categories"] = create_db(db[game])

    json_object = json.dumps(db, indent=3)

    with open(path, "w") as outfile:
        outfile.write(json_object)

    post("Database generated successfully!", False)

    gen_help()

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

        vars_list = []
        for variable in variables:
            if variable["is-subcategory"] == True:
                var = {
                    "name": variable["name"],
                    "var_id": variable["id"]
                }

                values = {}
                for value in variable["values"]["values"]:
                    var_name = variable["values"]["values"][value]["label"].lower().replace(" ","_")

                    if var_name in exceptions.keys():
                        var_name = exceptions[var_name]
                        
                    values[var_name] = value

                var["values"] = values

                vars_list.append(var)

        cat["variables"] = vars_list


    return result

def create_ce_db(game):
    categories = requests.get(f"{base_url}games/{game['id']}/categories").json()["data"]

    result = {
        "ce": {
            "fg": {},
            "il": {}
        },
        "ce ico": {
            "fg": {},
            "il": {}
        },
        "ce sotc": {
            "fg": {},
            "il": {}
        },
        "ce tlg": {
            "fg": {},
            "il": {}
        },
    }

    for category in categories:
        cat = {}
        cat["id"] = category["id"]
        
        variables = requests.get(f"{base_url}categories/{cat['id']}/variables").json()["data"]

        name = category["name"].lower().replace(" ","_")

        game_name = "ce"

        if name.split(":")[0][:-1] in db.keys():
            game_name += " " + name.split(":")[0][:-1]

        if name in exceptions.keys():
            name = exceptions[name]

        if category["type"] == "per-game":
            result[game_name]["fg"][name] = cat
        else:
            result[game_name]["il"][name] = cat

        vars_list = []
        for variable in variables:
            if variable["is-subcategory"] == True:
                var = {
                    "name": variable["name"],
                    "var_id": variable["id"]
                }

                values = {}
                for value in variable["values"]["values"]:
                    var_name = variable["values"]["values"][value]["label"].lower().replace(" ","_")

                    if var_name in exceptions.keys():
                        var_name = exceptions[var_name]
                        
                    values[var_name] = value

                var["values"] = values

                vars_list.append(var)

        cat["variables"] = vars_list
        

    return result

def gen_help():
    result = {}

    for game in db:
        if game == "ce":
            for ce_game in db[game]["categories"]:
                result[ce_game] = gen_help_text(db[game]["categories"][ce_game])

        else:
            result[game] = gen_help_text(db[game]["categories"])

    json_object = json.dumps(result, indent=3)

    with open("json/help.json", "w") as outfile:
        outfile.write(json_object)

    post("Help generated successfully!", False)

def gen_help_text(categories):
    text = "```"
    for category in categories["fg"]:
        cat_text = f"• {category}\n"
        for variable in categories["fg"][category]["variables"]:
            var_text = f"   • {variable['name']}\n"
            for value in variable["values"]:
                var_text += f"    • {value}\n"
            cat_text += var_text
        text += cat_text

    text += "```"
    return text