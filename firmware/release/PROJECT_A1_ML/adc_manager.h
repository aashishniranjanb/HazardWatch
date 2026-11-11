#pragma once

#include <Arduino.h>
#include "pin_config.h"
#include "config.h"

class ADCManager {
public:
    void begin() {
        analogReadResolution(ADC_RESOLUTION_BITS);
        analogSetPinAttenuation(PIN_MQ2_ADC, ADC_ATTEN_CONFIG);
        analogSetPinAttenuation(PIN_MQ135_ADC, ADC_ATTEN_CONFIG);
    }

    int readMQ2() {
        return analogRead(PIN_MQ2_ADC);
    }

    int readMQ135() {
        return analogRead(PIN_MQ135_ADC);
    }

    bool isMQ2Fault(int adc) {
        return (adc <= SENSOR_FAULT_ADC_MIN || adc >= SENSOR_FAULT_ADC_MAX);
    }

    bool isMQ135Fault(int adc) {
        return (adc <= SENSOR_FAULT_ADC_MIN || adc >= SENSOR_FAULT_ADC_MAX);
    }
};
