# Localización en interiores usando aprendizaje automatico y BLE 

Este Trabajo de Fin de Grado desarrolla un sistema de localización en interiores mediante señales Bluetooth Low Energy (BLE) captadas por nodos ESP32. Estas señales se procesan mediante técnicas de aprendizaje automático para estimar la posición de un dispositivo dentro de un entorno SmartHome. El sistema incluye visualización en tiempo real a través de una aplicación web.

---

## Tecnologías utilizadas

- ESP32 con BLE para escaneo de señal
- MQTT para transmisión de datos
- MongoDB como base de datos NoSQL
- Python para procesamiento y entrenamiento de modelos
- scikit-learn para machine learning
- Node.js para servidor backend y WebSocket
- Ionic + Angular como frontend web y móvil

---

## Estructura del proyecto

```
├── CreacionDataset.py               # Generación del dataset desde MongoDB
├── LectorTagRaspberry.py           # Lectura de posición UWB desde Raspberry
├── MQTTaMongoDB.py                 # Almacena datos MQTT en MongoDB
├── MensajeEscaneo.py               # Envía comandos de escaneo a ESP32
├── MachineLearningDefTFG.ipynb     # Entrenamiento de modelos de IA
├── Ionic/
│   ├── Back-End/                   # Backend Node.js: REST y WebSocket
│   └── local-map/                 # Aplicación Ionic: visualización y control
```

---

## Requisitos previos

- Python 3.9 o superior
- Node.js 16 o superior
- MongoDB local o en contenedor
- MQTT Broker (ej. Mosquitto)
- Dispositivos ESP32 con firmware cargado
- Docker (opcional para MongoDB y MQTT)

---

## Ejecución del backend

```
cd Ionic/Back-End
node server.js
```

---

## Ejecución del frontend (Ionic)

```
cd Ionic/local-map
ionic serve
```

---

## Entrenamiento del modelo

Ejecutar el notebook `MachineLearningDefTFG.ipynb` para entrenar el modelo MLP o Random Forest. Se guardará en formato `.pkl` para ser utilizado en la inferencia.

---

## Funcionamiento del sistema

1. Los ESP32 escanean señales BLE de un dispositivo objetivo.
2. Los datos se transmiten por MQTT al servidor.
3. Un proceso Python los almacena en MongoDB.
4. El modelo de IA estima la ubicación (x, y) cada 9 segundos.
5. Los resultados se envían al backend mediante POST.
6. La interfaz web visualiza la posición, zonas y mapa de calor.

---

## Modos de visualización en la web

- Ubicación precisa en plano
- Mapa de calor por franja horaria
- Vista por zonas
- Selección del dispositivo a monitorizar
- Actualización en tiempo real vía WebSocket

---

## Modelos evaluados

- Regresión Lineal
- Regresión Ridge
- MLPRegressor
- Random Forest Regressor (mejor rendimiento)
- kNN
- SVM
---

## Dataset

- Entradas: valores RSSI de ESP32
- Salidas: coordenadas reales obtenidas con UWB
- Dataset generado mediante sincronización de timestamps
- Preprocesamiento: normalización, limpieza, exclusión de valores extremos

---

## Autor

José Luis López García  
Director: Marcos Lupión Lorente  
Codirector: Vicente González Ruiz  
Universidad de Almería  
Grado en Ingeniería Informática  
Curso 2024/2025
