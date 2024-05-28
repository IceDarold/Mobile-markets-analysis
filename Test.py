import requests
from bs4 import BeautifulSoup
import utilities

# print("Res: ", utilities.get_developers_information((1481, 2136), "test.json", "a"))
# print(utilities.get_info_about_developer_by_name("Kolesa Group", "data.json"))
print(utilities.get_info_about_app_by_link("/application/boom_beach/com.supercell.boombeach"))
# print(utilities.get_all_developer_games(6715068722362591614))