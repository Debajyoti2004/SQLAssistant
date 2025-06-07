import sqlite3
import pandas as pd
from table_utils import offer_download_df, display_df_preview

class DatabaseManager:
    def __init__(self, db_name="assistant_db.sqlite"):
        self.db_name = db_name
        self.conn = None

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.conn.row_factory = sqlite3.Row
            print(f"✅ Successfully connected to database: {self.db_name}")
            return True
        except sqlite3.Error as e:
            print(f"❌ Error connecting to database '{self.db_name}': {e}")
            self.conn = None
            return False

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            print(f"🔒 Database connection to '{self.db_name}' closed.")

    def execute_query(self, sql_query, params=None, fetch_all=False, fetch_one=False, is_ddl_dml=False, show_code=True):
        if not self.conn:
            print("⚠️ Error: No active database connection.")
            if not self.connect():
                return None

        if show_code:
            print("\n🔍 [SQL EXECUTING]")
            print("──────────────────────────────")
            print(sql_query)
            if params:
                print("📌 Parameters:", params)
            print("──────────────────────────────")

        cursor = self.conn.cursor()
        try:
            cursor.execute(sql_query, params or ())

            if is_ddl_dml:
                self.conn.commit()
                print("✅ Query executed successfully (DDL/DML).")
                return True

            result = None
            if fetch_all:
                result = cursor.fetchall()
                if result:
                    df = pd.DataFrame(result, columns=[desc[0] for desc in cursor.description])
                    print("\n📊 [QUERY RESULT]")
                    print(df.to_string() if not df.empty else "No rows returned.")
                    return df
                else:
                    print("ℹ️ Query executed, no results to fetch.")
                    return pd.DataFrame()
            elif fetch_one:
                result = cursor.fetchone()
                if result:
                    row_dict = dict(result)
                    print("\n📄 [QUERY RESULT (Single Row)]")
                    print(row_dict)
                    return row_dict
                else:
                    print("ℹ️ Query executed, no single row result to fetch.")
                    return None

            if not is_ddl_dml and not fetch_all and not fetch_one:
                print("✅ Query executed (no fetch specified).")
                return True

        except sqlite3.Error as e:
            print(f"🚨 SQL Error: {e}")
            self.conn.rollback()
            return None

    def list_tables(self, show_output=True):
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        tables_df = self.execute_query(query, fetch_all=True, show_code=False)
        if tables_df is not None and not tables_df.empty:
            table_names = tables_df['name'].tolist()
            if show_output:
                print("\n📁 --- Available Tables ---")
                for name in table_names:
                    print(f"🔸 {name}")
            return table_names
        else:
            if show_output:
                print("❌ No user tables found.")
            return []

    def get_table_columns(self, table_name):
        query = f"PRAGMA table_info({table_name});"
        if not self.conn:
            self.connect()
        if not self.conn:
            return []

        cursor = self.conn.cursor()
        try:
            cursor.execute(query)
            columns_info = cursor.fetchall()
            if columns_info:
                return [col_info['name'] for col_info in columns_info]
            return []
        except sqlite3.Error as e:
            print(f"⚠️ Error fetching column info for {table_name}: {e}")
            return []

    def load_df_to_table(self, df, table_name, if_exists='replace'):
        if df is None or df.empty:
            print(f"❌ Cannot load empty DataFrame to table '{table_name}'.")
            return False
        if not self.conn:
            print("⚠️ Error: No active database connection to load DataFrame.")
            if not self.connect():
                return False

        df.columns = [col.replace(' ', '_').replace('-', '_').replace('.', '_').replace('(', '').replace(')', '') for col in df.columns]
        df.columns = ['_'.join(filter(None, c.split('_'))) for c in df.columns]

        print(f"\n📥 Loading DataFrame into SQL table: '{table_name}' (if_exists='{if_exists}')")
        print("[🧾 SQL CODE GENERATED (Conceptual - via Pandas)]")
        print(f"DataFrame with columns {df.columns.tolist()} to be loaded into '{table_name}'.")

        try:
            df.to_sql(table_name, self.conn, if_exists=if_exists, index=False)
            print(f"✅ DataFrame successfully loaded into table '{table_name}'.")
            preview_df = self.execute_query(f"SELECT * FROM {table_name} LIMIT 3;", fetch_all=True, show_code=False)
            display_df_preview(preview_df, f"👀 Preview of '{table_name}' from DB")
            return True
        except Exception as e:
            print(f"🚨 Error loading DataFrame to SQL table '{table_name}': {e}")
            return False


if __name__ == "__main__":
    df = pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie"],
        "Age": [25, 30, 35],
        "City": ["New York", "Los Angeles", "Chicago"]
    })

    db = DatabaseManager("test_db.sqlite")
    db.connect()
    db.load_df_to_table(df, "people")
    db.list_tables()
    result_df = db.execute_query("SELECT * FROM people;", fetch_all=True)
    db.close()
