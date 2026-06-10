// Terrarium Controller — Custom Serial Protocol
// Replaces Firmata for robust, debuggable Arduino <-> Pi communication
//
// Protocol (115200 baud, newline-terminated text):
//   Pi → Arduino:
//     P<pin>,<value>*HH        Required. NMEA-style framing + CRC-8 checksum.
//                              HH = 2-hex-char CRC-8 (poly 0x07, init 0x00, no reflect, no xorout)
//                              over all preceding bytes. Mismatched checksum is rejected with
//                              ERR,CHKSUM,got,want and the previous PWM is preserved.
//                              Bare commands without *HH are rejected with ERR,NOSUM
//                              (backwards-compat removed 2026-05-18 PM after observing
//                              slip-throughs where corruption stripped the suffix and the
//                              bare-format fallback executed a wrong PWM value).
//     Q                        Query all pin states (checksum optional, same rules)
//   Arduino → Pi:
//     READY            Boot complete
//     H,<value>        Heartbeat with A0 reading (every 2s)
//     D22,<0|1>        Left door state change (+ periodic every 10s)
//     D24,<0|1>        Right door state change (+ periodic every 10s)
//     OK,P<pin>,<value>  PWM command acknowledged
//     S,P8=<v>,P12=<v>,P44=<v>,P45=<v>,P46=<v>,R=<c>/<f>/<o>/<i>  Full status (response to Q)
//     R,<circ>,<freeze>,<outlet>,<impeller>  Fan RPM (every 2s)
//     ERR,CHKSUM,<got>,<want>  Checksum verification failed for last command
//
// PWM frequencies:
//   Pin 8 (Timer 4): default ~490 Hz (fine for LED dimmer)
//   Pin 12 (Timer 1): 25 kHz (internal circulation fans, Noctua 4-pin PWM)
//   Pins 44,45,46 (Timer 5): 25 kHz (freezer/outlet/impeller fans)
//
// Tachometer inputs (external 4.7kΩ pull-ups to 5V required):
//   Pin 2 (INT4): circulation fan tach
//   Pin 3 (INT5): freezer fan tach
//   Pin 18 (INT3): outlet fan tach
//   Pin 19 (INT2): impeller fan tach
//   All fans: 2 pulses/rev, FALLING edge interrupts

// --- Pin definitions ---
const uint8_t PIN_DIMMER      = 8;
const uint8_t PIN_CIRCULATION = 12;  // Internal circulation fans (Timer 1B, OC1B)
const uint8_t PIN_FREEZER     = 44;
const uint8_t PIN_OUTLET      = 45;
const uint8_t PIN_IMPELLER    = 46;
const uint8_t PIN_HEARTBEAT   = A0;
const uint8_t PIN_DOOR_LEFT   = 22;
const uint8_t PIN_DOOR_RIGHT  = 24;

// Tachometer pins (hardware interrupt capable)
const uint8_t PIN_TACH_CIRC     = 2;   // INT4
const uint8_t PIN_TACH_FREEZER  = 3;   // INT5
const uint8_t PIN_TACH_OUTLET   = 18;  // INT3
const uint8_t PIN_TACH_IMPELLER = 19;  // INT2

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

// --- Tachometer ---
// ISR pulse counters (volatile, accessed from interrupts)
volatile uint16_t tachCount[4] = {0, 0, 0, 0};  // circ, freezer, outlet, impeller

// Computed RPM values (updated every 1s from tachCount)
uint16_t rpm[4] = {0, 0, 0, 0};

// ISRs — minimal: just increment counter
void isrTachCirc()     { tachCount[0]++; }
void isrTachFreezer()  { tachCount[1]++; }
void isrTachOutlet()   { tachCount[2]++; }
void isrTachImpeller() { tachCount[3]++; }

// --- Timing ---
unsigned long lastHeartbeat = 0;
unsigned long lastDoorPoll  = 0;
unsigned long lastDoorReport = 0;
unsigned long lastRpmCalc   = 0;
unsigned long lastRpmReport = 0;
const unsigned long HEARTBEAT_INTERVAL = 2000;   // 2s
const unsigned long DOOR_POLL_INTERVAL = 100;     // 100ms debounce
const unsigned long DOOR_REPORT_INTERVAL = 10000; // 10s periodic
const unsigned long RPM_CALC_INTERVAL  = 1000;    // 1s — count pulses over 1s window
const unsigned long RPM_REPORT_INTERVAL = 2000;   // 2s — send R, line

// --- Serial buffer ---
char cmdBuf[32];
uint8_t cmdLen = 0;

