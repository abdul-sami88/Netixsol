# Reproducibility Guide: End-to-End Pipeline Execution

**Client:** Zarya Digital Bank  
**Document:** Week 10 — Day 5: Pipeline Reproduction & Verification  
**Author:** Antigravity Senior AI/ML Engineering Lead  

---

## 1. System Requirements & Environment Setup

* **Python Version:** Python 3.10 or 3.11
* **Hardware (Training):** Single Nvidia GPU with $\ge 12\text{ GB}$ VRAM (e.g. Nvidia Tesla T4, A10G, RTX 3060/4070).
* **Hardware (Serving / Local Verification):** Standard 4-core CPU with $\ge 8\text{ GB}$ RAM.

### Step-by-Step Installation:
```bash
# 1. Clone repository
git clone https://github.com/Zarya-Bank/sovereign-urdulish-llm.git
cd sovereign-urdulish-llm

# 2. Create virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Install core dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 2. Reproducing Each Milestone

### Day 1: Master Synthetic Dataset & Golden Test
```bash
# Verify cleaned master dataset
python -c "import json; data=json.load(open('data/processed/zarya_master_cleaned.json', encoding='utf-8')); print(f'Loaded {len(data)} dialogues')"
```

### Day 2: Supervised Fine-Tuning (SFT)
Open [`notebooks/day2_sft_finetuning.ipynb`](file:///c:/Users/MEE/Anti-Gravity_projects/Fine-tuning-llm/notebooks/day2_sft_finetuning.ipynb) in Google Colab (Tesla T4) or local Jupyter:
- Base: `unsloth/Qwen2.5-3B-Instruct-bnb-4bit`
- Hyperparameters: LoRA rank $r=16$, $\alpha=32$, LR $2\times 10^{-4}$, Batch Size 8, 3 Epochs.
- Outputs saved to `zarya_lora_adapter/`.

### Day 3: DPO Alignment Pipeline
1. Generate preference dataset:
   ```bash
   python src/build_preference_dataset.py
   ```
2. Execute DPO training via [`notebooks/day3_dpo_alignment.ipynb`](file:///c:/Users/MEE/Anti-Gravity_projects/Fine-tuning-llm/notebooks/day3_dpo_alignment.ipynb):
   - Hyperparameters: $\beta = 0.10$, LR $5\times 10^{-5}$, 63 steps.
   - Outputs saved to `zarya_qwen2.5_3b_dpo/`.
3. Verify zero catastrophic forgetting:
   ```bash
   python src/check_catastrophic_forgetting.py
   ```

### Day 4: Quantization, Serving & RAG
1. Merge & Quantize via [`notebooks/day4_quantization_and_serving.ipynb`](file:///c:/Users/MEE/Anti-Gravity_projects/Fine-tuning-llm/notebooks/day4_quantization_and_serving.ipynb):
   - Produces `zarya_qwen2.5_3b_q4km_gguf/` (~1.89 GB).
2. Run complete local verification suite:
   ```bash
   python src/run_day4_local_demo.py
   ```

### Day 5: Production Server & UI Portal
```bash
# Launch interactive web portal & API
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
```
Navigate to:
* **Interactive Portal:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
