import asyncio
import json
import os
import re
import subprocess
import sys
import time

import aiohttp
import keyboard
from bs4 import BeautifulSoup
import telebot


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


async def get_info_about_developer_by_id(developer_id, session, func_information) -> dict | str:
    url = "https://www.androidrank.org/developer?id=" + str(developer_id)
    async with session.get(url, headers={
        "User-Agent": "Googlebot"
    }) as response:
        developer_info = {}
        # Check answer st тatus
        index = 0
        if response.status == 429:
            retry_after = int(response.headers.get("Retry-After", 1))
            pprint(f"Too many requests - retrying after {retry_after} seconds",
                   current_number=func_information["Get_apps_links"]["Link count"],
                   total=func_information["Get_apps_links"]["Total"],
                   start_time=func_information["Get_apps_links"]["Start time"],
                   fix_length=50
                   )
            await asyncio.sleep(retry_after)
            return await get_info_about_developer_by_id(developer_id, session, func_information)
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
            pprint(f"Got {function_information['Get_all_developers']['Count']} developers",
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
    dev_info = await get_info_about_developer_by_id(dev_id, session, func_information)
    if isinstance(dev_info, dict):
        func_information["Get_apps_links"]["Link count"] += 1
        pprint(f"Got info about {dev_id}",
               current_number=func_information["Get_apps_links"]["Link count"],
               total=func_information["Get_apps_links"]["Total"],
               start_time=func_information["Get_apps_links"]["Start time"],
               fix_length=50
               )
        func_information["Get_apps_links"]["Apps links"]["List"].extend(
            ["https://www.androidrank.org" + link for link in dev_info["Apps"].values()])
    else:
        print("Error {}".format(dev_info))
        with open("log.txt", "r+") as log:
            data = log.read()
            log.write(data + dev_info + "\n")


async def get_apps_links(developer_ids, func_information: dict):
    func_information["Get_apps_links"]["Link count"] = 0
    func_information["Get_apps_links"]["Start time"] = time.time()
    func_information["Get_apps_links"]["Total"] = len(developer_ids)
    async with aiohttp.ClientSession() as session:
        tasks = [get_developer_apps_links(session, dev_id, func_information) for dev_id in developer_ids]
        return await asyncio.gather(*tasks)


def write_to_log(message):
    def check_zero(number: int) -> str:
        return str(number) if len(str(number)) == 2 else f"0{number}"

    time_now = time.localtime()
    str_format = f"{check_zero(time_now.tm_hour)}:{check_zero(time_now.tm_min)}:{check_zero(time_now.tm_sec)}"
    with open("log.txt", "a") as log:
        try:
            log.write(f"{str_format}. {message}\n")
        except UnicodeEncodeError as err:
            log.write(f"UnicodeEncodeError: {err.reason}\n")


async def get_app_by_link(url, session):
    async with session.get(url, headers={
        "User-Agent": "Googlebot"
    }) as response:
        app_data = {}
        # Check answer status
        if response.status == 429:
            retry_after = int(response.headers.get("Retry-After", 1))
            pprint(f"Too many requests - retrying after {retry_after} seconds")
            await asyncio.sleep(retry_after)
            return await get_app_by_link(url, session)
        if response.status == 200:
            # GENERAL STATS
            try:
                soup = BeautifulSoup(await response.text(), 'html.parser')
            except asyncio.TimeoutError:
                write_to_log(f"{url}: asyncio.TimeoutError")
                await asyncio.sleep(1)
                await get_app_by_link(url, session)
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
    try:
        app_info = await get_app_by_link(url, session)
    except aiohttp.client_exceptions.ServerDisconnectedError:
        pprint("Server disconnected unexpectedly")
        write_to_log("Server disconnected unexpectedly")
        await asyncio.sleep(1)
        await get_app(session, url, func_information)
        return
    except aiohttp.ClientError as e:
        await asyncio.sleep(1)
        await get_app(session, url, func_information)
        write_to_log(f"Client error occurred: {e}")
        pprint(f"Client error occurred: {e}")
        return
    except TimeoutError:
        await asyncio.sleep(1)
        await get_app(session, url, func_information)
        write_to_log(f"Timeout error")
        pprint(f"Timeout error")
        return
    if isinstance(app_info, dict):
        func_information["Get_all_applications"]["Got application count"] += 1
        pprint(f'Got info about {url} (#{func_information["Get_all_applications"]["Got application count"]})',
               func_information["Get_all_applications"]["Start time"],
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
    if file_type == "d":
        file_name = "developers.json"
    elif file_type == "l":
        file_name = "apps_links.json"
    elif file_type == "a":
        file_name = "apps.json"
    else:
        raise ValueError(f"invalid file type: '{file_type}'")

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


def send_file_to_user(tg_user_id, file_name):
    API_TOKEN = '6995683060:AAEibC05Mf-l2xQKo0DGyXu5WE5A2JRL0XY'
    bot = telebot.TeleBot(API_TOKEN)
    with open(file_name, 'rb') as file:
        try:
            bot.send_document(tg_user_id, file)
        except telebot.apihelper.ApiTelegramException:
            return False, "ApiTelegramException"
    return True,


def main():
    func_information: dict = {
        "Main": {
            "Start time": time.time()
        }
    }
    print("Starting all processes...")

    print("1/4. Trying to get information about developers")
    func_information["Get_all_developers"] = {
        "Developers": {}
    }
    information = check_developer_info_exist("d")
    update = True
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
            func_information["Get_all_developers"]["Developers"]["Update date"] = time.strftime("%Y-%m-%d %H:%M:%S",
                                                                                                time.gmtime(
                                                                                                    time.time()))
            json.dump(func_information["Get_all_developers"]["Developers"], f)
        print("\nGot all developers information!")
    else:
        with open("developers.json", "r") as f:
            func_information["Get_all_developers"]["Developers"] = dict(json.load(f))

    print("2/4. Trying to get developers links")
    time.sleep(1)
    func_information["Developers links"] = {
        "Ids list": []
    }
    for value in list(func_information["Get_all_developers"]["Developers"].values())[:-1]:
        func_information["Developers links"]["Ids list"].append(str(value["Id"]))

    print("3/4. Trying to get apps links")
    func_information["Get_apps_links"] = {
        "Function start time": time.time(),
        "Apps links": {
            "List": []
        }
    }
    information = check_developer_info_exist("l")
    update = True
    if information[0]:
        print(f"Apps links already exists. It was updated on {information[1]}. Do you want to "
              f"check it? [y]-check, [n]-update database", end="")
        while True:
            if keyboard.is_pressed('y'):
                print()
                print("Okay! Checking apps links...")
                time.sleep(1)
                result = check_files("l")
                if not result[0]:
                    print("Unfortunately the file is damaged. The file needs to be updated")
                    break
                else:
                    print("The data is ok! Do you want to go on or to update it? [y]-update, [n]-go on", end="")
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
        print("Getting apps links...")
        asyncio.run(get_apps_links(func_information["Developers links"]["Ids list"], func_information))
        with open("apps_links.json", "w") as f:
            func_information["Get_apps_links"]["Apps links"]["Update date"] = time.strftime("%Y-%m-%d %H:%M:%S",
                                                                                            time.gmtime(
                                                                                                time.time()))
            json.dump(func_information["Get_apps_links"]["Apps links"], f)
        print("\nGot all apps links!")
    else:
        with open("apps_links.json", "r") as f:
            func_information["Get_apps_links"]["Apps links"] = dict(json.load(f))

    print("4/4. Trying to get application information and create database")
    func_information["Get_all_applications"] = {}
    func_information["Get_all_applications"]["Apps list"] = []
    func_information["Get_all_applications"]["Start time"] = time.time()
    func_information["Get_all_applications"]["Got application count"] = 0
    func_information["Get_all_applications"]["Total applications"] = len(
        func_information["Get_apps_links"]["Apps links"]["List"])
    asyncio.run(get_all_applications(func_information["Get_apps_links"]["Apps links"]["List"], func_information))
    file_name = f"apps_{time.strftime('%Y-%m-%d', time.gmtime(time.time()))}.json"
    with open(file_name, "w") as file:
        json.dump(func_information["Get_all_applications"]["Apps list"], file)
    print("\nFinished. It took {}. Database in the file apps.json".format(
        time.time() - func_information["Main"]["Start time"]))

    print(f"Do you want to send it to you in telegram? [y]-enter id and send to it, [n]-don't send, [s]-send to standard user", end="")
    while True:
        if keyboard.is_pressed('y'):
            print()
            while True:
                try:
                    tg_id = int(input("\nOkay! Please, enter your id (you can get it by writing to the https://t.me/userinfobot: "))
                    break
                except Exception:
                    print("Wrong answer")
            time.sleep(1)
            while True:
                res = send_file_to_user(tg_id, file_name)
                if res[0]:
                    print("Sent!")
                    break
                elif res[1] == "ApiTelegramException":
                    print("You need to start the bot https://t.me/androidrank_parsing_bot and try again")
                    print("Press [r], when you are ready")
                    while True:
                        if keyboard.is_pressed('r'):
                            break
            break

        if keyboard.is_pressed('n'):
            print("\nOkay! That's it")
            break
        if keyboard.is_pressed("s"):
            standard_user_id = 7183822341
            print("\nOkay! Sending to standard user...")
            while True:
                res = send_file_to_user(standard_user_id, file_name)
                if res[0]:
                    print("Sent!")
                    break
                else:
                    print(f"Error: {res[1]}")
                    print(f"Idk how, but try to fix it and press [r], when you are ready")
                    while True:
                        if keyboard.is_pressed('r'):
                            break
            break


if __name__ == "__main__":
    main()
