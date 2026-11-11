#pragma once

#include <Arduino.h>
#include "protocol.h"
#include "config.h"

struct RuleEvaluationResult {
    HazardState hazardState;
    const char* patternName;
    bool relayCommand;
    bool isFault;
    const char* reason;
};

class RuleEngine {
public:
    static RuleEvaluationResult evaluate(
        int mq2_adc,
        int mq135_adc,
        float base_mq2,
        float base_mq135,
        bool sensorFault
    ) {
        RuleEvaluationResult res;
        res.relayCommand = false;
        res.isFault = sensorFault;

        if (sensorFault) {
            res.hazardState = HAZARD_SENSOR_FAULT;
            res.patternName = "SENSOR_FAULT";
            res.relayCommand = false; // Decoupled: Safe OFF
            res.reason = "Sensor hardware fault (pin short or open circuit)";
            return res;
        }

        float deltaMQ2 = mq2_adc - base_mq2;
        float deltaMQ135 = mq135_adc - base_mq135;

        // Level 3: Critical Hazard (Advisory Pattern Only)
        // CRITICAL SAFETY MANDATE (M5.0):
        // Neither the MQ-2 / MQ-135 sensors nor the prototype air pump are certified
        // for hazardous / explosive atmospheres. Relay command MUST remain FALSE (disabled by default)
        // in all automated scenarios. Relay actuation is strictly isolated to explicit manual operator command.
        if (deltaMQ2 >= DELTA_CRITICAL_ADC || deltaMQ135 >= DELTA_CRITICAL_ADC ||
            mq2_adc >= RELAY_ACTUATE_MQ2_ADC || mq135_adc >= RELAY_ACTUATE_MQ135_ADC) {
            
            res.hazardState = HAZARD_CRITICAL;
            res.relayCommand = false; // Strictly FALSE: Disabled by default in prototype
            
            if (deltaMQ2 > deltaMQ135 * 1.5f) {
                res.patternName = "COMBUSTIBLE_RESPONSE_PATTERN";
                res.reason = "Massive combustible-like response on MQ-2 (Relay isolated safe OFF)";
            } else if (deltaMQ135 > deltaMQ2 * 1.5f) {
                res.patternName = "VOC_RESPONSE";
                res.reason = "Massive VOC/Solvent-like response on MQ-135 (Relay isolated safe OFF)";
            } else {
                res.patternName = "SMOKE_RESPONSE";
                res.reason = "Rapid dual-sensor response typical of dense smoke (Relay isolated safe OFF)";
            }
            return res;
        }
                res.reason = "Massive VOC/Solvent response on MQ-135";
            } else {
                res.patternName = "SMOKE_RESPONSE";
                res.reason = "Rapid dual-sensor response typical of dense smoke";
            }
            return res;
        }

        // Level 2: Warning Hazard
        if (deltaMQ2 >= DELTA_WARNING_ADC || deltaMQ135 >= DELTA_WARNING_ADC) {
            res.hazardState = HAZARD_WARNING;
            res.relayCommand = false; // Advisory warning; await confirmation
            res.patternName = (deltaMQ2 > deltaMQ135) ? "COMBUSTIBLE_RESPONSE_PATTERN" : "VOC_RESPONSE";
            res.reason = "Atmospheric reading significantly elevated above baseline";
            return res;
        }

        // Level 1: Advisory
        if (deltaMQ2 >= DELTA_ADVISORY_ADC || deltaMQ135 >= DELTA_ADVISORY_ADC) {
            res.hazardState = HAZARD_ADVISORY;
            res.relayCommand = false;
            res.patternName = "ADVISORY_DRIFT";
            res.reason = "Minor baseline deviation observed";
            return res;
        }

        // Level 0: Clean baseline
        res.hazardState = HAZARD_NORMAL_BASELINE;
        res.patternName = "NORMAL_BASELINE";
        res.relayCommand = false;
        res.reason = "Atmospheric sensor baseline nominal";
        return res;
    }
};
