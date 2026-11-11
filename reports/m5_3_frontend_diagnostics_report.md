# Project_A1 — Milestone 5.3: Frontend Diagnostics & UI Layout Report

**Date:** 2026-11-11  
**Frontend Framework:** Next.js 14.2.35 (React 18, Tailwind CSS, Lucide Icons)  
**Host URL:** `http://localhost:3000`

---

## 1. UI Diagnostic Fixes

1. **Backend-Managed Serial Manager Component:**
   - Rewrote `SerialManager.tsx` to remove direct Web Serial calls in backend-managed mode.
   - Added live frame counter, last received timestamp, error indicator, and backend connection toggles (`START BACKEND ACQUISITION` / `STOP ACQUISITION`).
   - Unified connection status display with `SystemDiagnostics.tsx`.

2. **Sensor Cards Responsive Refinement:**
   - Corrected SENSOR FAULT banner styling in `SensorCards.tsx`:
     - Added `flex-wrap`, `min-w-0`, and `truncate` to prevent text clipping on narrow mobile or split-pane viewports.
     - Preserved explicit badge: `FAIL-SAFE ENGAGED` with red border and warning icon.
   - Individual sensor card metrics:
     - `MQ-2`: Displays live ADC values (`~695 ADC`), deviation from prototype baseline (`+357 ADC`), and baseline reference benchmark (`338 ADC`).
     - `MQ-135`: Displays `WAITING` with `null` indicator and `-- (No Live Stream)` deviation.
     - `DHT11`: Displays `UNAVAILABLE` badge with `-- °C` and `-- %RH`.
     - `Edge AI`: Displays `NOT AVAILABLE` / `No valid sensor window available for inference`.

3. **Global Dashboard Polling Loop:**
   - In `app/page.tsx`, added a synchronized background polling loop that queries `GET /api/v1/serial/status` every 3s and `GET /api/v1/telemetry/live` every 1s when in `LIVE_HARDWARE` mode.
   - Pushes live frames into the sliding history array (`setHistory`) without full page reloads.

---

## 2. Production Build Verification

```powershell
npm run build
```
```text
  ▲ Next.js 14.2.35
   Creating an optimized production build ...
 ✓ Compiled successfully
   Checking validity of types ...
   Collecting page data ...
 ✓ Generating static pages (5/5)
   Finalizing page optimization ...
   Collecting build traces ...

Route (app)                              Size     First Load JS
┌ ○ /                                    145 kB          233 kB
└ ○ /_not-found                          873 B          88.2 kB
+ First Load JS shared by all            87.3 kB

○  (Static)  prerendered as static content
```
*Result: 100% clean production build.*
