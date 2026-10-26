"""
Zarya Digital Bank - Hugging Face Model Publisher
Pushes the SFT+DPO LoRA adapter and Q4_K_M GGUF quantized models to private Hugging Face Hub.
"""

import os
import argparse
from huggingface_hub import HfApi, create_repo


def push_model(repo_id: str, token: str, private: bool = True):
    print(f"Connecting to Hugging Face Hub for repo: {repo_id}...")
    api = HfApi(token=token)

    # 1. Create Private Repository if it doesn't exist
    create_repo(repo_id=repo_id, token=token, private=private, exist_ok=True)
    print(f"Private repository verified: https://huggingface.co/{repo_id}")

    # 2. Upload Aligned DPO Adapter
    dpo_dir = os.path.abspath("zarya_qwen2.5_3b_dpo")
    if os.path.exists(dpo_dir):
        print(f"Uploading SFT+DPO adapter from {dpo_dir}...")
        api.upload_folder(
            folder_path=dpo_dir,
            repo_id=repo_id,
            path_in_repo="adapters/v1.0.0",
            commit_message="Release v1.0.0: Sovereign Qwen 2.5 3B UrduLish SFT+DPO Aligned Adapter"
        )
        print("Adapter upload completed.")
    else:
        print(f"Warning: Adapter directory {dpo_dir} not found.")

    # 3. Upload Quantized GGUF Model
    gguf_dir = os.path.abspath("zarya_qwen2.5_3b_q4km_gguf")
    if os.path.exists(gguf_dir):
        print(f"Uploading 4-bit Q4_K_M quantized model from {gguf_dir}...")
        api.upload_folder(
            folder_path=gguf_dir,
            repo_id=repo_id,
            path_in_repo="quantized_gguf/v1.0.0",
            commit_message="Release v1.0.0: 4-bit Q4_K_M GGUF model for CPU/Edge serving"
        )
        print("Quantized GGUF model upload completed.")

    print("\nAll model artifacts successfully published to Hugging Face Hub!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Push Zarya Bank model to Hugging Face")
    parser.add_argument("--repo-id", type=str, default="Zarya-Bank/qwen2.5-3b-urdulish-sovereign", help="Target HF Repo ID")
    parser.add_argument("--token", type=str, default=os.getenv("HUGGING_FACE_TOKEN", ""), help="Hugging Face Write Token")
    args = parser.parse_args()

    if not args.token:
        print("Note: Provide your Hugging Face write token via --token <TOKEN> or set HUGGING_FACE_TOKEN in .env")
    else:
        push_model(args.repo_id, args.token)
