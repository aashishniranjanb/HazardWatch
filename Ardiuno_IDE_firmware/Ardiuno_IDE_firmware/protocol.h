#pragma once

#include <Arduino.h>

// =========================================================================
// PROTOCOL ENUMERATIONS & STATE SERIALIZATION
// =========================================================================

enum MonitorState { 
    INITIALIZING, 
    BASELINE_MODE, 
    LIVE_MONITORING, 
    SENSOR_FAULT 
};

enum HazardState { 
    HAZARD_NORMAL_BASELINE, 
    HAZARD_ADVISORY, 
    HAZARD_WARNING, 
    HAZARD_CRITICAL, 
    HAZARD_UNKNOWN, 
    HAZARD_SENSOR_FAULT 
};

inline const char* stateName(MonitorState s) {
    switch (s) {
        case INITIALIZING: return "INITIALIZING";
        case BASELINE_MODE: return "BASELINE_MODE";
        case LIVE_MONITORING: return "LIVE_MONITORING";
        case SENSOR_FAULT: return "SENSOR_FAULT";
        default: return "UNKNOWN";
    }
}

inline const char* hazardName(HazardState h) {
    switch (h) {
        case HAZARD_NORMAL_BASELINE: return "NORMAL_BASELINE";
        case HAZARD_ADVISORY: return "ADVISORY";
        case HAZARD_WARNING: return "WARNING";
        case HAZARD_CRITICAL: return "CRITICAL";
        case HAZARD_UNKNOWN: return "UNKNOWN";
        case HAZARD_SENSOR_FAULT: return "SENSOR_FAULT";
        default: return "UNKNOWN";
    }
}
