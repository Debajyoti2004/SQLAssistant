import pandas as pd

def offer_download_df(dataframe, default_filename="output_table"):
    if dataframe is None or dataframe.empty:
        print("⚠️ No data to download.")
        return

    while True:
        choice = input("💬 Do you want to download this table? (yes/no): ").strip().lower()
        if choice == 'yes':
            format_choice = input("📂 Download as (c)sv or (e)xcel? ").strip().lower()
            filename_base = input(f"📝 Enter filename (without extension, default: {default_filename}): ").strip()
            if not filename_base:
                filename_base = default_filename

            try:
                if format_choice.startswith('c'):
                    filename = f"{filename_base}.csv"
                    dataframe.to_csv(filename, index=False)
                    print(f"✅ Table saved as {filename}")
                elif format_choice.startswith('e'):
                    filename = f"{filename_base}.xlsx"
                    dataframe.to_excel(filename, index=False)
                    print(f"✅ Table saved as {filename}")
                else:
                    print("❌ Invalid format choice. Please choose 'c' or 'e'.")
                    continue
                break
            except Exception as e:
                print(f"🔥 Error saving file: {e}")
                break
        elif choice == 'no':
            break
        else:
            print("❗ Invalid input. Please type 'yes' or 'no'.")

def display_df_preview(df, title="Data Preview"):
    if df is None or df.empty:
        print(f"📭 [{title}] No data to display.")
        return
    print(f"\n📊 [{title} (first 5 rows)]")
    print(df.head().to_string())