// --- TX buffer guard ---
// Minimum free bytes in TX buffer before we'll attempt a print.
// Prevents loop() from blocking when 16U2 USB bridge stalls.
const uint8_t TX_MIN_FREE = 16;

// Returns true if TX buffer has enough room for a short message
bool txReady() {
  return Serial.availableForWrite() >= TX_MIN_FREE;
}

// Map pin number to pwmValues index, returns 255 if invalid
uint8_t pinToIndex(uint8_t pin) {
  for (uint8_t i = 0; i < 5; i++) {
    if (pwmPins[i] == pin) return i;
  }
  return 255;
}

// --- Checksum helpers (CRC-8, poly 0x07) ----------------------------------
// Returns 0-15 for '0'-'9' and 'A'-'F'/'a'-'f', or 255 if not a hex digit.
uint8_t hexDigit(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'A' && c <= 'F') return 10 + (c - 'A');
  if (c >= 'a' && c <= 'f') return 10 + (c - 'a');
  return 255;
}

// CRC-8 with polynomial 0x07, init 0x00, no reflection, no xorout
// (the "CRC-8/SMBUS" style — same as ITU-T I.432.1 generic CRC-8).
// Bit-by-bit; ~16 cycles/byte on AVR. Cheap for ≤32-byte commands.
uint8_t crc8(const uint8_t *data, size_t len) {
  uint8_t crc = 0;
  for (size_t i = 0; i < len; i++) {
    crc ^= data[i];
    for (uint8_t j = 0; j < 8; j++) {
      crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0x07) : (uint8_t)(crc << 1);
    }
  }
  return crc;
}

// Strip and verify a trailing "*HH" checksum from cmdBuf (NUL-terminated).
// Returns:
//    0  -> no checksum present (legacy command); buf is unchanged.
//    1  -> checksum present and matches; '*' has been overwritten with '\0'
//          so the command portion behaves as before for the rest of parsing.
//   -1  -> checksum present but invalid; outGot/outWant filled.
// Bug 7 fix (2026-05-18): require '*' to be at exactly strlen-3, not just
// "some '*' anywhere via strrchr". A stray '*' mid-string used to be matched
// (followed by length check failure → ERR,CHKSUM,0,0) when ERR,UNKNOWN would
// be more honest.
int8_t verifyChecksum(char *buf, uint8_t *outGot, uint8_t *outWant) {
  size_t n = strlen(buf);
  if (n < 3 || buf[n-3] != '*') return 0;  // no suffix at the canonical position
  char *star = &buf[n-3];
  uint8_t hi = hexDigit(star[1]);
  uint8_t lo = hexDigit(star[2]);
  if (hi == 255 || lo == 255) return -1;
  uint8_t want = (hi << 4) | lo;
  uint8_t got = crc8((const uint8_t *)buf, (size_t)(star - buf));
  if (outGot)  *outGot  = got;
  if (outWant) *outWant = want;
  if (got != want) return -1;
  *star = '\0';   // strip suffix so existing parsing keeps working
  return 1;
}

// Set PWM for Timer 1 pin 12 (OC1B) using direct register access
// Maps 0-255 input to 0-TIMER_TOP_25K range
// When value=0: disconnect output compare and force pin LOW to avoid
// narrow pulse at BOTTOM of phase-correct PWM keeping MOSFET gate charged
void setTimer1PWM(uint8_t value) {
  if (value == 0) {
    TCCR1A &= ~(1 << COM1B1);  // Disconnect OC1B
    digitalWrite(12, LOW);       // Force pin LOW
    OCR1B = 0;
  } else {
    TCCR1A |= (1 << COM1B1);   // Reconnect OC1B
    OCR1B = ((uint32_t)value * TIMER_TOP_25K) / 255;
  }
}

