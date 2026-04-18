#include <Arduino.h>
#include <DallasTemperature.h>
#include <OneWire.h>
#include <PubSubClient.h>
#include <WiFi.h>

// Network / MQTT
const char *WIFI_SSID = "FASTWEB-D6DCCF";
const char *WIFI_PASS = "ET2E3T7AE3";
const char *MQTT_SERVER = "192.168.1.168";
const int MQTT_PORT = 1883;
const char *MQTT_TOPIC = "zeer/darlingtonia/status";
const char *MQTT_CLIENT_ID = "darlingtonia-zeer";

// ESP32-C3 SuperMini pins
const int PIN_DS18B20 = 4;   // Shared OneWire bus
const int PIN_PUMP = 3;      // MOSFET gate
const int PIN_FLOAT_SW = 5;  // HIGH = water OK (external 10k pull-up, open when float is up)
const int PIN_MOISTURE = 2;  // ADC from capacitive probe

// If you know the DS18B20 addresses, fill them in here.
// Leave all zeros to auto-assign on first successful boot.
const DeviceAddress ROOT_ADDR_MANUAL = {0, 0, 0, 0, 0, 0, 0, 0};
const DeviceAddress AMB_ADDR_MANUAL = {0, 0, 0, 0, 0, 0, 0, 0};

// Cooling strategy
const float TEMP_ON = 21.0f;
const float TEMP_OFF = 18.0f;
const float TEMP_HIGH = 25.0f;

const int PUMP_SECS_NORMAL = 20;
const int PUMP_SECS_HIGH = 40;
const int SLEEP_NORMAL_MIN = 5;
const int SLEEP_HOT_MIN = 2;

// Moisture probe is telemetry-only by default.
// Use a capacitive 3.3V analog probe, not a resistive fork sensor.
// Tune these two values after a dry and wet calibration readout.
const int MOISTURE_DRY_RAW = 3000;
const int MOISTURE_WET_RAW = 1500;

// Reporting cadence
const float REPORT_TEMP_DELTA = 1.0f;
const int REPORT_MOISTURE_DELTA = 5;
const int HEARTBEAT_BOOTS = 6;

OneWire oneWire(PIN_DS18B20);
DallasTemperature sensors(&oneWire);
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

RTC_DATA_ATTR int bootCount = 0;
RTC_DATA_ATTR int bootsSinceReport = 0;
RTC_DATA_ATTR bool wasPumping = false;
RTC_DATA_ATTR bool sensorsIdentified = false;
RTC_DATA_ATTR float lastReportedTemp = 0.0f;
RTC_DATA_ATTR int lastReportedMoisture = -1;
RTC_DATA_ATTR DeviceAddress addrRoot = {0};
RTC_DATA_ATTR DeviceAddress addrAmb = {0};

bool isZeroAddress(const DeviceAddress addr) {
  for (int i = 0; i < 8; ++i) {
    if (addr[i] != 0) {
      return false;
    }
  }
  return true;
}

void copyAddress(DeviceAddress dst, const DeviceAddress src) {
  memcpy(dst, src, 8);
}

bool validTemperature(float value) {
  return value != DEVICE_DISCONNECTED_C && value > -10.0f && value < 60.0f;
}

bool connectWiFi(int timeoutMs = 5000) {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  const unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if ((millis() - start) > (unsigned long)timeoutMs) {
      return false;
    }
    delay(100);
  }
  return true;
}

int moisturePercentFromRaw(int raw) {
  long pct = map(raw, MOISTURE_DRY_RAW, MOISTURE_WET_RAW, 0, 100);
  return constrain((int)pct, 0, 100);
}

int readMoistureRaw() {
  // Throw away the first sample after wake for a steadier reading.
  analogRead(PIN_MOISTURE);
  delay(10);
  return analogRead(PIN_MOISTURE);
}

bool assignManualSensorAddresses() {
  if (isZeroAddress(ROOT_ADDR_MANUAL) || isZeroAddress(AMB_ADDR_MANUAL)) {
    return false;
  }

  copyAddress(addrRoot, ROOT_ADDR_MANUAL);
  copyAddress(addrAmb, AMB_ADDR_MANUAL);
  sensorsIdentified = true;
  return true;
}

bool identifySensors() {
  if (assignManualSensorAddresses()) {
    return true;
  }

  if (sensors.getDeviceCount() < 2) {
    sensorsIdentified = false;
    return false;
  }

  DeviceAddress candidateA;
  DeviceAddress candidateB;
  if (!sensors.getAddress(candidateA, 0) || !sensors.getAddress(candidateB, 1)) {
    sensorsIdentified = false;
    return false;
  }

  sensors.requestTemperatures();
  const float tempA = sensors.getTempC(candidateA);
  const float tempB = sensors.getTempC(candidateB);
  if (!validTemperature(tempA) || !validTemperature(tempB)) {
    sensorsIdentified = false;
    return false;
  }

  // Fallback heuristic if manual addresses were not configured.
  if (tempA <= tempB) {
    copyAddress(addrRoot, candidateA);
    copyAddress(addrAmb, candidateB);
  } else {
    copyAddress(addrRoot, candidateB);
    copyAddress(addrAmb, candidateA);
  }

  sensorsIdentified = true;
  return true;
}

