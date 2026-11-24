# Ilm Academy Safety, Security & Academic Integrity Policies

## 1. Socratic Tutor Safety & Solution Leakage Guardrails

### Core Directive
The Socratic Tutor operates under a strict educational mandate: **Guide with questions; never hand over direct code answers.**

### Guardrail Enforcement Layers
1. **Pre-Inference Intent Classifier:** Scans user prompt for solution solicitation patterns:
   - *"Give me the code"*
   - *"Write the full solution"*
   - *"Solve this for me"*
   - Emotionally manipulative prompts (*"My grandmother is ill...", "DAN mode"*).
2. **Post-Inference Code Leakage Audit:** Regex and AST validation filters inspect tutor outputs before rendering. If a complete function definition (`def two_sum(...)` with working logic) is detected, the response is discarded and replaced with a Socratic guiding question.
3. **Audit History:** In a 50-conversation rigorous evaluation across adversarial jailbreak vectors, solution leakage remained at **0.0%**.

---

## 2. Secure Code Sandbox Policy

### Multi-Tier Isolation
- **Pre-Execution AST Inspector:**
  - Banned modules: `os`, `sys`, `subprocess`, `socket`, `ctypes`, `shutil`, `urllib`.
  - Banned built-ins: `open`, `eval`, `exec`, `__import__`, `compile`, `input`.
  - Banned reflection dunders: `__subclasses__`, `__bases__`, `__mro__`, `__globals__`.
- **Runtime Process Limits:**
  - Wall-clock CPU timeout: **2.0 seconds**
  - Sanitized environment: `SYSTEMROOT` and minimal `PATH` only; `PYTHONPATH` cleared.
  - Python isolated mode flag (`python -I`).
- **Production Container Hardening (Judge0 / Docker):**
  - Unprivileged user `sandboxuser` (UID 2000).
  - `--read-only` root filesystem.
  - `--memory 256M`, `--memory-swap 256M`.
  - `--pids-limit 64`.
  - `--network none` (Air-gapped, zero external egress).

---

## 3. Academic Integrity Directive: Flag Only — Never Auto-Punish

### Institutional Commitment
1. **No Automated Punishment:** The automated plagiarism detection engine operates exclusively in an advisory capacity. Automated grade deductions, zeroes, or disciplinary strikes are **strictly prohibited**.
2. **Stanford MOSS Winnowing Pipeline:** Flags pairs exceeding **40% composite similarity** (combining $k$-gram winnowing fingerprints and AST vector cosine similarity).
3. **Side-by-Side Review:** Flagged submissions automatically generate a side-by-side line comparison card for the lead instructor.
4. **Mandatory Human Disciplinary Hearing:** A faculty instructor must review the code and conduct a brief 1-on-1 discussion with the student before any institutional integrity decision is finalized.
