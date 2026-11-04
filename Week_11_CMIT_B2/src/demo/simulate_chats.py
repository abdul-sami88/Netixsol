import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from src.assistant.shopping_assistant import ShoppingAssistantTools, UrduLishShoppingAssistant

tools = ShoppingAssistantTools()
assistant = UrduLishShoppingAssistant(tools=tools)

test_chats = [
    "Assalam-o-Alaikum! Aap kya kar sakte hain?",
    "football",
    "Ammi ke liye Eid gift chahiye, 3000 tak.",
    "Pehla product cart mein add kardo",
    "Add to cart PROD-10016",
    "PROD-10016 kaisa hai? Reviews batayein.",
    "Mujhe achi kurti dikhayein under 4000",
    "Shoes dikhao saste wale",
    "Order status kya hai?",
    "Mera order ORD-0004466 kahan pohancha hai?",
    "Compare PROD-10016 aur PROD-11399",
    "Kuch trending products recommend karein",
    "Koi acha laptop mil sakta hai?",
    "cricket bat",
    "Shukriya bohot bohot"
]

print("=" * 75)
print("   SIMULATING 15 USER CHATS WITH SHOPPING ASSISTANT")
print("=" * 75)
for idx, q in enumerate(test_chats, 1):
    print(f"\n[{idx}/15] 🗣️ User: \"{q}\"")
    reply = assistant.chat(q, user_id="USR-00746")
    print(f"🤖 Assistant:\n{reply}")