// Set PWM for Timer 5 pins (44, 45, 46) using direct register access
// Maps 0-255 input to 0-TIMER_TOP_25K range
// When value=0: disconnect output compare and force pin LOW to avoid
// narrow pulse at BOTTOM of phase-correct PWM keeping MOSFET gate charged
void setTimer5PWM(uint8_t pin, uint8_t value) {
  if (value == 0) {
    switch (pin) {
      case 44: TCCR5A &= ~(1 << COM5C1); break;  // Disconnect OC5C
      case 45: TCCR5A &= ~(1 << COM5B1); break;  // Disconnect OC5B
      case 46: TCCR5A &= ~(1 << COM5A1); break;  // Disconnect OC5A
    }
    digitalWrite(pin, LOW);  // Force pin LOW
    switch (pin) {
      case 44: OCR5C = 0; break;
      case 45: OCR5B = 0; break;
      case 46: OCR5A = 0; break;
    }
  } else {
    switch (pin) {
      case 44: TCCR5A |= (1 << COM5C1); break;  // Reconnect OC5C
      case 45: TCCR5A |= (1 << COM5B1); break;  // Reconnect OC5B
      case 46: TCCR5A |= (1 << COM5A1); break;  // Reconnect OC5A
    }
    uint16_t mapped = ((uint32_t)value * TIMER_TOP_25K) / 255;
    switch (pin) {
      case 44: OCR5C = mapped; break;
      case 45: OCR5B = mapped; break;
      case 46: OCR5A = mapped; break;
    }
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

  // Bug 5 fix (2026-05-18): leave COM1B1 DISCONNECTED at setup time and pin LOW.
  // The previous order (enable COM1B1 → then OCR1B = 0) produced exactly the
  // BOTTOM-pulse MOSFET-gate glitch that setTimer1PWM(0) was built to avoid,
  // for the ~1s window between timer start and the first NR PWM command.
  TCCR1A &= ~(1 << COM1B1);   // start DISCONNECTED
  digitalWrite(12, LOW);       // force pin LOW
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

  // Bug 5 fix (2026-05-18): leave COM5x1 DISCONNECTED at setup time and pins LOW
  // for the same reason as Timer 1 above — engaging the channel before writing
  // OCR = 0 emits glitch pulses at BOTTOM for the boot window. setTimer5PWM(v)
  // will engage COM5x1 when v != 0.
  TCCR5A &= ~(1 << COM5A1);
  TCCR5A &= ~(1 << COM5B1);
  TCCR5A &= ~(1 << COM5C1);
  digitalWrite(44, LOW);
  digitalWrite(45, LOW);
  digitalWrite(46, LOW);
  OCR5A = 0;
  OCR5B = 0;
  OCR5C = 0;

  sei();
}

void setup() {
  Serial.begin(115200);

  // LED dimmer — standard analogWrite (~490 Hz, fine for LED driver)
  // Bug 3 fix (2026-05-18): pin 8 uses inverted PWM (255 = LED OFF, 0 = LED FULL).
  // Initialising to 0 made the LEDs go to FULL brightness for the entire boot
  // window (1 s setup delay + first NR command latency). Initialise to 255 so
  // the safe state is OFF; NR's first PWM command will set the actual value.
  pinMode(PIN_DIMMER, OUTPUT);
  analogWrite(PIN_DIMMER, 255);
  pwmValues[0] = 255;

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

  // Tachometer inputs — using internal pull-ups (~20-50kΩ)
  // Upgrade to external 4.7kΩ pull-ups if readings are noisy
  pinMode(PIN_TACH_CIRC, INPUT_PULLUP);
  pinMode(PIN_TACH_FREEZER, INPUT_PULLUP);
  pinMode(PIN_TACH_OUTLET, INPUT_PULLUP);
  pinMode(PIN_TACH_IMPELLER, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_TACH_CIRC),     isrTachCirc,     FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_TACH_FREEZER),  isrTachFreezer,  FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_TACH_OUTLET),   isrTachOutlet,   FALLING);
  attachInterrupt(digitalPinToInterrupt(PIN_TACH_IMPELLER), isrTachImpeller, FALLING);

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

  // Required trailing "*HH" CRC-8 suffix. Bare commands (no *) are rejected
  // with ERR,NOSUM; suffix present but mismatched -> ERR,CHKSUM,got,want.
  // The previously-set PWM is preserved on any rejection. Backwards-compat
  // for bare commands removed 2026-05-18 PM (was the most common slip-through
  // path: corruption stripping the suffix made the bare-format fallback
  // execute a corrupted value).
  uint8_t got = 0, want = 0;
  int8_t cs = verifyChecksum(cmdBuf, &got, &want);
  if (cs == 0) {
    if (txReady()) Serial.println("ERR,NOSUM");
    return;
  }
  if (cs < 0) {
    if (txReady()) {
      Serial.print("ERR,CHKSUM,");
      Serial.print(got);
      Serial.print(",");
      Serial.println(want);
    }
    return;
  }

  // Bug 1 fix (2026-05-18): every reply path now guarded by txReady(). Previously
  // only ERR,CHKSUM/ERR,OVERFLOW were guarded; the ~70-byte Q reply and ACKs
  // could block the main loop on a stalled USB bridge, starving tach ISRs,
  // door polling, and heartbeats. PWM mutation still happens — only the ACK
  // is dropped when TX is back-pressured (the Pi can retry Q if it cares).
  if (cmdBuf[0] == 'Q') {
    if (!txReady()) return;
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
    Serial.print(pwmValues[4]);
    Serial.print(",R=");
    Serial.print(rpm[0]);
    Serial.print("/");
    Serial.print(rpm[1]);
    Serial.print("/");
    Serial.print(rpm[2]);
    Serial.print("/");
    Serial.println(rpm[3]);
  }
  else if (cmdBuf[0] == 'P') {
    // Parse P<pin>,<value>
    char *comma = strchr(cmdBuf + 1, ',');
    if (comma == NULL) {
      if (txReady()) Serial.println("ERR,NOCOMMA");
      return;
    }
    *comma = '\0';
    int pin = atoi(cmdBuf + 1);
    int value = atoi(comma + 1);

    // Validate pin
    uint8_t idx = pinToIndex((uint8_t)pin);
    if (idx == 255) {
      if (txReady()) {
        Serial.print("ERR,BADPIN,");
        Serial.println(pin);
      }
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

    // Acknowledge — ACK dropped if TX back-pressured (PWM was applied already)
    if (txReady()) {
      Serial.print("OK,P");
      Serial.print(pin);
      Serial.print(",");
      Serial.println(value);
    }
  }
  else {
    if (txReady()) {
      Serial.print("ERR,UNKNOWN,");
      Serial.println(cmdBuf);
    }
  }
}

