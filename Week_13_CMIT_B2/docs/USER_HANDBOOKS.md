# Ilm Academy Platform — User Handbooks

---

## Part A: Teacher & Teaching Assistant Handbook

### 1. Daily Workflow Overview
1. **Morning Check (09:00 AM):** Open the **Teacher Dashboard** (`teacher_dashboard/index.html`). Check the **Priority Student Interventions** table.
2. **Review At-Risk Students:**
   - **Critical Tier (Risk > 70%):** Click *"Trigger Batch WhatsApp Reminders"* or send a personalized 1-on-1 TA invite.
   - **Bottleneck Concepts:** Identify concepts where failure rate exceeds 50% (e.g. C17 Recursion, C32 Decorators) and dedicate Wednesday live review sessions to those topics.
3. **Sunday Grading Review:**
   - 93.4% of assignments are graded automatically with Socratic feedback.
   - Inspect the **Flagged for Human Review** queue (plagiarism similarity $\ge 40\%$ and edge-case exceptions).
   - Use the side-by-side diff viewer. Strictly adhere to: **Flag Only — Never Auto-Punish**.

### 2. Intervention Playbook by Student Persona
- **The Frustrated Struggler (e.g. Ali):** High effort, low mastery in abstract concepts.  
  *Action:* Review prerequisite DAG; assign bite-sized coding tasks in the 60-80% ZPD band.
- **The Fast Careless Learner (e.g. Sara):** High speed, occasional slip errors due to rushing.  
  *Action:* Congratulate speed, but enforce test case trace steps before allowing final submission.
- **The Inactive Disengaged Student:** Inactivity streak $> 4$ days.  
  *Action:* Automated friendly WhatsApp outreach in UrduLish with a short 3-minute video recap link.

---

## Part B: Student Guide

### 1. Getting Started
- Navigate to the **Student Portal** (`api_server/student_portal.html`).
- Your dashboard displays your **Personalized Recommended Task** calculated specifically for your current mastery level.

### 2. Using the 24/7 Socratic AI Tutor
- When stuck on an error or logic puzzle, click the **Socratic AI Tutor** chat window.
- The tutor will never give away full code solutions. Instead, it offers a 4-step hint ladder:
  - Step 1: A guiding question to make you think about edge cases or base cases.
  - Step 2: A pointer to the exact lesson and video timestamp.
  - Step 3: A partial trace of inputs and stack frames.
  - Step 4: A similar toy example to illustrate the pattern.

### 3. Submitting Assignments
- Type your Python solution into the code editor.
- Click **"Submit to Sandbox"**.
- Within 0.2 seconds, you will receive:
  - Unit test pass/fail score (Visible + Hidden + Scale Efficiency).
  - Code Quality analysis (McCabe Complexity, Maintainability Index, PEP 8 style).
  - Exactly **ONE** actionable next step to elevate your code.
