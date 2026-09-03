import os
import re
import time
from typing import Generator, List, Dict, Any, Optional
from config import config

class DualLLMClient:
    def __init__(self):
        self.gemini_key = config.GEMINI_API_KEY
        self.groq_key = config.GROQ_API_KEY
        self.gemini_model = config.GEMINI_MODEL
        self.groq_model = config.GROQ_MODEL
        
        self.gemini_client = None
        self.groq_client = None

        self._init_clients()

    def _init_clients(self):
        # 1. Initialize Gemini if actual key is provided
        if self.gemini_key and "your_" not in self.gemini_key and len(self.gemini_key) > 15:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.gemini_key)
            except Exception as e:
                print(f"[LLM Client] Gemini SDK Init Warning: {e}")
                self.gemini_client = None

        # 2. Initialize Groq if actual key is provided
        if self.groq_key and "your_" not in self.groq_key and len(self.groq_key) > 15:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_key)
            except Exception as e:
                print(f"[LLM Client] Groq SDK Init Warning: {e}")
                self.groq_client = None

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.6,
        stream: bool = False
    ) -> Any:
        """
        Attempts primary generation via Google Gemini.
        Falls back to Groq if Gemini fails or key is unconfigured.
        Falls back to context-aware mock generator if both keys are unconfigured.
        """
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        # Strategy 1: Primary - Google Gemini
        if self.gemini_client:
            try:
                if stream:
                    return self._stream_gemini(messages, system_prompt, temperature)
                else:
                    return self._sync_gemini(messages, system_prompt, temperature)
            except Exception as e:
                print(f"[LLM Client] Primary Gemini call failed ({e}). Falling back to Groq...")

        # Strategy 2: Backup - Groq
        if self.groq_client:
            try:
                if stream:
                    return self._stream_groq(full_messages, temperature)
                else:
                    return self._sync_groq(full_messages, temperature)
            except Exception as e:
                print(f"[LLM Client] Backup Groq call failed ({e}). Falling back to Mock generator...")

        # Strategy 3: Context-Aware Fallback Generator
        if stream:
            return self._stream_mock(messages, system_prompt)
        else:
            return self._sync_mock(messages, system_prompt)

    def _sync_gemini(self, messages: List[Dict[str, str]], system_prompt: str, temperature: float) -> str:
        prompt_parts = [system_prompt]
        for m in messages:
            prompt_parts.append(f"{m['role'].upper()}: {m['content']}")
        prompt_text = "\n\n".join(prompt_parts)
        
        models_to_try = [self.gemini_model, "gemini-2.5-flash", "gemini-1.5-flash"]
        last_exc = None
        
        for m_name in models_to_try:
            try:
                chat = self.gemini_client.chats.create(
                    model=m_name,
                    config={"temperature": temperature}
                )
                response = chat.send_message(prompt_text)
                return response.text.strip()
            except Exception as e:
                last_exc = e
                continue
                
        raise last_exc or Exception("Gemini generation failed")

    def _stream_gemini(self, messages: List[Dict[str, str]], system_prompt: str, temperature: float) -> Generator[str, None, None]:
        prompt_parts = [system_prompt]
        for m in messages:
            prompt_parts.append(f"{m['role'].upper()}: {m['content']}")
        prompt_text = "\n\n".join(prompt_parts)

        models_to_try = [self.gemini_model, "gemini-2.5-flash", "gemini-1.5-flash"]
        
        for m_name in models_to_try:
            try:
                chat = self.gemini_client.chats.create(
                    model=m_name,
                    config={"temperature": temperature}
                )
                response = chat.send_message_stream(prompt_text)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                return
            except Exception:
                continue

        fallback_text = self._sync_mock(messages, system_prompt)
        for w in fallback_text.split(" "):
            yield w + " "
            time.sleep(0.04)

    def _sync_groq(self, messages: List[Dict[str, str]], temperature: float) -> str:
        response = self.groq_client.chat.completions.create(
            model=self.groq_model,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()

    def _stream_groq(self, messages: List[Dict[str, str]], temperature: float) -> Generator[str, None, None]:
        response = self.groq_client.chat.completions.create(
            model=self.groq_model,
            messages=messages,
            temperature=temperature,
            stream=True
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _sync_mock(self, messages: List[Dict[str, str]], system_prompt: str = "") -> str:
        """
        Intelligent context-aware female fallback generator when API keys are not configured.
        Parses system_prompt to extract retrieved SQL properties and legal documents.
        """
        last_msg = messages[-1]["content"].lower() if messages else ""

        # 0. Out-of-Coverage City Handling (Multan, Peshawar, Rawalpindi, etc.)
        if "OUT-OF-COVERAGE CITY REQUESTED" in system_prompt or any(w in last_msg for w in ["multan", "peshawar", "faisalabad", "rawalpindi", "pindi", "quetta", "sialkot"]):
            return "Acha... filhal mere paas sirf Lahore, Islamabad, aur Karachi ka data available hai. Mujhay batayein agar aap ko in cities ke baaray mein information chahiye?"

        # 1. Fresh Call / No City Specified Yet
        if "NO CITY SPECIFIED YET" in system_prompt or any(w in last_msg for w in ["who is speaking", "who are you", "kon", "kaun", "assalam", "hello", "hi", "salam"]):
            return "Assalam-o-Alaikum sir! RealEstate Hub se Zara baat kar rahi hoon. Main RealEstate Hub ki AI Sales Executive hoon. Aap ka preferred budget aur city (Lahore, Islamabad, ya Karachi) kaun sa hai?"

        # 2. Buy vs Rent Clarification check when purpose is unstated
        if "PURPOSE NOT SPECIFIED" in system_prompt and not any(w in last_msg for w in ["buy", "khareedna", "rent", "kiraya", "sale"]):
            return "Acha... property dekh rahe hain sir! Ji bilkul, kya aap property khareedna (Buy) chahte hain ya rent (Kiraya) par lena chahte hain sir?"

        # 3. Document / Transfer / Legal query detection
        if "document" in last_msg or "transfer" in last_msg or "paper" in last_msg or "noc" in last_msg or "legal" in last_msg or "requirement" in last_msg:
            if "dha transfer" in system_prompt.lower() or "cnic copies" in system_prompt.lower():
                return "Ji bilkul sir! DHA transfer ke liye CNIC copies, Allotment Letter, NDC (No Demand Certificate), aur tax paid challans darkaar hotay hain. Direct owner transfer 3 se 5 working days mein ho jata hai. Main hamare Senior Manager Shehryar Khan (+92-321-9988112) se aap ki meeting fix karwa deti hoon?"
            else:
                return "Ji bilkul sir! Property transfer ke liye Allotment letter, CNIC copies, NDC (No Demand Certificate), aur tax challan documents zaroori hotay hain. Main aap ko mazeed details bata sakti hoon."

        # 4. Installments / Payment Plan queries ("اقساط کا پلان کیا ہے")
        if "installment" in last_msg or "installments" in last_msg or "down payment" in last_msg or "qist" in last_msg:
            return "Ji bilkul sir! Hamare paas flexible 3-year installment plans available hain. 25% down payment par booking ho jati hai aur 18 months mein physical possession mil jati hai. Full cash payment par 10% se 15% tak upfront discount bhi mil sakta hai."

        # 5. Extract retrieved property matches from system_prompt
        options = re.findall(r'Option \d+:\s*(.*?)\n\s*-\s*Price:\s*(.*?)\n\s*-\s*Location:\s*(.*?)\n\s*-\s*Details:\s*(.*?)\n', system_prompt)
        
        if options:
            op1_title, op1_price, op1_loc, op1_det = options[0]
            if len(options) >= 2:
                op2_title, op2_price, op2_loc, op2_det = options[1]
                return f"Ji bilkul sir! {op1_loc} mein hamare paas {op1_title} available hai price {op1_price} mein. Is ke ilawa {op2_loc} mein {op2_title} price {op2_price} mein hai. Kya aap is ka site visit schedule karna chahein ge?"
            else:
                return f"Ji bilkul sir! {op1_loc} mein hamare paas {op1_title} available hai price {op1_price} mein ({op1_det}). Kya main site visit schedule kar doon?"

        # 6. Handling price objections
        if "mehnga" in last_msg or "price" in last_msg or "high" in last_msg:
            return "Hmm... dekhein sir, pehli nazar mein price lagti hai, lekin yeh prime location par hai jahan annual appreciation 15-20% hai. Is ke sath 3-year easy installment plan bhi main arrange karwa sakti hoon."

        # 7. Handling appointment visit
        if "appointment" in last_msg or "visit" in last_msg or "schedule" in last_msg or "zror" in last_msg or "g zror" in last_msg:
            return "Acha... bilkul sahi! Aap kal sham 4 baje ya Saturday morning 11 baje comfortable hain sir? Main hamare Senior Relationship Manager ki slot aap ke liye reserve kar deti hoon."

        return "Ji bilkul sir! RealEstate Hub ke paas Lahore, Islamabad aur Karachi ke prime areas mein best investment options hain. Aap ka preferred budget aur city kaun sa hai?"

    def _stream_mock(self, messages: List[Dict[str, str]], system_prompt: str = "") -> Generator[str, None, None]:
        full_text = self._sync_mock(messages, system_prompt)
        words = full_text.split(" ")
        for w in words:
            yield w + " "
            time.sleep(0.04)

llm_client = DualLLMClient()
