# Ilm Academy Adaptive Platform — REST API Reference (OpenAPI v3)

**Base URL:** `http://localhost:8000/api/v1`  
**Authentication:** HTTP Bearer Header (`Authorization: Bearer <JWT_TOKEN>`)

---

## 1. Authentication Endpoints

### `POST /auth/login`
Authenticates a student, instructor, or admin.
- **Request Body:**
```json
{
  "email": "ali@ilm.edu",
  "password": "password123"
}
```
- **Response `200 OK`:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "STU-1001",
  "name": "Ali Raza",
  "role": "STUDENT",
  "email": "ali@ilm.edu"
}
```

---

## 2. Student Adaptive Learning Endpoints

### `GET /student/path`
Returns the real-time personalized learning recommendation and UrduLish motivational nudge.
- **Headers:** `Authorization: Bearer <STUDENT_TOKEN>`
- **Response `200 OK`:**
```json
{
  "student_id": "STU-1001",
  "name": "Ali Raza",
  "persona": "Strong in loops, struggling with functions & call stacks",
  "current_mastery_avg": 0.64,
  "next_recommended_concept": {
    "id": "C14",
    "name": "Functions & Variable Scope",
    "zpd_success_prob": 0.68,
    "strategy": "Prerequisite Reinforcement",
    "estimated_minutes": 35,
    "motivational_nudge": "Ali bhai, aap loops bohot achay se samajhtay hain! Aaj functions ke local scope aur return values ko connect karein ge. Step by step chalain ge, tension nahi leni!"
  }
}
```

### `POST /tutor/chat`
Interacts with the 24/7 Socratic AI Tutor.
- **Request Body:**
```json
{
  "student_id": "STU-1001",
  "concept_id": "C17",
  "message": "Mujhe recursion ka base case samajh nahi aa raha.",
  "current_hint_level": 1,
  "language": "UrduLish"
}
```
- **Response `200 OK`:**
```json
{
  "verdict": "SOCRATIC_GUIDANCE",
  "socratic_response": "Sochiye ke recursive call ko ruknay ke liye kis condition ki zaroorat hoti hai? Base case kya define kiya hai aap ne?",
  "hint_level": 1,
  "next_hint_level": 2,
  "solution_leaked": false,
  "lesson_citation": "Lesson 17: Base Cases and Call Stack @ 08:45"
}
```

---

## 3. Sandboxed Assignment & Grading Endpoints

### `POST /assignments/submit`
Submits code to the isolated execution sandbox for automated grading and formative feedback.
- **Request Body:**
```json
{
  "student_id": "STU-1001",
  "problem_id": "two_sum",
  "code": "def two_sum(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        comp = target - num\n        if comp in seen:\n            return [seen[comp], i]\n        seen[num] = i\n    return []\n"
}
```
- **Response `200 OK`:**
```json
{
  "submission_id": "SUB-API",
  "autograder_score": 100.0,
  "verdict": "ACCEPTED",
  "execution_time_sec": 0.0021,
  "code_quality": {
    "cyclomatic_complexity": 3,
    "complexity_rating": "A (Low Complexity / Clean)",
    "maintainability_index": 64.5
  },
  "actionable_improvement": "Add a concise docstring specifying the expected argument types, time complexity O(N), and return value.",
  "lesson_link": {
    "concept": "C09: Dictionaries & Hash Maps",
    "lesson": "Lesson 09: Fast Key-Value Lookups and Complement Searching",
    "video_timestamp": "14:20"
  }
}
```

---

## 4. Teacher & Admin Endpoints

### `GET /teacher/dashboard`
Returns live platform KPIs, weak concept analytics, and at-risk student queues.
- **Headers:** `Authorization: Bearer <TEACHER_TOKEN>`
- **Response `200 OK`:** *(Consolidated JSON telemetry matching `dashboard_kpi_summary.json`)*

### `POST /teacher/plagiarism/review`
Submits a human instructor's judgment on a flagged plagiarism case.
- **Request Body:**
```json
{
  "pair_id": "PAIR-11",
  "teacher_decision": "REQUEST_MEETING",
  "notes": "Student B's variables appear identical to Student A with aliases. Meeting scheduled for Tuesday 3 PM."
}
```
