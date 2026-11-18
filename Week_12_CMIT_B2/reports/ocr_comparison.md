# Urdu OCR Benchmark (10 Legal Pages, CER)

Character Error Rate (CER) computed after Unicode NFKC & Urdu character normalization (`jiwer.cer`). Lower is better.

## Aggregate Results

| OCR Tool | Language Pack | Pages | Avg CER | Avg Time / Page |
| :--- | :--- | ---: | ---: | ---: |
| **EasyOCR** | `ur` (CPU) | 10 | 0.0579 | 49.80s |
| **Tesseract OCR** | `urd` (LSTM) | 10 | 0.1375 | 0.72s |

## Per-Page Breakdown

| page                            |   gt_chars |   easyocr_cer |   easyocr_sec |   tesseract_cer |   tesseract_sec |
|:--------------------------------|-----------:|--------------:|--------------:|----------------:|----------------:|
| 01_kiraya_nama_lahore           |        390 |        0.0872 |         81.94 |          0.0103 |            1    |
| 02_fir_report_karachi           |        350 |        0.0714 |         55.21 |          0.0114 |            0.79 |
| 03_qanooni_notice_islamabad     |        331 |        0.0393 |         52.02 |          0.1752 |            0.6  |
| 04_darkhwast_zamanat_rawalpindi |        336 |        0.0774 |         44.32 |          0.122  |            0.65 |
| 05_bayan_e_halfi_multan         |        318 |        0.044  |         44.81 |          0.1069 |            1.02 |
| 06_iqrarnama_farokht_faisalabad |        330 |        0.0394 |         43.9  |          0.0758 |            0.59 |
| 07_mulazmat_muahida_peshawar    |        298 |        0.0403 |         40.56 |          0.1007 |            0.65 |
| 08_mukhtar_nama_aam_quetta      |        315 |        0.0349 |         47.7  |          0.0095 |            1.11 |
| 09_dawa_naan_nafaqa_sialkot     |        329 |        0.0578 |         51.71 |          0.7538 |            0.25 |
| 10_hukamnama_adalat_lahore      |        320 |        0.0875 |         35.81 |          0.0094 |            0.54 |

## Analysis & Production Recommendation
- **Accuracy vs. Consistency:** EasyOCR achieved the lower average CER (**0.0579** vs. **0.1375**) and stayed highly consistent across skewed scans (`0.0349–0.0875` CER).
- **Speed & Clean-Page Accuracy:** Tesseract (`urd`) ran **~69× faster** on CPU (**0.72s/page** vs. **49.80s/page**) and outperformed EasyOCR on well-aligned pages (`01`, `02`, `08`, `10` at **0.0094–0.0114 CER**), but suffered on `09_dawa_naan_nafaqa_sialkot` (`0.7538` CER) where slight scan rotation caused default page segmentation to drop lines.
- **Pipeline Decision for Khan & Associates (8 GB RAM CPU):** Use **Tesseract (`urd`/`eng`) as the primary OCR engine** for bulk ingestion, and route pages with unusually low extracted character density or high skew to **EasyOCR** (or deskew preprocessing).