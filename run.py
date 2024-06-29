import asyncio
import json
import os
import re
import subprocess
import sys
import time

import aiohttp
import keyboard
import requests
from bs4 import BeautifulSoup


def pprint(data, start_time=-1, current_number=-1, total=-1, fix_length=100, show_additional_info=True):
    def format_time(seconds):
        if re.match(r'^-?\d+([.,]\d+)?$', str(seconds)):
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return ""

    def truncate_string(string, max_length):
        if len(string) > max_length:
            return string[:max_length - 3] + "..."
        return string

    if show_additional_info:
        if start_time != -1:
            elapsed_time = int(time.time() - start_time)
            time_passed = format_time(elapsed_time)
        else:
            time_passed = "-"
            elapsed_time = 0
        output = truncate_string(data, fix_length)
        if current_number != -1 and total != -1 and start_time != -1:
            time_left = int(
                (total - current_number) / (int(current_number) / elapsed_time)) if elapsed_time > 0 else "-"
            time_left = format_time(time_left)
        else:
            time_left = "-"
        if current_number == -1: current_number = "-"
        if total == -1: total = "-"
        result = f"{current_number}/{total}"
        percents = (str(round(int(current_number) / total * 100,
                              2)) if current_number != "-" and total != "-" else "-") + "%"
        final_str = f"\r{output.ljust(fix_length)} {result} {percents} | {time_passed} | Left: {time_left}"
    else:
        final_str = data
    print(final_str, end="", flush=True)


def install_packages():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


async def get_info_about_developer_by_id(developer_id, session) -> dict | str:
    url = "https://www.androidrank.org/developer?id=" + str(developer_id)
    async with session.get(url, headers={
        "User-Agent": "Googlebot"
    }) as response:
        developer_info = {}
        # Check answer st тatus
        index = 0
        if response.status == 429:
            retry_after = int(response.headers.get("Retry-After", 1))
            print(f"Too many requests - retrying after {retry_after} seconds")
            await asyncio.sleep(retry_after)
            return await get_info_about_developer_by_id(developer_id, session)
        elif response.status == 200:
            # Parse HTML content with BeautifulSoup
            soup = BeautifulSoup(await response.text(), 'html.parser')
            divs = soup.find_all('table', class_='appstat')[0].find_all("tr")
            developer_info["Title"] = ""
            developer_info["Country"] = ""
            developer_info["Address"] = ""
            developer_info["Web"] = ""
            developer_info["Total ratings"] = -1
            developer_info["Average rating"] = -1
            developer_info["Installs (achieved)"] = -1
            if divs[index].find("th").text == "Title:":
                developer_info["Title"] = divs[index].find("td").text
                index += 1
            if divs[index].find("th").text == "Country:":
                developer_info["Country"] = divs[index].find("td").a.text
                index += 1
            if divs[index].find("th").text == "Address:":
                developer_info["Address"] = divs[index].find("td").text
                index += 1
            if divs[index].find("th").text == "Web:":
                developer_info["Web"] = divs[index].find("td").text
                index += 1
            if divs[index].find("th").text == "Total ratings:":
                developer_info["Total ratings"] = int(divs[index].find("td").text.replace(",", ""))
                index += 1
            if divs[index].find("th").text == "Average rating:":
                developer_info["Average rating"] = float(divs[index].find("td").text)
                index += 1
            if divs[index].find("th").text == "Installs (achieved):":
                developer_info["Installs (achieved)"] = int(divs[index].find("td").text.replace(",", ""))
                index += 1

            apps = soup.find_all("table", class_="table")
            apps_dict = {}
            for app in apps[0].find_all("tr")[1:]:
                apps_dict[app.a.text] = app.a["href"]
            developer_info["Apps"] = apps_dict
            return developer_info
        else:
            return await response.text()


