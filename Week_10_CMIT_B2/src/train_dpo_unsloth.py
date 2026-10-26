"""
Task 4: Direct Preference Optimization (DPO) Training Script for Google Colab / Unsloth.
Week 10 — Day 3

Trains the SFT model with DPO using the 500 preference pairs in data/preference/dpo_train_500.jsonl.

Run in Google Colab (with Tesla T4 GPU):
    python train_dpo_unsloth.py
"""

import os
import torch
from datasets import load_dataset
from unsloth import FastLanguageModel, PatchDPOTrainer
from transformers import TrainingArguments
from trl import DPOTrainer

PatchDPOTrainer()

def main():
    max_seq_length = 1024
    dpo_data_path = "data/preference/dpo_train_500.jsonl"
    if not os.path.exists(dpo_data_path):
        dpo_data_path = "/content/dpo_train_500.jsonl"

    print("=======================================================")
    print("Initializing Model for DPO Preference Tuning")
    print("=======================================================")

    # 1. Load Base Model with QLoRA
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/Qwen2.5-3B-Instruct-bnb-4bit",
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )

    # 2. Add LoRA Adapters for Policy Model
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=32,
        lora_dropout=0.0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )

    # 3. Load & Format Preference Dataset
    print(f"Loading DPO Dataset from {dpo_data_path}...")
    dataset = load_dataset("json", data_files=dpo_data_path, split="train")

    def format_dpo_row(example):
        # Format ChatML prompt
        prompt_msgs = example["prompt"]
        prompt_text = tokenizer.apply_chat_template(prompt_msgs, tokenize=False, add_generation_prompt=True)
        return {
            "prompt": prompt_text,
            "chosen": example["chosen"] + "<|im_end|>\n",
            "rejected": example["rejected"] + "<|im_end|>\n",
        }

    formatted_dataset = dataset.map(format_dpo_row)
    print(f"Prepared {len(formatted_dataset)} preference pairs.")

    # 4. Training Arguments
    training_args = TrainingArguments(
        output_dir="./dpo_outputs",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        num_train_epochs=1,
        learning_rate=5e-5,          # Lower LR for DPO than SFT
        fp16=True,                   # T4 compatible
        logging_steps=10,
        optim="paged_adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        seed=3407,
        report_to="none"
    )

    # 5. Initialize DPO Trainer
    print("\nStarting DPO Alignment Training (Beta = 0.10)...")
    dpo_trainer = DPOTrainer(
        model=model,
        ref_model=None,              # Unsloth automatically handles frozen reference policy
        args=training_args,
        beta=0.10,                   # Implicit reward scale
        train_dataset=formatted_dataset,
        tokenizer=tokenizer,
        max_length=max_seq_length,
        max_prompt_length=512,
    )

    dpo_trainer.train()

    # 6. Save Fine-Tuned DPO Adapter
    output_dpo_dir = "/content/zarya_qwen2.5_3b_dpo"
    print(f"\nSaving DPO aligned adapter to {output_dpo_dir}...")
    model.save_pretrained_merged(output_dpo_dir, tokenizer, save_method="lora")
    print("DPO Alignment Completed Successfully!")

if __name__ == "__main__":
    main()
