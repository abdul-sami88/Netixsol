/**
 * City Care Clinics — Attending Physician Dashboard Client
 * Enforces:
 * 1. Strict Doctor Authentication check.
 * 2. Patient Isolation: Renders ONLY patients assigned to the logged-in doctor.
 * 3. Human-in-the-Loop Approval Action handling.
 */

let currentDoctor = null;
let allDoctorPatients = [];

async function initDashboard() {
  try {
    // 1. Verify Authentication
    const meRes = await fetch("/api/doctor/me");
    if (!meRes.ok) {
      window.location.href = "/doctor-login";
      return;
    }

    currentDoctor = await meRes.json();
    renderDoctorProfile(currentDoctor);

    // 2. Fetch Assigned Patients (Isolated to this doctor)
    await loadDoctorPatients();

    // 3. Fetch Pending Approvals
    await loadDoctorApprovals();
  } catch (err) {
    console.error("Dashboard error:", err);
    window.location.href = "/doctor-login";
  }
}

function renderDoctorProfile(doc) {
  document.getElementById("docNameDisplay").innerText = doc.name;
  document.getElementById("docSpecialtyDisplay").innerText = `${doc.specialty} • PMDC: ${doc.pmdc}`;
  document.getElementById("docEmailDisplay").innerText = doc.email;
  document.getElementById("docInitials").innerText = doc.name.split(" ").map(n => n[0]).join("").substring(1, 3);
}

// Fetch only patients checked up by this doctor
async function loadDoctorPatients() {
  const res = await fetch("/api/doctor/patients");
  if (!res.ok) return;

  const data = await res.json();
  allDoctorPatients = data.patients || [];

  document.getElementById("statTotalPatients").innerText = data.total_patients_checked || 0;
  document.getElementById("statTotalConsultations").innerText = data.total_appointments || 0;

  renderPatientsTable(allDoctorPatients);
}

function renderPatientsTable(patients) {
  const tbody = document.getElementById("patientsTableBody");
  tbody.innerHTML = "";

  if (patients.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:32px; color:#64748b;">No patients found for your account.</td></tr>`;
    return;
  }

  patients.forEach((item, idx) => {
    const pat = item.patient;
    const urgency = item.urgency_tier || "ROUTINE";
    const badgeClass = urgency === "EMERGENCY" ? "badge-emergency" : (urgency === "URGENT" ? "badge-urgent" : "badge-routine");

    const isYetToCome = item.status === "booked";
    const statusBadge = isYetToCome
      ? `<span style="background:rgba(234, 179, 8, 0.12); color:#b45309; padding:3px 8px; border-radius:9999px; font-weight:700; font-size:11.5px; border:1px solid #fde68a; display:inline-block;">⏳ Yet to Come</span>`
      : `<span style="background:rgba(16, 185, 129, 0.12); color:#047857; padding:3px 8px; border-radius:9999px; font-weight:700; font-size:11.5px; border:1px solid #a7f3d0; display:inline-block;">✅ Checkup Done</span>`;

    const row = document.createElement("tr");
    row.innerHTML = `
      <td><strong>${item.token_number}</strong></td>
      <td>
        <div style="font-weight:600; color:#0f172a;">${pat.name}</div>
        <div style="font-size:12px; color:#64748b;">${pat.gender} • Blood: ${pat.blood_group || "N/A"}</div>
      </td>
      <td><code>${pat.cnic}</code></td>
      <td>${pat.phone}</td>
      <td>${item.appointment_date}</td>
      <td>${statusBadge}</td>
      <td><span class="badge-tag ${badgeClass}">${urgency}</span></td>
      <td>
        <div style="font-weight:500;">${item.chief_complaint}</div>
        <div style="font-size:12px; color:#64748b;">${item.clinical_notes}</div>
      </td>
      <td style="text-align:center;">
        <div style="display:flex; justify-content:center; gap:6px; flex-wrap:wrap;">
          <button onclick="openSoapModal('${pat.id}', '${item.appointment_id || ''}', '${escapeJsStr(pat.name)}')" style="background:#4f46e5; color:white; border:none; padding:5px 9px; border-radius:6px; cursor:pointer; font-size:12px; font-weight:600; display:inline-flex; align-items:center; gap:4px; box-shadow:0 1px 2px rgba(0,0,0,0.05); transition:0.2s;" title="Clinical Summary Agent Pre-Visit SOAP Note">
            <span>📝</span> SOAP
          </button>
          <button onclick="openRecordsQaModal('${pat.id}', '${escapeJsStr(pat.name)}')" style="background:#0284c7; color:white; border:none; padding:5px 9px; border-radius:6px; cursor:pointer; font-size:12px; font-weight:600; display:inline-flex; align-items:center; gap:4px; box-shadow:0 1px 2px rgba(0,0,0,0.05); transition:0.2s;" title="Records Agent FHIR & Lab Q&A">
            <span>💬</span> Q&A
          </button>
          <button onclick="openEhrModal('${pat.id}')" style="background:#0369a1; color:white; border:none; padding:5px 9px; border-radius:6px; cursor:pointer; font-size:12px; font-weight:600; display:inline-flex; align-items:center; gap:4px; box-shadow:0 1px 2px rgba(0,0,0,0.05); transition:0.2s;">
            <span>📁</span> EHR
          </button>
          <button onclick="openRxModal('${pat.id}', '${item.appointment_id || ''}', '${escapeJsStr(pat.name)}', '${pat.gender || ''}', '${pat.blood_group || ''}')" style="background:#0d9488; color:white; border:none; padding:5px 9px; border-radius:6px; cursor:pointer; font-size:12px; font-weight:600; display:inline-flex; align-items:center; gap:4px; box-shadow:0 1px 2px rgba(0,0,0,0.05); transition:0.2s;">
            <span>🛡️</span> Prescribe
          </button>
        </div>
      </td>
    `;
    tbody.appendChild(row);
  });
}