async def get_developers_page(session, url, function_information):
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

    async with session.get(url, headers={
        "User-Agent": "Googlebot"
    }) as response:
        if response.status == 429:
            retry_after = int(response.headers.get("Retry-After", 1))
            print(f"Too many requests - retrying after {retry_after} seconds")
            await asyncio.sleep(retry_after)
            return await get_developers_page(session, url, function_information)
        elif response.status == 200:
            soup = BeautifulSoup(await response.text(), 'html.parser')
            divs = soup.find_all('tr', class_='odd')
            function_information["Get_all_developers"]["Developers"].update(convert_div_to_dict(divs))
            divs = soup.find_all('tr', class_='even')
            function_information["Get_all_developers"]["Developers"].update(convert_div_to_dict(divs))
            current_count = function_information["Get_all_developers"]["Count"]
            got_count = 20 if function_information["Get_all_developers"]["Total developers"] > current_count + 20 else \
                function_information["Get_all_developers"]["Total developers"] - current_count
            function_information["Get_all_developers"]["Count"] += got_count
            pprint(f"Got {function_information["Get_all_developers"]["Count"]} developers",
                   function_information["Main"]["Start time"],
                   function_information["Get_all_developers"]["Count"],
                   function_information["Get_all_developers"]["Total developers"])
        else:
            print(f'Error {response.text}')


def get_max_index():
    return 2144


async def get_all_developers(func_information):
    url = "https://www.androidrank.org/developers/ranking?&start="
    func_information["Get_all_developers"]["Total developers"] = get_max_index()
    func_information["Get_all_developers"]["Count"] = 0
    pprint("Connecting to server")
    async with aiohttp.ClientSession() as session:
        tasks = [get_developers_page(session, url + str(index), func_information) for index in
                 range(1, func_information["Get_all_developers"]["Total developers"], 20)]
        return await asyncio.gather(*tasks)


async def get_developer_apps_links(session, dev_id, func_information: dict):
    dev_info = await get_info_about_developer_by_id(dev_id, session)
    if isinstance(dev_info, dict):
        func_information["Get_apps_links"]["Link count"] += 1
        print(f"Got info about {dev_id} (#{func_information["Get_apps_links"]["Link count"]})")
        func_information["Get_apps_links"]["Apps links list"].extend(
            ["https://www.androidrank.org" + link for link in dev_info["Apps"].values()])
        return func_information["Get_apps_links"]["Apps links list"]
    else:
        print("Error {}".format(dev_info))
        with open("log.txt", "r+") as log:
            data = log.read()
            log.write(data + dev_info + "\n")


async def get_apps_links(developer_ids, func_information: dict):
    func_information["Get_apps_links"]["Link count"] = 0
    func_information["Get_apps_links"]["Apps links list"] = []
    async with aiohttp.ClientSession() as session:
        tasks = [get_developer_apps_links(session, dev_id, func_information) for dev_id in developer_ids]
        return await asyncio.gather(*tasks)


async def get_app_by_link(url, session):
    async with session.get(url, headers={
        "User-Agent": "Googlebot"
    }) as response:
        app_data = {}
        # Check answer status
        if response.status == 429:
            retry_after = int(response.headers.get("Retry-After", 1))
            global time_error_count
            time_error_count += 1
            pprint(f"Too many requests - retrying after {retry_after} seconds")
            await asyncio.sleep(retry_after)
            return await get_app_by_link(url, session)
        if response.status == 200:
            # GENERAL STATS
            soup = BeautifulSoup(await response.text(), 'html.parser')
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
            app_data["Meta data"] = {"Service link": url}

            return app_data
        else:
            return response.text


async def get_app(session, url, func_information):
    app_info = await get_app_by_link(url, session)
    if isinstance(app_info, dict):
        func_information["Get_all_applications"]["Got application count"] += 1
        pprint(f"Got info about {url} (#{func_information["Get_all_applications"]["Got application count"]})",
               func_information["Main"]["Start time"],
               func_information["Get_all_applications"]["Got application count"],
               func_information["Get_all_applications"]["Total applications"])
        func_information["Get_all_applications"]["Apps list"].append(app_info)
    else:
        print("Error {}".format(app_info))
        with open("log.txt", "r+") as log:
            data = log.read()
            log.write(data + app_info + "\n")


