#pragma once

#include <Arduino.h>
#include <DHT.h>
#include "pin_config.h"

class DHTManager {
private:
    DHT dht;
    float lastTemp = 25.0f;
    float lastHum = 50.0f;
    bool hasValidReading = false;

public:
    DHTManager() : dht(PIN_DHT_DATA, DHT11) {}

    void begin() {
        dht.begin();
    }

    bool read(float &temperature, float &humidity) {
        float t = dht.readTemperature();
        float h = dht.readHumidity();

        if (isnan(t) || isnan(h)) {
            hasValidReading = false;
            return false;
        }

        lastTemp = t;
        lastHum = h;
        hasValidReading = true;
        temperature = t;
        humidity = h;
        return true;
    }

    bool isValid() const { return hasValidReading; }
};