function escapeJsStr(str) {
  if (!str) return "";
  return str.replace(/'/g, "\\'").replace(/"/g, "&quot;");
}

function closeAllModals() {
  const ehr = document.getElementById("ehrModalOverlay");
  const rx = document.getElementById("rxSafetyModalOverlay");
  const soap = document.getElementById("soapModalOverlay");
  const qa = document.getElementById("recordsQaModalOverlay");
  if (ehr) ehr.style.display = "none";
  if (rx) rx.style.display = "none";
  if (soap) soap.style.display = "none";
  if (qa) qa.style.display = "none";
}

// --------------------------------------------------------------------------
// PATIENT MEDICAL HISTORY & EHR MODAL
// --------------------------------------------------------------------------
async function openEhrModal(patientId) {
  closeAllModals();
  const overlay = document.getElementById("ehrModalOverlay");
  overlay.style.display = "flex";

  document.getElementById("ehrPatientName").innerText = "Loading Medical Record...";
  document.getElementById("ehrPatientMeta").innerText = "Fetching EHR details from database...";
  document.getElementById("ehrConditionsList").innerHTML = "<div style='color:#64748b;'>Loading conditions...</div>";
  document.getElementById("ehrAllergiesList").innerHTML = "<div style='color:#64748b;'>Loading allergies...</div>";
  document.getElementById("ehrMedicationsList").innerHTML = "<div style='color:#64748b;'>Loading prescriptions...</div>";
  document.getElementById("ehrObservationsList").innerHTML = "<div style='color:#64748b;'>Loading lab observations...</div>";
  document.getElementById("ehrEncountersList").innerHTML = "<div style='color:#64748b;'>Loading past visits...</div>";

  try {
    const res = await fetch(`/api/doctor/patients/${patientId}/ehr`);
    if (!res.ok) throw new Error("Could not retrieve patient medical records.");

    const data = await res.json();
    const p = data.patient;

    document.getElementById("ehrPatientName").innerText = p.name;
    document.getElementById("ehrBloodGroupBadge").innerText = `🩸 ${p.blood_group || "N/A"}`;
    document.getElementById("ehrPatientMeta").innerText = 
      `${p.age ? p.age + ' yrs • ' : ''}${p.gender} • CNIC: ${p.cnic} • Phone: ${p.phone} • City: ${p.city} • Address: ${p.address}`;

    // 1. Chronic Conditions
    const condContainer = document.getElementById("ehrConditionsList");
    if (!data.chronic_diseases || data.chronic_diseases.length === 0) {
      condContainer.innerHTML = `<span style="color:#64748b; font-style:italic;">No chronic conditions documented.</span>`;
    } else {
      condContainer.innerHTML = data.chronic_diseases.map(c => `
        <div style="background:#ffffff; border:1px solid #e2e8f0; padding:8px 12px; border-radius:6px; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <strong>${c.code}</strong>
            <div style="font-size:11.5px; color:#64748b; margin-top:2px;">Status: ${c.status} • Onset: ${c.onset_date}</div>
          </div>
          <span style="font-size:11px; background:#e0f2fe; color:#0369a1; padding:2px 8px; border-radius:9999px; font-weight:600;">${c.severity}</span>
        </div>
      `).join("");
    }

    // 2. Allergies
    const allContainer = document.getElementById("ehrAllergiesList");
    if (!data.allergies || data.allergies.length === 0) {
      allContainer.innerHTML = `<span style="color:#64748b; font-style:italic;">No known allergies documented.</span>`;
    } else {
      allContainer.innerHTML = data.allergies.map(a => `
        <div style="background:#ffffff; border:1px solid #fed7aa; padding:8px 12px; border-radius:6px; display:flex; justify-content:space-between; align-items:center;">
          <strong style="color:#9a3412;">${a.allergen}</strong>
          <span style="font-size:11px; background:#fee2e2; color:#991b1b; padding:2px 8px; border-radius:9999px; font-weight:700;">${a.severity}</span>
        </div>
      `).join("");
    }

    // 3. Prescriptions
    const medContainer = document.getElementById("ehrMedicationsList");
    if (!data.prescriptions || data.prescriptions.length === 0) {
      medContainer.innerHTML = `<span style="color:#64748b; font-style:italic; font-size:13px;">No active or past prescriptions on record.</span>`;
    } else {
      medContainer.innerHTML = `
        <table style="width:100%; border-collapse:collapse; font-size:12.5px; text-align:left;">
          <thead>
            <tr style="background:#f1f5f9; color:#475569;">
              <th style="padding:8px 10px;">Brand Name</th>
              <th style="padding:8px 10px;">Generic Drug</th>
              <th style="padding:8px 10px;">Dosage Instruction</th>
              <th style="padding:8px 10px;">Status</th>
              <th style="padding:8px 10px;">Date Prescribed</th>
            </tr>
          </thead>
          <tbody>
            ${data.prescriptions.map(m => `
              <tr style="border-bottom:1px solid #f1f5f9;">
                <td style="padding:8px 10px; font-weight:600; color:#0f172a;">${m.brand_name}</td>
                <td style="padding:8px 10px; color:#64748b;">${m.medication_name}</td>
                <td style="padding:8px 10px;">${m.dosage}</td>
                <td style="padding:8px 10px;"><span class="badge-tag ${m.status === 'active' ? 'badge-routine' : 'badge-urgent'}">${m.status}</span></td>
                <td style="padding:8px 10px; color:#64748b;">${m.prescribed_date}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    }

    // 4. Observations / Lab History
    const obsContainer = document.getElementById("ehrObservationsList");
    if (!data.observations || data.observations.length === 0) {
      obsContainer.innerHTML = `<span style="color:#64748b; font-style:italic; font-size:13px;">No diagnostic observations or lab values on record.</span>`;
    } else {
      obsContainer.innerHTML = `
        <table style="width:100%; border-collapse:collapse; font-size:12.5px; text-align:left;">
          <thead>
            <tr style="background:#f1f5f9; color:#475569;">
              <th style="padding:8px 10px;">Test / Observation</th>
              <th style="padding:8px 10px;">Measured Value</th>
              <th style="padding:8px 10px;">Reference Interval</th>
              <th style="padding:8px 10px;">Clinical Flag</th>
              <th style="padding:8px 10px;">Recorded Date</th>
            </tr>
          </thead>
          <tbody>
            ${data.observations.map(o => `
              <tr style="border-bottom:1px solid #f1f5f9;">
                <td style="padding:8px 10px; font-weight:600;">${o.test_name}</td>
                <td style="padding:8px 10px;">${o.value} ${o.unit}</td>
                <td style="padding:8px 10px; color:#64748b;">${o.reference_range}</td>
                <td style="padding:8px 10px;"><span class="badge-tag ${o.interpretation === 'normal' ? 'badge-routine' : (o.interpretation === 'critical' ? 'badge-emergency' : 'badge-urgent')}">${o.interpretation.toUpperCase()}</span></td>
                <td style="padding:8px 10px; color:#64748b;">${o.issued_date}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    }

    // 5. Past Encounters
    const encContainer = document.getElementById("ehrEncountersList");
    if (!data.encounters || data.encounters.length === 0) {
      encContainer.innerHTML = `<span style="color:#64748b; font-style:italic; font-size:13px;">No past consultation history.</span>`;
    } else {
      encContainer.innerHTML = `
        <table style="width:100%; border-collapse:collapse; font-size:12.5px; text-align:left;">
          <thead>
            <tr style="background:#f1f5f9; color:#475569;">
              <th style="padding:8px 10px;">Token</th>
              <th style="padding:8px 10px;">Encounter Date</th>
              <th style="padding:8px 10px;">Urgency Tier</th>
              <th style="padding:8px 10px;">Chief Complaint</th>
              <th style="padding:8px 10px;">Clinical Notes</th>
            </tr>
          </thead>
          <tbody>
            ${data.encounters.map(e => `
              <tr style="border-bottom:1px solid #f1f5f9;">
                <td style="padding:8px 10px; font-weight:600;">${e.token_number}</td>
                <td style="padding:8px 10px; color:#64748b;">${e.date}</td>
                <td style="padding:8px 10px;"><span class="badge-tag ${e.urgency_tier === 'EMERGENCY' ? 'badge-emergency' : (e.urgency_tier === 'URGENT' ? 'badge-urgent' : 'badge-routine')}">${e.urgency_tier}</span></td>
                <td style="padding:8px 10px;">${e.chief_complaint}</td>
                <td style="padding:8px 10px; color:#475569;">${e.clinical_notes}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    }

  } catch (err) {
    document.getElementById("ehrPatientName").innerText = "Error Loading Record";
    document.getElementById("ehrPatientMeta").innerText = err.message;
  }
}

