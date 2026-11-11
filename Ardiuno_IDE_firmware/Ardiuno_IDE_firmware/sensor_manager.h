#pragma once

#include <Arduino.h>
#include <DHT.h>
#include "pin_config.h"
#include "config.h"

struct SensorData {
    uint32_t ts;
    uint16_t mq2;
    uint16_t mq135;
    float temperature;
    float humidity;
    bool mq2Valid;
    bool mq135Valid;
    bool dhtValid;
};

class SensorManager {
private:
    DHT dht;

public:
    SensorManager() : dht(PIN_DHT, DHT_TYPE) {}

    void begin() {
        analogReadResolution(12);
        analogSetPinAttenuation(PIN_MQ2, ADC_11db);
        analogSetPinAttenuation(PIN_MQ135, ADC_11db);
        dht.begin();
    }

    bool isAdcValid(uint16_t val) const {
        return (val >= ADC_MIN_VALID && val <= ADC_MAX_VALID);
    }

    SensorData readAll() {
        SensorData s{};
        s.ts = millis();
        s.mq2 = analogRead(PIN_MQ2);
        s.mq135 = analogRead(PIN_MQ135);
        s.mq2Valid = isAdcValid(s.mq2);
        s.mq135Valid = isAdcValid(s.mq135);

        s.humidity = dht.readHumidity();
        s.temperature = dht.readTemperature();
        s.dhtValid = !isnan(s.humidity) && !isnan(s.temperature) &&
                     s.humidity >= 0.0f && s.humidity <= 100.0f &&
                     s.temperature >= -20.0f && s.temperature <= 80.0f;
        return s;
    }
};
