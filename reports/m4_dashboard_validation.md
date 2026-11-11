# Milestone 4 Dashboard UI & Frontend Integration Validation Report

**Frontend Platform:** Next.js 14 (App Router) + TailwindCSS + Lucide Icons + React  
**Build Status:** ✅ Production Build Succeeded (Static Generation 5/5 routes)  
**Host Bundle Size:** 142 kB page route, 87.3 kB shared runtime  

---

## 1. Operating Mode Architecture in UI

The SCADA dashboard features three strictly isolated operational modes selectable from the header:

```
[ SCADA Header Mode Selector ]
  ├── 🟢 LIVE HARDWARE (Web Serial API / USB COM Port)
  │      └── Status Badge: "DISCONNECTED / UNVERIFIED"
  │      └── Diagnostic Alert: Explicit notice that physical serial input is not yet verified
  │      └── No synthetic fallback: Real serial stream or explicit error prompt
  │
  ├── 🟡 HISTORICAL REPLAY (Verified Research CSV Datasets)
  │      └── Selectable Datasets: Multi-Sensor Rig (812 rows), Continuous Baseline (12,175 rows), MOS Bench (6,400 rows)
  │      └── Playback Controls: Step forward, Auto-replay, scrub index, pause
  │      └── Provenance Badge: VERIFIED_RESEARCH_DATASET
  │
  └── 🟣 SYNTHETIC SIMULATION (8 Industrial Hazard Scenarios)
         └── Scenarios: H01 Gas Line Flare, H02 Solvent Evap, H03 Electrical Smolder, H04 Battery Off-gas, etc.
         └── Zone Selection: Z01 Mechanical Workshop through Z08 Perimeter
         └── Provenance Badge: SYNTHETIC_SIMULATION (Explicit amber watermark)
```

---

## 2. Industrial SCADA Dashboard Component Verification

| Dashboard Component | Functionality Verified | Industrial Safety & Provenance Rules |
| :--- | :--- | :--- |
| **Zone Map Selector (Z01 - Z08)** | Allows operator to monitor specific factory zones | Highlights zone hazard rating and local ventilation state |
| **Sensor Cards (MQ-2, MQ-135, DHT11)** | Live ADC counts, voltage, delta-baseline, and temperature/RH | Null values display as `DISCONNECTED / NULL` during sensor fault; never faked |
| **Dual Inference Telemetry Card** | Displays Edge INT8 prediction alongside Server Python XGBoost prediction | Highlights any parity mismatch; triggers `OOD` warning if feature distance $z > 4.0\sigma$ |
| **Safety Interlock Card** | Displays Relay Control State vs. Sensor Status | Explicit indicator verifying that sensor fault decouples ventilation relay actuation |
| **Incident Management Table** | Active `INC-xxxx` cards with severity badges (CRITICAL, HIGH, WARNING, NORMAL) | Allows one-click Operator Acknowledgment and Resolution with audit logging |
| **Provenance Watermark** | Prominently displays the active data stream's legal origin | Prevents operators or stakeholders from mistaking synthetic scenarios for real sensor telemetry |

---

## 3. Production Build Output

```
Route (app)                              Size     First Load JS
┌ ○ /                                    142 kB          229 kB
└ ○ /_not-found                          873 B          88.2 kB
+ First Load JS shared by all            87.3 kB
  ├ chunks/117-5840e53afe153d68.js       31.7 kB
  ├ chunks/fd9d1056-7af6a7ccbdd77626.js  53.6 kB
  └ other shared chunks (total)          1.96 kB

○  (Static)  prerendered as static content
```
Result: **Zero TypeScript errors, zero hydration errors, and fully optimized production bundle.**
