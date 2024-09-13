from flask import Flask, render_template, request, jsonify, send_file
import datetime
import random
import sqlite3
import re  

import io

app = Flask(__name__)

# Conexion a la base de datos
def init_db():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sorteos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero INTEGER NOT NULL,
                ganador TEXT,
                fecha TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reservas (
                numero INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vaciar_sorteos', methods=['POST'])
def vaciar_sorteos():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sorteos')
        conn.commit()
    return jsonify({'message': 'Todos los sorteos han sido eliminados.'}), 200

@app.route('/registrar_reserva', methods=['POST'])
def registrar_reserva():
    nombre = request.form['nombre']
    numero = int(request.form['numero'])

    if not re.match("^[A-Za-zñÑáéíóúÁÉÍÓ ]+$", nombre):
        return jsonify({'message': 'El nombre solo puede contener letras.'}), 400

    if 0 <= numero <= 99:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nombre FROM reservas WHERE numero = ?', (numero,))
            existing_reserva = cursor.fetchone()

            if existing_reserva:
                return jsonify({'message': 'El numero ya esta reservado. Elige otro numero.'}), 400
            else:
                cursor.execute('INSERT INTO reservas (numero, nombre) VALUES (?, ?)', (numero, nombre))
                conn.commit()
                return jsonify({'message': f'Numero {numero} reservado para {nombre}.'}), 200
    else:
        return jsonify({'message': 'Por favor, ingresa un nombre y un numero válido.'}), 400

@app.route('/mostrar_reservas', methods=['GET'])
def mostrar_reservas():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM reservas')
        reservas = cursor.fetchall()
    return jsonify({numero: nombre for numero, nombre in reservas})

@app.route('/realizar_sorteo', methods=['GET'])
def realizar_sorteo():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM reservas')
        reservas = cursor.fetchall()

    if not reservas:
        return jsonify({'message': '¡Por favor, reserva al menos un numero!'}), 400
    
    numero_ganador = random.randint(0, 99)
    ahora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ganador = next((nombre for numero, nombre in reservas if numero == numero_ganador), None)

    
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO sorteos (numero, ganador, fecha) VALUES (?, ?, ?)', 
                       (numero_ganador, ganador, ahora))
        conn.commit()

    
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM reservas')
        conn.commit()

    return jsonify({'numero': numero_ganador, 'ganador': ganador, 'fecha': ahora}), 200



@app.route('/mostrar_sorteos', methods=['GET'])
def mostrar_sorteos():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sorteos ORDER BY fecha DESC')
        sorteos = cursor.fetchall()
    return jsonify(sorteos)

if __name__ == '__main__':
    app.run(debug=True)
