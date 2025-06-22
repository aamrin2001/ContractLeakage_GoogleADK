
import sys
import os
import streamlit as st
import asyncio
import json
import pandas as pd
import nest_asyncio
from PyPDF2 import PdfReader

from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

from agent import (
    ContractQA_PipelineAgent,
    SequentialInvoiceAnomalyAgent,
    ContractQAAgent,
    AnomalyDetectorAgent
)
# from tools.apex_table_parser import extract_apex_rate_table

# === Constants ===
EXCEL_PATH = "datasets/SUBSET.xlsx"
CONTRACT_PDF_PATH = "datasets/ExampleContract.pdf"
APP_NAME = "root_agent_app"
USER_ID = "local_user"
SESSION_ID = "streamlit_session"
# rate_table = r"C:\Google_ADK_Hackathon\datasets\apex_rate_table.json"
# === Streamlit Setup ===
st.set_page_config(page_title="Smart Logistics Assistant", layout="wide")
st.title("📦 Smart Logistics Assistant")

# === Sidebar Navigation ===
selected_option = st.sidebar.radio(
    "Choose your task:",
    ("Ask Contract Based Questions", "Ask About Anomaly")
)

# Track last selection to reset inputs
if "last_selected_option" not in st.session_state:
    st.session_state.last_selected_option = selected_option

if selected_option != st.session_state.last_selected_option:
    st.session_state.question_input = ""
    st.session_state.last_selected_option = selected_option

# === Question Input ===
user_question = st.text_input("🔎 Ask your question:", key="question_input")
 
# === ALERTS & KPIs SECTION ===
st.subheader("🚨 Alerts & KPIs")
 
try:
    df = pd.read_excel(EXCEL_PATH).astype(str)
 
    df["Total_Amount"] = df["Total_Amount"].astype(float)
    df["ADDISRCHG"] = df["ADDISRCHG"].astype(float)
 
    # === KPI Row 1 ===
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Invoices Loaded", len(df))
    k2.metric("Unique Customers", df["Customer_Code"].nunique())
    k3.metric("Unique Zones", df["ZONE"].nunique())
 
    # Max surcharge % per customer
    customer_surcharge = df.groupby("Customer_Code").agg({
        "ADDISRCHG": "sum",
        "Total_Amount": "sum"
    })
    customer_surcharge["Surcharge_Pct"] = (customer_surcharge["ADDISRCHG"] / customer_surcharge["Total_Amount"]) * 100
    max_surcharge_customer = customer_surcharge["Surcharge_Pct"].idxmax()
    max_surcharge_pct = customer_surcharge["Surcharge_Pct"].max()
 
    k4.metric("Max Surcharge % (Customer)", f"{max_surcharge_pct:.2f}%", delta=max_surcharge_customer)
 
    # === KPI Row 2 ===
    k5, k6, k7, k8 = st.columns(4)
 
    # Duplicate detection
    duplicate_df = df[df.duplicated(subset=["Customer_Code", "Origin_Area", "Destination_Area", "Batch_Date"], keep=False)]
    k5.metric("Duplicate Invoices", len(duplicate_df))
 
    # Overbilling logic (simplified for KPI – assume if ADDISRCHG > threshold)
    overbilling_df = df[df["Total_Amount"] > df["ADDISRCHG"] + df["Total_Amount"] * 0.8]
    k6.metric("Overbilling Cases", len(overbilling_df))
 
    # Max overbilling (approximated by diff from Total_Amount and threshold)
    if not overbilling_df.empty:
        overbilling_df["Overbilled_By"] = overbilling_df["Total_Amount"] - (overbilling_df["ADDISRCHG"] + overbilling_df["Total_Amount"] * 0.8)
        max_overbilling_amt = overbilling_df["Overbilled_By"].max()
    else:
        max_overbilling_amt = 0
 
    k7.metric("Max Overbilling ₹", f"{max_overbilling_amt:.2f}")
 
    # AWBs with surcharge > 0
    surcharge_awbs = df[df["ADDISRCHG"] > 0]
    k8.metric("AWBs with Surcharge", len(surcharge_awbs))
 
    # === Alerts ===
    alerts = []
 
    # Overbilling % in North
    total_amt = df["Total_Amount"].sum()
    north_amt = df[df["ZONE"].str.upper() == "NORTH"]["Total_Amount"].sum()
    if total_amt > 0:
        north_pct = (north_amt / total_amt) * 100
        alerts.append(f"📊 **{north_pct:.2f}%** of the overbilling has occurred in the **NORTH** zone")
 
    # Top duplicate customer
    customer_dup_counts = duplicate_df["Customer_Code"].value_counts()
    if not customer_dup_counts.empty:
        top_dup_customer = customer_dup_counts.idxmax()
        top_dup_count = customer_dup_counts.max()
        alerts.append(f"🔁 **{top_dup_customer}** - customer has **{top_dup_count}** (maximum) duplicate invoice instances")
 
    # Max total surcharge customer
    surcharge_by_customer = df.groupby("Customer_Code")["ADDISRCHG"].sum()
    max_surcharge_customer = surcharge_by_customer.idxmax()
    max_surcharge_value = surcharge_by_customer.max()
    alerts.append(f"💰 **{max_surcharge_customer}** - customer has the **maximum total surcharge** – ₹{max_surcharge_value:.2f}")
 
    for alert in alerts:
        st.warning(alert)
 
