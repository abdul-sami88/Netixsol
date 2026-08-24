# RealEstate Hub Voice Agent — Mermaid Diagrams

All 8 diagrams from the design doc, each standalone and independently copy-pasteable.

---

## 1. System Architecture

```mermaid
flowchart TB
    Caller((Caller<br/>PSTN/Mobile))
    Telephony[Telephony Gateway<br/>Twilio/Exotel SIP]
    VAD[VAD + Barge-in Detector]
    STT[Streaming STT<br/>Deepgram/AssemblyAI<br/>Urdu-English]
    Orchestrator{{Workflow Orchestrator<br/>State Machine / LangGraph}}
    LLM[LLM Reasoning Engine<br/>+ Tool Calling]
    RAG[(Retrieval<br/>Vector DB: listings, FAQs)]
    Tools[Tool Layer<br/>CRM · Calendar · Pricing API · SMS]
    STM[(Short-Term Memory<br/>Redis session store)]
    LTM[(Long-Term Memory<br/>Customer CRM profile)]
    TTS[Streaming TTS<br/>Urdu-English]
    Logging[[Call Logging /<br/>Analytics / QA]]
    Human[Human Agent<br/>Escalation Path]

    Caller <--> Telephony
    Telephony --> VAD
    VAD --> STT
    STT -- partial + final transcripts --> Orchestrator
    Orchestrator <--> STM
    Orchestrator -- caller_id lookup --> LTM
    Orchestrator --> LLM
    LLM <--> RAG
    LLM <--> Tools
    Tools <--> LTM
    LLM -- streamed tokens --> Orchestrator
    Orchestrator --> TTS
    TTS -- streamed audio --> Telephony
    Orchestrator -. barge-in interrupt .-> TTS
    Orchestrator -- escalation trigger --> Human
    Orchestrator --> Logging

    style Orchestrator fill:#2563eb,color:#fff
    style LLM fill:#7c3aed,color:#fff
    style TTS fill:#059669,color:#fff
    style STT fill:#059669,color:#fff
    style Human fill:#dc2626,color:#fff
```

---

## 2. Buyer Inquiry Flow

```mermaid
flowchart TD
    A[Greeting + identify caller] --> B{New or returning?}
    B -- New --> C[Ask: buy/rent/commercial/invest?]
    B -- Returning --> R[Pull CRM profile, greet by name,<br/>reference last inquiry]
    C --> D[Qualify: location, budget,<br/>property type, timeline, family size]
    R --> D
    D --> E[Retrieve matching listings from RAG/DB]
    E --> F{Matches found?}
    F -- Yes --> G[Present 2-3 top options with<br/>key highlights, one at a time]
    F -- No --> H[Acknowledge + widen criteria<br/>or offer to notify when available]
    G --> I{Caller interested?}
    I -- Objection --> J[Objection handling]
    J --> I
    I -- Yes --> K[Propose site visit: offer 2 time slots]
    K --> L[Confirm date/time, collect/verify phone]
    L --> M[Book via calendar tool, send SMS confirmation]
    M --> N[Warm close + set expectation for callback]
    I -- Not now --> O[Offer to add to watchlist, ask permission<br/>for follow-up call, close politely]
    H --> O
```

---

## 3. Rental Inquiry Flow

```mermaid
flowchart TD
    A[Greeting] --> B[Confirm: looking to rent]
    B --> C[Qualify: location, budget/month,<br/>move-in date, furnished/unfurnished,<br/>family/bachelor]
    C --> D[Retrieve matching rentals]
    D --> E{Available now?}
    E -- Yes --> F[Present option: rent, deposit,<br/>advance months required]
    E -- No, but similar --> G[Offer closest alternative,<br/>ask if flexible on area/budget]
    F --> H{Interested?}
    G --> H
    H -- Objection: price/deposit --> J[Objection handling]
    J --> H
    H -- Yes --> I[Book viewing slot + explain<br/>documents needed for rental]
    I --> K[Confirm + SMS + close]
    H -- No --> L[Offer to notify on new listings, close]
```

---

