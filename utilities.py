import json
import os

import requests
from bs4 import BeautifulSoup
import data_class


def convert_div_to_dict(divs) -> dict[int, dict]:
    devs = {}
    for div in divs:
        link = div.find_all("td")[1].a["href"]
        sign_index = link.find("=")
        developer_id = link[sign_index + 1:]
        data = div.text.split("\n")
        devs[data[2]] = {
            "Rating index": int(data[1][:-1]),
            "Id": developer_id
        }
    return devs


def save_to_json(data: dict | list, json_name: str, operation_type: str = "r", sort_key_func=None) -> (int, str):
    """
    Save data to json file
    :param data: dict with information
    :param json_name: json file name
    :param operation_type: type of interaction with json file: a - append new data to file, r - rewrite all information
    :param sort_key_func: is you want to sort data, write here function, which will sort data
    """
    with open(os.path.abspath(json_name), 'w+') as file:
        if operation_type == "a":
            json_data = file.read()
            if json_data == "":
                additional_data = {} if isinstance(data, dict) else []
                print(f"No data in file: {json_data}")
            else:
                additional_data = json.loads(json_data)
            if isinstance(data, dict):
                additional_data.update(data)
            elif isinstance(data, list):
                additional_data.extend(data)
            else:
                return 203, "Error data"
            if len(additional_data) < data_class.size_history:
                return 202, f"Size history fail. Was: {data_class.size_history}. Now: {len(additional_data)}"
            data_class.size_history = len(additional_data)
        if isinstance(data, dict):
            sorted_data = dict((sorted(additional_data.items(), key=sort_key_func)))
        elif isinstance(data, list):
            sorted_data = list(sorted(additional_data, key=sort_key_func))
        else:
            return 203, "Error data"
        json.dump(sorted_data, file, indent=4)
        return 200, "Succeed"


def get_developers_information(rating_range: tuple, json_name: str = "", operation_type: str = "r") -> dict[int, dict]:
    """
    Return information about developers from rating, which presents most installed application developers on Google Play
    :param rating_range: range of rating
    :param json_name: if you want to save information to json file, you can provide json file name
    :param operation_type: type of interaction with json file: a - append new data to file, r - rewrite all information
    :return: dict with information
    """
    url = "https://www.androidrank.org/developers/ranking?&start="
    developers = {}
    for index in range(rating_range[0], rating_range[1], 20):
        print(index)
        using_url = url + str(index)
        response = requests.get(using_url, headers={
            "User-Agent": "Googlebot"
        })
        # Проверяем статус ответа
        if response.status_code == 200:
            # Парсим HTML контент с помощью BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            divs = soup.find_all('tr', class_='odd')
            developers.update(convert_div_to_dict(divs))
            divs = soup.find_all('tr', class_='even')
            converted_divs = convert_div_to_dict(divs)
            developers.update(converted_divs)
        else:
            print(f'Error {response.text}')
    # for i in range(rating_range[1] + 1, index + 20):
    #     developers.pop(i, None)
    sorted_dict = dict(sorted(developers.items(), key=lambda info: info[1]["Rating index"]))
    if json_name != "":
        save_to_json(sorted_dict, json_name, operation_type, sort_key_func=lambda info: info[1]["Rating index"])
    return sorted_dict


def get_info_about_developer_by_id(developer_id) -> dict | str:
    url = "https://www.androidrank.org/developer?id=" + str(developer_id)
    response = requests.get(url, headers={
        "User-Agent": "Googlebot"
    })
    developer_info = {}
    # Check answer status
    if response.status_code == 200:
        # Parse HTML contet with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        divs = soup.find_all('table', class_='appstat')[0].find_all("tr")
        developer_info["Title"] = divs[0].find("td").text
        developer_info["Country"] = divs[1].find("td").a.text
        developer_info["Address"] = divs[2].find("td").text
        developer_info["Web"] = divs[3].find("td").text
        developer_info["Total ratings"] = int(divs[4].find("td").text.replace(",", ""))
        developer_info["Average rating"] = float(divs[5].find("td").text)
        developer_info["Installs (achieved)"] = int(divs[6].find("td").text.replace(",", ""))

        apps = soup.find_all("table", class_="table")
        developer_info["Number of apps"] = len(apps[0].find_all("tr")) - 1
        apps_dict = {}
        for app in apps[0].find_all("tr")[1:]:
            apps_dict[app.a.text] = app.a["href"]
        developer_info["Apps"] = apps_dict
        return developer_info
    else:
        return response.text


def get_info_about_developer_by_name(developer_name: str, json_name: str) -> dict | str:
    with open(json_name, "r") as json_file:
        json_data = json_file.read()
    developers: dict = json.loads(json_data)
    developer: dict | str = developers.get(developer_name, "None")
    if developer == "None":
        return "There is no such a developer"
    else:
        developer_id = developer["Id"]
        return get_info_about_developer_by_id(developer_id)


def get_info_about_app_by_link(link: str) -> dict | str:
    """
    Return information about application
    :param link: link to application on androidrank.org.
    For example /application/clash_of_clans/com.supercell.clashofclans
    :return: if everything is okay, return dict with information, otherwise return error text
    """
    url = "https://www.androidrank.org" + link
    response = requests.get(url, headers={
        "User-Agent": "Googlebot"
    })
    app_data = {}
    # Check answer status
    if response.status_code == 200:
        # GENERAL STATS
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table', class_='appstat')
        for table in tables:
            application_info = {}
            for stat in table.find_all("tr"):
                application_info[stat.th.text[:-1]] = stat.td.text
            app_data[table.caption.text] = application_info
        rating_div = soup.find_all("div", class_="row")
        current_market_position = int(rating_div[2].find_next_sibling().find_all("em")[-2].text[1:])
        app_data["Rating scores"]["Current market position by number of ratings"] = current_market_position

        # RELATED APPS
        related_apps_list = []
        for related_apps in rating_div[1].find_all("div", class_="flex-shrink-0 m-1"):
            related_apps_list.append(related_apps.img["alt"])
        app_data["Related apps"] = related_apps_list

        # DOWNLOAD MILESTONES
        milestone_table = soup.find_all('table', class_='download_milestones')
        milestones_dict: dict[int, str] = {}
        for milestone in milestone_table[0].find_all("tr"):
            date = milestone.th.text
            number = int(milestone.td.find_all("em")[1].text.replace(",", ""))
            milestones_dict[number] = date
            milestones_dict = dict(sorted(milestones_dict.items()))
        app_data["Download level stats"] = milestones_dict

        # META DATA
        app_data["Meta data"] = {"Service link": link}

        return app_data
    else:
        return response.text


def get_all_developer_games(developer_id: int | str, limit: int = -1) -> tuple[tuple[str, str], dict]:
    """
    Return information about operation in format of ((operation code, operation code description), list with links to
    all developer games)
    """
    try:
        developer = get_info_about_developer_by_id(developer_id)
        app_list = {}
        if isinstance(developer, str):
            separation_index = developer.find(":")
            return (developer[:separation_index], developer[separation_index:]), app_list
        else:
            apps: dict = developer["Apps"]
            count = 0
            for link in apps.values():
                if 0 < limit <= count:
                    return ("201", "Operation was interrupted"), app_list
                count += 1
                app = get_info_about_app_by_link(link)
                if isinstance(app, str):
                    separation_index = app.find(":")
                    return (app[:separation_index], app[separation_index:]), app_list
                app_list[app["Android application info"]["Title"]] = app
    except Exception as err:
        return ("404", str(err)), {}
    return ("200", "Succeed"), app_list
