/**
 * City Care Clinics — Patient Floating Chatbot Client
 * Handles:
 * 1. Open/Close floating chat modal.
 * 2. Sequential turn-by-turn conversational intake in UrduLish / English.
 * 3. Real-time message bubbles and typing indicator.
 * 4. Slot booking and confirmation email notification.
 */

const sessionId = "sess_" + Math.random().toString(36).substring(2, 10);
let isChatOpen = false;
let isIntakeComplete = false;

// DOM Elements
const launcherBtn = document.getElementById("chatLauncherBtn");
const chatWindow = document.getElementById("chatWindow");
const closeChatBtn = document.getElementById("closeChatBtn");
const chatBody = document.getElementById("chatBody");
const chatInput = document.getElementById("chatInput");
const sendChatBtn = document.getElementById("sendChatBtn");
const widgetFileInput = document.getElementById("widgetFileInput");
const widgetAttachBtn = document.getElementById("widgetAttachBtn");

// Toggle Chat Window
function toggleChat() {
  isChatOpen = !isChatOpen;
  if (isChatOpen) {
    chatWindow.classList.add("open");
    launcherBtn.style.display = "none";
    chatInput.focus();
    // Load initial greeting if empty
    if (chatBody.children.length === 0) {
      appendMessage("assistant", "Assalam-o-Alaikum! City Care Clinics mein khushamdeed. Main aap ki AI clinic assistant hoon. Yeh appointment aap apne liye book kar rahe hain ya kisi bache, walidain ya ghar ke fard ke liye?\n\n*(Agar aap ke paas koi lab report hai to aap niche diye gaye paperclip 📎 icon se attach kar saktay hain.)*");
    }
  } else {
    chatWindow.classList.remove("open");
    launcherBtn.style.display = "flex";
  }
}

if (launcherBtn) launcherBtn.addEventListener("click", toggleChat);
if (closeChatBtn) closeChatBtn.addEventListener("click", toggleChat);

// Append message bubble with formatting support
function appendMessage(role, text) {
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble bubble-${role}`;
  
  // Format bold **text** and backticks `code`
  let formatted = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, "<br>");
    
  bubble.innerHTML = formatted;
  chatBody.appendChild(bubble);
  chatBody.scrollTop = chatBody.scrollHeight;
}

// Show/Hide typing indicator
let typingIndicatorElem = null;

function showTyping() {
  if (typingIndicatorElem) return;
  typingIndicatorElem = document.createElement("div");
  typingIndicatorElem.className = "typing-indicator";
  typingIndicatorElem.innerHTML = `
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
  `;
  chatBody.appendChild(typingIndicatorElem);
  chatBody.scrollTop = chatBody.scrollHeight;
}

function hideTyping() {
  if (typingIndicatorElem) {
    typingIndicatorElem.remove();
    typingIndicatorElem = null;
  }
}

// Send user message to FastAPI backend
async function sendUserMessage() {
  const text = chatInput.value.trim();
  if (!text) return;

  appendMessage("user", text);
  chatInput.value = "";
  chatInput.disabled = true;
  sendChatBtn.disabled = true;
  showTyping();

  try {
    const res = await fetch("/api/chat/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        message: text,
        patient_name: "Patient",
        recipient_email: "samiworkspace11@gmail.com"
      })
    });

    const data = await res.json();
    hideTyping();

    if (data.message) {
      appendMessage("assistant", data.message);
    }

    if (data.is_complete) {
      isIntakeComplete = true;
    }
  } catch (err) {
    hideTyping();
    appendMessage("assistant", "⚠️ Takneeki masla pesh aaya hai. Baraye meherbani dubara koshish karein.");
  } finally {
    chatInput.disabled = false;
    sendChatBtn.disabled = false;
    chatInput.focus();
  }
}

if (sendChatBtn) sendChatBtn.addEventListener("click", sendUserMessage);
if (chatInput) {
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      sendUserMessage();
    }
  });
}

// Lab Report Attachment Handling in Floating Widget
if (widgetAttachBtn && widgetFileInput) {
  widgetAttachBtn.addEventListener("click", () => {
    widgetFileInput.click();
  });

  widgetFileInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    appendMessage("user", `📎 Attached File: <strong>${file.name}</strong> (${(file.size / 1024).toFixed(1)} KB)`);
    showTyping();

    const formData = new FormData();
    formData.append("file", file);
    formData.append("session_id", sessionId);

    try {
      const res = await fetch("/api/chat/upload-lab-report", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      hideTyping();

      if (data.status === "success" && data.chat_message) {
        appendMessage("assistant", data.chat_message);

        // If human approval is required, poll for doctor review
        if (data.requires_approval && data.approval_id) {
          startApprovalPolling(data.approval_id);
        }
      } else {
        appendMessage("assistant", "⚠️ Report parse nahi ho saki. Baraye meherbani saaf PDF ya tasweer upload karein.");
      }
    } catch (err) {
      hideTyping();
      appendMessage("assistant", "⚠️ File upload karne mein masla pesh aaya.");
    } finally {
      e.target.value = "";
    }
  });

  function startApprovalPolling(approvalId) {
    let pollCount = 0;
    const maxPolls = 60; // poll for up to 3 minutes
    const pollInterval = setInterval(async () => {
      pollCount++;
      if (pollCount > maxPolls) {
        clearInterval(pollInterval);
        return;
      }

      try {
        const res = await fetch(`/api/chat/approval-status/${approvalId}`);
        if (!res.ok) return;
        const statusData = await res.json();

        if (statusData.status === "approved" || statusData.status === "edited") {
          clearInterval(pollInterval);
          const approvedMsg = `
            <div style="background: rgba(16, 185, 129, 0.08); border-left: 4px solid #10b981; padding: 12px; border-radius: 6px; margin-top: 8px;">
              <div style="font-weight: 700; color: #059669; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                ✅ <span>Doctor Verified & Approved / ڈاکٹر کی تصدیق</span>
              </div>
              <div style="font-size: 0.82rem; color: #64748b; margin-bottom: 8px;">Reviewed by: <strong>${statusData.doctor_name || "Attending Physician"}</strong></div>
              <div style="font-size: 0.95rem; line-height: 1.5; color: #1e293b;">${statusData.final_explanation || statusData.proposed_message}</div>
              ${statusData.doctor_notes ? `<div style="margin-top: 8px; font-size: 0.85rem; background: white; padding: 8px; border-radius: 4px; border: 1px dashed #cbd5e1;"><strong>Doctor's Clinical Note:</strong> ${statusData.doctor_notes}</div>` : ''}
            </div>
          `;
          appendMessage("assistant", approvedMsg);
        } else if (statusData.status === "rejected") {
          clearInterval(pollInterval);
          appendMessage("assistant", `❌ Attending Doctor reviewed this report and declined automatic summary release. Please consult directly during your clinical appointment. ${statusData.doctor_notes ? '<br>Note: ' + statusData.doctor_notes : ''}`);
        }
      } catch (err) {
        console.error("Polling error", err);
      }
    }, 3000);
  }
}

