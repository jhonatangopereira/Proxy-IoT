from flask import Flask, render_template, request
import argparse
import dash
import socket
import json
import time
from multiprocessing import Process
import numpy as np
import threading

app_flask = Flask(__name__)
app_dash = dash.Dash(__name__, server=app_flask)

# Layout do aplicativo Dash
app_dash.layout = dash.html.Div([
    dash.html.H1("Calculadora de Gasto Calórico"),
    dash.html.Label("Digite seu peso (Kg):"),
    dash.dcc.Input(id='weight-input', type='number', value= 0),
    dash.html.Div(id='output-calories'),
    dash.dcc.Graph(id='calories-graph')
])

# Dados iniciais para o gráfico
initial_data = {'distance': 0, 'speed': 0, 'calories': 0}
esp32_data = {"acceleration": {"x": [], "y": [], "z": []}}

# Inicializando o servidor Flask
@app_flask.route('/')
def index():
    return app_dash.index()

# Callback para atualizar a saída com o gasto calórico e o gráfico
@app_dash.callback(
    [dash.Output('output-calories', 'children'),
     dash.Output('calories-graph', 'figure')],
    [dash.Input('weight-input', 'value')]
)
def update_calories(weight):
    global esp32_data
    accelerationX = np.abs(np.array(esp32_data["acceleration"]["x"])) / 100
    accelerationY = np.abs(np.array(esp32_data["acceleration"]["y"])) / 100
    accelerationZ = np.abs(np.array(esp32_data["acceleration"]["z"])) / 100

    print(accelerationX)
    print(accelerationY)

    # calcular velocidade a partir de aceleração nos eixos X e Y
    speed = np.sqrt(np.sum(accelerationX ** 2 + accelerationY ** 2))
    print(speed)

    # Fórmula de gasto calórico
    caloric_expenditure = speed * weight * 0.0175
    print(caloric_expenditure)

    # Convertendo para calorias por minuto
    caloric_expenditure_per_minute = caloric_expenditure * 60
    print(caloric_expenditure_per_minute)

    # Distância percorrida (exemplo simples, ajuste conforme necessário)
    distance = speed * len(accelerationX) # Supondo que a distância seja proporcional à velocidade
    print(distance)

    # CORRIGIR TOTAL MINUTES PARA O TEMPO TOTAL RECEBIDO DO ESP32
    total_minutes = len(accelerationX)  # Número total de minutos
    print(total_minutes)

    # Calculando o gasto calórico total
    caloric_expenditure_total = caloric_expenditure_per_minute * total_minutes
    print(caloric_expenditure_total)

    # Atualizando dados para o gráfico
    # updated_data = {'Distancia': distance, 'Speed': speed, 'Calorias': caloric_expenditure_per_minute, 'Calorias total': caloric_expenditure_total}

    # Criando o gráfico de barras
    figure = {
        'data': [
            {'x': ['Distancia', 'Velocidade', 'Calorias', 'Calorias total'], 'y': [distance, speed, caloric_expenditure_per_minute, caloric_expenditure_total], 'type': 'bar', 'name': 'Metrics'},
        ],
        'layout': {
            'title': 'Estatísticas da Corrida',
            'yaxis': {'title': 'Valores'},
            'barmode': 'group'
        }
    }

    #return f"Gasto calórico por minuto: {caloric_expenditure_per_minute:.2f} Cal", figure
    #return f"Gasto calórico por minuto: {caloric_expenditure_per_minute:.2f} Cal  " f" | Distância percorrida: {distance:.2f} mts   " f" |  Velocidade: {speed:.2f} m/s", figure
    return f" Distância percorrida: {distance:.2f} metros  |  Velocidade: {speed:.2f} m/s |  Gasto calórico por minuto: {caloric_expenditure_per_minute:.2f} Cal  |  Gasto calórico total: {caloric_expenditure_total:.2f} Cal", figure

def receive_data(ap):
    args = vars(ap.parse_args())

    HOST = args['address']  
    PORT = int(args['port']) 
    device_id = args['deviceid']

    # Create a socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the remote host and port
    sock.connect((HOST, PORT))

    print("Conectado!")

    # Send a request to the host
    sock.send("app\n".encode()[:-1])

    # Get the host's response, no more than, say, 1,024 bytes
    response_data = sock.recv(1024).decode("utf-8") 
    print(f"Resposta da conexão: {response_data}")

    if response_data == "fail":
        sock.close()
        exit()

    # Send a request to the host
    sock.send(f"{device_id}\n".encode()[:-1])
    # Receive data from the server
    response = sock.recv(1024).decode("utf-8") 
    print(f"Resposta do device: {response}")

    if response == "fail":
        sock.close()
        exit()

    global esp32_data
    
    # loop to listen to the server and receive data when is available
    while True:
        response_data = sock.recv(1024).decode("utf-8")
        if response_data == "":
            continue

        # Convert data to JSON
        data_json = json.loads(response_data)
        print(data_json)
        print(data_json['x'])

        # EXEMPLO X = [60 VALORES]
        # PRA X = [30 VALORES]
        x = list()
        y = list()
        z = list()
        for i in range(0, len(data_json['x']), 2):            
            x.append((data_json['x'][i] + data_json['x'][i + 1]) / 2)
            y.append((data_json['y'][i] + data_json['y'][i + 1]) / 2)
            z.append((data_json['z'][i] + data_json['z'][i + 1]) / 2)

        # Atualizando dados para esp32_data
        esp32_data["acceleration"]["x"].extend(x)
        esp32_data["acceleration"]["y"].extend(y)
        esp32_data["acceleration"]["z"].extend(z)

        print(esp32_data["acceleration"])

        # Update the Dash app
        # app_dash.callback_map.get('update-calories')(0)

def run_flask():
    app_flask.run()

if __name__ == '__main__':
    # Construct the argument parser
    ap = argparse.ArgumentParser()

    # Get arguments from .env
    from dotenv import load_dotenv
    load_dotenv()
    import os
    HOST = os.getenv("HOST")
    PORT = os.getenv("PORT")
    DEVICE_ID = os.getenv("DEVICE_ID")

    # Add the arguments to the parser
    ap.add_argument("-a", "--address", required=False,
    help="Server IP Address or URL", default=HOST)
    ap.add_argument("-p", "--port", required=False,
    help="Server Port", default=PORT)
    ap.add_argument("-d", "--deviceid", required=False,
    help="Device ID", default=DEVICE_ID)

    # flask_process = threading.Thread(target=run_flask)
    # flask_process.start()
    
    flask_process = Process(target=run_flask)
    flask_process.start()

    # # Create and start the TCP server process
    tcp_process = Process(target=receive_data, kwargs={"ap": ap})
    tcp_process.start()
    try:
        # receive_data(ap=ap)

        # Create a thread for the Flask app

        # Wait for both processes to finish
        flask_process.join()
        tcp_process.join()
    except KeyboardInterrupt:
        # Handle keyboard interrupt (Ctrl+C) to gracefully stop the processes
        flask_process.terminate()
        tcp_process.terminate()
        flask_process.join()
        tcp_process.join()
    