function closeEhrModal() {
  const overlay = document.getElementById("ehrModalOverlay");
  if (overlay) overlay.style.display = "none";
}


// Search filter for patient table
document.getElementById("patientSearchInput")?.addEventListener("input", (e) => {
  const query = e.target.value.toLowerCase().trim();
  const filtered = allDoctorPatients.filter(item => {
    const p = item.patient;
    return p.name.toLowerCase().includes(query) ||
           p.cnic.toLowerCase().includes(query) ||
           p.phone.toLowerCase().includes(query) ||
           (item.chief_complaint && item.chief_complaint.toLowerCase().includes(query)) ||
           item.token_number.toLowerCase().includes(query);
  });
  renderPatientsTable(filtered);
});

// Load Approvals
async function loadDoctorApprovals() {
  const res = await fetch("/api/doctor/approvals");
  if (!res.ok) return;

  const data = await res.json();
  const pending = data.pending || [];

  document.getElementById("statPendingReviews").innerText = pending.length;
  const container = document.getElementById("approvalsContainer");
  container.innerHTML = "";

  if (pending.length === 0) {
    container.innerHTML = `<div style="background:#f0fdf4; border:1px solid #bbf7d0; color:#166534; padding:16px; border-radius:10px; font-size:14px;">🎉 All clinical approvals are signed off. No pending safety flags.</div>`;
    return;
  }

  pending.forEach(appr => {
    const card = document.createElement("div");
    card.style = "background:#ffffff; border:1px solid #fed7aa; border-left:4px solid #f97316; border-radius:10px; padding:18px; margin-bottom:16px; box-shadow:0 1px 3px rgba(0,0,0,0.05); max-width:100%; box-sizing:border-box; overflow:hidden; word-break:break-word;";

    const payload = appr.payload || {};
    let contentHtml = "";

    if (appr.approval_type === "LAB_EXPLANATION") {
      const panel = payload.panel_name || "Diagnostic Laboratory Panel";
      const params = payload.parameters || [];
      const explanation = payload.urdulish_explanation || "";

      let paramRows = "";
      params.forEach(p => {
        const flag = p.flag || "NORMAL";
        let flagClass = "badge-routine";
        if (flag === "HIGH" || flag === "LOW") flagClass = "badge-urgent";
        else if (flag === "CRITICAL") flagClass = "badge-emergency";

        paramRows += `
          <tr>
            <td style="padding:6px 10px; font-weight:600; border-bottom:1px solid #f1f5f9;">${p.name}</td>
            <td style="padding:6px 10px; border-bottom:1px solid #f1f5f9;">${p.value} ${p.unit || ""}</td>
            <td style="padding:6px 10px; color:#64748b; border-bottom:1px solid #f1f5f9;">${p.reference_range || "N/A"}</td>
            <td style="padding:6px 10px; border-bottom:1px solid #f1f5f9;"><span class="badge-tag ${flagClass}">${flag}</span></td>
          </tr>
        `;
      });

      contentHtml = `
        <div style="margin:12px 0;">
          <div style="margin-bottom:8px; font-size:13.5px; font-weight:700; color:#0369a1;">
            🔬 Clinical Panel: ${panel}
          </div>
          ${params.length > 0 ? `
            <div style="overflow-x:auto; background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; margin-bottom:10px; max-width:100%;">
              <table style="width:100%; border-collapse:collapse; font-size:12.5px; text-align:left;">
                <thead>
                  <tr style="background:#f8fafc; border-bottom:1px solid #e2e8f0; color:#475569;">
                    <th style="padding:8px 10px;">Test Parameter</th>
                    <th style="padding:8px 10px;">Measured Value</th>
                    <th style="padding:8px 10px;">Reference Interval</th>
                    <th style="padding:8px 10px;">Clinical Flag</th>
                  </tr>
                </thead>
                <tbody>${paramRows}</tbody>
              </table>
            </div>
          ` : ''}
          <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; padding:12px 14px; font-size:13px; color:#166534; line-height:1.55; white-space:normal; word-break:break-word; max-width:100%;">
            <strong>💡 AI UrduLish Patient Guidance:</strong><br>
            ${explanation}
          </div>
        </div>
      `;
    } else if (appr.approval_type === "PRESCRIPTION") {
      const meds = payload.doctor_draft_prescription || payload.medications || [];
      const alerts = payload.alerts || [];
      let medsHtml = Array.isArray(meds) 
        ? meds.map(m => `• <strong>${m.drug_name || m.name || m}</strong>: ${m.dose || m.dosage || ''}`).join('<br>') 
        : JSON.stringify(meds, null, 2);

      contentHtml = `
        <div style="margin:12px 0; font-size:13px; white-space:normal; word-break:break-word; max-width:100%;">
          <strong>Draft Medications:</strong>
          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px; margin-top:6px; line-height:1.5;">${medsHtml}</div>
          ${alerts.length > 0 ? `<div style="color:#b91c1c; font-weight:600; margin-top:8px;">⚠️ Safety Contraindications: ${alerts.join(", ")}</div>` : ''}
        </div>
      `;
    } else {
      contentHtml = `<pre style="background:#f8fafc; border:1px solid #e2e8f0; padding:10px; border-radius:8px; font-size:12px; margin:8px 0; white-space:pre-wrap; word-break:break-word; overflow-x:auto; max-width:100%;">${JSON.stringify(payload, null, 2)}</pre>`;
    }

    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
        <span style="background:#fee2e2; color:#991b1b; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:700;">${appr.approval_type}</span>
        <span style="font-size:12px; color:#64748b;">ID: ${appr.approval_id}</span>
      </div>
      <h4 style="margin:10px 0 4px 0; font-size:15px; color:#0f172a;">Patient: ${appr.patient_name} (${appr.patient_id})</h4>
      ${contentHtml}
      <div style="margin-top:14px; display:flex; flex-wrap:wrap; gap:10px; align-items:center;">
        <input type="text" id="notes_${appr.approval_id}" placeholder="Doctor clinical rationale..." style="flex:1; min-width:200px; padding:8px 12px; border:1px solid #cbd5e1; border-radius:6px; font-size:13px;">
        <button onclick="submitApproval('${appr.approval_id}', 'APPROVE')" style="background:#16a34a; color:white; border:none; padding:8px 16px; border-radius:6px; cursor:pointer; font-weight:600; font-size:13px; white-space:nowrap;">Approve</button>
        <button onclick="submitApproval('${appr.approval_id}', 'EDIT')" style="background:#0284c7; color:white; border:none; padding:8px 16px; border-radius:6px; cursor:pointer; font-weight:600; font-size:13px; white-space:nowrap;">Edit Order</button>
        <button onclick="submitApproval('${appr.approval_id}', 'REJECT')" style="background:#dc2626; color:white; border:none; padding:8px 16px; border-radius:6px; cursor:pointer; font-weight:600; font-size:13px; white-space:nowrap;">Reject</button>
      </div>
    `;
    container.appendChild(card);
  });
}

async function submitApproval(approvalId, action) {
  const notesInput = document.getElementById(`notes_${approvalId}`);
  const notes = notesInput ? notesInput.value : "";

  let editedPayload = null;
  if (action === "EDIT") {
    const newDrug = prompt("Enter replacement medication / rationale:", "Klaricid 500mg bd (Penicillin allergy substitution)");
    if (!newDrug) return;
    editedPayload = { substitute_order: newDrug };
  }

  try {
    const res = await fetch(`/api/doctor/approvals/${approvalId}/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: action,
        notes: notes,
        edited_payload: editedPayload
      })
    });
    if (res.ok) {
      alert(`Approval ${approvalId} marked as ${action}!`);
      await loadDoctorApprovals();
    }
  } catch (err) {
    alert("Error submitting decision: " + err);
  }
}

