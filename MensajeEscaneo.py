import paho.mqtt.client as mqtt
import time
import json

# Configuración del broker MQTT
BROKER = "192.168.137.100"
PORT = 1883  # TCP, para Python
TOPICS = ["ble/scanH", "ble/scanC", "ble/scanS", "ble/scanA", "ble/scanS2"]
MESSAGE = "start"
DEVICE = "IphoneSelu"
timeEsc = 8
topicweb = "Ion/disp"

# ========== Callbacks ==========
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Conectado al broker MQTT en {BROKER}")
        client.subscribe(topicweb)
        print(f"Suscrito al tópico: {topicweb}")
    else:
        print(f"Error al conectar al broker MQTT, código: {rc}")

def on_message(client, userdata, msg):
    global DEVICE
    payload = msg.payload.decode()
    print("Payload recibido:", payload)
    try:
        data = json.loads(payload)
        if "device" in data:
            DEVICE = data["device"]
            print(f"Dispositivo cambiado a: {DEVICE}")
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

def on_publish(client, userdata, mid):
    print(f"Mensaje publicado con ID: {mid}")

def on_disconnect(client, userdata, rc):
    print("Desconectado del broker MQTT. Intentando reconectar...")
    while True:
        try:
            client.reconnect()
            print("Re-conectado al broker MQTT.")
            break
        except:
            print("Reintentando conexión en 5 segundos...")
            time.sleep(5)

# ========== Crear cliente MQTT ==========
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message     
mqtt_client.on_publish = on_publish
mqtt_client.on_disconnect = on_disconnect

# ========== Conectar ==========
try:
    print(f"Conectando al broker MQTT en {BROKER}:{PORT}...")
    mqtt_client.connect(BROKER, PORT, keepalive=60)
except Exception as e:
    print(f"Error al conectar al broker MQTT: {e}")
    exit()

mqtt_client.loop_start()

# ========== Bucle principal ==========
print(f"Enviando mensaje '{MESSAGE}' con timestamp a los topics {TOPICS} cada {timeEsc} segundos. Presiona Ctrl+C para detener.")
try:
    count = 1
    while True:
        if mqtt_client.is_connected():
            timestamp = int(time.time())
            message_with_timestamp = f"{MESSAGE}|{timestamp}|{DEVICE}"
            print(f"\nEnvío #{count}: Publicando '{message_with_timestamp}' en los topics...")
            for topic in TOPICS:
                result = mqtt_client.publish(topic, message_with_timestamp)
                status = result.rc
                if status == 0:
                    print(f"Mensaje enviado correctamente a '{topic}'")
                else:
                    print(f"Error al enviar el mensaje a '{topic}'")
            count += 1
        else:
            print("Cliente MQTT desconectado. Esperando reconexión...")

        time.sleep(timeEsc)
except KeyboardInterrupt:
    print("\nPrograma detenido por el usuario")
finally:
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print("Desconectado del broker MQTT")
