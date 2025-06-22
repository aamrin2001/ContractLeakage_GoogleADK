import asyncio
import json
import pandas as pd
from google.adk.agents.sequential_agent import SequentialAgent
# from google.adk.agents.parallel_agent import ParallelAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
 

import os
import json
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import pandas as pd
import re
from dotenv import load_dotenv
# from tools.apex_table_parser import extract_apex_rate_table
from google.genai import types
# from google.adk.types import Content, Part
load_dotenv()

APP_NAME = "contract_leakage_app"
USER_ID = "test_user"
SESSION_ID = "contract_test_session"
GEMINI_MODEL_2_FLASH = "gemini-2.0-flash"
GEMINI_MODEL_1_5_FLASH = "gemini-1.5-flash"
GEMINI_MODEL_2_5_FLASH_PREVIEW = "gemini-2.5-flash-preview-05-20"
GEMINI_MODEL_2_FLASH_LITE = "gemini-2.0-flash-lite"
GEMINI_MODEL_1_5_FLASH_8B = "gemini-1.5-flash-8b"
 
# agent.py
 
import json
from google.adk.agents.llm_agent import LlmAgent
# from google.adk.agents.sequential_agent import SequentialAgent
 

ContractExtractorAgent = LlmAgent(
    name="ContractExtractorAgent",
    model="gemini-2.0-flash",
    instruction="""
You are a contract extraction assistant. Your task is to extract structured information from logistics contracts provided as PDF file paths.
 
Input:
{
Use the pdf file path "sample_pdf" to extract the contract text and rate table.
}
 
Your responsibilities:
1. Extract the complete contract text.
2. Extract the rate table — typically found on page 5.
3. Convert the table into both:
   - A list of dictionaries (`contract_table_json`)
   - A DataFrame-like structure (`contract_table_df`) – retain column headers like 'From', 'To', 'Rate'.
 
Return the final output strictly in this JSON format:
{
  "contract_text": "extracted text content...",
  "contract_table_json": [
    {
      "From": "WEST",
      "To": "NORTH",
      "Rate": 45.67
    },
    ...
  ],
  "contract_table_df": "table data in DataFrame format"
}
 
Do not add markdown, explanations, or notes. Output only valid structured data. Prioritize page 5 for table extraction if it exists.
""",
    output_key="contract_extraction_output"
)
# agents/contract_qa.py
 
ContractQAAgent = LlmAgent(
    name="ContractQAAgent",
    model="gemini-2.5-flash",
    instruction="""
You are a logistics contract question-answering assistant.

📥 Input Format:
You will receive input in the form:
{
  "contract_text": "<full contract text>",
  "rate_table": [ list of lane rate entries like {"From": "North", "To": "West", "Rate": "37.02"} ],
  "question": "<user's question>"
}

Your responsibilities:
1. If the user's question is about **contract terms, clauses, or validity**, answer using `contract_text`. Use bullet points for clarity when needed.
2. If the question asks about **rates or charges between zones**, look up the `From` and `To` in `rate_table` and return the `Rate`. Always say "according to the Apex Rate Table".
3. If the information is not found, politely state that it's not available.

📋 Guidelines:
- Be accurate, factual, and clear.
- Use **bullet points** when listing multiple elements.
- Avoid vague language or speculation.
- Say "according to the Apex Rate Table" for any rate-related answers.
- Never invent or assume values.
- whenever you are mentioning the parties name or any date or any important keywords make it bold always

📄 If asked for a **contract summary**:
- Give a concise summary (within ~400 words).
- Use simple headings (e.g., Overview, Key Terms, Validity).
- Summarize only the most relevant parts – no full quotes.
- Be formal and clear. Use bullets or numbered lists where suitable.

Return only the final answer as plain text. No JSON or markdown.
"""
)


ContractQA_PipelineAgent = SequentialAgent(
    name="ContractQAPipelineAgent",
    description="Extracts contract and answers question using contract text. Only requires a question as input.",
    sub_agents=[ContractExtractorAgent, ContractQAAgent]
)