bool readTemperatures(float &rootTemp, float &ambTemp) {
  if (!sensorsIdentified && !identifySensors()) {
    return false;
  }

  sensors.requestTemperatures();
  rootTemp = sensors.getTempC(addrRoot);
  ambTemp = sensors.getTempC(addrAmb);

  if (validTemperature(rootTemp)) {
    if (!validTemperature(ambTemp)) {
      ambTemp = -99.0f;
    }
    return true;
  }

  if (!identifySensors()) {
    return false;
  }

  sensors.requestTemperatures();
  rootTemp = sensors.getTempC(addrRoot);
  ambTemp = sensors.getTempC(addrAmb);
  if (!validTemperature(rootTemp)) {
    return false;
  }
  if (!validTemperature(ambTemp)) {
    ambTemp = -99.0f;
  }
  return true;
}

void publishMQTT(float rootTemp, float ambTemp, bool pumpRan, bool waterOk,
                 int sleepMin, int moistureRaw, int moisturePct) {
  if (!connectWiFi()) {
    return;
  }

  mqtt.setServer(MQTT_SERVER, MQTT_PORT);
  if (mqtt.connect(MQTT_CLIENT_ID)) {
    char payload[320];
    const float delta = (ambTemp > -50.0f) ? (ambTemp - rootTemp) : -99.0f;

    snprintf(
        payload, sizeof(payload),
        "{\"root\":%.1f,\"ambient\":%.1f,\"delta\":%.1f,"
        "\"pump\":%s,\"water\":%s,\"moist_raw\":%d,\"moist_pct\":%d,"
        "\"sleep_min\":%d,\"boot\":%d}",
        rootTemp, ambTemp, delta, pumpRan ? "true" : "false",
        waterOk ? "true" : "false", moistureRaw, moisturePct, sleepMin,
        bootCount);

    mqtt.publish(MQTT_TOPIC, payload);
    mqtt.disconnect();
  }

  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
}

void goToSleep(int minutes) {
  esp_sleep_enable_timer_wakeup((uint64_t)minutes * 60ULL * 1000000ULL);
  esp_deep_sleep_start();
}

void setup() {
  bootCount++;

  pinMode(PIN_PUMP, OUTPUT);
  digitalWrite(PIN_PUMP, LOW);
  pinMode(PIN_FLOAT_SW, INPUT);
  pinMode(PIN_MOISTURE, INPUT);

  analogReadResolution(12);
  sensors.begin();

  float rootTemp = -99.0f;
  float ambTemp = -99.0f;
  if (!readTemperatures(rootTemp, ambTemp)) {
    publishMQTT(-99.0f, -99.0f, false, true, SLEEP_NORMAL_MIN, -1, -1);
    goToSleep(SLEEP_NORMAL_MIN);
    return;
  }

  const int moistureRaw = readMoistureRaw();
  const int moisturePct = moisturePercentFromRaw(moistureRaw);
  const bool waterOk = (digitalRead(PIN_FLOAT_SW) == HIGH);

  const bool shouldPump =
      wasPumping ? (rootTemp > TEMP_OFF) : (rootTemp > TEMP_ON);

  bool pumpRan = false;
  if (shouldPump && waterOk) {
    const int pumpSeconds =
        (rootTemp > TEMP_HIGH) ? PUMP_SECS_HIGH : PUMP_SECS_NORMAL;
    digitalWrite(PIN_PUMP, HIGH);
    delay((unsigned long)pumpSeconds * 1000UL);
    digitalWrite(PIN_PUMP, LOW);
    pumpRan = true;
    wasPumping = true;
  } else {
    wasPumping = false;
  }

  const int sleepMin = (rootTemp > TEMP_ON) ? SLEEP_HOT_MIN : SLEEP_NORMAL_MIN;

  bootsSinceReport++;
  const float tempDelta = fabsf(rootTemp - lastReportedTemp);
  const int moistureDelta =
      (lastReportedMoisture >= 0) ? abs(moisturePct - lastReportedMoisture)
                                  : REPORT_MOISTURE_DELTA;

  const bool shouldReport =
      pumpRan || !waterOk || (tempDelta >= REPORT_TEMP_DELTA) ||
      (moistureDelta >= REPORT_MOISTURE_DELTA) ||
      (bootsSinceReport >= HEARTBEAT_BOOTS);

  if (shouldReport) {
    publishMQTT(rootTemp, ambTemp, pumpRan, waterOk, sleepMin, moistureRaw,
                moisturePct);
    lastReportedTemp = rootTemp;
    lastReportedMoisture = moisturePct;
    bootsSinceReport = 0;
  }

  goToSleep(sleepMin);
}

void loop() {}
