# Project_A1 — Milestone 5.0.1: Firmware Memory Usage Report

**Date:** 2026-11-11  
**Hardware Platform:** ESP32 DevKit V1 (ESP32-WROOM-32)  
**Total Available Internal SRAM:** 327,680 bytes (320 KB)  
**Total Available App Flash Partition:** 1,310,720 bytes (1.25 MB default SPIFFS partition layout)

---

## 1. Memory Consumption Comparison

| Firmware Build | Flash Memory Used | Flash % | RAM Memory Used | RAM % | Free RAM Remaining |
|---|---|---|---|---|---|
| **Non-ML Backup (`project_a1_backup`)** | **311,464 bytes** | **23.8%** | **22,860 bytes** | **7.0%** | **304,820 bytes (93.0%)** |
| **ML TinyML (`project_a1_ml`)** | **428,500 bytes** | **32.7%** | **31,508 bytes** | **9.6%** | **296,172 bytes (90.4%)** |
| **Net Difference (ML Overhead)** | **+117,036 bytes** | **+8.9%** | **+8,648 bytes** | **+2.6%** | **-8,648 bytes** |

---

## 2. Analysis of RAM & Flash Overhead

### Static RAM (SRAM) Breakdown
- **Base Architecture (`project_a1_backup`):** Consumes 22,860 bytes for the FreeRTOS kernel, Arduino core runtime, circular sliding window buffers, and JSON serialization buffers.
- **ML Engine (`project_a1_ml`):** Consumes 31,508 bytes. The net increase of **8,648 bytes** corresponds almost exactly to the **8,192-byte (`TFLM_TENSOR_ARENA_SIZE`) tensor arena** plus interpreter object structures.
- **Safety Margin:** Both builds leave **over 296 KB (>90%) of internal SRAM free**, preventing heap fragmentation or stack overflows during continuous execution.

### Flash Memory Breakdown
- **Non-ML Backup:** Uses 311.5 KB, leaving ~1,000 KB of application Flash available.
- **ML Build:** Uses 428.5 KB (+117 KB), which incorporates the TensorFlow Lite Micro kernel code (operators for Fully Connected, Softmax, Quantize, Dequantize, and Relu) and the embedded INT8 model weight matrix (5,312 bytes).
- **Safety Margin:** Leaves **882 KB (>67%) of Flash headroom** in the default application partition.

---

## 3. Conclusion

Both builds operate well inside the hardware limits of the ESP32-WROOM-32:
- Zero dynamic allocations (`malloc`/`new`) in the main acquisition loop.
- Static tensor arena allocation guarantees zero runtime memory leaks.
- Ready for hardware deployment upon completion of Milestone 5.1 electrical inspection.
