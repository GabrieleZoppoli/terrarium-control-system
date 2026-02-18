// Terrarium Controller — Custom Serial Protocol
// Replaces Firmata for robust, debuggable Arduino <-> Pi communication
//
// Protocol (115200 baud, newline-terminated text):
//   Pi → Arduino:
//     P<pin>,<value>   Set PWM (pins 8,12,44,45,46 only, value 0-255)
//     Q                Query all pin states
//   Arduino → Pi:
//     READY            Boot complete
//     H,<value>        Heartbeat with A0 reading (every 2s)
//     D22,<0|1>        Left door state change (+ periodic every 10s)
//     D24,<0|1>        Right door state change (+ periodic every 10s)
//     OK,P<pin>,<value>  PWM command acknowledged
//     S,P8=<v>,P12=<v>,P44=<v>,P45=<v>,P46=<v>  Full status (response to Q)
//
// PWM frequencies:
//   Pin 8 (Timer 4): default ~490 Hz (fine for LED dimmer)
//   Pin 12 (Timer 1): 25 kHz (internal circulation fans, Noctua 4-pin PWM)
//   Pins 44,45,46 (Timer 5): 25 kHz (freezer/outlet/impeller fans)

// --- Pin definitions ---
const uint8_t PIN_DIMMER      = 8;
const uint8_t PIN_CIRCULATION = 12;  // Internal circulation fans (Timer 1B, OC1B)
const uint8_t PIN_FREEZER     = 44;
const uint8_t PIN_OUTLET      = 45;
const uint8_t PIN_IMPELLER    = 46;
const uint8_t PIN_HEARTBEAT   = A0;
const uint8_t PIN_DOOR_LEFT   = 22;
const uint8_t PIN_DOOR_RIGHT  = 24;

// --- Timer config for 25 kHz ---
// Phase-correct PWM, ICRn as TOP
// f = 16MHz / (2 * prescaler * TOP) = 16000000 / (2 * 1 * 320) = 25000 Hz
const uint16_t TIMER_TOP_25K = 320;

// --- PWM state tracking (0-255 input range, mapped internally for timer pins) ---
uint8_t pwmValues[5] = {0, 0, 0, 0, 0};  // pins 8, 12, 44, 45, 46
const uint8_t pwmPins[5] = {PIN_DIMMER, PIN_CIRCULATION, PIN_FREEZER, PIN_OUTLET, PIN_IMPELLER};

// --- Door state tracking ---
uint8_t lastDoorLeft  = HIGH;  // pullup: HIGH = closed
uint8_t lastDoorRight = HIGH;

// --- Timing ---
unsigned long lastHeartbeat = 0;
unsigned long lastDoorPoll  = 0;
unsigned long lastDoorReport = 0;
const unsigned long HEARTBEAT_INTERVAL = 2000;   // 2s
const unsigned long DOOR_POLL_INTERVAL = 100;     // 100ms debounce
const unsigned long DOOR_REPORT_INTERVAL = 10000; // 10s periodic

// --- Serial buffer ---
char cmdBuf[32];
uint8_t cmdLen = 0;

// Map pin number to pwmValues index, returns 255 if invalid
uint8_t pinToIndex(uint8_t pin) {
  for (uint8_t i = 0; i < 5; i++) {
    if (pwmPins[i] == pin) return i;
  }
  return 255;
}

// Set PWM for Timer 1 pin 12 (OC1B) using direct register access
// Maps 0-255 input to 0-TIMER_TOP_25K range
void setTimer1PWM(uint8_t value) {
  OCR1B = ((uint16_t)value * TIMER_TOP_25K) / 255;
}

// Set PWM for Timer 5 pins (44, 45, 46) using direct register access
// Maps 0-255 input to 0-TIMER_TOP_25K range
void setTimer5PWM(uint8_t pin, uint8_t value) {
  uint16_t mapped = ((uint16_t)value * TIMER_TOP_25K) / 255;
  switch (pin) {
    case 44: OCR5C = mapped; break;  // Pin 44 = OC5C
    case 45: OCR5B = mapped; break;  // Pin 45 = OC5B
    case 46: OCR5A = mapped; break;  // Pin 46 = OC5A
  }
}

void setupTimer1() {
  // Configure Timer 1 for 25 kHz phase-correct PWM on pin 12 (OC1B)
  // Mode 10: Phase Correct PWM with ICR1 as TOP
  // WGM1[3:0] = 1010 → WGM13=1, WGM12=0, WGM11=1, WGM10=0
  // Prescaler = 1: CS12=0, CS11=0, CS10=1

  pinMode(12, OUTPUT);

  cli();

  TCCR1A = 0;
  TCCR1B = 0;

  // WGM bits for Mode 10
  TCCR1A |= (1 << WGM11);
  TCCR1B |= (1 << WGM13);

  // Prescaler = 1
  TCCR1B |= (1 << CS10);

  // TOP value for 25 kHz
  ICR1 = TIMER_TOP_25K;

  // Enable only channel B (pin 12), non-inverting
  TCCR1A |= (1 << COM1B1);

  // Initialize to 0
  OCR1B = 0;

  sei();
}