InvoiceExtractorAgent = LlmAgent(
    name="InvoiceExtractorAgent",
    model="gemini-2.0-flash",
    instruction="""
You are an invoice data processing assistant.
 
You will receive tabular invoice data extracted from an Excel sheet. Your task is to:
1. Standardize and rename the following fields using case-insensitive and fuzzy matching:
   - 'AWB Number', 'Awb', 'awb_no' → `AWB_Number`
   - 'Origin Area', 'origin', 'from' → `Origin_Area`
   - 'Destination Area', 'destination', 'to' → `Destination_Area`
   - 'ORIGIN_ZONE', 'origin zone','OORIGIN ZONE' → `Origin_Zone`
   - 'Zone', 'zone' → `ZONE`
   - 'Batch Date', 'Date', 'batch_date' → `Batch_Date`
   - 'Actual Weight', 'Weight', 'actual_wt' → `Actual_Weight`
   - 'Total Amount', 'Amount', 'Total' → `Total_Amount`
   - 'ADDISRCHG', 'Surcharge', 'Additional Surcharge' → `ADDISRCHG`
   - 'FS Amount', 'Fuel Surcharge', 'fs_amt' → `FS_Amount`
   - 'Customer Code', 'Customer', 'Cust Code' → `Customer_Code`
 
2. Ensure all date fields are formatted as strings in `"YYYY-MM-DD"` format.
 
3. Remove irrelevant or unrecognized columns.
 
4. Return a clean JSON list of dictionaries in the following format:
```json
[
  {
    "AWB_Number": "ABC123",
    "Origin_Area": "Bangalore",
    "Destination_Area": "Hyderabad",
    "Origin_Zone":"South"
    "ZONE": "SOUTH",
    "Batch_Date": "2024-11-05",
    "Actual_Weight": 4.0,
    "FS_Amount": 10.5,
    "ADDISRCHG": 3.75,
    "Total_Amount": 45.20,
    "Customer_Code": "CUSTX123"
  }
]""",
output_key="invoice_extraction_output"
)

AnomalyDetectorAgent = LlmAgent(
    name="AnomalyDetectorAgent",
    model="gemini-2.0-flash",
    instruction="""
You are a logistics anomaly detection assistant.

You can handle the following tasks:
1. Overbilling Detection
2. Duplicate Shipments Detection
3. Rate Lookup
4. Surcharge Percentage Calculation

---

📥 Input Format:
You will receive input in the form:
{
  "invoice_data": [ list of invoice entries ],
  "rate_table": [ list of lane rate entries like {"From": "North", "To": "West", "Rate": "37.02"} ],
  "zone": "ALL" or a specific zone like "NORTH",
  "question": "<user's question>"
}

---

📦 Rate Lookup Task:
If the user asks about a shipment rate (e.g., "rate for north to east"), find the matching entry in the `rate_table` where `From` and `To` match (case-insensitive).

✅ Example:
User: "Rate for North to East"  
Response: "The shipment rate from North to East is 44.24 units according to the Apex Rate Table."

If no match is found, respond politely saying the rate is not available.

---

💰 Overbilling Detection Logic:
A shipment is considered **overbilled** if:

    Total_Amount > (Actual_Weight × Lane Rate) + FS_Amount + ADDISRCHG

- Lane Rate is looked up from `rate_table`, where `From` = `Origin_Zone`, `To` = `ZONE`
- Zones should be matched case-insensitively
- If a specific `zone` is provided, only analyze rows where `ZONE` matches

✅ Output Columns:
| AWB_Number | Route | Actual_Weight | Lane_Rate | FS_Amount | ADDISRCHG | Total_Amount | Calculated_Amount | Overbilled_By |

---

# 🧾 Duplicate Detection Logic:
# A shipment is considered **duplicate** if:
# - It shares the same combination of:
#   - `Origin_Area`
#   - `Destination_Area`
#   - `Customer_Code`
#   - `Batch_Date`
# - Return all duplicate rows, not just one.

✅ Output Columns:
| AWB_Number | Origin_Area | Destination_Area | Customer_Code | Batch_Date | Total_Amount |

---

📊 Surcharge Percentage Detection:
When user asks about surcharge percentage, calculate:

    (ADDISRCHG / Total_Amount) * 100

- Skip rows where ADDISRCHG = 0
- Perform this row by row
- Show results in the table below

✅ Output Columns:
| AWB_Number | ADDISRCHG | Total_Amount | Surcharge Percentage |

At the end of the table, add one line:
**"Highest surcharge percentage is X%"** (rounded to two decimal places)

---

📤 Output Format Rules:
- Return only a **markdown table**.
- No JSON, no explanations, no headings.
- If no results, return the table header with no rows.
- After the table (only for surcharge task), add the **final line for highest surcharge**.

""",
    output_key="anomaly_detection_output",
)


SequentialInvoiceAnomalyAgent = SequentialAgent(
    name="SequentialInvoiceAnomalyAgent",
    sub_agents=[
        InvoiceExtractorAgent,
        AnomalyDetectorAgent
    ]
)

RootRoutingAgent = LlmAgent(
    name="RootRoutingAgent",
    model="gemini-2.0-flash",
    instruction="""
You are an AI routing assistant.

You receive a user question and must decide which pipeline agent should handle it.

There are two options:
1. If the question is related to **contracts** (e.g. rate agreement, shipment terms, contract clauses), then route to `ContractQA_PipelineAgent`.
2. If the question is about **invoice issues** (e.g. overbilling, surcharge %, duplicate billing), route to `SequentialInvoiceAnomalyAgent`.

Return the name of the agent to invoke:
- "ContractQA_PipelineAgent"
- "SequentialInvoiceAnomalyAgent"

Only return the agent name. Do not explain.
""",
    output_key="selected_agent"
)

######################################################Testing AGENT4#######################################
