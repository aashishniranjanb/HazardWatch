#pragma once

#include <Arduino.h>
#include "pin_config.h"

class RelayManager {
private:
    bool commandedState = false;

public:
    void begin() {
        pinMode(PIN_RELAY_IN, OUTPUT);
        // Default safe OFF (Active LOW relay module)
        digitalWrite(PIN_RELAY_IN, HIGH);
        commandedState = false;
    }

    void setCommand(bool active) {
        commandedState = active;
        // Active LOW: LOW = Relay ON, HIGH = Relay OFF
        digitalWrite(PIN_RELAY_IN, active ? LOW : HIGH);
    }

    bool isCommandedActive() const { return commandedState; }

    const char* getFeedbackStatus() const {
        // Physical ESP32 has open-loop relay unless auxiliary contact pin wired
        return "UNAVAILABLE";
    }
};
