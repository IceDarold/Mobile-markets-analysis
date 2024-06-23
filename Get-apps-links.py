import json
import time

import aiohttp
from bs4 import BeautifulSoup

import utilities
import asyncio

count = 0
links = []


async def get_info_about_developer_by_id(developer_id, session) -> dict | str:
    url = "https://www.androidrank.org/developer?id=" + str(developer_id)
    async with session.get(url, headers={
        "User-Agent": "Googlebot"
    }) as response:
        developer_info = {}
        # Check answer status
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


async def get_developer_links(session, dev_id):
    global count, links
    dev_info = await get_info_about_developer_by_id(dev_id, session)
    if isinstance(dev_info, dict):
        count += 1
        print(f"Got info about {dev_id} (#{count})")
        links.extend(["https://www.androidrank.org" + link for link in dev_info["Apps"].values()])
        return links
    else:
        print("Error {}".format(dev_info))
        with open("log.txt", "r+") as log:
            data = log.read()
            log.write(data + dev_info + "\n")


async def a_main(ids):
    async with aiohttp.ClientSession() as session:
        tasks = [get_developer_links(session, dev_id) for dev_id in ids]
        return await asyncio.gather(*tasks)

    # async with asyncio.TaskGroup() as group:
    #     try:
    #         for dev_id in ids:
    #             group.create_task(get_developer_links(dev_id, links))
    #     except Exception as error:
    #         print(error)
    #         with open("log.txt", "r+") as log_file:
    #             cur = log_file.read()
    #             log_file.write(cur + str(error) + "\n")


# def main():
#     with open("developers.json", "r") as file:
#         developers_dict: dict = json.loads(file.read())
#
#     links = []
#     count = 0
#     for key, value in developers_dict.items():
#         try:
#             count += 1
#             if count == 5:
#                 x = key["119"]
#             print(f"Trying to get info about {key} (#{count})")
#             dev_info = utilities.get_info_about_developer_by_id(value["Id"])
#             links.extend(["https://www.androidrank.org" + link for link in dev_info["Apps"].values()])
#         except Exception as error:
#             print(error)
#             with open("log.txt", "r+") as log_file:
#                 cur = log_file.read()
#                 log_file.write(cur + str(error) + "\n")
#
#     with open("apps_links.json", "w") as file:
#         json.dump(links, file)


if __name__ == "__main__":
    start_time = time.time()
    with open("dev_urls.json", "r") as urls:
        ids = json.load(urls)
    links = []
    asyncio.run(a_main(ids))
    with open("apps_links.json", "w") as file:
        json.dump(links, file)
    print("It took {} seconds".format(time.time() - start_time))
    # main()
