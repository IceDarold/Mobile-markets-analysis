import json


def simplify_json(original_file_name, output_file_name, limit=-1):
    """
    Make database less readable, but lighter
    :param original_file_name: name of complicated database
    :param output_file_name: name of new file
    :param limit: maximum number of apps
    :return:
    """
    structure_dict = {"Title": {
        "Android application info": {
            "Title": "",
            "Developer": "",
            "Category": "",
            "Price": "",
            "System": ""
        },
        "Rating scores": {
            "Total ratings": "",
            "Growth (30 days)": "",
            "Growth (60 days)": "",
            "Average rating": "",
            "Current market position by number of ratings": ""
        },
        "App installs": {
            "Installs (achieved)": "",
            "Installs (estimated)": ""
        },
        "Rating values": {
            "5 star ratings": "",
            "4 star ratings": "",
            "3 star ratings": "",
            "2 star ratings": "",
            "1 star ratings": ""
        },
        "Related apps": [],
        "Download level stats": {
            "level": "date"
        },
        "Meta data": {
            "Service link": ""
        }
    }}
    # Structure
    # [{}, [name : [[], [], [], [], [], {}, []]]
    # name: [[]
    with open(original_file_name, "r") as file:
        data = file.read()
        data_dict = dict(json.loads(data))
    result_list = [structure_dict]
    count = 0
    for key, value in data_dict.items():
        aai = list(value["Android application info"].values())
        rs = list(value["Rating scores"].values())
        ai = list(value["App installs"].values())
        rv = list(value["Rating values"].values())
        ra = list(value["Related apps"])
        dls = list(value["Download level stats"].values())
        md = list(value["Meta data"].values())
        result_list.append([aai, rs, ai, rv, ra, dls, md])
        count += 1
        if 0 <= limit < count:
            break
    with open(output_file_name, "w") as file:
        json.dump(result_list, file)


def complicate_json(simple_file_name, output_file_name, limit=-1):
    """
    Make database more readable and lighter
    :param simple_file_name: name of simple file
    :param output_file_name: name of new file
    :param limit: maximum number of apps
    :return:
    """
    with open(simple_file_name, "r") as file:
        data = file.read()
        data_dict = list(json.loads(data))

    complicated_data = {}
    count = 0
    for app in data_dict:
        if count == 0:
            count += 1
            continue
        aai = app[0]
        rs = app[1]
        ai = app[2]
        rv = app[3]
        ra = app[4]
        dls = app[5]
        md = app[6]
        app_data = {
            "Android application info": {
                "Title": aai[0],
                "Developer": aai[1],
                "Category": aai[2],
                "Price": aai[3],
                "System": aai[4]
            },
            "Rating scores": {
                "Total ratings": rs[0],
                "Growth (30 days)": rs[1],
                "Growth (60 days)": rs[2],
                "Average rating": rs[3],
                "Current market position by number of ratings": rs[4]
            },
            "App installs": {
                "Installs (achieved)": ai[0],
                "Installs (estimated)": ai[1]
            },
            "Rating values": {
                "5 star ratings": rv[0],
                "4 star ratings": rv[1],
                "3 star ratings": rv[2],
                "2 star ratings": rv[3],
                "1 star ratings": rv[4]
            },
            "Related apps": ra,
            "Download level stats": dls,
            "Meta data": {
                "Service link": md[0]
            }
        }
        complicated_data[aai[0]] = app_data
        count += 1
        if 0 <= limit <= count:
            break
    with open(output_file_name, "w") as file:
        json.dump(complicated_data, file, indent=4)

# simplify_json("apps.json", "output.json", 20000)
# complicate_json("output.json", "coml.json", 10)
