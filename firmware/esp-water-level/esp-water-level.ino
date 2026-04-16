/*
 * ESP8266 Water Level Monitor — HC-SR04P Ultrasonic Sensor
 *
 * Measures water level in mister tank and publishes percentage
 * to MQTT topic esp/mistertank/tank_percent every 10 seconds.
 *
 * Wiring (ESP-12F → HC-SR04P):
 *   VCC  → 3.3V
 *   GND  → GND
 *   TRIG → GPIO5  (D1)
 *   ECHO → GPIO4  (D2)
 *
 * HC-SR04P operates at 3.3V — no level shifter needed.
 */

#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// ── Configuration ───────────────────────────────────────────
const char* WIFI_SSID     = "FASTWEB-D6DCCF";
const char* WIFI_PASS     = "ET2E3T7AE3";

const char* MQTT_SERVER   = "192.168.1.168";
const int   MQTT_PORT     = 1883;
const char* MQTT_CLIENT   = "esp-mistertank";

const char* TOPIC_PERCENT = "esp/mistertank/tank_percent";
const char* TOPIC_DIST    = "esp/mistertank/distance_cm";
const char* TOPIC_STATUS  = "esp/mistertank/status";

// Sensor pins
const int PIN_TRIG = 5;   // GPIO5 = D1
const int PIN_ECHO = 4;   // GPIO4 = D2

// Tank geometry (cm)
// SENSOR_OFFSET: distance from sensor face to water surface when tank is 100% full
// TANK_HEIGHT:   distance from sensor face to bottom of empty tank
const float SENSOR_OFFSET = 3.0;  // sensor mounted ~3cm above max water line
const float TANK_HEIGHT   = 35.0; // total measurable range in cm

// Timing
const unsigned long PUBLISH_INTERVAL_MS = 10000;  // 10 seconds
const unsigned long WIFI_RETRY_MS       = 5000;
const unsigned long MQTT_RETRY_MS       = 5000;

// Median filter: take N readings, pick the middle value
const int NUM_SAMPLES = 5;
const int SAMPLE_DELAY_MS = 60;  // ms between pings

// ── Globals ─────────────────────────────────────────────────
WiFiClient espClient;
PubSubClient mqtt(espClient);

unsigned long lastPublish = 0;
unsigned long lastWifiAttempt = 0;
unsigned long lastMqttAttempt = 0;

// ── Ultrasonic measurement ──────────────────────────────────
float pingOnce() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  unsigned long duration = pulseIn(PIN_ECHO, HIGH, 30000);  // 30ms timeout (~5m max)
  if (duration == 0) return -1.0;  // no echo

  // Speed of sound ~343 m/s at 20°C → 0.0343 cm/µs → distance = duration * 0.01715
  return duration * 0.01715;
}

// Insertion sort for small array
void sortFloats(float* arr, int n) {
  for (int i = 1; i < n; i++) {
    float key = arr[i];
    int j = i - 1;
    while (j >= 0 && arr[j] > key) {
      arr[j + 1] = arr[j];
      j--;
    }
    arr[j + 1] = key;
  }
}

float measureDistanceCm() {
  float samples[NUM_SAMPLES];
  int valid = 0;

  for (int i = 0; i < NUM_SAMPLES; i++) {
    float d = pingOnce();
    if (d > 0 && d < 400) {  // HC-SR04P range: 2–400cm
      samples[valid++] = d;
    }
    delay(SAMPLE_DELAY_MS);
  }

  if (valid == 0) return -1.0;  // all readings failed

  sortFloats(samples, valid);
  return samples[valid / 2];  // median
}

// ── WiFi ────────────────────────────────────────────────────
void wifiConnect() {
  if (WiFi.status() == WL_CONNECTED) return;
  if (millis() - lastWifiAttempt < WIFI_RETRY_MS) return;
  lastWifiAttempt = millis();

  Serial.printf("WiFi: connecting to %s...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  // Wait up to 10s for connection
  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 20) {
    delay(500);
    Serial.print(".");
    tries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\nWiFi: connected, IP=%s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\nWiFi: failed, will retry");
  }
}

// ── MQTT ────────────────────────────────────────────────────
void mqttConnect() {
  if (mqtt.connected()) return;
  if (WiFi.status() != WL_CONNECTED) return;
  if (millis() - lastMqttAttempt < MQTT_RETRY_MS) return;
  lastMqttAttempt = millis();

  Serial.printf("MQTT: connecting to %s:%d...\n", MQTT_SERVER, MQTT_PORT);

  // LWT: publish "offline" on disconnect
  if (mqtt.connect(MQTT_CLIENT, NULL, NULL, TOPIC_STATUS, 1, true, "offline")) {
    Serial.println("MQTT: connected");
    mqtt.publish(TOPIC_STATUS, "online", true);
  } else {
    Serial.printf("MQTT: failed rc=%d, will retry\n", mqtt.state());
  }
}

// ── Setup & Loop ────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println("\n\n=== ESP Water Level Monitor ===");

  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  digitalWrite(PIN_TRIG, LOW);

  WiFi.persistent(false);
  mqtt.setServer(MQTT_SERVER, MQTT_PORT);

  wifiConnect();
}

void loop() {
  wifiConnect();
  mqttConnect();
  mqtt.loop();

  if (millis() - lastPublish >= PUBLISH_INTERVAL_MS) {
    lastPublish = millis();

    float distCm = measureDistanceCm();

    if (distCm < 0) {
      Serial.println("Sensor: no valid reading");
      return;
    }

    // Convert distance to water level percentage
    // distCm = distance from sensor to water surface
    // When full:  distCm ≈ SENSOR_OFFSET         → 100%
    // When empty: distCm ≈ SENSOR_OFFSET + TANK_HEIGHT → 0%
    float waterCm = (SENSOR_OFFSET + TANK_HEIGHT) - distCm;
    float percent = (waterCm / TANK_HEIGHT) * 100.0;

    // Clamp to 0–100
    if (percent > 100.0) percent = 100.0;
    if (percent < 0.0) percent = 0.0;

    // Round to 1 decimal
    percent = roundf(percent * 10.0) / 10.0;

    Serial.printf("Dist=%.1fcm  Water=%.1fcm  Level=%.1f%%\n", distCm, waterCm, percent);

    if (mqtt.connected()) {
      char buf[16];

      // Publish percentage (what Node-RED expects)
      dtostrf(percent, 1, 1, buf);
      mqtt.publish(TOPIC_PERCENT, buf, true);

      // Publish raw distance for debugging
      dtostrf(distCm, 1, 1, buf);
      mqtt.publish(TOPIC_DIST, buf, true);
    }
  }
}
