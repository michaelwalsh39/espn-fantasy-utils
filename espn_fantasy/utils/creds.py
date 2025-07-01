import json


def get(cred_name: str) -> str :
    try :
        with open("creds.json") as f :
            creds = json.loads(f.read())
    except FileNotFoundError :
        print("creds.json file doesn't exist in your local repo!")

    if cred_name in creds :
        return creds[cred_name]

    print(f"Cred {cred_name} doesn't exist in your creds.json file!")
