# Security Policy for HazardWatch

## 1. Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## 2. Reporting a Vulnerability

We take the security and safety of industrial IoT systems seriously. If you discover a security vulnerability or safety-critical flaw (e.g. unexpected actuator triggering or authentication bypass):

1. **Do not create a public GitHub issue.**
2. Report the vulnerability privately via GitHub's **Private Vulnerability Reporting** feature or contact maintainers via email at: `aashishniranjanb@gmail.com`.
3. Include:
   - Description of the vulnerability.
   - Exact steps or proof of concept to reproduce.
   - Potential impact on physical hardware or host network.
4. Maintainers will review and respond within 48 hours.

---

## 3. Physical & Actuator Safety Notice

- **Actuator Limits:** This prototype features an active-LOW relay driver configured for air pumps and fans. It is **not** certified for explosive, flammable, or oxygen-depleted atmospheres.
- **Physical Isolation:** Actuation outputs must remain physically disconnected or controlled via manual safety switches during development.
- **Sensor Scope:** The MQ-2 and MQ-135 sensors provide uncalibrated, broad-spectrum analog responses. They must never be relied upon as life-safety devices.