// Logout
async function doctorLogout() {
  await fetch("/api/auth/logout", { method: "POST" });
  window.location.href = "/doctor-login";
}

// --------------------------------------------------------------------------
// PRESCRIPTION SAFETY AGENT (DAY 2 ENGINE)
// --------------------------------------------------------------------------
let activeRxPatient = null;

async function openRxModal(patientId, appointmentId, patientName, gender, blood) {
  closeAllModals();
  activeRxPatient = {
    id: patientId,
    appointmentId: appointmentId,
    name: patientName,
    gender: gender
  };

  const overlay = document.getElementById("rxSafetyModalOverlay");
  overlay.style.display = "flex";

  document.getElementById("rxPatientName").innerText = patientName || patientId;
  document.getElementById("rxPatientMeta").innerText = `ID: ${patientId} • ${gender || 'Patient'} • Blood: ${blood || 'N/A'}`;
  document.getElementById("rxDocumentedAllergies").innerHTML = "<span style='color:#64748b;'>Checking EHR records...</span>";
  document.getElementById("rxActiveMedications").innerHTML = "<span style='color:#64748b;'>Checking active prescriptions...</span>";
  
  // Clear inputs and results
  document.getElementById("draftDrugName").value = "";
  document.getElementById("draftDosage").value = "";
  document.getElementById("draftIsPregnant").checked = false;
  document.getElementById("draftIsLactating").checked = false;
  document.getElementById("rxSafetyResultsBox").style.display = "none";
  document.getElementById("rxSafetyResultsBox").innerHTML = "";
  
  const signBtn = document.getElementById("btnSignPrescription");
  signBtn.disabled = true;
  signBtn.style.background = "#cbd5e1";
  signBtn.style.color = "#64748b";
  signBtn.style.cursor = "not-allowed";

  // Fetch patient EHR to show context
  try {
    const res = await fetch(`/api/doctor/patients/${patientId}/ehr`);
    if (res.ok) {
      const ehr = await res.json();
      const allergies = ehr.allergies || [];
      const meds = ehr.prescriptions || [];

      if (allergies.length > 0) {
        document.getElementById("rxDocumentedAllergies").innerHTML = allergies.map(a => 
          `<span style="background:#fee2e2; color:#b91c1c; padding:2px 6px; border-radius:4px; font-weight:700; display:inline-block; margin-right:4px;">⚠️ ${a.allergen || a.display || a.code}</span>`
        ).join(" ");
      } else {
        document.getElementById("rxDocumentedAllergies").innerHTML = "<span style='color:#059669; font-weight:600;'>✅ No known drug allergies documented</span>";
      }

      if (meds.length > 0) {
        document.getElementById("rxActiveMedications").innerHTML = meds.map(m => 
          `<span style="background:#e0f2fe; color:#0369a1; padding:2px 6px; border-radius:4px; font-weight:600; display:inline-block; margin-right:4px;">💊 ${m.brand_name || m.medication_name} (${m.dosage || ''})</span>`
        ).join(" ");
      } else {
        document.getElementById("rxActiveMedications").innerHTML = "<span style='color:#64748b;'>No active prescriptions on file</span>";
      }
    }
  } catch (err) {
    console.error("Error fetching patient EHR for Rx modal:", err);
  }
}

