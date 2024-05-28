try:
    import utilities
    import time
    import os

    data_file_name = "data.json"


    def clear():
        # Очистить консоль с использованием ANSI escape codes
        os.system('cls' if os.name == 'nt' else 'clear')
    while True:
        command = input("Введите команду:\n"
                        "1 - получить информацию о разработчике по названию\n"
                        "2 - получить список разработчиков из рейтинга по количеству скачиваний\n"
                        "E - выйти из приложения\n")
        if command.lower() == "e" or command.lower() == "е":
            print("Спасибо за пользование.\n"
                  "Ждем вас снова!")
            time.sleep(2)
            break
        elif command == "1":
            name = input("Введите название разработчика:\n")
            clear()
            data = utilities.get_info_about_developer_by_name(name, data_file_name)
            if type(data) == str:
                print(data)
            else:
                for key, value in data.items():
                    print(f"{key}: {value}")
        elif command == "2":
            clear()
            info_range = input("Введите интересующий вас диапазон рейтинга в формате <начало - конец>. Например: 234 - "
                               "982:\n")
            try:
                data_sep = [int(s.replace(' ', '')) for s in info_range.split("-")]
                if data_sep[0] > data_sep[1]:
                    raise ValueError("Второе значение диапазона должно быть больше первого!")
            except Exception as err:
                clear()
                print("Ошибка:", err)
                input("Нажмите чтобы продолжить")
                continue
            clear()
            print("Отлично! Ожидайте 3...")
            time.sleep(1)
            clear()
            print("Отлично! Ожидайте 2...")
            time.sleep(1)
            clear()
            print("Отлично! Ожидайте 1...")
            time.sleep(1)
            clear()
            print("Результаты!")
        else:
            clear()
            print("Команда не найдена, попробуйте ещё раз")
        input("\nНажмите чтобы продолжить")
        clear()
except Exception as err:
    print(err)
    input()