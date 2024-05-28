import utilities
import json

with open("developers.json", "r") as file:
    developers_dict = json.loads(file.read())
