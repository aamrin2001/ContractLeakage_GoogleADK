# # runner/test_invoice_reader.py

# import sys, os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# from utils.file_reader import load_invoice_data
# import pandas as pd
# import json
# from pprint import pprint

# def main():
#     invoice_path = "datasets/SUBSET.xlsx"  # ✅ Make sure this file exists

#     # Run the extractor agent
#     result = load_invoice_data(invoice_path)

#     # Internal use (DataFrame)
#     invoice_df: pd.DataFrame = result["invoice_df"]
#     print("✅ Invoice DataFrame (first 5 rows):")
#     print(invoice_df.head())

#     # LLM use (JSON)
#     invoice_json = result["invoice_json"]
#     print("\n✅ Invoice JSON (first 3 rows):")
#     pprint(invoice_json[:3])

#     # Optional: save to disk for downstream
#     with open("runner/output_invoice.json", "w") as f:
#         json.dump(invoice_json, f, indent=2)


# #if __name__ == "__main__":
# #    main()

# def get_invoice_data():
#     invoice_path = "datasets/SUBSET.xlsx"
#     result = load_invoice_data(invoice_path)
#     return result["invoice_df"], result["invoice_json"]

# # Add this to run directly only when executed as script
# if __name__ == "__main__":
#     invoice_df, invoice_json = get_invoice_data()
#     print(invoice_df.head())

# runner/test_invoice_reader.py

# runner/test_invoice_reader.py

import os
import sys
import json
import asyncio
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.invoice_extractor import run_invoice_reader_agent

APP_NAME = "invoice_reader"
USER_ID = "test_user"
SESSION_ID = "invoice_session_01"

async def main():
    file_path = input("📄 Enter invoice Excel path: ").strip()
    if not file_path or not os.path.exists(file_path):
        print("❌ Invalid or missing file path.")
        return

    # Run the invoice reader
    result = run_invoice_reader_agent(file_path)

    # Create output directory if not exists
    os.makedirs("runner", exist_ok=True)

    # Save JSON output
    with open("runner/output_invoice.json", "w", encoding="utf-8") as f:
        json.dump(result["invoice_json"], f, indent=2)

    # Save CSV output
    df: pd.DataFrame = result["invoice_df"]
    df.to_csv("runner/output_invoice.csv", index=False)

    print("\n✅ Invoice Reader Output:")
    print(f"- Rows extracted: {len(result['invoice_json'])}")
    print(f"- CSV saved to: runner/output_invoice.csv")

if __name__ == "__main__":
    asyncio.run(main())
