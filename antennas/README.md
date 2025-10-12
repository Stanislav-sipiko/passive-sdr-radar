# LPDA Build Instructions (514–594 MHz)

This document describes how to construct the broadband Log-Periodic Dipole Array (LPDA) antenna designed for 514–594 MHz operation.

## 1. Electrical and Mechanical Summary

| Parameter | Value |
|------------|--------|
| Frequency Range | 514–594 MHz |
| Wavelength Range | 0.49–0.58 m |
| Number of Elements | 10–12 |
| Tau (τ) | 0.95 |
| Sigma (σ) | 0.06 |
| Boom Length | ≈1.2 m |
| Longest Element | ≈290 mm |
| Shortest Element | ≈190 mm |
| Element Spacing | 60–80 mm |
| Expected Gain | 8–10 dBi |
| VSWR Bandwidth | ~20% (SWR < 1.5) |

---

## 2. Materials

**Elements:** Aluminum (6061-T6 or similar). Diameter 8–12 mm. Wall thickness 1–2 mm.  
**Booms:** Two parallel aluminum tubes or square bars (20×20 mm). Distance between booms: 40 mm.  
**Insulators:** Nylon/PTFE or fiberglass spacers every 100–150 mm.  
**Fasteners:** Stainless bolts, aluminum rivets, or conductive clamps.  
**Coax:** 50 Ω (RG-400, RG-58, or LMR-240).

---

## 3. Feeding and Balun

### Feed Point
- Connect coax center conductor to one boom, braid to the other.
- Feed at the longest dipole pair (rear element).

### Balun 1:1 (Choke Type)
- Wind 5–6 turns of RG-400 or RG-58 on ferrite core FT240-43 (Ø50 mm).  
- Place within 10 cm of feed point.

### Optional λ/4 Transformer
If impedance mismatch occurs, use a λ/4 coax section with impedance  
\(Z_t = \sqrt{Z_{ant} Z_{feed}} ≈ 60–70 Ω\).

---

## 4. Assembly Steps

1. Mark boom holes as per `lpda_elements.csv`.  
2. Drill element holes at correct positions and ensure perpendicularity.  
3. Mount dipole pairs alternately (phase reversal every element).  
4. Secure booms with dielectric spacers every 10–15 cm.  
5. Connect coax feed and balun.  
6. Check SWR with VNA; fine-tune by trimming rear element if needed.  
7. Paint or anodize for weather protection.

---

## 5. Mounting and Array Configuration

- Polarization: **Horizontal**.  
- Height above ground: ≥1.5 m.  
- For four antennas (radar array): spacing ≈0.5–0.6 λ (27–32 cm).  
- Feed all in-phase via 1→4 power divider with equal cable lengths.

---

## 6. Key Notes

- τ = 0.95 → moderate gain and good bandwidth.  
- Smaller τ (e.g., 0.93) increases length and gain; larger τ reduces both.  
- σ = 0.06 → spacing compromise between compactness and coupling.  
- Typical LPDA impedance ≈ 50 Ω, minimal matching required.  
- Expected gain 9–10 dBi, front-to-back ratio 20–25 dB.

---

## 7. Construction Summary

| Component | Specification |
|------------|---------------|
| Element Material | Aluminum rod Ø10 mm |
| Boom Material | 2× Aluminum square 20×20 mm |
| Boom Spacing | 40 mm |
| Balun | 1:1 choke (5 turns RG-400 on FT240-43) |
| Feed Impedance | 50 Ω |
| Gain | 9–10 dBi |
| Polarization | Horizontal |
| Weight | ~1 kg |

---

This LPDA covers the entire 514–594 MHz band with stable impedance, smooth gain, and is ideal for passive radar or broadband reception systems.
