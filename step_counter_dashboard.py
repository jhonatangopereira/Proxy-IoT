from flask import Flask
from multiprocessing import Process

import argparse
import dash
import json
import numpy as np
import pandas as pd
import socket


app_flask = Flask(__name__)
app_dash = dash.Dash(__name__, server=app_flask)

# Inicializando o servidor Flask
@app_flask.route('/')
def index():
    return app_dash.index()

# Layout do aplicativo Dash
app_dash.layout = dash.html.Div([
    dash.html.H1("Calculadora de Gasto Calórico"),
    # dash.html.Button('Atualizar dados', id='atualizar-dados', n_clicks=0),
    dash.html.Br(),
    dash.html.Button('Limpar dados', id='limpar-dados', n_clicks=0),
    dash.html.Br(),
    dash.html.Label("Digite seu peso (Kg):\t", id='weight-label'),
    dash.dcc.Input(id='weight-input', type='number', value= 0),
    dash.html.Br(),
    dash.html.Br(),
    dash.html.Div(id='output-distance'),
    dash.html.Br(),
    dash.html.Div(id='output-speed'),
    dash.html.Br(),
    dash.html.Div(id='output-caloriesperminute'),
    dash.html.Br(),
    dash.html.Div(id='output-totalcalories'),
    dash.dcc.Graph(id='calories-graph')
])

# Dados iniciais para o gráfico
initial_data = {'distance': 0, 'speed': 0, 'calories': 0}

# Botão para limpar dados do arquivo esp32_data.csv
@app_dash.callback(
    [dash.Output('weight-input', 'value')],
    [dash.dependencies.Input('limpar-dados', 'n_clicks')],
    [dash.State('weight-input', 'value')]
)
def clear_data(n_clicks, weight):
    print("Limpar dados")
    if n_clicks > 0:
        esp32_data = pd.DataFrame(columns=["x", "y", "z"])
        esp32_data.to_csv("esp32_data.csv", index=False)
    return weight,

# Botão para limpar dados do arquivo esp32_data.csv
# @app_dash.callback(
#     [dash.Output('weight-input', 'value')],
#     [dash.dependencies.Input('atualizar-dados', 'n_clicks')],
#     [dash.State('weight-input', 'value'),
#      dash.State('weight-label', 'children')]
# )
# def update_data(n_clicks, weight, weight_label):
#     print("Limpar dados")
#     return weight,

# Callback para atualizar a saída com o gasto calórico e o gráfico
@app_dash.callback(
    [dash.Output('output-distance', 'children'),
     dash.Output('output-speed', 'children'),
     dash.Output('output-caloriesperminute', 'children'),
     dash.Output('output-totalcalories', 'children'),
     dash.Output('calories-graph', 'figure')],
    [dash.Input('weight-input', 'value')]
)
def update_calories(weight):
    esp32_data = pd.read_csv("esp32_data.csv")
    print(esp32_data)
    accelerationX = np.abs(np.array(esp32_data["x"]))
    accelerationY = np.abs(np.array(esp32_data["y"]))
    accelerationZ = np.abs(np.array(esp32_data["z"]))

    # calcular velocidade a partir de aceleração nos eixos X e Y
    speed = np.sqrt(np.sum(accelerationX ** 2 + accelerationY ** 2))

    # Fórmula de gasto calórico
    caloric_expenditure = speed * weight * 0.0175

    # Convertendo para calorias por minuto
    caloric_expenditure_per_minute = caloric_expenditure * 60

    # Distância percorrida (exemplo simples, ajuste conforme necessário)
    distance = speed * len(accelerationX) # Supondo que a distância seja proporcional à velocidade

    total_minutes = len(accelerationX)  # Número total de minutos

    # Calculando o gasto calórico total
    caloric_expenditure_total = caloric_expenditure_per_minute * total_minutes

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

    return f" Distância percorrida: {distance:.2f} metros", f"Velocidade: {speed:.2f} m/s", f"Gasto calórico por minuto: {caloric_expenditure_per_minute:.2f} Cal", f"Gasto calórico total: {caloric_expenditure_total:.2f} Cal", figure

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

    # loop to listen to the server and receive data when is available
    while True:
        response_data = sock.recv(1024).decode("utf-8")
        if response_data == "":
            continue

        # Convert data to JSON
        data_json = json.loads(response_data)
        print(data_json)
        print(data_json['x'])

        esp32_data = pd.read_csv("esp32_data.csv")
        print(esp32_data)

        x = list()
        y = list()
        z = list()
        for i in range(0, len(data_json['x']), 2):            
            x.append((data_json['x'][i] + data_json['x'][i + 1]) / 2 / 100)
            y.append((data_json['y'][i] + data_json['y'][i + 1]) / 2 / 100)
            z.append((data_json['z'][i] + data_json['z'][i + 1]) / 2 / 100)
        new_df = pd.DataFrame({"x": x, "y": y, "z": z})
        print(new_df)

        # Atualizando dados para esp32_data
        esp32_data = pd.concat([esp32_data, new_df], axis=0, ignore_index=True)
        print(esp32_data)

        # Salvando dados no esp32_data.csv
        esp32_data.to_csv("esp32_data.csv", index=False)

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
    
    # Create a thread for the Flask app
    flask_process = Process(target=run_flask)
    flask_process.start()

    # # Create and start the TCP server process
    tcp_process = Process(target=receive_data, kwargs={"ap": ap})
    tcp_process.start()
    try:
        # receive_data(ap=ap)
        # Wait for both processes to finish
        flask_process.join()
        tcp_process.join()
    except KeyboardInterrupt:
        # Handle keyboard interrupt (Ctrl+C) to gracefully stop the processes
        flask_process.terminate()
        tcp_process.terminate()
        flask_process.join()
        tcp_process.join()
    