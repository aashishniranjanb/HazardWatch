#pragma once

// =========================================================================
// COMMON TELEMETRY PROTOCOL & STATE DEFINITIONS
// Shared identically by both ML and Rule-Based Firmware Builds
// =========================================================================

enum MonitoringState {
    STATE_STARTUP_WARMUP,
    STATE_LIVE_MONITORING,
    STATE_SENSOR_FAULT,
    STATE_OFFLINE_LOCAL
};

enum HazardState {
    HAZARD_NORMAL_BASELINE,
    HAZARD_ADVISORY,
    HAZARD_WARNING,
    HAZARD_CRITICAL,
    HAZARD_UNKNOWN,
    HAZARD_SENSOR_FAULT
};

inline const char* monitoringStateToString(MonitoringState s) {
    switch (s) {
        case STATE_STARTUP_WARMUP:  return "STARTUP_WARMUP";
        case STATE_LIVE_MONITORING: return "LIVE_MONITORING";
        case STATE_SENSOR_FAULT:    return "SENSOR_FAULT";
        case STATE_OFFLINE_LOCAL:   return "OFFLINE_LOCAL";
        default:                    return "UNKNOWN";
    }
}

inline const char* hazardStateToString(HazardState h) {
    switch (h) {
        case HAZARD_NORMAL_BASELINE: return "NORMAL_BASELINE";
        case HAZARD_ADVISORY:        return "ADVISORY";
        case HAZARD_WARNING:         return "WARNING";
        case HAZARD_CRITICAL:        return "CRITICAL";
        case HAZARD_UNKNOWN:         return "UNKNOWN";
        case HAZARD_SENSOR_FAULT:    return "SENSOR_FAULT";
        default:                     return "UNKNOWN";
    }
}
