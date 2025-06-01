import paho.mqtt.client as mqtt
from pymongo import MongoClient
import json

# Configuración del broker MQTT
BROKER =  "192.168.137.100"
PORT = 1883
TOPICS = ["ble/halls", "ble/salons", "ble/salons2", "ble/cocinas", "ble/habitas"]

# Configuración de MongoDB
MONGO_URI = "mongodb://esp32_user:secure_password@192.168.137.100:27017/Datos-ESP32?authSource=Datos-ESP32"
DATABASE_NAME = "Datos-ESP32"
COLLECTION_NAME = "esp32"

# Conexión a MongoDB
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Callback al conectarse al broker MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado al broker MQTT")
        for topic in TOPICS:
            client.subscribe(topic)
            print(f"Suscrito al tópico: {topic}")
    else:
        print(f"Error al conectar al broker MQTT, código: {rc}")

# Callback al recibir un mensaje MQTT
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        print("Payload recibido:", payload)
        data = json.loads(payload)

        esp32_name = data.get("esp32Name")
        timestamp = data.get("timestamp")

        if "esp32Name" and "timestamp" in data:
            collection.insert_one(data)
            print(f"Mensaje de {esp32_name}, {timestamp}")
        else:
            print("Mensaje recibido pero no contiene los campos necesarios, ignorado.")

    except Exception as e:
        print(f"Error al procesar el mensaje: {e}")

# Crear el cliente MQTT y asignar los callbacks
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Conexión al broker MQTT
try:
    mqtt_client.connect(BROKER, PORT, keepalive=60)
except Exception as e:
    print(f"Error al conectar al broker MQTT: {e}")
    exit()

# Mantener el cliente MQTT en ejecución
print("Escuchando mensajes MQTT...")
mqtt_client.loop_forever()