async def get_all_applications(urls, func_information):
    async with aiohttp.ClientSession() as session:
        tasks = [get_app(session, url, func_information) for url in urls]
        return await asyncio.gather(*tasks)


def check_developer_info_exist(file_type) -> (bool, dict | None):
    """
    File types:
    "d" - developer info,
    "l" - apps links,
    "a" - apps info
    """
    if file_type == "d": file_name = "developers.json"
    elif file_type == "l": file_name = "apps_links.json"
    elif file_type == "a": file_name = "apps.json"
    else: raise ValueError(f"invalid file type: '{file_type}'")

    if not os.path.exists(file_name): return False,
    with open(file_name, "r") as f:
        try:
            data = json.load(f)
        except json.decoder.JSONDecodeError:
            return False,

    # Data should be in dict format
    if not isinstance(data, dict):
        return False,
    update_date = data.get("Update date")
    # File is damaged
    if update_date is None: return False,
    return True, update_date


def check_files(file_type):
    """
    File types:
    "d" - developer info,
    "l" - apps links,
    "a" - apps info
    """
    return True,


def main():
    func_information: dict = {
        "Main": {
            "Start time": time.time()
        }
    }
    print("Starting all processes...")

    print("1/3. Trying to get information about developers")
    func_information["Get_all_developers"] = {
        "Developers": {}
    }
    information = check_developer_info_exist("d")
    update = False #Need to be true
    if False:#Need to be deleted
        if information[0]:
            print(f"Information about developers already exists. It was updated on {information[1]}. Do you want to "
                   f"check it? [y]-check, [n]-update database", end="")
            while True:
                if keyboard.is_pressed('y'):
                    print()
                    print("Okay! Checking developers data...")
                    result = check_files("d")
                    time.sleep(2)
                    if not result[0]:
                        print("Unfortunately the file is damaged. The database needs to be updated")
                        break
                    else:
                        print("Data base is ok! Do you want to go on or to update it? [y]-update, [n]-go on", end="")
                    while True:
                        if keyboard.is_pressed('y'):
                            print()
                            break
                        if keyboard.is_pressed('n'):
                            print()
                            update = False
                            break
                    break
                if keyboard.is_pressed('n'):
                    print()
                    break
    if update:
        print("Getting information about developers...")
        asyncio.run(get_all_developers(func_information))
        with open("developers.json", "w") as f:
            func_information["Get_all_developers"]["Developers"]["Update date"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()))
            json.dump(func_information["Get_all_developers"]["Developers"], f)
        print("\nGot all developers information!")
    else:
        with open("developers.json", "r") as f:
            func_information["Get_all_developers"]["Developers"] = dict(json.load(f))

    print("2/3. Trying to get apps links")
    func_information["Get_apps_links"] = {
        "Function start time": time.time()
    }
    links = []
    asyncio.run(get_apps_links(func_information["Get_all_developers"]["Developers"], func_information))
    with open("apps_links.json", "w") as file:
        json.dump(links, file)
    print("Got all apps links!")

    print("3/3. Trying to get application information and create database")
    with open("apps_links.json", "r") as apps_urls:
        links = json.load(apps_urls)
    func_information["Get_all_applications"] = {}
    func_information["Get_all_applications"]["Apps list"] = []
    func_information["Get_all_applications"]["Got application count"] = 0
    func_information["Get_all_applications"]["Total applications"] = len(links)
    asyncio.run(get_all_applications(links, func_information))
    with open("apps_list.json", "w") as file:
        json.dump(func_information["Get_all_applications"]["Apps list"], file)
    print("Finished. It took {}".format(time.time() - func_information["Main"]["Start time"]))


if __name__ == "__main__":
    main()
