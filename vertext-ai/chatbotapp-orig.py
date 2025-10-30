import re
import base64
import google.generativeai as genai
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn

# --- Gemini API Key ---
genai.configure(api_key="")

# --- System Prompt ---
SYSTEM_PROMPT = """
You are a helpful, friendly assistant supporting someone who is filling out a digital wellness form. The person you're helping may not be technical — they could be office staff or operators. Your job is to guide them through just **one field at a time**, using simple, clear language.

You are currently helping with the field: "{current_field}"

You have access to:
- The user’s latest message: "{chat_input}"
- The current field being completed: "{current_field}"
- Previous answers they've provided: {form_answers}
- The full chat history so far: {chat_history}

---

How to help:

- Briefly explain what the current field means in everyday language.
- Use clues from previous answers if helpful.
- Ask **one small, clear follow-up question** to help them move forward.
- Use real-world hints (labels, stickers, screen names).
- Be warm and relaxed — like a helpful coworker.
- Avoid jargon unless necessary — and explain it simply.

---

If the user gives a possible or partial answer (like “CentOS” or “DL360” or “physical”):

- Acknowledge it clearly and kindly.
- Repeat their **exact wording and capitalization**.
- Suggest that as the value for the current field.
- Ask them to confirm it with this format:

  ➤ “If that’s correct, please confirm by typing: Yes, it is CentOS”

---

Confirmation handling:

- If the user replies with:
  - “Yes”, “Yup”, “Sure”, “Correct”, “Right”, “Yeah”, “Ok”

→ Treat that as full confirmation.
→ Don’t ask again.
→ End the session with:

  ➤ “Perfect — I’ve marked the {current_field} as CentOS. That’s all for this one. Thanks!”

*(Replace “CentOS” with confirmed value)*

---

If the user says “maybe”, “not sure”, etc.:

- Help them think it through
- Offer a likely answer
- Ask them to confirm it again, same format

---

If user is confused:

- Simplify again
- Give one small example
- Be calm and encouraging

---

Greeting handling:

- If user starts with “hi” or “hello”:
  ➤ “Hi there! Would you like help understanding the '{current_field}' field?”

---

Off-topic:

- If user talks about unrelated stuff:
  ➤ “That’s interesting, but I’m here to help with the ‘{current_field}’ field on the form — happy to help whenever you're ready!”

---

Uncertainty loop:

- If user gives 3+ “I don’t know”/“not sure”:
  ➤ “Totally understandable — it’s not always easy to tell. You might check with someone in your IT team. We can mark this one as ‘unknown’ for now.”

---

Stop session after:

- User confirms
- 15 turns without confirmation:
  ➤ “Looks like we couldn’t finish the '{current_field}' field. You might want to check with someone on your IT team.”

---

🗂️ Field Reference:

- **System Name** – Name given to the server (e.g., “Factory Control Server”)
- **Type (Physical/Virtual)** – A physical box vs. a virtual one (e.g., Azure, VMware)
- **Model** – Code like “DL380 Gen11” or “Standard B2s”
- **Provider** – Who made the system (HP, Dell, Siemens)
- **Operating System** – Windows, Ubuntu, VMware, etc.
- **IP Address** – A number like 192.168.1.5
- **Network Gateway** – A number like 10.5.1.254
- **Exposed on Internet** – Is it accessible outside?
- **Used on IT Network** – Is it used inside your company?
- **Automated Discovery** – Was it detected automatically?
- **Backup** – When and how often it’s backed up
- **Log Retention** – How long logs are kept (90 days, 1 year)
- **Description** – Sentence like “Used for CCTV storage”
- **Network Card / Port** – “eth0”, “LAN Port 1”

Your job is to help with this one field. Be warm, clear, and calm.
"""


# --- Utils ---
def user_confirmed(text: str) -> bool:
    confirmations = ["yes", "yeah", "yup", "sure", "correct", "right", "ok"]
    return any(word in text.lower() for word in confirmations)

def bot_is_asking_confirmation(bot_reply: str) -> bool:
    return "please confirm by typing" in bot_reply.lower()

# --- Core Logic ---
def chat_node(chat_input: str, current_field: str, form_answers: Dict[str, Any],
              chat_history: List[Dict[str, str]], is_image: bool = False,
              chat_image: Optional[str] = None, is_confirming: bool = False,
              pending_value: Optional[str] = None):

    try:
        # ✅ If confirming and user said yes
        if is_confirming and user_confirmed(chat_input) and pending_value:
            assistant_reply = f"Perfect — I’ve marked the {current_field} as {pending_value}. That’s all for this one. Thanks!"
            chat_history.append({"role": "user", "content": chat_input})
            chat_history.append({"role": "assistant", "content": assistant_reply})

            return {
                "assistant_reply": assistant_reply,
                "chat_history": chat_history,
                "is_confirming": False,
                "pending_value": None,
                "session_complete": True
            }

        # --- Build prompt ---
        formatted_prompt = SYSTEM_PROMPT.format(
            chat_input=chat_input,
            current_field=current_field,
            form_answers=form_answers,
            chat_history=chat_history
        )
        prompt = formatted_prompt + f"\nUser: {chat_input}\nAssistant:"

        # --- Call Gemini ---
        model = genai.GenerativeModel("gemini-1.5-pro")

        if is_image and chat_image:
            image_bytes = base64.b64decode(chat_image)
            response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_bytes}])
        else:
            response = model.generate_content(prompt)

        assistant_reply = response.text.strip()

        # --- Update chat history ---
        chat_history.append({"role": "user", "content": chat_input})
        chat_history.append({"role": "assistant", "content": assistant_reply})

        # --- Detect confirmation ---
        is_now_confirming = bot_is_asking_confirmation(assistant_reply)

        next_pending_value = None
        if is_now_confirming:
            match = re.search(r"it is (.*?)(?:[.\n]|$)", assistant_reply, re.IGNORECASE)
            if match:
                next_pending_value = match.group(1).strip()

        # --- Detect session end ---
        session_complete = any(
            phrase in assistant_reply.lower()
            for phrase in ["that’s all for this one", "marked the", "we can mark this one as", "thanks for giving it a shot"]
        )

        return {
            "assistant_reply": assistant_reply,
            "chat_history": chat_history,
            "is_confirming": is_now_confirming,
            "pending_value": next_pending_value,
            "session_complete": session_complete
        }

    except Exception as e:
        return {
            "assistant_reply": f"❌ Error: {str(e)}",
            "chat_history": chat_history,
            "is_confirming": False,
            "pending_value": None,
            "session_complete": False
        }

# --- FastAPI App ---
app = FastAPI()

class ChatRequest(BaseModel):
    chat_input: str
    current_field: str
    form_answers: Dict[str, Any]
    chat_history: List[Dict[str, str]] = []
    is_image: bool = False
    chat_image: Optional[str] = None
    is_confirming: bool = False
    pending_value: Optional[str] = None

@app.get("/status")
def status():
    return {"status": "ok"}

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    return chat_node(
        chat_input=req.chat_input,
        current_field=req.current_field,
        form_answers=req.form_answers,
        chat_history=req.chat_history,
        is_image=req.is_image,
        chat_image=req.chat_image,
        is_confirming=req.is_confirming,
        pending_value=req.pending_value
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)