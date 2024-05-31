import json


def combine_two_files(first_name, second_name):
    """
    Combine two databases
    :param first_name: file in which you need to update data
    :param second_name: file from which you get additional data
    :return:
    """
    with open(second_name, "r") as file:
        data = file.read()
        data_dict = json.loads(data)
    with open(first_name, "r+") as file:
        data = file.read()
        data2_dict: dict = json.loads(data)
        data2_dict.update(data_dict)
        file.seek(0)
        file.truncate()
        json.dump(data2_dict, file, indent=4)


combine_two_files("apps.json", "apps2.json")
