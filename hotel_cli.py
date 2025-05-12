import mysql.connector
from mysql.connector import Error
import getpass
from datetime import datetime, date, timedelta
import sys


class HotelManagementSystem:
    def __init__(self):
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                database='pm07hotel',
                user='root',
                password='Evropa20'
            )
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
        except Error as e:
            print(f"Ошибка подключения к MySQL: {e}")
            sys.exit(1)

        self.current_user = None
        self.is_manager = False

    def login(self):
        print("\n=== Вход в систему ===")
        username = input("Имя пользователя: ")
        password = getpass.getpass("Пароль: ")

        query = "SELECT * FROM employees WHERE username = %s"
        self.cursor.execute(query, (username,))
        user = self.cursor.fetchone()

        if user and user['password'] == password:
            self.current_user = user
            self.is_manager = user['is_manager']
            print(f"\nДобро пожаловать, {user['first_name']} {user['last_name']}!")
            return True
        else:
            print("\nНеверное имя пользователя или пароль.")
            return False

    def guest_menu(self):
        while True:
            print("\n=== Меню гостя ===")
            print("1. Просмотреть доступные номера")
            print("2. Забронировать номер")
            print("3. Посмотреть мои бронирования")
            print("4. Выйти")

            choice = input("Выберите действие: ")

            if choice == '1':
                self.show_available_rooms()
            elif choice == '2':
                self.make_booking()
            elif choice == '3':
                self.view_guest_bookings()
            elif choice == '4':
                break
            else:
                print("Неверный выбор. Попробуйте снова.")

    def admin_menu(self):
        while True:
            print("\n=== Меню администратора ===")
            print("1. Управление бронированиями")
            print("2. Управление номерами")
            print("3. Управление гостями")
            print("4. Управление уборкой")
            print("5. Финансовые операции")
            print("6. Выйти")

            choice = input("Выберите действие: ")

            if choice == '1':
                self.manage_bookings()
            elif choice == '2':
                self.manage_rooms()
            elif choice == '3':
                self.manage_guests()
            elif choice == '4':
                self.manage_cleaning()
            elif choice == '5':
                self.financial_operations()
            elif choice == '6':
                break
            else:
                print("Неверный выбор. Попробуйте снова.")

    def manager_menu(self):
        while True:
            print("\n=== Меню руководителя ===")
            print("1. Просмотреть статистику")
            print("2. Управление персоналом")
            print("3. Управление расписанием")
            print("4. Анализ продаж")
            print("5. Выйти")

            choice = input("Выберите действие: ")

            if choice == '1':
                self.view_statistics()
            elif choice == '2':
                self.manage_staff()
            elif choice == '3':
                self.manage_schedule()
            elif choice == '4':
                self.analyze_sales()
            elif choice == '5':
                break
            else:
                print("Неверный выбор. Попробуйте снова.")

    def show_available_rooms(self):
        print("\n=== Доступные номера ===")
        check_in = input("Дата заезда (ГГГГ-ММ-ДД): ")
        check_out = input("Дата выезда (ГГГГ-ММ-ДД): ")

        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()

            if check_out_date <= check_in_date:
                print("Дата выезда должна быть позже даты заезда.")
                return
        except ValueError:
            print("Неверный формат даты. Используйте ГГГГ-ММ-ДД.")
            return

        query = """
        SELECT r.room_id, r.room_number, r.floor, rc.name as category, rc.base_price, rc.capacity
        FROM rooms r
        JOIN room_categories rc ON r.category_id = rc.category_id
        WHERE r.status = 'Чистый'
        AND r.room_id NOT IN (
            SELECT b.room_id 
            FROM bookings b
            WHERE (
                (b.check_in_date <= %s AND b.check_out_date >= %s) OR
                (b.check_in_date <= %s AND b.check_out_date >= %s) OR
                (b.check_in_date >= %s AND b.check_out_date <= %s)
            )
            AND b.status = 'Подтверждено'
        )
        """

        self.cursor.execute(query, (
        check_out_date, check_in_date, check_in_date, check_out_date, check_in_date, check_out_date))
        available_rooms = self.cursor.fetchall()

        if available_rooms:
            print("\nСписок доступных номеров:")
            for room in available_rooms:
                print(f"Номер: {room['room_number']} | Этаж: {room['floor']} | Категория: {room['category']} | "
                      f"Вместимость: {room['capacity']} | Цена за ночь: {room['base_price']}")
        else:
            print("Нет доступных номеров на выбранные даты.")

    def make_booking(self):
        print("\n=== Создание бронирования ===")

        # Получаем информацию о госте
        print("\nИнформация о госте:")
        first_name = input("Имя: ")
        last_name = input("Фамилия: ")
        email = input("Email: ")
        phone = input("Телефон: ")
        passport = input("Номер паспорта: ")

        query = """
        INSERT INTO guests (first_name, last_name, email, phone, passport_number)
        VALUES (%s, %s, %s, %s, %s)
        """
        try:
            self.cursor.execute(query, (first_name, last_name, email, phone, passport))
            guest_id = self.cursor.lastrowid
            self.connection.commit()
        except Error as e:
            print(f"Ошибка при добавлении гостя: {e}")
            return

        # Показываем доступные номера
        self.show_available_rooms()

        # Выбираем номер
        room_number = input("\nВведите номер комнаты для бронирования: ")

        # Проверяем доступность номера
        query = """
        SELECT r.room_id, rc.base_price
        FROM rooms r
        JOIN room_categories rc ON r.category_id = rc.category_id
        WHERE r.room_number = %s AND r.status = 'Чистый'
        """
        self.cursor.execute(query, (room_number,))
        room = self.cursor.fetchone()

        if not room:
            print("Выбранный номер недоступен для бронирования.")
            return

        # Получаем даты
        check_in = input("Дата заезда (ГГГГ-ММ-ДД): ")
        check_out = input("Дата выезда (ГГГГ-ММ-ДД): ")

        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()

            if check_out_date <= check_in_date:
                print("Дата выезда должна быть позже даты заезда.")
                return

            nights = (check_out_date - check_in_date).days
            total_price = nights * room['base_price']
        except ValueError:
            print("Неверный формат даты. Используйте ГГГГ-ММ-ДД.")
            return

        # Создаем бронирование
        query = """
        INSERT INTO bookings (guest_id, room_id, check_in_date, check_out_date, total_price)
        VALUES (%s, %s, %s, %s, %s)
        """
        try:
            self.cursor.execute(query, (guest_id, room['room_id'], check_in_date, check_out_date, total_price))
            booking_id = self.cursor.lastrowid
            self.connection.commit()

            print(f"\nБронирование успешно создано! Номер бронирования: {booking_id}")
            print(f"Общая стоимость: {total_price}")
        except Error as e:
            print(f"Ошибка при создании бронирования: {e}")

    def view_guest_bookings(self):
        passport = input("Введите номер паспорта: ")

        query = """
        SELECT b.booking_id, r.room_number, b.check_in_date, b.check_out_date, 
               b.total_price, b.status, b.payment_status
        FROM bookings b
        JOIN guests g ON b.guest_id = g.guest_id
        JOIN rooms r ON b.room_id = r.room_id
        WHERE g.passport_number = %s
        ORDER BY b.check_in_date DESC
        """

        self.cursor.execute(query, (passport,))
        bookings = self.cursor.fetchall()

        if bookings:
            print("\nВаши бронирования:")
            for booking in bookings:
                print(f"Бронирование #{booking['booking_id']}")
                print(f"Номер: {booking['room_number']}")
                print(f"Даты: {booking['check_in_date']} - {booking['check_out_date']}")
                print(f"Стоимость: {booking['total_price']}")
                print(f"Статус: {booking['status']}")
                print(f"Статус оплаты: {booking['payment_status']}")
                print("-" * 30)
        else:
            print("Бронирований не найдено.")

    def manage_bookings(self):
        while True:
            print("\n=== Управление бронированиями ===")
            print("1. Просмотреть все бронирования")
            print("2. Найти бронирование по ID")
            print("3. Зарегистрировать заезд")
            print("4. Зарегистрировать выезд")
            print("5. Отменить бронирование")
            print("6. Вернуться в главное меню")

            choice = input("Выберите действие: ")

            if choice == '1':
                self.view_all_bookings()
            elif choice == '2':
                self.find_booking_by_id()
            elif choice == '3':
                self.check_in_guest()
            elif choice == '4':
                self.check_out_guest()
            elif choice == '5':
                self.cancel_booking()
            elif choice == '6':
                break
            else:
                print("Неверный выбор. Попробуйте снова.")

    def view_all_bookings(self):
        query = """
        SELECT b.booking_id, g.first_name, g.last_name, r.room_number, 
               b.check_in_date, b.check_out_date, b.status, b.payment_status
        FROM bookings b
        JOIN guests g ON b.guest_id = g.guest_id
        JOIN rooms r ON b.room_id = r.room_id
        ORDER BY b.check_in_date DESC
        LIMIT 50
        """

        self.cursor.execute(query)
        bookings = self.cursor.fetchall()

        if bookings:
            print("\nСписок бронирований:")
            for booking in bookings:
                print(f"ID: {booking['booking_id']} | Гость: {booking['first_name']} {booking['last_name']}")
                print(
                    f"Номер: {booking['room_number']} | Даты: {booking['check_in_date']} - {booking['check_out_date']}")
                print(f"Статус: {booking['status']} | Оплата: {booking['payment_status']}")
                print("-" * 50)
        else:
            print("Бронирований не найдено.")

    def find_booking_by_id(self):
        booking_id = input("Введите ID бронирования: ")

        query = """
        SELECT b.*, g.first_name, g.last_name, g.passport_number, g.phone, g.email,
               r.room_number, r.floor, rc.name as room_category
        FROM bookings b
        JOIN guests g ON b.guest_id = g.guest_id
        JOIN rooms r ON b.room_id = r.room_id
        JOIN room_categories rc ON r.category_id = rc.category_id
        WHERE b.booking_id = %s
        """

        self.cursor.execute(query, (booking_id,))
        booking = self.cursor.fetchone()

        if booking:
            print("\nИнформация о бронировании:")
            print(f"ID: {booking['booking_id']}")
            print(f"Гость: {booking['first_name']} {booking['last_name']}")
            print(f"Паспорт: {booking['passport_number']}")
            print(f"Телефон: {booking['phone']} | Email: {booking['email']}")
            print(f"Номер: {booking['room_number']} (Этаж: {booking['floor']}, Категория: {booking['room_category']})")
            print(f"Даты: {booking['check_in_date']} - {booking['check_out_date']}")
            print(f"Стоимость: {booking['total_price']}")
            print(f"Статус: {booking['status']}")
            print(f"Статус оплаты: {booking['payment_status']}")
        else:
            print("Бронирование не найдено.")

    def check_in_guest(self):
        booking_id = input("Введите ID бронирования для заселения: ")

        # Проверяем бронирование
        query = """
        SELECT b.*, r.room_id, r.status as room_status
        FROM bookings b
        JOIN rooms r ON b.room_id = r.room_id
        WHERE b.booking_id = %s AND b.status = 'Подтверждено'
        """
        self.cursor.execute(query, (booking_id,))
        booking = self.cursor.fetchone()

        if not booking:
            print("Бронирование не найдено или не подтверждено.")
            return

        if booking['room_status'] != 'Чистый':
            print(f"Номер не готов к заселению. Текущий статус: {booking['room_status']}")
            return

        # Регистрируем заезд
        query = """
        INSERT INTO check_ins (booking_id, employee_id)
        VALUES (%s, %s)
        """
        try:
            self.cursor.execute(query, (booking_id, self.current_user['employee_id']))
            self.connection.commit()

            # Обновляем статус бронирования
            query = "UPDATE bookings SET status = 'Завершено' WHERE booking_id = %s"
            self.cursor.execute(query, (booking_id,))

            # Обновляем статус номера
            query = "UPDATE rooms SET status = 'Занят' WHERE room_id = %s"
            self.cursor.execute(query, (booking['room_id'],))

            self.connection.commit()

            print("Гость успешно заселен!")
        except Error as e:
            print(f"Ошибка при регистрации заезда: {e}")

    def check_out_guest(self):
        booking_id = input("Введите ID бронирования для выселения: ")

        # Проверяем, что гость заселен
        query = """
        SELECT ci.check_in_id, b.room_id, ci.check_out_time
        FROM check_ins ci
        JOIN bookings b ON ci.booking_id = b.booking_id
        WHERE ci.booking_id = %s AND ci.check_out_time IS NULL
        """
        self.cursor.execute(query, (booking_id,))
        check_in = self.cursor.fetchone()

        if not check_in:
            print("Гость не заселен или уже выселен.")
            return

        # Регистрируем выезд
        query = "UPDATE check_ins SET check_out_time = NOW() WHERE check_in_id = %s"
        self.cursor.execute(query, (check_in['check_in_id'],))

        # Обновляем статус номера
        query = "UPDATE rooms SET status = 'Грязный' WHERE room_id = %s"
        self.cursor.execute(query, (check_in['room_id'],))

        self.connection.commit()

        print("Гость успешно выселен. Номер помечен как 'Грязный'.")

    def cancel_booking(self):
        booking_id = input("Введите ID бронирования для отмены: ")

        # Проверяем бронирование
        query = "SELECT status FROM bookings WHERE booking_id = %s"
        self.cursor.execute(query, (booking_id,))
        booking = self.cursor.fetchone()

        if not booking:
            print("Бронирование не найдено.")
            return

        if booking['status'] == 'Отменено':
            print("Бронирование уже отменено.")
            return

        # Отменяем бронирование
        query = "UPDATE bookings SET status = 'Отменено' WHERE booking_id = %s"
        self.cursor.execute(query, (booking_id,))
        self.connection.commit()

        print("Бронирование успешно отменено.")

    def manage_rooms(self):
        while True:
            print("\n=== Управление номерами ===")
            print("1. Просмотреть все номера")
            print("2. Просмотреть номер по номеру")
            print("3. Изменить статус номера")
            print("4. Просмотреть категории номеров")
            print("5. Вернуться в главное меню")

            choice = input("Выберите действие: ")

            if choice == '1':
                self.view_all_rooms()
            elif choice == '2':
                self.view_room_by_number()
            elif choice == '3':
                self.change_room_status()
            elif choice == '4':
                self.view_room_categories()
            elif choice == '5':
                break
            else:
                print("Неверный выбор. Попробуйте снова.")

    def view_all_rooms(self):
        query = """
        SELECT r.room_number, r.floor, rc.name as category, r.status, rc.base_price, rc.capacity
        FROM rooms r
        JOIN room_categories rc ON r.category_id = rc.category_id
        ORDER BY r.floor, r.room_number
        """

        self.cursor.execute(query)
        rooms = self.cursor.fetchall()

        if rooms:
            print("\nСписок номеров:")
            for room in rooms:
                print(f"Номер: {room['room_number']} | Этаж: {room['floor']} | Категория: {room['category']}")
                print(f"Статус: {room['status']} | Цена: {room['base_price']} | Вместимость: {room['capacity']}")
                print("-" * 50)
        else:
            print("Номера не найдены.")

    def view_room_by_number(self):
        room_number = input("Введите номер комнаты: ")

        query = """
        SELECT r.*, rc.name as category, rc.description, rc.base_price, rc.capacity
        FROM rooms r
        JOIN room_categories rc ON r.category_id = rc.category_id
        WHERE r.room_number = %s
        """

        self.cursor.execute(query, (room_number,))
        room = self.cursor.fetchone()

        if room:
            print("\nИнформация о номере:")
            print(f"Номер: {room['room_number']} | Этаж: {room['floor']}")
            print(f"Категория: {room['category']}")
            print(f"Описание: {room['description']}")
            print(f"Цена за ночь: {room['base_price']}")
            print(f"Вместимость: {room['capacity']}")
            print(f"Текущий статус: {room['status']}")
        else:
            print("Номер не найден.")

    def change_room_status(self):
        room_number = input("Введите номер комнаты: ")
        new_status = input("Введите новый статус (Чистый/Грязный/Занят/Назначен к уборке/На ремонте): ")

        if new_status not in ['Чистый', 'Грязный', 'Занят', 'Назначен к уборке', 'На ремонте']:
            print("Неверный статус.")
            return

        query = "UPDATE rooms SET status = %s WHERE room_number = %s"
        try:
            self.cursor.execute(query, (new_status, room_number))
            if self.cursor.rowcount == 0:
                print("Номер не найден.")
            else:
                self.connection.commit()
                print("Статус номера успешно обновлен.")
        except Error as e:
            print(f"Ошибка при обновлении статуса: {e}")

    def view_room_categories(self):
        query = "SELECT * FROM room_categories ORDER BY base_price DESC"
        self.cursor.execute(query)
        categories = self.cursor.fetchall()

        if categories:
            print("\nКатегории номеров:")
            for category in categories:
                print(f"Категория: {category['name']}")
                print(f"Описание: {category['description']}")
                print(f"Базовая цена: {category['base_price']}")
                print(f"Вместимость: {category['capacity']}")
                print("-" * 50)
        else:
            print("Категории номеров не найдены.")

    def manage_guests(self):
        while True:
            print("\n=== Управление гостями ===")
            print("1. Поиск гостя по имени")
            print("2. Поиск гостя по паспорту")
            print("3. Просмотреть историю пребывания гостя")
            print("4. Вернуться в главное меню")

            choice = input("Выберите действие: ")

            if choice == '1':
                self.find_guest_by_name()
            elif choice == '2':
                self.find_guest_by_passport()
            elif choice == '3':
                self.view_guest_history()
            elif choice == '4':
                break
            else:
                print("Неверный выбор. Попробуйте снова.")

    def find_guest_by_name(self):
        name = input("Введите имя или фамилию гостя: ")

        query = """
        SELECT * FROM guests 
        WHERE first_name LIKE %s OR last_name LIKE %s
        LIMIT 20
        """

        self.cursor.execute(query, (f"%{name}%", f"%{name}%"))
        guests = self.cursor.fetchall()

        if guests:
            print("\nНайденные гости:")
            for guest in guests:
                print(f"ID: {guest['guest_id']} | Имя: {guest['first_name']} {guest['last_name']}")
                print(f"Паспорт: {guest['passport_number']} | Телефон: {guest['phone']}")
                print(f"Email: {guest['email']} | Дата регистрации: {guest['registration_date']}")
                print("-" * 50)
        else:
            print("Гости не найдены.")

    def find_guest_by_passport(self):
        passport = input("Введите номер паспорта: ")

        query = "SELECT * FROM guests WHERE passport_number = %s"
        self.cursor.execute(query, (passport,))
        guest = self.cursor.fetchone()

        if guest:
            print("\nИнформация о госте:")
            print(f"ID: {guest['guest_id']} | Имя: {guest['first_name']} {guest['last_name']}")
            print(f"Паспорт: {guest['passport_number']} | Телефон: {guest['phone']}")
            print(f"Email: {guest['email']} | Дата регистрации: {guest['registration_date']}")
        else:
            print("Гость не найден.")

    def view_guest_history(self):
        guest_id = input("Введите ID гостя: ")

        query = """
        SELECT b.booking_id, r.room_number, b.check_in_date, b.check_out_date, 
               b.total_price, b.status, ci.check_in_time, ci.check_out_time
        FROM bookings b
        JOIN rooms r ON b.room_id = r.room_id
        LEFT JOIN check_ins ci ON b.booking_id = ci.booking_id
        WHERE b.guest_id = %s
        ORDER BY b.check_in_date DESC
        """

        self.cursor.execute(query, (guest_id,))
        history = self.cursor.fetchall()

        if history:
            print("\nИстория пребывания гостя:")
            for record in history:
                print(f"Бронирование #{record['booking_id']} | Номер: {record['room_number']}")
                print(f"Даты: {record['check_in_date']} - {record['check_out_date']}")
                if record['check_in_time']:
                    print(f"Заезд: {record['check_in_time']}")
                if record['check_out_time']:
                    print(f"Выезд: {record['check_out_time']}")
                print(f"Стоимость: {record['total_price']} | Статус: {record['status']}")
                print("-" * 50)
        else:
            print("История пребывания не найдена.")

    def manage_cleaning(self):
        while True:
            print("\n=== Управление уборкой ===")
            print("1. Просмотреть номера, требующие уборки")
            print("2. Назначить уборку номера")
            print("3. Просмотреть назначенные уборки")
            print("4. Отметить уборку как выполненную")
            print("5. Вернуться в главное меню")

            choice = input("Выберите действие: ")

            if choice == '1':
                self.view_rooms_needing_cleaning()
            elif choice == '2':
                self.schedule_cleaning()
            elif choice == '3':
                self.view_scheduled_cleanings()
            elif choice == '4':
                self.mark_cleaning_completed()
            elif choice == '5':
                break
            else:
                print("Неверный выбор. Попробуйте снова.")

    def view_rooms_needing_cleaning(self):
        query = """
        SELECT r.room_number, r.floor, r.status
        FROM rooms r
        WHERE r.status = 'Грязный' OR r.status = 'Назначен к уборке'
        ORDER BY r.floor, r.room_number
        """

        self.cursor.execute(query)
        rooms = self.cursor.fetchall()

        if rooms:
            print("\nНомера, требующие уборки:")
            for room in rooms:
                print(f"Номер: {room['room_number']} | Этаж: {room['floor']} | Статус: {room['status']}")
        else:
            print("Все номера чистые или уборка уже назначена.")

    def schedule_cleaning(self):
        room_number = input("Введите номер комнаты для уборки: ")
        cleaning_date = input("Дата уборки (ГГГГ-ММ-ДД): ")
        cleaning_time = input("Время уборки (ЧЧ:ММ): ")
        employee_id = input("ID сотрудника для уборки: ")

        try:
            # Проверяем, существует ли номер и требует ли он уборки
            query = """
            SELECT room_id, status FROM rooms 
            WHERE room_number = %s AND (status = 'Грязный' OR status = 'Назначен к уборке')
            """
            self.cursor.execute(query, (room_number,))
            room = self.cursor.fetchone()

            if not room:
                print("Номер не найден или не требует уборки.")
                return

            # Назначаем уборку
            query = """
            INSERT INTO cleaning (room_id, employee_id, scheduled_date, scheduled_time, status)
            VALUES (%s, %s, %s, %s, 'Назначено')
            """
            self.cursor.execute(query, (room['room_id'], employee_id, cleaning_date, cleaning_time))

            # Обновляем статус номера
            query = "UPDATE rooms SET status = 'Назначен к уборке' WHERE room_id = %s"
            self.cursor.execute(query, (room['room_id'],))

            self.connection.commit()
            print("Уборка успешно назначена.")
        except Error as e:
            print(f"Ошибка при назначении уборки: {e}")

    def view_scheduled_cleanings(self):
        query = """
        SELECT c.cleaning_id, r.room_number, e.first_name, e.last_name, 
               c.scheduled_date, c.scheduled_time, c.status
        FROM cleaning c
        JOIN rooms r ON c.room_id = r.room_id
        JOIN employees e ON c.employee_id = e.employee_id
        ORDER BY c.scheduled_date, c.scheduled_time
        """

        self.cursor.execute(query)
        cleanings = self.cursor.fetchall()

        if cleanings:
            print("\nНазначенные уборки:")
            for cleaning in cleanings:
                print(f"ID: {cleaning['cleaning_id']} | Номер: {cleaning['room_number']}")
                print(f"Сотрудник: {cleaning['first_name']} {cleaning['last_name']}")
                print(f"Дата/время: {cleaning['scheduled_date']} {cleaning['scheduled_time']}")
                print(f"Статус: {cleaning['status']}")
                print("-" * 50)
        else:
            print("Назначенные уборки не найдены.")

    def mark_cleaning_completed(self):
        cleaning_id = input("Введите ID уборки для отметки о выполнении: ")

        query = """
        UPDATE cleaning 
        SET completion_time = NOW(), status = 'Выполнено' 
        WHERE cleaning_id = %s AND status = 'Назначено'
        """
        self.cursor.execute(query, (cleaning_id,))

        if self.cursor.rowcount == 0:
            print("Уборка не найдена или уже выполнена/отменена.")
            return


        query = "SELECT room_id FROM cleaning WHERE cleaning_id = %s"
        self.cursor.execute(query, (cleaning_id,))
        cleaning = self.cursor.fetchone()

        # Обновляем статус номера
        query = "UPDATE rooms SET status = 'Чистый' WHERE room_id = %s"
        self.cursor.execute(query, (cleaning['room_id'],))

        self.connection.commit()
        print("Уборка отмечена как выполненная. Номер помечен как 'Чистый'.")

    def financial_operations(self):
        while True:
            print("\n=== Финансовые операции ===")
            print("1. Просмотреть все платежи")
            print("2. Зарегистрировать платеж")
            print("3. Просмотреть неоплаченные бронирования")
            print("4. Вернуться в главное меню")

            choice = input("Выберите действие: ")

            if choice == '1':
                self.view_all_payments()
            elif choice == '2':
                self.register_payment()
            elif choice == '3':
                self.view_unpaid_bookings()
            elif choice == '4':
                break
            else:
                print("Неверный выбор. Попробуйте снова.")

    def view_all_payments(self):
        query = """
        SELECT p.payment_id, b.booking_id, g.first_name, g.last_name, 
               p.amount, p.payment_date, p.payment_method
        FROM payments p
        JOIN bookings b ON p.booking_id = b.booking_id
        JOIN guests g ON b.guest_id = g.guest_id
        ORDER BY p.payment_date DESC
        LIMIT 50
        """

        self.cursor.execute(query)
        payments = self.cursor.fetchall()

        if payments:
            print("\nСписок платежей:")
            for payment in payments:
                print(f"ID платежа: {payment['payment_id']} | Бронирование: {payment['booking_id']}")
                print(f"Гость: {payment['first_name']} {payment['last_name']}")
                print(f"Сумма: {payment['amount']} | Дата: {payment['payment_date']}")
                print(f"Метод оплаты: {payment['payment_method']}")
                print("-" * 50)
        else:
            print("Платежи не найдены.")

    def register_payment(self):
        booking_id = input("Введите ID бронирования: ")
        amount = input("Введите сумму платежа: ")
        payment_method = input("Метод оплаты (Наличные/Карта/Банковский перевод): ")

        try:
            amount = float(amount)
            if amount <= 0:
                print("Сумма должна быть положительной.")
                return
        except ValueError:
            print("Неверная сумма.")
            return

        if payment_method not in ['Наличные', 'Карта', 'Банковский перевод']:
            print("Неверный метод оплаты.")
            return

        # Регистрируем платеж
        query = """
        INSERT INTO payments (booking_id, amount, payment_method)
        VALUES (%s, %s, %s)
        """
        self.cursor.execute(query, (booking_id, amount, payment_method))

        # Обновляем статус оплаты бронирования
        query = """
        UPDATE bookings 
        SET payment_status = CASE 
            WHEN (SELECT SUM(amount) FROM payments WHERE booking_id = %s) >= total_price THEN 'Оплачено'
            ELSE 'Частично оплачено'
        END
        WHERE booking_id = %s
        """
        self.cursor.execute(query, (booking_id, booking_id))

        self.connection.commit()
        print("Платеж успешно зарегистрирован.")

    def view_unpaid_bookings(self):
        query = """
        SELECT b.booking_id, g.first_name, g.last_name, r.room_number, 
               b.check_in_date, b.check_out_date, b.total_price,
               (SELECT IFNULL(SUM(amount), 0) FROM payments WHERE booking_id = b.booking_id) as paid_amount,
               b.total_price - (SELECT IFNULL(SUM(amount), 0) FROM payments WHERE booking_id = b.booking_id) as remaining_amount
        FROM bookings b
        JOIN guests g ON b.guest_id = g.guest_id
        JOIN rooms r ON b.room_id = r.room_id
        WHERE b.payment_status != 'Оплачено' AND b.status != 'Отменено'
        ORDER BY b.check_in_date
        """

        self.cursor.execute(query)
        bookings = self.cursor.fetchall()

        if bookings:
            print("\nНеоплаченные бронирования:")
            for booking in bookings:
                print(f"Бронирование #{booking['booking_id']} | Гость: {booking['first_name']} {booking['last_name']}")
                print(
                    f"Номер: {booking['room_number']} | Даты: {booking['check_in_date']} - {booking['check_out_date']}")
                print(f"Общая стоимость: {booking['total_price']} | Оплачено: {booking['paid_amount']}")
                print(f"Остаток к оплате: {booking['remaining_amount']}")
                print("-" * 50)
        else:
            print("Неоплаченные бронирования не найдены.")

    def view_statistics(self):
        while True:
            print("\n=== Просмотр статистики ===")
            print("1. Статистика загрузки номерного фонда")
            print("2. Средний доход на номер (RevPAR)")
            print("3. Средняя цена номера (ADR)")
            print("4. Вернуться в главное меню")

            choice = input("Выберите действие: ")

            if choice == '1':
                self.view_occupancy_statistics()
            elif choice == '2':
                self.view_revpar_statistics()
            elif choice == '3':
                self.view_adr_statistics()
            elif choice == '4':
                break
            else:
                print("Неверный выбор. Попробуйте снова.")

    def view_occupancy_statistics(self):
        start_date = input("Начальная дата (ГГГГ-ММ-ДД): ")
        end_date = input("Конечная дата (ГГГГ-ММ-ДД): ")

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            if end_date <= start_date:
                print("Конечная дата должна быть позже начальной.")
                return
        except ValueError:
            print("Неверный формат даты. Используйте ГГГГ-ММ-ДД.")
            return

        # Общее количество номеров
        query = "SELECT COUNT(*) as total_rooms FROM rooms"
        self.cursor.execute(query)
        total_rooms = self.cursor.fetchone()['total_rooms']

        # Количество проданных ночей
        query = """
        SELECT SUM(DATEDIFF(
            LEAST(b.check_out_date, %s), 
            GREATEST(b.check_in_date, %s)
        )) as sold_nights
        FROM bookings b
        WHERE b.status != 'Отменено'
        AND b.check_in_date <= %s
        AND b.check_out_date >= %s
        """
        self.cursor.execute(query, (end_date, start_date, end_date, start_date))
        sold_nights = self.cursor.fetchone()['sold_nights'] or 0

        # Общее количество возможных ночей
        total_nights = total_rooms * (end_date - start_date).days

        # Процент загрузки
        occupancy_rate = (sold_nights / total_nights) * 100 if total_nights > 0 else 0

        print("\nСтатистика загрузки номерного фонда:")
        print(f"Период: {start_date} - {end_date}")
        print(f"Общее количество номеров: {total_rooms}")
        print(f"Количество проданных ночей: {sold_nights}")
        print(f"Процент загрузки: {occupancy_rate:.2f}%")

    def view_revpar_statistics(self):
        date = input("Дата для расчета (ГГГГ-ММ-ДД): ")

        try:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            print("Неверный формат даты. Используйте ГГГГ-ММ-ДД.")
            return

        # Общее количество номеров
        query = "SELECT COUNT(*) as total_rooms FROM rooms"
        self.cursor.execute(query)
        total_rooms = self.cursor.fetchone()['total_rooms']

        # Выручка за день
        query = """
        SELECT SUM(b.total_price / DATEDIFF(b.check_out_date, b.check_in_date)) as daily_revenue
        FROM bookings b
        WHERE b.status != 'Отменено'
        AND b.check_in_date <= %s
        AND b.check_out_date > %s
        """
        self.cursor.execute(query, (date, date))
        daily_revenue = self.cursor.fetchone()['daily_revenue'] or 0

        revpar = daily_revenue / total_rooms if total_rooms > 0 else 0

        print("\nСредний доход на номер (RevPAR):")
        print(f"Дата: {date}")
        print(f"Общее количество номеров: {total_rooms}")
        print(f"Общая выручка за день: {daily_revenue:.2f}")
        print(f"RevPAR: {revpar:.2f}")

    def view_adr_statistics(self):
        start_date = input("Начальная дата (ГГГГ-ММ-ДД): ")
        end_date = input("Конечная дата (ГГГГ-ММ-ДД): ")

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            if end_date <= start_date:
                print("Конечная дата должна быть позже начальной.")
                return
        except ValueError:
            print("Неверный формат даты. Используйте ГГГГ-ММ-ДД.")
            return

        # Общая выручка
        query = """
        SELECT SUM(b.total_price) as total_revenue
        FROM bookings b
        WHERE b.status != 'Отменено'
        AND b.check_in_date <= %s
        AND b.check_out_date >= %s
        """
        self.cursor.execute(query, (end_date, start_date))
        total_revenue = self.cursor.fetchone()['total_revenue'] or 0

        # Количество проданных ночей
        query = """
        SELECT SUM(DATEDIFF(
            LEAST(b.check_out_date, %s), 
            GREATEST(b.check_in_date, %s)
        )) as sold_nights
        FROM bookings b
        WHERE b.status != 'Отменено'
        AND b.check_in_date <= %s
        AND b.check_out_date >= %s
        """
        self.cursor.execute(query, (end_date, start_date, end_date, start_date))
        sold_nights = self.cursor.fetchone()['sold_nights'] or 0

        adr = total_revenue / sold_nights if sold_nights > 0 else 0

        print("\nСредняя цена номера (ADR):")
        print(f"Период: {start_date} - {end_date}")
        print(f"Общая выручка: {total_revenue:.2f}")
        print(f"Количество проданных ночей: {sold_nights}")
        print(f"ADR: {adr:.2f}")

    def manage_staff(self):
        while True:
            print("\n=== Управление персоналом ===")
            print("1. Просмотреть всех сотрудников")
            print("2. Добавить нового сотрудника")
            print("3. Изменить данные сотрудника")
            print("4. Удалить сотрудника")
            print("5. Вернуться в главное меню")

            choice = input("Выберите действие: ")

            if choice == '1':
                self.view_all_employees()
            elif choice == '2':
                self.add_employee()
            elif choice == '3':
                self.edit_employee()
            elif choice == '4':
                self.delete_employee()
            elif choice == '5':
                break
            else:
                print("Неверный выбор. Попробуйте снова.")

    def view_all_employees(self):
        query = "SELECT * FROM employees ORDER BY last_name, first_name"
        self.cursor.execute(query)
        employees = self.cursor.fetchall()

        if employees:
            print("\nСписок сотрудников:")
            for employee in employees:
                print(f"ID: {employee['employee_id']} | Имя: {employee['first_name']} {employee['last_name']}")
                print(f"Должность: {employee['position']}")
                print(f"Email: {employee['email']} | Телефон: {employee['phone']}")
                print(f"Дата приема: {employee['hire_date']}")
                print(f"Руководитель: {'Да' if employee['is_manager'] else 'Нет'}")
                print("-" * 50)
        else:
            print("Сотрудники не найдены.")

    def add_employee(self):
        print("\nДобавление нового сотрудника:")
        first_name = input("Имя: ")
        last_name = input("Фамилия: ")
        position = input("Должность: ")
        email = input("Email: ")
        phone = input("Телефон: ")
        hire_date = input("Дата приема (ГГГГ-ММ-ДД): ")
        is_manager = input("Руководитель? (да/нет): ").lower() == 'да'
        username = input("Имя пользователя: ")
        password = getpass.getpass("Пароль: ")

        query = """
        INSERT INTO employees 
        (first_name, last_name, position, email, phone, hire_date, is_manager, username, password)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        try:
            self.cursor.execute(query, (
            first_name, last_name, position, email, phone, hire_date, is_manager, username, password))
            self.connection.commit()
            print("Сотрудник успешно добавлен.")
        except Error as e:
            print(f"Ошибка при добавлении сотрудника: {e}")

    def edit_employee(self):
        employee_id = input("Введите ID сотрудника для редактирования: ")

        query = "SELECT * FROM employees WHERE employee_id = %s"
        self.cursor.execute(query, (employee_id,))
        employee = self.cursor.fetchone()

        if not employee:
            print("Сотрудник не найден.")
            return

        print("\nТекущие данные сотрудника:")
        print(f"1. Имя: {employee['first_name']}")
        print(f"2. Фамилия: {employee['last_name']}")
        print(f"3. Должность: {employee['position']}")
        print(f"4. Email: {employee['email']}")
        print(f"5. Телефон: {employee['phone']}")
        print(f"6. Руководитель: {'Да' if employee['is_manager'] else 'Нет'}")
        print(f"7. Имя пользователя: {employee['username']}")
        print("8. Пароль: ********")

        field = input("\nВведите номер поля для изменения (или 0 для отмены): ")

        if field == '0':
            return

        fields = {
            '1': 'first_name',
            '2': 'last_name',
            '3': 'position',
            '4': 'email',
            '5': 'phone',
            '6': 'is_manager',
            '7': 'username',
            '8': 'password'
        }

        if field not in fields:
            print("Неверный выбор поля.")
            return

        field_name = fields[field]
        new_value = input(f"Введите новое значение для {field_name}: ")

        if field == '6':
            new_value = new_value.lower() == 'да'
        elif field == '8':
            new_value = getpass.getpass("Введите новый пароль: ")

        query = f"UPDATE employees SET {field_name} = %s WHERE employee_id = %s"
        try:
            self.cursor.execute(query, (new_value, employee_id))
            self.connection.commit()
            print("Данные сотрудника успешно обновлены.")
        except Error as e:
            print(f"Ошибка при обновлении данных: {e}")

    def delete_employee(self):
        employee_id = input("Введите ID сотрудника для удаления: ")

        # Проверяем, существует ли сотрудник
        query = "SELECT * FROM employees WHERE employee_id = %s"
        self.cursor.execute(query, (employee_id,))
        employee = self.cursor.fetchone()

        if not employee:
            print("Сотрудник не найден.")
            return

        # Проверяем, не является ли сотрудник текущим пользователем
        if employee_id == str(self.current_user['employee_id']):
            print("Нельзя удалить текущего пользователя.")
            return

        confirm = input(
            f"Вы уверены, что хотите удалить сотрудника {employee['first_name']} {employee['last_name']}? (да/нет): ")
        if confirm.lower() != 'да':
            print("Удаление отменено.")
            return

        query = "DELETE FROM employees WHERE employee_id = %s"
        try:
            self.cursor.execute(query, (employee_id,))
            self.connection.commit()
            print("Сотрудник успешно удален.")
        except Error as e:
            print(f"Ошибка при удалении сотрудника: {e}")

    def manage_schedule(self):
        while True:
            print("\n=== Управление расписанием ===")
            print("1. Просмотреть расписание уборки")
            print("2. Просмотреть график работы сотрудников")
            print("3. Назначить смену сотруднику")
            print("4. Вернуться в главное меню")

            choice = input("Выберите действие: ")

            if choice == '1':
                self.view_cleaning_schedule()
            elif choice == '2':
                self.view_employee_schedule()
            elif choice == '3':
                self.assign_shift()
            elif choice == '4':
                break
            else:
                print("Неверный выбор. Попробуйте снова.")

    def view_cleaning_schedule(self):
        start_date = input("Начальная дата (ГГГГ-ММ-ДД): ")
        end_date = input("Конечная дата (ГГГГ-ММ-ДД): ")

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            if end_date <= start_date:
                print("Конечная дата должна быть позже начальной.")
                return
        except ValueError:
            print("Неверный формат даты. Используйте ГГГГ-ММ-ДД.")
            return

        query = """
        SELECT c.cleaning_id, r.room_number, e.first_name, e.last_name, 
               c.scheduled_date, c.scheduled_time, c.status
        FROM cleaning c
        JOIN rooms r ON c.room_id = r.room_id
        JOIN employees e ON c.employee_id = e.employee_id
        WHERE c.scheduled_date BETWEEN %s AND %s
        ORDER BY c.scheduled_date, c.scheduled_time
        """

        self.cursor.execute(query, (start_date, end_date))
        cleanings = self.cursor.fetchall()

        if cleanings:
            print(f"\nРасписание уборки с {start_date} по {end_date}:")
            for cleaning in cleanings:
                print(f"ID: {cleaning['cleaning_id']} | Номер: {cleaning['room_number']}")
                print(f"Сотрудник: {cleaning['first_name']} {cleaning['last_name']}")
                print(f"Дата/время: {cleaning['scheduled_date']} {cleaning['scheduled_time']}")
                print(f"Статус: {cleaning['status']}")
                print("-" * 50)
        else:
            print("Уборки не запланированы на выбранный период.")

    def view_employee_schedule(self):

        print("\nФункционал просмотра графика работы сотрудников будет реализован в следующей версии.")

    def assign_shift(self):

        print("\nФункционал назначения смен будет реализован в следующей версии.")

    def analyze_sales(self):
        while True:
            print("\n=== Анализ продаж ===")
            print("1. Анализ по категориям номеров")
            print("2. Анализ по периодам")
            print("3. Вернуться в главное меню")

            choice = input("Выберите действие: ")

            if choice == '1':
                self.sales_by_category()
            elif choice == '2':
                self.sales_by_period()
            elif choice == '3':
                break
            else:
                print("Неверный выбор. Попробуйте снова.")

    def sales_by_category(self):
        start_date = input("Начальная дата (ГГГГ-ММ-ДД): ")
        end_date = input("Конечная дата (ГГГГ-ММ-ДД): ")

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            if end_date <= start_date:
                print("Конечная дата должна быть позже начальной.")
                return
        except ValueError:
            print("Неверный формат даты. Используйте ГГГГ-ММ-ДД.")
            return

        query = """
        SELECT rc.name as category, COUNT(b.booking_id) as bookings_count, 
               SUM(b.total_price) as total_revenue,
               SUM(DATEDIFF(
                   LEAST(b.check_out_date, %s), 
                   GREATEST(b.check_in_date, %s)
               )) as nights_sold
        FROM bookings b
        JOIN rooms r ON b.room_id = r.room_id
        JOIN room_categories rc ON r.category_id = rc.category_id
        WHERE b.status != 'Отменено'
        AND b.check_in_date <= %s
        AND b.check_out_date >= %s
        GROUP BY rc.name
        ORDER BY total_revenue DESC
        """

        self.cursor.execute(query, (end_date, start_date, end_date, start_date))
        sales = self.cursor.fetchall()

        if sales:
            print(f"\nАнализ продаж по категориям номеров с {start_date} по {end_date}:")
            for sale in sales:
                print(f"\nКатегория: {sale['category']}")
                print(f"Количество бронирований: {sale['bookings_count']}")
                print(f"Количество проданных ночей: {sale['nights_sold']}")
                print(f"Общая выручка: {sale['total_revenue']:.2f}")
                print(f"Средняя цена за ночь: {sale['total_revenue'] / sale['nights_sold']:.2f}" if sale[
                                                                                                        'nights_sold'] > 0 else "Средняя цена за ночь: 0.00")
        else:
            print("Нет данных о продажах за выбранный период.")

    def sales_by_period(self):
        period = input("Выберите период (день/неделя/месяц/год): ").lower()

        if period not in ['день', 'неделя', 'месяц', 'год']:
            print("Неверный период. Доступные варианты: день, неделя, месяц, год.")
            return

        if period == 'день':
            date1 = input("Дата (ГГГГ-ММ-ДД): ")
            try:
                date1 = datetime.strptime(date1, '%Y-%m-%d').date()
                start_date = date1
                end_date = date1
            except ValueError:
                print("Неверный формат даты. Используйте ГГГГ-ММ-ДД.")
                return
        elif period == 'неделя':
            week = input("Год и номер недели (ГГГГ-НН): ")
            try:
                year, week_num = map(int, week.split('-'))
                start_date = datetime.strptime(f"{year}-W{week_num}-1", "%Y-W%W-%w").date()
                end_date = start_date + timedelta(days=6)
            except ValueError:
                print("Неверный формат. Используйте ГГГГ-НН.")
                return
        elif period == 'месяц':
            month = input("Год и месяц (ГГГГ-ММ): ")
            try:
                year, month_num = map(int, month.split('-'))
                start_date = date(year, month_num, 1)
                end_date = date(year, month_num + 1, 1) - timedelta(days=1) if month_num < 12 else date(year + 1, 1,
                                                                                                        1) - timedelta(
                    days=1)
            except ValueError:
                print("Неверный формат. Используйте ГГГГ-ММ.")
                return
        elif period == 'год':
            year = input("Год (ГГГГ): ")
            try:
                year_num = int(year)
                start_date = date(year_num, 1, 1)
                end_date = date(year_num, 12, 31)
            except ValueError:
                print("Неверный формат. Используйте ГГГГ.")
                return

        query = """
        SELECT DATE(b.booking_date) as booking_day, 
               COUNT(b.booking_id) as bookings_count, 
               SUM(b.total_price) as total_revenue
        FROM bookings b
        WHERE b.booking_date BETWEEN %s AND %s
        AND b.status != 'Отменено'
        GROUP BY DATE(b.booking_date)
        ORDER BY booking_day
        """

        self.cursor.execute(query, (start_date, end_date))
        sales = self.cursor.fetchall()

        if sales:
            print(f"\nАнализ продаж за {period} с {start_date} по {end_date}:")
            for sale in sales:
                print(f"\nДата: {sale['booking_day']}")
                print(f"Количество бронирований: {sale['bookings_count']}")
                print(f"Общая выручка: {sale['total_revenue']:.2f}")

            # Итого
            total_bookings = sum(sale['bookings_count'] for sale in sales)
            total_revenue = sum(sale['total_revenue'] for sale in sales)

            print(f"\nИтого за период:")
            print(f"Общее количество бронирований: {total_bookings}")
            print(f"Общая выручка: {total_revenue:.2f}")
        else:
            print("Нет данных о продажах за выбранный период.")

    def run(self):
        print("=== Система управления гостиницей ===")

        while True:
            if not self.current_user:
                if not self.login():
                    continue

            if self.is_manager:
                self.manager_menu()
            else:
                self.admin_menu()


if __name__ == "__main__":
    system = HotelManagementSystem()
    system.run()