function closeRxModal() {
  document.getElementById("rxSafetyModalOverlay").style.display = "none";
}

async function runSafetyEngineCheck() {
  if (!activeRxPatient) return;

  const drugName = document.getElementById("draftDrugName").value.trim();
  const dosage = document.getElementById("draftDosage").value.trim();
  const frequency = document.getElementById("draftFrequency").value;
  const isPregnant = document.getElementById("draftIsPregnant").checked;
  const isLactating = document.getElementById("draftIsLactating").checked;

  if (!drugName) {
    alert("Please enter a drug or brand name to test safety (e.g. Augmentin, Amoxicillin, Panadol, Brufen).");
    return;
  }

  const resultsBox = document.getElementById("rxSafetyResultsBox");
  resultsBox.style.display = "block";
  resultsBox.style.background = "#f8fafc";
  resultsBox.style.border = "1px solid #cbd5e1";
  resultsBox.innerHTML = `
    <div style="display:flex; align-items:center; gap:8px; color:#0284c7; font-weight:600;">
      <div class="spinner" style="width:18px; height:18px; border:2px solid #0284c7; border-top-color:transparent; border-radius:50%; animation:spin 0.8s linear infinite;"></div>
      <span>Running Day 2 Safety Engine: 5 deterministic clinical checks (Allergies, DDIs, Max Dose, Duplicates, Special Populations)...</span>
    </div>
  `;

  try {
    const res = await fetch("/api/doctor/prescriptions/review-draft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        patient_id: activeRxPatient.id,
        proposed_medications: [
          {
            drug_name: drugName,
            dosage: dosage || "Standard",
            frequency: frequency
          }
        ],
        is_pregnant: isPregnant,
        is_lactating: isLactating
      })
    });

    const data = await res.json();
    if (!res.ok) {
      resultsBox.innerHTML = `<div style="color:#dc2626;">Error: ${data.detail || "Failed to run safety engine."}</div>`;
      return;
    }

    renderSafetyVerdictResults(data, drugName, dosage, frequency);

  } catch (err) {
    resultsBox.innerHTML = `<div style="color:#dc2626;">Network error: ${err.message}</div>`;
  }
}

