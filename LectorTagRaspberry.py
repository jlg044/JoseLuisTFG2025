import time
import serial
import serial.tools.list_ports
from pymongo import MongoClient
from datetime import datetime
from pydwm1001.dwm1001 import PassiveTag, ShellCommand, TagPosition

# Configuración de MongoDB
MONGO_URI = "mongodb://esp32_user:secure_password@192.168.1.39:27017/Datos-ESP32?authSource=Datos-ESP32"
DATABASE_NAME = "Datos-ESP32"
COLLECTION_NAME = "DWM1001_Posiciones"

# Conexión a MongoDB
mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = mongo_client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

BAUD_RATE = 115200
tag_mapping = {}  # Diccionario para asignar nombres a los Tags detectados
next_tag_number = 1  # Contador para asignar nombres únicos

def find_dwm1001_port():
    """Detecta automáticamente el puerto COM del DWM1001."""
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if "USB" in port.description or "UART" in port.description or "JLink" in port.description or "USB" in port.device or "AMA" in port.device or "tty" in port.device:
            return port.device
    return None

SERIAL_PORT = find_dwm1001_port()
if not SERIAL_PORT:
    exit(1)

serial_handle = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
dwm = PassiveTag(serial_handle)

dwm.enter_shell_mode()

# Obtener la ID del Tag
dwm.send_shell_command(ShellCommand.SI)
raw_data = serial_handle.read_until(b"dwm> ").decode(errors='ignore')

uwb_id = None
for line in raw_data.split("\n"):
    if "addr=" in line:
        uwb_id = line.strip().split("addr=")[-1]
        break

if uwb_id not in tag_mapping:
    tag_mapping[uwb_id] = f"persona-{next_tag_number}"
    next_tag_number += 1

tag_name = tag_mapping[uwb_id]

# Activar posicionamiento
dwm.send_shell_command(ShellCommand.LEP)

try:
    while True:
        raw_data = serial_handle.readline().decode(errors='ignore').strip()
        if raw_data:
            print(f"Datos recibidos crudos: {raw_data}")

            if raw_data.startswith("POS"):
                try:
                    parts = raw_data.split(",")
                    if len(parts) == 5:
                        _, x, y, z, quality = parts

                        position = TagPosition(float(x), float(y), float(z), int(quality))
                        timestamp = int(time.time())

                        print(f"x={position.x_m}, y={position.y_m}, z={position.z_m}, calidad={position.quality}, tiempo={timestamp}")

                        document = {
                            "tag_id": uwb_id,
                            "nombre": tag_name,
                            "x": position.x_m,
                            "y": position.y_m,
                            "z": position.z_m,
                            "calidad": position.quality,
                            "timestamp": timestamp
                        }
                        collection.insert_one(document)

                    else:
                        print(f"Formato inesperado: {raw_data}")
                except ValueError:
                    print(f"Error al convertir los datos: {raw_data}")

        time.sleep(1)

except KeyboardInterrupt:
    serial_handle.close()
    print("Conexión cerrada.")
