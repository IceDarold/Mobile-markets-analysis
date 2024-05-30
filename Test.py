import os
import time

import requests
from bs4 import BeautifulSoup
import utilities

# print("Res: ", utilities.get_developers_information((1481, 2136), "test.json", "a"))
# print(utilities.get_info_about_developer_by_name("Kolesa Group", "data.json"))
# print(utilities.get_info_about_app_by_link("/application/boom_beach/com.supercell.boombeach"))
# print(utilities.get_all_developer_games(6715068722362591614))
# time.sleep(-10)
# url = "https://www.androidrank.org"
# count = 0
# for i in range(1000):
#     response = requests.get(url, headers={
#             "User-Agent": "Googlebot"
#         })
#     # response = requests.get(url)
#     if response.status_code != 200:
#         print(response.text)
#     else:
#         count += 1
#         print("Succeed", count)
with open("apps.json", "+") as test:
    print(test.read())
# print(os.path.abspath("log.txt"))