except Exception as e:
    st.info(f"Unable to generate alerts preview – {e}")
 
 ## ====================== MAIN LOGIC =====================================================
if st.button("Submit") and user_question.strip():
    
    async def ask_agent(selected_agent):
        session_service = InMemorySessionService()
        await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
        APEX_TABLE_PATH = "datasets/apex_rate_table.json"
        with open(APEX_TABLE_PATH, "r", encoding="utf-8") as f:
            rate_table = json.load(f)
        if selected_agent == "ContractQAAgent":
        # === Load contract text ===
            def load_pdf_text(file_path):
                reader = PdfReader(file_path)
                return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())

            contract_text = load_pdf_text(CONTRACT_PDF_PATH)

        # === Load rate table ===
            # APEX_TABLE_PATH = r"C:\Google_ADK_Hackathon\datasets\apex_rate_table.json"
            # with open(APEX_TABLE_PATH, "r", encoding="utf-8") as f:
            #     rate_table = json.load(f)

            payload = {
            "contract_text": contract_text,
            "rate_table": rate_table,
            "question": user_question
        }

            content = types.Content(
            role="user",
            parts=[
                types.Part(text="Contract QA with contract and rate table."),
                types.Part(text=json.dumps(payload))
            ]
        )
            runner = Runner(agent=ContractQAAgent, app_name=APP_NAME, session_service=session_service)
            agent_to_display = ContractQAAgent.name

        elif selected_agent == "SequentialInvoiceAnomalyAgent":
            invoice_data = df.to_dict(orient="records") #changed this line
            zone = "ALL"
            for z in ["NORTH", "SOUTH", "EAST", "WEST", "JK", "NORTH EAST"]:
                if z.lower() in user_question.lower():
                    zone = z
                    break

            input_payload = {
                "invoice_data": invoice_data,
                "rate_table": rate_table,
                "zone": zone,
                "question": user_question
            }

            content = types.Content(
                role="user",
                parts=[
                    types.Part(text="Run invoice anomaly detection pipeline."),
                    types.Part(text=json.dumps(input_payload))
                ]
            )
            runner = Runner(agent=SequentialInvoiceAnomalyAgent, app_name=APP_NAME, session_service=session_service)
            agent_to_display = AnomalyDetectorAgent.name

        else:
            st.error("❌ Could not determine which agent to use.")
            return

        final_response = ""
        try:
            async for event in runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content):
                if event.is_final_response() and event.content and event.content.parts:
                    final_response = "".join(part.text.strip() for part in event.content.parts)

        except Exception as e:
            st.error(f"❌ An error occurred during agent execution: {e}")
            return

        try:
            parsed = json.loads(final_response)

            # Show large tables smartly
            if isinstance(parsed, list):
                if len(parsed) > 10:
                    st.success("✅ Showing results in table format:")
                    st.dataframe(pd.DataFrame(parsed))
                elif parsed:
                    st.success("✅ Answer:")
                    st.write(pd.DataFrame(parsed))
                else:
                    st.info("✅ No results found.")

            elif isinstance(parsed, dict):
                st.success("✅ Answer:")
                st.json(parsed)

            else:
                st.success("✅ Answer:")
                st.write(parsed)

        except json.JSONDecodeError:
            st.success("✅ Answer:")
            st.write(final_response)
        except Exception as e:
            st.error(f"❌ Error parsing or displaying the output: {e}")
            st.success("✅ Raw Answer:")
            st.write(final_response)

    if selected_option == "Ask Contract Based Questions":
        asyncio.run(ask_agent("ContractQAAgent"))

    elif selected_option == "Ask About Anomaly":
        asyncio.run(ask_agent("SequentialInvoiceAnomalyAgent"))