void readSerial() {
  // Bug 8 fix (2026-05-18): on overflow, discard everything until next newline.
  // Without this, the first 32 bytes of any post-overflow re-sync command were
  // silently consumed before the newline. discardUntilNewline survives across
  // readSerial() calls because it's static.
  static bool discardUntilNewline = false;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (!discardUntilNewline && cmdLen > 0) {
        processCommand();
      }
      cmdLen = 0;
      discardUntilNewline = false;
    } else if (discardUntilNewline) {
      // drop bytes until we see a newline
    } else if (cmdLen < sizeof(cmdBuf) - 1) {
      cmdBuf[cmdLen++] = c;
    } else {
      // Buffer overflow — enter discard mode until newline arrives
      discardUntilNewline = true;
      cmdLen = 0;
      if (txReady()) Serial.println("ERR,OVERFLOW");
    }
  }
}

void sendHeartbeat() {
  unsigned long now = millis();
  if (now - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    if (!txReady()) return;  // Skip this cycle, retry next loop iteration
    lastHeartbeat = now;
    int a0 = analogRead(PIN_HEARTBEAT);
    Serial.print("H,");
    Serial.println(a0);
  }
}

void calcRpm() {
  unsigned long now = millis();
  if (now - lastRpmCalc >= RPM_CALC_INTERVAL) {
    lastRpmCalc = now;
    // Atomic read and reset of each counter
    for (uint8_t i = 0; i < 4; i++) {
      cli();
      uint16_t count = tachCount[i];
      tachCount[i] = 0;
      sei();
      // 2 pulses/rev, counted over 1s → RPM = count * 30
      rpm[i] = (uint16_t)(count * 30);
    }
  }
}

void reportRpm() {
  unsigned long now = millis();
  if (now - lastRpmReport >= RPM_REPORT_INTERVAL) {
    if (!txReady()) return;
    lastRpmReport = now;
    Serial.print("R,");
    Serial.print(rpm[0]);
    Serial.print(",");
    Serial.print(rpm[1]);
    Serial.print(",");
    Serial.print(rpm[2]);
    Serial.print(",");
    Serial.println(rpm[3]);
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
      if (txReady()) {
        Serial.print("D22,");
        Serial.println(left);
      }
      changed = true;
    }

    if (right != lastDoorRight) {
      lastDoorRight = right;
      if (txReady()) {
        Serial.print("D24,");
        Serial.println(right);
      }
      changed = true;
    }

    // Bug 6 fix (2026-05-18): also reset lastDoorReport when we emitted a
    // change-driven message. Previously, after any door transition, the next
    // poll iteration would fire the "periodic" branch with `!changed` true
    // and re-emit both door states unnecessarily.
    if (changed) {
      lastDoorReport = now;
    } else if (now - lastDoorReport >= DOOR_REPORT_INTERVAL) {
      lastDoorReport = now;
      if (txReady()) {
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
  calcRpm();
  reportRpm();
}
