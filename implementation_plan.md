# Implementation Plan: Optimize Anti-Spoofing Thresholds

## Goal
Improve the detection rate of phone screen spoofing by refining the parameters of existing algorithms in `liveness_detector.py`.

## Proposed Refinements

### 1. Moire Pattern Detection (`detect_moire_pattern`)
- **Problem:** False negatives on modern high-res screens (moire pattern is subtle).
- **Optimization:**
    - Reduce the base threshold (`moire_thresh`) from **45.0** to **35.0**.
    - Reduce the threshold for "GOOD" lighting from **40.0** to **30.0**.
    - This increases sensitivity to high-frequency patterns typical of pixel grids.

### 2. Chromatic Aberration (`check_chromatic_aberration`)
- **Problem:** Current threshold (50.0) is too loose, allowing screens with slight color shifting to pass.
- **Optimization:**
    - Reduce `chromatic_thresh` from **50.0** to **30.0**.
    - Screens often exhibit RGB separation (color fringing) more than real/printed faces.

### 3. Texture Analysis (`check_texture`)
- **Problem:** "Blurry" screen images might pass if the adaptive threshold drops too low in dim light.
- **Optimization:**
    - Increase the `laplacian_base_threshold` slightly from **20.0** to **25.0**.
    - Adjust the adaptive formula to be stricter (require higher sharpness) even in lower light.

### 4. Head Movement Movement (`check_head_movement_ratio`)
- **Review:** Make sure the "ratio" logic is consistent. No major changes proposed here unless user reports issues with turning steps.

## Verification Plan
1.  **Code Update:** Apply new thresholds variables in `__init__` and method logic.
2.  **Manual Test:**
    - **Scenario A:** Real face in normal light -> Should PAss.
    - **Scenario B:** Phone screen in normal light -> Should FAIL (catch via MOIRE or CHROMATIC).
    - **Scenario C:** Real face in low light -> Should PASS (ensure texture check isn't too strict).