function renderSafetyVerdictResults(data, drugName, dosage, frequency) {
  const resultsBox = document.getElementById("rxSafetyResultsBox");
  const signBtn = document.getElementById("btnSignPrescription");

  const verdict = data.safety_verdict || "PASS";
  const canSign = data.can_sign;

  let borderColor = "#10b981";
  let bgColor = "#f0fdf4";
  let titleColor = "#065f46";
  let verdictBadge = `<span style="background:#10b981; color:white; padding:4px 10px; border-radius:9999px; font-weight:700; font-size:12px;">✅ 100% CLINICALLY SAFE (PASS)</span>`;

  if (verdict === "BLOCKED") {
    borderColor = "#ef4444";
    bgColor = "#fef2f2";
    titleColor = "#991b1b";
    verdictBadge = `<span style="background:#dc2626; color:white; padding:4px 10px; border-radius:9999px; font-weight:700; font-size:12px;">⛔ PRESCRIPTION BLOCKED (CONTRAINDICATION)</span>`;
  } else if (verdict === "WARNING") {
    borderColor = "#f59e0b";
    bgColor = "#fffbeb";
    titleColor = "#92400e";
    verdictBadge = `<span style="background:#f59e0b; color:white; padding:4px 10px; border-radius:9999px; font-weight:700; font-size:12px;">⚠️ CLINICAL WARNINGS DETECTED</span>`;
  }

  // Doctor alerts list
  const alertsHtml = (data.doctor_alerts && data.doctor_alerts.length > 0)
    ? data.doctor_alerts.map(a => `<div style="margin-top:4px; font-size:13px; color:#7f1d1d; font-weight:600;">${a}</div>`).join("")
    : `<div style="font-size:13px; color:#047857;">All 5 safety modules verified: Zero allergy conflicts, zero toxic DDIs, within daily max dose bounds.</div>`;

  resultsBox.style.display = "block";
  resultsBox.style.background = bgColor;
  resultsBox.style.border = `2px solid ${borderColor}`;
  resultsBox.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
      <h4 style="margin:0; font-size:15px; color:${titleColor}; font-weight:700; display:flex; align-items:center; gap:6px;">
        <span>🛡️</span> Day 2 Safety Engine Verification Result
      </h4>
      ${verdictBadge}
    </div>

    <!-- Doctor Clinical Warnings -->
    <div style="background:white; border-radius:8px; padding:12px; margin-bottom:10px; border:1px solid ${borderColor};">
      <div style="font-size:12px; font-weight:700; text-transform:uppercase; color:#475569; margin-bottom:4px;">Doctor Clinical Warnings & Directives:</div>
      ${alertsHtml}
      ${data.doctor_warning_summary_ur ? `
        <div style="margin-top:8px; padding-top:8px; border-top:1px dashed #e2e8f0; font-size:13px; color:#0f172a; font-weight:600; white-space:pre-line;">
          🇵🇰 <strong>UrduLish Doctor Summary:</strong><br>${data.doctor_warning_summary_ur}
        </div>
      ` : ''}
    </div>

    <!-- Patient Explanation Preview -->
    <div style="background:white; border-radius:8px; padding:12px; border:1px dashed #cbd5e1;">
      <div style="font-size:12px; font-weight:700; text-transform:uppercase; color:#0284c7; margin-bottom:4px;">Patient Counseling Explanation (Bilingual Generated by LLM Explainer):</div>
      <div style="font-size:13px; color:#1e293b; line-height:1.5;"><strong>UrduLish:</strong> ${data.patient_explanation_ur || 'N/A'}</div>
      <div style="font-size:12px; color:#64748b; margin-top:4px; line-height:1.4;"><strong>English:</strong> ${data.patient_explanation_en || 'N/A'}</div>
    </div>
  `;

  if (canSign) {
    signBtn.disabled = false;
    signBtn.style.background = "#059669";
    signBtn.style.color = "#ffffff";
    signBtn.style.cursor = "pointer";
    signBtn.style.boxShadow = "0 2px 4px rgba(5,150,105,0.3)";
  } else {
    signBtn.disabled = true;
    signBtn.style.background = "#cbd5e1";
    signBtn.style.color = "#64748b";
    signBtn.style.cursor = "not-allowed";
    signBtn.style.boxShadow = "none";
  }
}

async function submitSignedPrescription() {
  if (!activeRxPatient) return;

  const drugName = document.getElementById("draftDrugName").value.trim();
  const dosage = document.getElementById("draftDosage").value.trim();
  const frequency = document.getElementById("draftFrequency").value;

  if (!drugName) {
    alert("Please enter medication details.");
    return;
  }

  const signBtn = document.getElementById("btnSignPrescription");
  signBtn.disabled = true;
  signBtn.innerText = "Saving to EHR Database...";

  try {
    const res = await fetch("/api/doctor/prescriptions/sign", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        patient_id: activeRxPatient.id,
        appointment_id: activeRxPatient.appointmentId || null,
        medications: [
          {
            drug_name: drugName,
            brand_name: drugName,
            dosage_instruction: `${dosage || ''} ${frequency}`.trim()
          }
        ],
        clinical_notes: `Prescribed ${drugName} (${dosage || ''} ${frequency}) after automated Day 2 safety review.`
      })
    });

    const data = await res.json();
    if (!res.ok) {
      alert("Error saving prescription: " + (data.detail || "Server error"));
      signBtn.disabled = false;
      signBtn.innerText = "✍️ Sign & Issue Prescription";
      return;
    }

    alert(`✅ Prescription for ${drugName} signed successfully! Patient record and appointment status updated.`);
    closeRxModal();
    await loadDoctorPatients(); // refresh patient table to show "Checkup Done"

  } catch (err) {
    alert("Network error: " + err.message);
    signBtn.disabled = false;
    signBtn.innerText = "✍️ Sign & Issue Prescription";
  }
}

// --------------------------------------------------------------------------
// CLINICAL SUMMARY AGENT: PRE-VISIT SOAP NOTE
// --------------------------------------------------------------------------
async function openSoapModal(patientId, appointmentId, patientName) {
  closeAllModals();
  const overlay = document.getElementById("soapModalOverlay");
  overlay.style.display = "flex";

  document.getElementById("soapPatientName").innerText = patientName || patientId;
  document.getElementById("soapLoadingState").style.display = "block";
  document.getElementById("soapContentContainer").style.display = "none";

  try {
    const url = `/api/doctor/patients/${patientId}/soap-summary${appointmentId ? `?appointment_id=${appointmentId}` : ''}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Could not generate clinical SOAP summary.");

    const data = await res.json();
    const soap = data.soap;

    // S (Subjective)
    const subj = soap.subjective || {};
    const symList = (subj.associated_symptoms && subj.associated_symptoms.length > 0)
      ? subj.associated_symptoms.join(", ") : "None reported";
    document.getElementById("soapSubjectiveContent").innerHTML = `
      <div><strong>Chief Complaint:</strong> ${subj.chief_complaint || "Routine Clinical Consultation"}</div>
      <div style="margin-top:4px;"><strong>Symptom Duration:</strong> ${subj.duration || "N/A"} • <strong>Severity Scale:</strong> ${subj.severity_scale || 5}/10</div>
      <div style="margin-top:4px;"><strong>Associated Symptoms:</strong> ${symList}</div>
    `;

    // O (Objective)
    const obj = soap.objective || {};
    const condStr = (obj.verified_chronic_conditions && obj.verified_chronic_conditions.length > 0)
      ? obj.verified_chronic_conditions.join(", ") : "None documented";
    const allgStr = (obj.documented_allergies && obj.documented_allergies.length > 0)
      ? `<span style="color:#dc2626; font-weight:700;">${obj.documented_allergies.join(", ")}</span>`
      : "None documented";
    const rxStr = (obj.active_medications && obj.active_medications.length > 0)
      ? obj.active_medications.join(", ") : "None active";
    
    let labsHtml = "None on record";
    if (obj.recent_laboratory_results && obj.recent_laboratory_results.length > 0) {
      labsHtml = obj.recent_laboratory_results.map(l => 
        `<span style="background:#e2e8f0; padding:2px 6px; border-radius:4px; font-size:11.5px; margin-right:4px;">${l.test_name}: <strong>${l.value} ${l.unit || ''}</strong> (${l.interpretation || 'NORMAL'})</span>`
      ).join(" ");
    }

    document.getElementById("soapObjectiveContent").innerHTML = `
      <div><strong>Verified Chronic Diagnoses:</strong> ${condStr}</div>
      <div style="margin-top:4px;"><strong>Documented Allergies:</strong> ${allgStr}</div>
      <div style="margin-top:4px;"><strong>Active Medications:</strong> ${rxStr}</div>
      <div style="margin-top:4px;"><strong>Recent Lab Observations:</strong> ${labsHtml}</div>
    `;

    // A (Assessment - AI Suggestions)
    const assess = soap.assessment_ai_suggestions || {};
    const diffs = (assess.provisional_differential_considerations && assess.provisional_differential_considerations.length > 0)
      ? assess.provisional_differential_considerations.map(d => `<li>${d}</li>`).join("")
      : "<li>Clinical evaluation indicated</li>";

    document.getElementById("soapAssessmentContent").innerHTML = `
      <div><strong>Provisional Differential Diagnoses (for Physician Consideration):</strong></div>
      <ul style="margin:6px 0 6px 20px; padding:0;">${diffs}</ul>
      <div style="margin-top:4px; font-size:12.5px;"><strong>Clinical Risk / Acuity Level:</strong> <span style="background:#fef3c7; color:#92400e; padding:2px 8px; border-radius:9999px; font-weight:700;">${assess.clinical_risk_tier || "ROUTINE"}</span></div>
    `;

    // P (Plan Suggestions)
    const plan = soap.plan_ai_suggestions || {};
    const workup = (plan.suggested_diagnostic_workup && plan.suggested_diagnostic_workup.length > 0)
      ? plan.suggested_diagnostic_workup.map(w => `<li>${w}</li>`).join("")
      : "<li>None currently recommended</li>";
    const counseling = (plan.counseling_talking_points && plan.counseling_talking_points.length > 0)
      ? plan.counseling_talking_points.map(c => `<li>${c}</li>`).join("")
      : "<li>Routine health counseling</li>";

    document.getElementById("soapPlanContent").innerHTML = `
      <div><strong>Suggested Diagnostic Investigations:</strong></div>
      <ul style="margin:6px 0 6px 20px; padding:0;">${workup}</ul>
      <div style="margin-top:6px;"><strong>Suggested Patient Counseling Points:</strong></div>
      <ul style="margin:6px 0 6px 20px; padding:0;">${counseling}</ul>
    `;

    if (soap.clinical_disclaimer) {
      document.getElementById("soapDisclaimerText").innerText = soap.clinical_disclaimer;
    }

    document.getElementById("soapLoadingState").style.display = "none";
    document.getElementById("soapContentContainer").style.display = "flex";

  } catch (err) {
    document.getElementById("soapLoadingState").innerHTML = `
      <div style="color:#dc2626; padding:20px;">
        ⚠️ Failed to load SOAP note: ${err.message}
      </div>
    `;
  }
}

