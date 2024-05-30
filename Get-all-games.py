import time

import utilities
import json


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


def clear_log():
    with open("log.txt", "w") as log:
        log.write("")


def clear_falied():
    with open("process_info.json", "r+") as file:
        data = file.read()
        process_info: dict[str, list] = json.loads(data)
        process_info["Failed"] = []
        json.dump(process_info, file, indent=4)


def main():
    app_limit = 100000

    # SLEEP SETTINGS
    sleep_time = 30
    add_time = 5
    was: bool = False
    app_list = {}
    total = 0
    this_session = 0
    start = 0
    failed_list = []
    # process_info = {"Done developers": [], "Current developer": [None, 0], "Failed": []}
    with open("process_info.json", "r") as file:
        data = file.read()
        process_info: dict[str, list] = json.loads(data)

    with open("developers.json", "r") as file:
        developers_dict: dict = json.loads(file.read())
    count = 0
    for key, value in developers_dict.items():
        count += 1
        if count < start:
            continue
        try:
            if key in process_info["Done developers"]:
                continue
            write_to_log(f"Trying to get apps from {key}...")
            games: tuple[tuple[str, str], dict] = utilities.get_all_developer_games(value["Id"])
            if games[0][0] == "429":
                if was:
                    sleep_time += add_time
                print(
                    f"Got error: {games[0][0]}: {games[0][1]}. Save {this_session + len(games[1])} apps to json and wait for {sleep_time}")
                process_info["Current developer"] = [key, len(games[1].items())]
                start_time = time.time()
                app_list.update(games[1])
                utilities.save_to_json(app_list, "apps.json", operation_type="a",
                                       sort_key_func=lambda app: app[1]["Rating scores"]["Total ratings"])
                json_save_time = time.time() - start_time
                print(f"Json save took {json_save_time} seconds")
                if sleep_time - json_save_time > 0:
                    while True:
                        time.sleep(sleep_time - json_save_time)
                        games: tuple[tuple[str, str], dict] = utilities.get_all_developer_games(value["Id"], app_limit)

                was = True
                this_session = 0
            elif games[0][0] == "200":
                process_info["Done developers"].append(key)
                process_info["Current developer"] = []
                write_to_log(f"Got {len(games[1])} apps. {total + len(games[1])} in total.")
            elif games[0][0] == "201":
                write_to_log(f"Got {len(games[1])} apps. {total + len(games[1])} in total.")
                process_info["Current developer"] = [key, len(games[1])]
            elif games[0][0] == "404":
                write_to_log(f"Error: {games[0][1]} in {key}")
                process_info["Failed"].append(key)
                continue
            was = False
            total += len(games[1])
            this_session += len(games[1])
            app_list.update(games[1])
            response = utilities.save_to_json(app_list, "apps.json", operation_type="a",
                                              sort_key_func=lambda app: app[1]["Rating scores"]["Total ratings"])
            if response[0] != 200:
                write_to_log(response[1])
            app_list = {}
            write_to_log(f"Save {this_session} apps to json")
            this_session = 0
            if len(app_list) >= app_limit:
                break
            with open("process_info.json", "w") as file:
                json.dump(process_info, file, indent=4)
        except Exception as err:
            write_to_log(f"{err}. In {key} searching")
    if this_session != 0:
        write_to_log(f"Save {this_session} apps to json")
        response = utilities.save_to_json(app_list, "apps.json", operation_type="a",
                                          sort_key_func=lambda app: app[1]["Rating scores"][
                                              "Current market position by number of ratings"])
        if response[0] != 200:
            write_to_log(response[1])
    write_to_log("Finished")


if __name__ == '__main__':
    main()
