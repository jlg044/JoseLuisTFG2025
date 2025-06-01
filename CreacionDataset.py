import csv
from datetime import datetime
from pymongo import MongoClient

def main():
    # Conexión a MongoDB
    MONGO_URI = "mongodb://esp32_user:secure_password@192.168.1.54:27017/Datos-ESP32?authSource=Datos-ESP32"
    client = MongoClient(MONGO_URI)
    db = client["Datos-ESP32"]

    escan = 6 # Cada cuanto tiempo se van a coger datos
    device = "IphoneSelu"

    # Colecciones
    collection_esp32 = db["esp32"]
    collection_dwm = db["DWM1001_Posiciones"]

    csv_filename = "Location.csv"
    fieldnames = ["timestamp"]

    # Obtener nombres únicos de ESP32
    esp_names = sorted(collection_esp32.distinct("esp32Name"))
    for esp_name in esp_names:
        fieldnames.append(f"{esp_name}")

    fieldnames.extend(["x", "y", "z"])

    with open(csv_filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

    # Buscar primer timestamp
    first_entry = collection_esp32.find_one({"deviceName": device}, sort=[("timestamp", 1)])
    if not first_entry:
        print("No hay datos para {device} en la colección ESP32")
        return

    start_time = first_entry["timestamp"]
    end_time = start_time + escan
    empty_counter = 0  # Contador de registros vacíos consecutivos

    print(f"Procesando datos desde {start_time}...")

    while True:
        row = {"timestamp": end_time}
        datos_validos = False

        # Para cada ESP32
        for esp_name in esp_names:
            data_esp = collection_esp32.find_one(
                {
                    "esp32Name": esp_name,
                    "deviceName": device,
                    "timestamp": {"$gte": start_time, "$lte": end_time}
                },
                sort=[("timestamp", -1)]
            )
            if data_esp:
                row[esp_name] = data_esp.get("rssi", "")
                datos_validos = True
            else:
                row[esp_name] = ""

        # Para la posición
        data_dwm = collection_dwm.find_one(
            {"timestamp": {"$gte": start_time, "$lte": end_time}},
            sort=[("timestamp", -1)]
        )
        if data_dwm:
            row["x"] = data_dwm.get("x", "")
            row["y"] = data_dwm.get("y", "")
            row["z"] = data_dwm.get("z", "")
            datos_validos = True
        else:
            row["x"] = row["y"] = row["z"] = ""

        if datos_validos:
            # Guardar fila válida
            empty_counter = 0
            with open(csv_filename, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerow(row)
            # Avanzar normalmente
            start_time = end_time
            end_time = start_time + escan

        else:
            empty_counter += 1
            if empty_counter > 10:
                print(f"⚡ Más de 10 vacíos encontrados. Buscando siguiente dato disponible...")
                next_entry = collection_esp32.find_one(
                    {"deviceName": device, "timestamp": {"$gt": end_time}},
                    sort=[("timestamp", 1)]
                )
                if next_entry:
                    start_time = next_entry["timestamp"]
                    end_time = start_time + escan
                    empty_counter = 0
                    print(f"➡️ Saltando a nuevo inicio en timestamp: {start_time}")
                else:
                    print("✅ No hay más datos disponibles. Finalizando...")
                    break
            else:
                # Si aún no pasamos de 10 vacíos, avanzar normalmente
                start_time = end_time
                end_time = start_time + escan

    print(f"✅ Proceso finalizado. Archivo '{csv_filename}' actualizado.")

if __name__ == "__main__":
    main()
