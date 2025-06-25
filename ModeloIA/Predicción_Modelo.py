import numpy as np
import joblib
import pandas as pd
from pymongo import MongoClient
import time
import warnings
import paho.mqtt.client as mqtt
import requests
import json

# ========== CONFIGURACIÓN ==========
BROKER = "192.168.1.54"
PORT = 9001  # WebSockets
TOPIC = "Ion/Loc"
MONGO_URI = "mongodb://esp32_user:secure_password@192.168.1.54:27017/Datos-ESP32?authSource=Datos-ESP32"
cols_esp = ["ESP32Cocina", "ESP32Habita", "ESP32Hall", "ESP32Salon", "ESP32Salon2"]

warnings.filterwarnings("ignore", category=UserWarning)

# ========== CARGA DE MODELOS ==========
modelo = joblib.load(r'C:\Users\jsire\Desktop\TFG\ModeloIA\modelo_randomforest.pkl')
scaler_in = joblib.load(r'C:\Users\jsire\Desktop\TFG\ModeloIA\scaler_entrada002.pkl')
scaler_out = joblib.load(r'C:\Users\jsire\Desktop\TFG\ModeloIA\scaler_salida002.pkl')

# ========== CONEXIÓN A MONGODB ==========
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["Datos-ESP32"]
collection_esp32 = db["esp32"]

# ========== CONFIGURAR CLIENTE MQTT ==========
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado a MQTT WebSockets")
    else:
        print(f"Error al conectar: {rc}")

client = mqtt.Client(transport="websockets")
client.on_connect = on_connect
client.connect(BROKER, PORT, 60)
client.loop_start()

# ========== FUNCIÓN PARA PUBLICAR DATOS AL BACK-END ==========
def send_to_backend(x, y, dispositivo, timestamp):
    url = "http://localhost:3000/api/posicion" 
    data = {
        "x": x,
        "y": y,
        "dispositivo": dispositivo,
        "timestamp": timestamp
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("Posición enviada al back-end correctamente.")
        else:
            print(f"Error al enviar datos: {response.status_code} - {response.text}")
    except Exception as e:
        print("Error de conexión con el back-end:", e)

# ========== FUNCIÓN PARA PUBLICAR DATOS MQTT ==========
#def send_message(x, y, device, timestamp):
#    data = {"x": x, "y": y, "device": device, "timestamp": timestamp}
#    payload = json.dumps(data)
#    client.publish(TOPIC, payload)
#    print(f"Mensaje enviado: {payload}")

# ========== BUCLE PRINCIPAL ==========
try:
    while True:
        # Obtener últimos RSSI por ESP32
        ultimo = collection_esp32.find_one(
            {},
            sort=[("timestamp", -1)]
        )

        if ultimo is None or "deviceName" not in ultimo:
            print("No se pudo determinar el dispositivo más reciente.")
            time.sleep(9)
            continue

        # Extraer el nombre del dispositivo más reciente
        device_name_actual = ultimo["deviceName"]
        ultimo_timestamp = ultimo["timestamp"]

        # Obtener todos los datos de ese timestamp y ese dispositivo
        datos_ultimo = collection_esp32.find(
            {"deviceName": device_name_actual, "timestamp": ultimo_timestamp}
        )

        # Construir el vector de entrada con -120 por defecto si falta algún ESP32
        datos_dict = {d["esp32Name"]: d["rssi"] for d in datos_ultimo if "rssi" in d}
        entrada_rssi = [datos_dict.get(esp_name, -120.0) for esp_name in cols_esp]

        # Crear DataFrame y predecir ubicación
        entrada_dict = dict(zip(cols_esp, entrada_rssi))
        entrada_df = pd.DataFrame([entrada_dict])[cols_esp]
        entrada_normalizada = scaler_in.transform(entrada_df)
        pred_normalizada = modelo.predict(entrada_normalizada)
        pred_real = scaler_out.inverse_transform(pred_normalizada)

        x, y = pred_real[0][:2]
        print(f"Ubicación estimada → x: {x:.2f}, y: {y:.2f}    [RSSI: {entrada_rssi}]")

        # Enviar por MQTT o por BACK-END
        send_to_backend(x, y, device_name_actual, ultimo_timestamp)
        #send_message(x, y, device_name_actual, ultimo_timestamp)

        time.sleep(9)

except KeyboardInterrupt:
    print("\nInterrupción manual. Cerrando programa...")

finally:
    client.loop_stop()
    client.disconnect()
    mongo_client.close()
    print("Conexiones cerradas.")