void setupTimer5() {
  // Configure Timer 5 for 25 kHz phase-correct PWM
  // Mode 10: Phase Correct PWM with ICR5 as TOP

  pinMode(44, OUTPUT);
  pinMode(45, OUTPUT);
  pinMode(46, OUTPUT);

  cli();

  TCCR5A = 0;
  TCCR5B = 0;

  // WGM bits for Mode 10
  TCCR5A |= (1 << WGM51);
  TCCR5B |= (1 << WGM53);

  // Prescaler = 1
  TCCR5B |= (1 << CS50);

  // TOP value for 25 kHz
  ICR5 = TIMER_TOP_25K;

  // Enable outputs: non-inverting mode for channels A, B, C
  TCCR5A |= (1 << COM5A1);  // Pin 46 (OC5A)
  TCCR5A |= (1 << COM5B1);  // Pin 45 (OC5B)
  TCCR5A |= (1 << COM5C1);  // Pin 44 (OC5C)

  // Initialize all channels to 0
  OCR5A = 0;
  OCR5B = 0;
  OCR5C = 0;

  sei();
}

void setup() {
  Serial.begin(115200);

  // LED dimmer — standard analogWrite (~490 Hz, fine for LED driver)
  pinMode(PIN_DIMMER, OUTPUT);
  analogWrite(PIN_DIMMER, 0);
  pwmValues[0] = 0;

  // Circulation fans — 25 kHz via Timer 1
  setupTimer1();
  pwmValues[1] = 0;

  // Freezer/outlet/impeller fans — 25 kHz via Timer 5
  setupTimer5();
  pwmValues[2] = 0;  // freezer
  pwmValues[3] = 0;  // outlet
  pwmValues[4] = 0;  // impeller

  // Door inputs with pullup
  pinMode(PIN_DOOR_LEFT, INPUT_PULLUP);
  pinMode(PIN_DOOR_RIGHT, INPUT_PULLUP);

  // Read initial door states
  lastDoorLeft  = digitalRead(PIN_DOOR_LEFT);
  lastDoorRight = digitalRead(PIN_DOOR_RIGHT);

  // Wait for serial port to settle after DTR reset, then signal ready
  delay(1000);
  Serial.println("READY");

  // Send initial door states
  Serial.print("D22,");
  Serial.println(lastDoorLeft);
  Serial.print("D24,");
  Serial.println(lastDoorRight);
}

void processCommand() {
  if (cmdLen == 0) return;
  cmdBuf[cmdLen] = '\0';

  if (cmdBuf[0] == 'Q') {
    // Query all states
    Serial.print("S,P8=");
    Serial.print(pwmValues[0]);
    Serial.print(",P12=");
    Serial.print(pwmValues[1]);
    Serial.print(",P44=");
    Serial.print(pwmValues[2]);
    Serial.print(",P45=");
    Serial.print(pwmValues[3]);
    Serial.print(",P46=");
    Serial.println(pwmValues[4]);
  }
  else if (cmdBuf[0] == 'P') {
    // Parse P<pin>,<value>
    char *comma = strchr(cmdBuf + 1, ',');
    if (comma == NULL) {
      Serial.println("ERR,NOCOMMA");
      return;
    }
    *comma = '\0';
    int pin = atoi(cmdBuf + 1);
    int value = atoi(comma + 1);

    // Validate pin
    uint8_t idx = pinToIndex((uint8_t)pin);
    if (idx == 255) {
      Serial.print("ERR,BADPIN,");
      Serial.println(pin);
      return;
    }

    // Clamp value
    if (value < 0) value = 0;
    if (value > 255) value = 255;

    // Apply PWM — route to correct timer
    if (pin == PIN_DIMMER) {
      analogWrite(pin, value);
    } else if (pin == PIN_CIRCULATION) {
      setTimer1PWM(value);
    } else {
      setTimer5PWM(pin, value);
    }
    pwmValues[idx] = (uint8_t)value;

    // Acknowledge
    Serial.print("OK,P");
    Serial.print(pin);
    Serial.print(",");
    Serial.println(value);
  }
  else {
    Serial.print("ERR,UNKNOWN,");
    Serial.println(cmdBuf);
  }
}

void readSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (cmdLen > 0) {
        processCommand();
        cmdLen = 0;
      }
    } else {
      if (cmdLen < sizeof(cmdBuf) - 1) {
        cmdBuf[cmdLen++] = c;
      } else {
        // Buffer overflow — discard
        cmdLen = 0;
        Serial.println("ERR,OVERFLOW");
      }
    }
  }
}

void sendHeartbeat() {
  unsigned long now = millis();
  if (now - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    lastHeartbeat = now;
    int a0 = analogRead(PIN_HEARTBEAT);
    Serial.print("H,");
    Serial.println(a0);
  }
}

void checkDoors() {
  unsigned long now = millis();

  if (now - lastDoorPoll >= DOOR_POLL_INTERVAL) {
    lastDoorPoll = now;

    uint8_t left  = digitalRead(PIN_DOOR_LEFT);
    uint8_t right = digitalRead(PIN_DOOR_RIGHT);

    bool changed = false;

    if (left != lastDoorLeft) {
      lastDoorLeft = left;
      Serial.print("D22,");
      Serial.println(left);
      changed = true;
    }

    if (right != lastDoorRight) {
      lastDoorRight = right;
      Serial.print("D24,");
      Serial.println(right);
      changed = true;
    }

    if (now - lastDoorReport >= DOOR_REPORT_INTERVAL) {
      lastDoorReport = now;
      if (!changed) {
        Serial.print("D22,");
        Serial.println(lastDoorLeft);
        Serial.print("D24,");
        Serial.println(lastDoorRight);
      }
    }
  }
}

void loop() {
  readSerial();
  sendHeartbeat();
  checkDoors();
}
