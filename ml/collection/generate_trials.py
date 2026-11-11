"""
Synthetic Multi-Trial Experiment Generator (M2.7)
Generates independent multi-session trial data across two distinct sensor boards:
- Board A: Training / Validation / Test Device
- Board B: Completely Held-Out Cross-Device Evaluation Device
"""

import os
import numpy as np
import pandas as pd
from ml.collection.trial_recorder import ExperimentTrialRecorder

def generate_multi_trial_corpus():
    trials = []

    # -------------------------------------------------------------
    # BOARD A: Primary Training & Development Device
    # -------------------------------------------------------------
    # Trial 1: Board A - Clean Air Baseline Startup & Warmup (1,000 samples)
    t1 = ExperimentTrialRecorder("EXP_A_001_CLEAN_AIR_WARMUP", "BOARD_A")
    for i in range(1000):
        drift = 100 * np.exp(-i / 200.0)
        mq2 = 350 + drift + np.random.normal(0, 5)
        mq135 = 1450 + drift * 0.8 + np.random.normal(0, 10)
        t1.log_reading(mq2, mq135, 24.5 + i*0.001, 52.0, "NORMAL_BASELINE", "CAL_A_CLEAN_REF", False, False)
    trials.append(t1.save())

    # Trial 2: Board A - Clean Air Overnight Stable Session 2 (1,200 samples)
    t2 = ExperimentTrialRecorder("EXP_A_002_CLEAN_AIR_STABLE", "BOARD_A")
    for i in range(1200):
        mq2 = 352 + np.random.normal(0, 6)
        mq135 = 1445 + np.random.normal(0, 12)
        t2.log_reading(mq2, mq135, 23.8, 55.0, "NORMAL_BASELINE", "CAL_A_CLEAN_REF", False, False)
    trials.append(t2.save())

    # Trial 3: Board A - Smoke Particulate Exposure Session 1 (600 samples)
    t3 = ExperimentTrialRecorder("EXP_A_003_SMOKE_TRIAL_1", "BOARD_A")
    for i in range(600):
        if 150 <= i <= 450:
            mq2 = 1250 + np.random.normal(0, 35)
            mq135 = 1580 + np.random.normal(0, 20)
            is_exp = True
        else:
            mq2 = 355 + np.random.normal(0, 8)
            mq135 = 1450 + np.random.normal(0, 12)
            is_exp = False
        t3.log_reading(mq2, mq135, 25.2, 51.0, "SMOKE" if is_exp else "NORMAL_BASELINE", "CAL_A_CLEAN_REF", is_exp, False)
    trials.append(t3.save())

    # Trial 4: Board A - VOC / Solvent Vapor Exposure Session 1 (600 samples)
    t4 = ExperimentTrialRecorder("EXP_A_004_VOC_TRIAL_1", "BOARD_A")
    for i in range(600):
        if 150 <= i <= 450:
            mq2 = 420 + np.random.normal(0, 15)
            mq135 = 2300 + np.random.normal(0, 45)
            is_exp = True
        else:
            mq2 = 350 + np.random.normal(0, 8)
            mq135 = 1450 + np.random.normal(0, 12)
            is_exp = False
        t4.log_reading(mq2, mq135, 25.5, 53.0, "VOC_RESPONSE" if is_exp else "NORMAL_BASELINE", "CAL_A_CLEAN_REF", is_exp, False)
    trials.append(t4.save())

    # Trial 5: Board A - Complex Mixture Exposure Session 1 (600 samples)
    t5 = ExperimentTrialRecorder("EXP_A_005_MIXTURE_TRIAL_1", "BOARD_A")
    for i in range(600):
        if 150 <= i <= 450:
            mq2 = 1100 + np.random.normal(0, 30)
            mq135 = 2150 + np.random.normal(0, 40)
            is_exp = True
        else:
            mq2 = 350 + np.random.normal(0, 8)
            mq135 = 1450 + np.random.normal(0, 12)
            is_exp = False
        t5.log_reading(mq2, mq135, 26.0, 50.0, "MIXTURE" if is_exp else "NORMAL_BASELINE", "CAL_A_CLEAN_REF", is_exp, False)
    trials.append(t5.save())

    # Trial 5b: Board A - Second Mixture Exposure Session 2 (600 samples for validation)
    t5b = ExperimentTrialRecorder("EXP_A_005B_MIXTURE_TRIAL_2", "BOARD_A")
    for i in range(600):
        if 150 <= i <= 450:
            mq2 = 1080 + np.random.normal(0, 30)
            mq135 = 2120 + np.random.normal(0, 40)
            is_exp = True
        else:
            mq2 = 352 + np.random.normal(0, 8)
            mq135 = 1448 + np.random.normal(0, 12)
            is_exp = False
        t5b.log_reading(mq2, mq135, 26.2, 49.0, "MIXTURE" if is_exp else "NORMAL_BASELINE", "CAL_A_CLEAN_REF", is_exp, False)
    trials.append(t5b.save())

    # -------------------------------------------------------------
    # BOARD B: Completely Independent Held-Out Device (Cross-Device Evaluation)
    # -------------------------------------------------------------
    # Trial 6: Board B - Independent Clean Air Baseline (1,000 samples)
    t6 = ExperimentTrialRecorder("EXP_B_006_CLEAN_AIR_HELD_OUT", "BOARD_B")
    for i in range(1000):
        mq2 = 320 + np.random.normal(0, 6)
        mq135 = 1520 + np.random.normal(0, 14)
        t6.log_reading(mq2, mq135, 22.5, 58.0, "NORMAL_BASELINE", "CAL_B_CLEAN_REF", False, False)
    trials.append(t6.save())

    # Trial 7: Board B - Independent Smoke Test (600 samples)
    t7 = ExperimentTrialRecorder("EXP_B_007_SMOKE_HELD_OUT", "BOARD_B")
    for i in range(600):
        if 150 <= i <= 450:
            mq2 = 1310 + np.random.normal(0, 35)
            mq135 = 1620 + np.random.normal(0, 20)
            is_exp = True
        else:
            mq2 = 322 + np.random.normal(0, 7)
            mq135 = 1518 + np.random.normal(0, 12)
            is_exp = False
        t7.log_reading(mq2, mq135, 23.0, 56.0, "SMOKE" if is_exp else "NORMAL_BASELINE", "CAL_B_CLEAN_REF", is_exp, False)
    trials.append(t7.save())

    # Trial 8: Board B - Independent VOC Solvent Test (600 samples)
    t8 = ExperimentTrialRecorder("EXP_B_008_VOC_HELD_OUT", "BOARD_B")
    for i in range(600):
        if 150 <= i <= 450:
            mq2 = 410 + np.random.normal(0, 15)
            mq135 = 2380 + np.random.normal(0, 50)
            is_exp = True
        else:
            mq2 = 320 + np.random.normal(0, 7)
            mq135 = 1520 + np.random.normal(0, 12)
            is_exp = False
        t8.log_reading(mq2, mq135, 23.5, 55.0, "VOC_RESPONSE" if is_exp else "NORMAL_BASELINE", "CAL_B_CLEAN_REF", is_exp, False)
    trials.append(t8.save())

    # Trial 9: Board B - Independent Mixture Test (600 samples)
    t9 = ExperimentTrialRecorder("EXP_B_009_MIXTURE_HELD_OUT", "BOARD_B")
    for i in range(600):
        if 150 <= i <= 450:
            mq2 = 1120 + np.random.normal(0, 30)
            mq135 = 2210 + np.random.normal(0, 40)
            is_exp = True
        else:
            mq2 = 321 + np.random.normal(0, 7)
            mq135 = 1522 + np.random.normal(0, 12)
            is_exp = False
        t9.log_reading(mq2, mq135, 24.0, 54.0, "MIXTURE" if is_exp else "NORMAL_BASELINE", "CAL_B_CLEAN_REF", is_exp, False)
    trials.append(t9.save())

    print(f"Generated {len(trials)} independent experiment trials across BOARD_A and BOARD_B.")
    return trials

if __name__ == "__main__":
    generate_multi_trial_corpus()