## 4. Commercial Property Inquiry Flow

```mermaid
flowchart TD
    A[Greeting] --> B[Confirm: commercial use —<br/>office/retail/warehouse]
    B --> C[Qualify: business type, area sqft needed,<br/>foot-traffic requirement, budget,<br/>buy vs lease]
    C --> D{Decision-maker on call?}
    D -- No --> E[Politely get decision-maker's<br/>availability, offer to call back<br/>or send info via WhatsApp]
    D -- Yes --> F[Retrieve matching commercial listings]
    F --> G[Present options with sqft,<br/>location advantage, price/lease terms]
    G --> H{Interested?}
    H -- Objection --> J[Objection handling]
    J --> H
    H -- Yes --> I[Offer site visit; note commercial deals<br/>often need a senior agent —<br/>flag for co-attendance]
    I --> K[Book + confirm + close]
    H -- No --> L[Offer to send brochure/deck, close]
```

---

## 5. Investment Inquiry Flow

```mermaid
flowchart TD
    A[Greeting] --> B[Confirm: investment purpose —<br/>capital growth vs rental yield]
    B --> C[Qualify: budget, investment horizon,<br/>risk appetite, preferred area/city,<br/>installment vs lump sum]
    C --> D[Retrieve investment-grade listings<br/>+ ROI/appreciation data from RAG]
    D --> E[Present option with expected ROI,<br/>payment plan, possession timeline]
    E --> F{Interested?}
    F -- Objection: risk/trust --> J[Objection handling —<br/>emphasize legal docs, track record]
    J --> F
    F -- Yes --> G{Wants site visit or<br/>consultation call?}
    G -- Site visit --> H[Book visit]
    G -- Consultation --> I[Book call with investment advisor]
    H --> K[Confirm + close]
    I --> K
    F -- No --> L[Offer investment newsletter/updates, close]
```

---

## 6. Returning Customer Flow

```mermaid
flowchart TD
    A[Caller ID matched in CRM] --> B[Greet by name,<br/>reference last interaction]
    B --> C{Reason for call known<br/>from context/CRM notes?}
    C -- Yes, e.g. pending visit --> D[Confirm purpose directly:<br/>"Aap ka Bahria Town visit<br/>confirm karna tha na?"]
    C -- No --> E[Ask how we can help today]
    D --> F[Proceed on relevant flow<br/>— reschedule/new inquiry/feedback]
    E --> F
    F --> G[Update CRM notes with new context]
    G --> H[Close warmly, thank for loyalty]
```

---

## 7. Appointment Rescheduling Flow

```mermaid
flowchart TD
    A[Caller requests reschedule] --> B[Locate existing booking in calendar]
    B --> C{Booking found?}
    C -- No --> D[Apologize, ask for details<br/>to search manually or escalate]
    C -- Yes --> E[Confirm which booking:<br/>property + old date/time]
    E --> F[Ask preferred new date/time]
    F --> G[Check agent/property availability]
    G --> H{Slot available?}
    H -- Yes --> I[Update calendar, cancel old slot]
    H -- No --> J[Offer 2 nearest alternatives]
    J --> F
    I --> K[Send SMS/WhatsApp confirmation]
    K --> L[Close: confirm caller is all set]
    D --> L
```

---

## 8. Appointment Cancellation Flow

```mermaid
flowchart TD
    A[Caller requests cancellation] --> B[Locate booking]
    B --> C{Found?}
    C -- No --> D[Apologize, ask details, escalate if needed]
    C -- Yes --> E[Confirm booking details before cancelling]
    E --> F[Ask reason — light touch,<br/>not interrogation]
    F --> G{Reason indicates<br/>lost interest vs. reschedule need?}
    G -- Reschedule need --> H[Offer to reschedule<br/>instead of cancel]
    G -- Genuinely cancelling --> I[Cancel in calendar tool]
    H --> Z[End]
    I --> J[Confirm cancellation via SMS]
    J --> K[Ask permission to stay in touch<br/>for future options]
    K --> L[Close politely, no pressure]
    D --> L
```
