#include <WiFi.h>
#include <PubSubClient.h>
#include <NimBLEDevice.h>

// Configuración WiFi
const char* ssid = "SmartHomeLocalPC";
const char* password = "12345678";

// Configuración MQTT
const char* mqtt_server = "192.168.137.100";
const int mqtt_port = 1883;
const char* mqtt_topic_pub = "ble/salons";
const char* mqtt_topic_sub = "ble/scanS";

WiFiClient espClient;
PubSubClient client(espClient);

// BLE
NimBLEScan* pBLEScan;
int scanTime = 8;
const String esp32Name = "ESP32Salon";

// Control
bool shouldScan = false;
String targetDeviceName = "";
unsigned long externalTimestamp = 0;

String getValue(String data, char separator, int index) {
  int found = 0;
  int start = 0;
  int end = -1;
  for (int i = 0; i <= data.length(); i++) {
    if (data.charAt(i) == separator || i == data.length()) {
      found++;
      if (found == index + 1) {
        return data.substring(start, i);
      }
      start = i + 1;
    }
  }
  return "";
}

void callback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (unsigned int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }

  String cmd = getValue(msg, '|', 0);
  String tsStr = getValue(msg, '|', 1);
  String devStr = getValue(msg, '|', 2);

  if (cmd == "start" && tsStr != "" && devStr != "") {
    targetDeviceName = devStr;
    externalTimestamp = tsStr.toInt();
    shouldScan = true;
    Serial.print(" Dispositivo objetivo: "); Serial.println(targetDeviceName);
    Serial.print(" Timestamp: "); Serial.println(externalTimestamp);
  } else {
    Serial.println(" Mensaje MQTT mal formado");
  }
}

void setupWiFi() {
  Serial.print(" Conectando a WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n WiFi conectado");
  Serial.println(WiFi.localIP());
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print(" Conectando a MQTT...");
    if (client.connect(esp32Name.c_str())) {
      Serial.println(" Conectado.");
      client.subscribe(mqtt_topic_sub);
    } else {
      Serial.print(" Estado: ");
      Serial.println(client.state());
      delay(3000);
    }
  }
}

void onResult(NimBLEAdvertisedDevice* advertisedDevice) {
  String devName = advertisedDevice->getName().c_str();
  int rssi = advertisedDevice->getRSSI();
  Serial.println(devName);
  if (devName == targetDeviceName) {
    Serial.print(" Dispositivo detectado: ");
    Serial.print(devName);
    Serial.print(" | RSSI: ");
    Serial.println(rssi);

    String json = "{";
    json += "\"esp32Name\":\"" + esp32Name + "\",";
    json += "\"deviceName\":\"" + devName + "\",";
    json += "\"rssi\":" + String(rssi) + ",";
    json += "\"timestamp\":" + String(externalTimestamp);
    json += "}";

    Serial.println(json.c_str());
    client.publish(mqtt_topic_pub, json.c_str());

    shouldScan = false;
    NimBLEDevice::getScan()->stop();
  }
}

class MyScanCallbacks : public NimBLEScanCallbacks {
  void onResult(const NimBLEAdvertisedDevice* advertisedDevice) override {
    ::onResult(const_cast<NimBLEAdvertisedDevice*>(advertisedDevice));  // si tu función espera no-const
  }
};


void setup() {
  Serial.begin(115200);
  setupWiFi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  NimBLEDevice::init("");
  pBLEScan = NimBLEDevice::getScan();
  pBLEScan->setActiveScan(true);
  pBLEScan->setScanCallbacks(new MyScanCallbacks());
}

void loop() {
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();

  if (shouldScan) {
    Serial.println(" Iniciando escaneo BLE...");
    pBLEScan->start(scanTime, false);
    pBLEScan->clearResults();
    Serial.println("---------------------------------------------------------");
  }

  delay(100);
}
