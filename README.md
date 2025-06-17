
# 📄 Contract & Invoice Intelligence using Google ADK

This project leverages **Google's Agent Development Kit (ADK)** to build intelligent agents that extract, interpret, and analyze data from logistics contracts and invoices. The goal is to automate document understanding for use cases like contract-based Q\&A, rate extraction, invoice data normalization, and anomaly detection.

### 🔧 Components

* **Contract Reader Agent**
  Extracts full text and rate tables from scanned or digital logistics contracts (PDFs). Outputs structured text, JSON tables, and CSVs for downstream use.

* **Contract QA Agent**
  Takes user questions and answers them based on the extracted contract content, using LLM reasoning while staying grounded to contract facts.

* **Invoice Reader Agent**
  Processes Excel-based invoice files, normalizes headers, and extracts structured data in both JSON and CSV formats.

* **Streamlined Runner Scripts**
  CLI interfaces for triggering each agent independently, saving outputs for manual inspection or further LLM-based validation.

### 🚀 Goals

* Build a modular, local-friendly document intelligence framework
* Enable automated contract Q\&A and charge validation
* Support future integration with RAG pipelines or audit dashboards

