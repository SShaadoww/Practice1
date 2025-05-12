from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from mysql.connector import Error
from datetime import datetime, date

app = Flask(__name__)

db_config = {
    'host': 'localhost',
    'database': 'hotel_management',
    'user': 'hotel_user',
    'password': 'hotel_password'
}


def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Ошибка подключения к MySQL: {e}")
        return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/rooms', methods=['GET', 'POST'])
def rooms():
    if request.method == 'POST':
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')

        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()

            if check_out_date <= check_in_date:
                error = "Дата выезда должна быть позже даты заезда."
                return render_template('rooms.html', error=error)
        except ValueError:
            error = "Неверный формат даты. Используйте ГГГГ-ММ-ДД."
            return render_template('rooms.html', error=error)

        connection = get_db_connection()
        if not connection:
            return render_template('rooms.html', error="Ошибка подключения к базе данных")

        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT r.room_id, r.room_number, r.floor, rc.name as category, 
               rc.description, rc.base_price, rc.capacity
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
        ORDER BY rc.base_price DESC
        """

        cursor.execute(query, (
            check_out_date, check_in_date,
            check_in_date, check_out_date,
            check_in_date, check_out_date
        ))
        available_rooms = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template('rooms.html', rooms=available_rooms,
                               check_in=check_in, check_out=check_out)

    return render_template('rooms.html')


@app.route('/book/<int:room_id>', methods=['GET', 'POST'])
def book(room_id):
    if request.method == 'POST':
        # Получаем данные из формы
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        passport = request.form.get('passport')
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')

        if not all([first_name, last_name, phone, passport, check_in, check_out]):
            error = "Пожалуйста, заполните все обязательные поля."
            return render_template('booking.html', error=error, room_id=room_id,
                                   check_in=check_in, check_out=check_out)

        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()

            if check_out_date <= check_in_date:
                error = "Дата выезда должна быть позже даты заезда."
                return render_template('booking.html', error=error, room_id=room_id)
        except ValueError:
            error = "Неверный формат даты. Используйте ГГГГ-ММ-ДД."
            return render_template('booking.html', error=error, room_id=room_id)

        connection = get_db_connection()
        if not connection:
            return render_template('booking.html', error="Ошибка подключения к базе данных", room_id=room_id)

        try:
            cursor = connection.cursor(dictionary=True)

            # Проверяем доступность номера
            query = """
            SELECT r.room_id, rc.base_price
            FROM rooms r
            JOIN room_categories rc ON r.category_id = rc.category_id
            WHERE r.room_id = %s AND r.status = 'Чистый'
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

            cursor.execute(query, (
                room_id,
                check_out_date, check_in_date,
                check_in_date, check_out_date,
                check_in_date, check_out_date
            ))
            room = cursor.fetchone()

            if not room:
                error = "Выбранный номер больше недоступен для бронирования."
                return render_template('booking.html', error=error, room_id=room_id)

            # Рассчитываем стоимость
            nights = (check_out_date - check_in_date).days
            total_price = nights * room['base_price']

            # Добавляем гостя
            query = """
            INSERT INTO guests (first_name, last_name, email, phone, passport_number)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (first_name, last_name, email, phone, passport))
            guest_id = cursor.lastrowid

            # Создаем бронирование
            query = """
            INSERT INTO bookings (guest_id, room_id, check_in_date, check_out_date, total_price)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (guest_id, room_id, check_in_date, check_out_date, total_price))
            booking_id = cursor.lastrowid

            connection.commit()

            return redirect(url_for('my_bookings', passport=passport))

        except Error as e:
            connection.rollback()
            error = f"Ошибка при создании бронирования: {e}"
            return render_template('booking.html', error=error, room_id=room_id)

        finally:
            cursor.close()
            connection.close()

    # показываем форму бронирования
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')

    connection = get_db_connection()
    if not connection:
        return render_template('booking.html', error="Ошибка подключения к базе данных", room_id=room_id)

    cursor = connection.cursor(dictionary=True)

    # Получаем информацию о номере
    query = """
    SELECT r.room_number, r.floor, rc.name as category, rc.base_price, rc.capacity
    FROM rooms r
    JOIN room_categories rc ON r.category_id = rc.category_id
    WHERE r.room_id = %s
    """
    cursor.execute(query, (room_id,))
    room = cursor.fetchone()

    cursor.close()
    connection.close()

    if not room:
        return redirect(url_for('rooms'))

    return render_template('booking.html', room=room, room_id=room_id,
                           check_in=check_in, check_out=check_out)


@app.route('/my-bookings')
def my_bookings():
    passport = request.args.get('passport')

    if not passport:
        return render_template('my_bookings.html', error="Введите номер паспорта для просмотра бронирований")

    connection = get_db_connection()
    if not connection:
        return render_template('my_bookings.html', error="Ошибка подключения к базе данных")

    cursor = connection.cursor(dictionary=True)

    # Получаем бронирования гостя
    query = """
    SELECT b.booking_id, r.room_number, b.check_in_date, b.check_out_date, 
           b.total_price, b.status, b.payment_status
    FROM bookings b
    JOIN guests g ON b.guest_id = g.guest_id
    JOIN rooms r ON b.room_id = r.room_id
    WHERE g.passport_number = %s
    ORDER BY b.check_in_date DESC
    """
    cursor.execute(query, (passport,))
    bookings = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('my_bookings.html', bookings=bookings, passport=passport)


if __name__ == '__main__':
    app.run(debug=True)