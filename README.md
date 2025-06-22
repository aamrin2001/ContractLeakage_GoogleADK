# 📦 Smart Logistics Assistant

An AI-powered assistant for logistics contract analysis and invoice anomaly detection. This application combines contract document understanding and invoice intelligence using Google ADK (Agents Development Kit), Streamlit for UI, and Gemini models (2.0 & 2.5) for reasoning and LLM-based responses.

---

## 🚀 Features

### 📝 Contract QA Assistant
- Extracts and interprets logistics contract PDFs.
- Answers questions about:
  - Contract terms, validity, clauses.
  - Shipment rate lookups using a predefined Apex Rate Table (`apex_rate_table.json`).
  - Detailed contract summaries using structured headings and bullet points.
- Uses Google Gemini 2.5 Flash model for responses.

### 📊 Invoice Anomaly Detection
- Detects the following anomalies from invoice Excel files:
- The model detects anomalies based on zones.
  - **Overbilling** – compares total amount against lane rates and surcharges.
  - **Duplicate Shipments** – checks for repeated shipment entries based on key fields.
  - **Surcharge Percentage** – calculates `(ADDISRCHG / Total_Amount) * 100` and highlights the highest surcharge.
- Returns clean **markdown tables** as output (for easy display).

---

## 🛠️ Tech Stack

| Component              | Technology Used                       |
|------------------------|----------------------------------------|
| 🧠 LLM Agents           | Google ADK (`LlmAgent`, `SequentialAgent`) |
| 🤖 LLM Model           | Gemini 2.0 & 2.5 Flash (Google GenAI)  |
| 📄 PDF Parsing         | `PyPDF2` for full contract text        |
| 📊 Excel Processing    | `pandas`, `openpyxl`                   |
| 🌐 Frontend            | Streamlit                              |
| 📁 File Support        | PDF + Excel + JSON                     |
---

## 📥 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/smart-logistics-assistant.git
cd smart-logistics-assistant
```

### 2. Install Dependencies

Make sure you are in a virtual environment:

```bash
pip install -r requirements.txt
```

### 3. Set Your Google ADK & GenAI Credentials

Make sure `.env` file or system environment variables include:

```bash
GOOGLE_API_KEY=your_api_key
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=your_location
```

### 4. Run the Application

```bash
streamlit run frontend.py
```

---

## 🧪 Usage Flow

1. **Select Task**: From sidebar - choose:
   - "Ask Contract Based Questions" or
   - "Ask About Anomaly"

2. **Ask Your Question**:
   - e.g., _"What is the rate from North to East?"_
   - e.g., _"Summarize the contract"_
   - e.g., _"Detect overbilling for North zone"_

3. **Get Results**:
   - Contracts: Detailed answers or summaries.
   - Invoices: Clear markdown tables showing anomalies or surcharge insights.


