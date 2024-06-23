import asyncio
import json
import time

import aiohttp
from bs4 import BeautifulSoup

number = ""

def write_to_log(message):
    def check_zero(number: int) -> str:
        return str(number) if len(str(number)) == 2 else f"0{number}"

    time_now = time.localtime()
    str_format = f"{check_zero(time_now.tm_hour)}:{check_zero(time_now.tm_min)}:{check_zero(time_now.tm_sec)}"
    print(f"{str_format} {message}")
    with open("log.txt", "a") as log:
        try:
            log.write(f"{str_format}. {message}\n")
        except UnicodeEncodeError as err:
            log.write(f"UnicodeEncodeError: {err.reason}\n")

def pprint(data):
    def format_time(seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def truncate_string(string, max_length):
        if len(string) > max_length:
            return string[:max_length - 3] + "..."
        return string

    global start_time, time_error_count, number, total
    elapsed_time = int(time.time() - start_time)
    formatted_time = format_time(elapsed_time)
    time_error_info = f"Too many requests x{time_error_count}"
    number = data[data.find("#") + 1:-1] if data.find("#") != -1 else number
    output = data[:data.find("#") - 2]
    output = truncate_string(output, 113)
    last_time = int(total / (int(number) / elapsed_time))
    print(f"\r{output}.".ljust(115) + " " + number + f"/{total} ({round(int(number) / total, 3)}%)" + " | " + formatted_time + " | " + format_time(last_time) + " left" + " | " + time_error_info,
          end="", flush=True)


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


async def get_app(session, url):
    global count, apps_list, start_time
    app_info = await get_app_by_link(url, session)
    if isinstance(app_info, dict):
        count += 1
        pprint(f"Got info about {url} (#{count})")
        apps_list.append(app_info)
        return links
    else:
        print("Error {}".format(app_info))
        with open("log.txt", "r+") as log:
            data = log.read()
            log.write(data + app_info + "\n")


async def main(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [get_app(session, url) for url in urls]
        return await asyncio.gather(*tasks)


if __name__ == "__main__":
    start_time = time.time()
    with open("apps_links.json", "r") as apps_urls:
        links = json.load(apps_urls)
    apps_list = []
    count = 0
    total = len(links)
    time_error_count = 0
    try:
        asyncio.run(main(links))
    except Exception as err:
        pprint(str(err))
        write_to_log(err)
    with open("apps_list.json", "w") as file:
        json.dump(apps_list, file)
    print("It took {} seconds".format(time.time() - start_time))
    # main()