function closeSoapModal() {
  document.getElementById("soapModalOverlay").style.display = "none";
}

// --------------------------------------------------------------------------
// RECORDS AGENT Q&A
// --------------------------------------------------------------------------
let activeQaPatient = null;

function openRecordsQaModal(patientId, patientName) {
  closeAllModals();
  activeQaPatient = { id: patientId, name: patientName };
  document.getElementById("qaPatientName").innerText = patientName || patientId;
  document.getElementById("recordsQaModalOverlay").style.display = "flex";
  
  const chatBox = document.getElementById("qaChatContainer");
  chatBox.innerHTML = `
    <div style="background:#e0f2fe; color:#0369a1; padding:12px 16px; border-radius:8px; font-size:13px;">
      👨‍⚕️ <strong>Records Agent Ready:</strong> Ask any question regarding <strong>${patientName}</strong>'s documented diagnoses, active medications, allergy history, or laboratory test values (CBC, HbA1c, LFTs, Lipid Profile).
    </div>
  `;
  document.getElementById("qaQueryInput").value = "";
  document.getElementById("qaQueryInput").focus();
}

function closeRecordsQaModal() {
  document.getElementById("recordsQaModalOverlay").style.display = "none";
  activeQaPatient = null;
}

function setQaPrompt(text) {
  document.getElementById("qaQueryInput").value = text;
  submitRecordsQa();
}

