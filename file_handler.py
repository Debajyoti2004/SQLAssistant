import pandas as pd
import os
import re

def read_data_file(file_path):
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return None, None
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            print("⚠️ Unsupported file type. Please use CSV or Excel.")
            return None, None
        print(f"✅ File '{file_path}' read successfully.")
        df.columns = [re.sub(r'\W+', '_', str(col)).strip('_') for col in df.columns]
        df.columns = [col if col else f"unnamed_col_{i}" for i, col in enumerate(df.columns)]
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        suggested_table_name = re.sub(r'\W+', '_', base_name).strip('_') + "_table"
        return df, suggested_table_name
    except Exception as e:
        print(f"🔥 Error reading or processing file '{file_path}': {e}")
        return None, None

if __name__ == "__main__":
    file_path = "test.csv"
    df, table_name = read_data_file(file_path)

    if df is not None:
        print(f"\n📋 Suggested Table Name: {table_name}")
        print("\n🔍 Data Preview:")
        print(df.head())
    else:
        print("❗ Failed to read the file.")
