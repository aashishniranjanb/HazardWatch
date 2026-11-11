#pragma once

#include <Arduino.h>
#include "pin_config.h"

class RelayManager {
private:
    bool commanded = false;

public:
    void begin() {
        pinMode(PIN_RELAY, OUTPUT);
        // Active-LOW relay: HIGH is OFF
        digitalWrite(PIN_RELAY, HIGH);
        commanded = false;
    }

    void setSafeOff() {
        commanded = false;
        digitalWrite(PIN_RELAY, HIGH);
    }

    void setManualOverride(bool active) {
        commanded = active;
        // Only explicit manual commands may alter GPIO
        digitalWrite(PIN_RELAY, active ? LOW : HIGH);
    }

    bool isCommanded() const { return commanded; }
    const char* getFeedback() const { return "UNAVAILABLE"; }
};