async function submitRecordsQa() {
  if (!activeQaPatient) return;
  const input = document.getElementById("qaQueryInput");
  const query = input.value.trim();
  if (!query) return;

  const chatBox = document.getElementById("qaChatContainer");

  // Append user message
  const userBubble = document.createElement("div");
  userBubble.style.cssText = "align-self:flex-end; background:#0284c7; color:white; padding:10px 14px; border-radius:12px 12px 2px 12px; font-size:13px; max-width:80%;";
  userBubble.innerText = query;
  chatBox.appendChild(userBubble);

  input.value = "";

  // Append loading bubble
  const loadingBubble = document.createElement("div");
  loadingBubble.style.cssText = "align-self:flex-start; background:#f1f5f9; color:#475569; padding:10px 14px; border-radius:12px 12px 12px 2px; font-size:13px;";
  loadingBubble.innerHTML = "🔍 <em>Records Agent analyzing FHIR records & lab data...</em>";
  chatBox.appendChild(loadingBubble);
  chatBox.scrollTop = chatBox.scrollHeight;

  const sendBtn = document.getElementById("btnSendQa");
  sendBtn.disabled = true;

  try {
    const res = await fetch(`/api/doctor/patients/${activeQaPatient.id}/records-qa`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query })
    });

    if (!res.ok) throw new Error("Could not answer records query");
    const data = await res.json();

    loadingBubble.style.background = "#ffffff";
    loadingBubble.style.border = "1px solid #e2e8f0";
    loadingBubble.style.color = "#0f172a";
    loadingBubble.style.maxWidth = "85%";
    loadingBubble.innerHTML = `
      <div style="font-weight:700; color:#0369a1; font-size:12px; margin-bottom:4px; display:flex; align-items:center; gap:4px;">
        <span>📁</span> Records Agent Grounded Response
      </div>
      <div style="font-size:13px; line-height:1.5;">${data.english_answer || data.message || "No answer found."}</div>
      ${data.urdulish_answer ? `
        <div style="margin-top:8px; padding-top:6px; border-top:1px dashed #e2e8f0; font-size:12.5px; color:#475569;">
          <strong>UrduLish:</strong> ${data.urdulish_answer}
        </div>
      ` : ''}
      <div style="margin-top:6px; font-size:11px; color:#94a3b8; font-family:monospace;">
        Source: City Care FHIR Store • Verified Clinical Data
      </div>
    `;

  } catch (err) {
    loadingBubble.innerHTML = `<span style="color:#dc2626;">⚠️ Error: ${err.message}</span>`;
  } finally {
    sendBtn.disabled = false;
    chatBox.scrollTop = chatBox.scrollHeight;
  }
}

document.addEventListener("DOMContentLoaded", initDashboard);
