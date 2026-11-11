#pragma once

#include <Arduino.h>
#include "config.h"
#include "protocol.h"

struct RuleResult {
    HazardState state;
    const char* pattern;
    const char* reason;
    bool relayCommand;
};

class RuleEngine {
public:
    static RuleResult evaluate(uint16_t mq2, uint16_t mq135, float baseMq2, float baseMq135, bool fault) {
        RuleResult r{};
        r.relayCommand = false; // CRITICAL: Always default safe-OFF

        if (fault) {
            r.state = HAZARD_SENSOR_FAULT;
            r.pattern = "SENSOR_FAULT";
            r.reason = "Sensor rail short or open circuit detected";
            return r;
        }

        float delta2 = (float)mq2 - baseMq2;
        float delta135 = (float)mq135 - baseMq135;

        // Critical Advisory Threshold
        if (delta2 >= DELTA_CRITICAL_ADC || delta135 >= DELTA_CRITICAL_ADC || mq2 >= 600 || mq135 >= 1800) {
            r.state = HAZARD_CRITICAL;
            r.relayCommand = false; // Strictly isolated safe-OFF (unrated pump)
            if (delta2 > delta135 * 1.5f) {
                r.pattern = "COMBUSTIBLE_RESPONSE_PATTERN";
                r.reason = "High MQ-2 response typical of combustible fuel gas";
            } else if (delta135 > delta2 * 1.5f) {
                r.pattern = "VOC_RESPONSE";
                r.reason = "High MQ-135 response typical of volatile solvent vapors";
            } else {
                r.pattern = "SMOKE_RESPONSE";
                r.reason = "Rapid dual-sensor response typical of particulate smoke";
            }
            return r;
        }

        // Warning Tier
        if (delta2 >= DELTA_WARNING_ADC || delta135 >= DELTA_WARNING_ADC) {
            r.state = HAZARD_WARNING;
            r.pattern = (delta2 > delta135) ? "COMBUSTIBLE_RESPONSE_PATTERN" : "VOC_RESPONSE";
            r.reason = "Significant sensor baseline deviation";
            return r;
        }

        // Advisory Tier
        if (delta2 >= DELTA_ADVISORY_ADC || delta135 >= DELTA_ADVISORY_ADC) {
            r.state = HAZARD_ADVISORY;
            r.pattern = "ADVISORY_DRIFT";
            r.reason = "Minor baseline elevation detected";
            return r;
        }

        r.state = HAZARD_NORMAL_BASELINE;
        r.pattern = "NORMAL_BASELINE";
        r.reason = "Atmospheric baseline nominal";
        return r;
    }
};
