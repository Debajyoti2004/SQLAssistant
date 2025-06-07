import os
import re
from dotenv import load_dotenv
import time
import pandas as pd
import google.generativeai as genai

load_dotenv()

from file_handler import read_data_file
from database_manager import DatabaseManager
from image_extractor import ImageHandler 
from paragraph_handler import ParagraphHandler
from sql_assistant_gui import SQLAssistantGUI

class SQLAssistant:
    def __init__(self, gui: SQLAssistantGUI, db_name="assistant_db.sqlite"):
        self.gui = gui
        self.db_mgr = DatabaseManager(db_name)
        self.image_handler = None
        self.paragraph_handler = None
        self.text_to_sql_model = None
        self._init_llm_handlers()

    def _init_llm_handlers(self):
        image_api_key = os.getenv("IMAGE_GOOGLE_API_KEY")
        if image_api_key:
            self.image_handler = ImageHandler(api_key=image_api_key)
        
        text_api_key = os.getenv("GOOGLE_API_KEY")
        if text_api_key:
            genai.configure(api_key=text_api_key)
            self.paragraph_handler = ParagraphHandler(api_key=text_api_key)
            self.text_to_sql_model = genai.GenerativeModel("gemini-1.5-flash")

    def run(self):
        self.gui.display_message("Welcome!", "👋 SQL Assistant Starting Up!", symbol="🤖")
        if not self.db_mgr.connect():
            self.gui.display_message("Error", "❌ Oh no! I couldn't connect to the database.", symbol="🚨")
            return
        
        time.sleep(1.5)
        try:
            while True:
                choice = self.gui.prompt_for_menu_choice("Main Menu", "What would you like to do?", self.main_menu_options)
                if not choice or choice == '0':
                    break
                self._process_choice(choice)
        finally:
            self.db_mgr.close()
            self.gui.display_message("Goodbye!", "Talk to you later! 👋", symbol="🚪")
            time.sleep(2)
            self.gui.root.quit()

    @property
    def main_menu_options(self):
        return [
            {"value": "1", "text": "📄 Scan File (CSV/Excel)"}, {"value": "2", "text": "🖼️ Extract Table from Image"},
            {"value": "3", "text": "🗣️ Chat with Data (Natural Language Query)"}, {"value": "4", "text": "↔️ Move/Copy Data Between Tables"},
            {"value": "5", "text": "📝 Create Table from Paragraph"}, {"value": "6", "text": "📋 List All Tables"},
            {"value": "7", "text": "💻 Execute Custom SQL Query"}, {"value": "0", "text": "🚪 Exit"}
        ]
        
    def _process_choice(self, choice):
        needs_return_prompt = True

        if choice == '1': self._handle_scan_file()
        elif choice == '2': self._handle_image_to_table()
        elif choice == '3':
            self._handle_natural_language_query()
            needs_return_prompt = False
        elif choice == '4': self._handle_move_data()
        elif choice == '5': self._handle_paragraph_to_table()
        elif choice == '6': self._list_all_tables()
        elif choice == '7': self._handle_custom_sql()
        else:
            self.gui.display_message("Invalid Choice", "Please select a valid option from the menu.", symbol="❓")

        if needs_return_prompt:
            self.gui.root.update_idletasks()
            self.gui.prompt_for_menu_choice("Action Complete", "Press button to return to Main Menu.", [{"value": "ok", "text": "Return to Menu"}])

    def _sanitize_table_name(self, raw_name, default_suggestion="new_table"):
        final_name = re.sub(r'\W+', '_', raw_name).strip('_')
        if not final_name: final_name = default_suggestion
        return final_name
        
    def _offer_download(self, df: pd.DataFrame, filename: str):
        if df is not None and not df.empty:
            try:
                output_filename = f"{filename}.csv"
                df.to_csv(output_filename, index=False)
                self.gui.update_status(f"Success! Full table also saved as {output_filename}")
            except Exception as e:
                self.gui.update_status(f"Could not save file: {e}")

    def _list_all_tables(self):
        tables = self.db_mgr.list_tables(show_output=True)
        if tables:
            df = pd.DataFrame(tables, columns=["Available Tables"])

            self.gui.update_status("🚀 Wait for 10 seconds.")
            self.gui.display_table(df, "Database Tables")
            time.sleep(10)
        else:
            self.gui.display_message("Info", "No tables in the database yet.", symbol="📂")

    def _handle_scan_file(self):
        file_path = self.gui.prompt_for_file("a data file (CSV/Excel)")
        if not file_path: return
        
        self.gui.display_message("Processing", f"Reading file: {os.path.basename(file_path)}...", symbol="⚙️")
        df, suggested_name = read_data_file(file_path)
        
        if df is not None:
            self.gui.display_table(df, f"Full Data from: {os.path.basename(file_path)}")
            self.gui.root.update_idletasks()
            self._offer_download(df, suggested_name)
            
            raw_table_name = self.gui.prompt_for_text_input(f"Enter table name to save this data (default: {suggested_name})")
            table_name = self._sanitize_table_name(raw_table_name or suggested_name)
            
            if self.db_mgr.load_df_to_table(df, table_name):
                self.gui.display_message("Success!", f"🎉 Data loaded into table '{table_name}'.", symbol="✅")
            else:
                self.gui.display_message("Error", f"😬 Failed to load data into '{table_name}'.", symbol="❌")
        else:
            self.gui.display_message("Error", "Could not read the uploaded file.", symbol="❌")

    def _handle_image_to_table(self):
        if not self.image_handler:
            self.gui.display_message("Feature Unavailable", "Image Handler is not ready. Check your API key.", symbol="🖼️")
            return
        
        image_path = self.gui.prompt_for_file("an image file (PNG/JPG)")
        if not image_path: return

        self.gui.display_message("Processing", "Asking Gemini Vision to extract table...", symbol="🤖")
        df, suggested_name = self.image_handler.image_to_dataframe(image_path)

        if df is not None and not df.empty:
            self.gui.display_table(df, f"Table from {os.path.basename(image_path)}")
            self.gui.root.update_idletasks()
            self._offer_download(df, suggested_name)
            
            raw_table_name = self.gui.prompt_for_text_input(f"Enter table name to save this data (default: {suggested_name})")
            table_name = self._sanitize_table_name(raw_table_name or suggested_name)
            
            if self.db_mgr.load_df_to_table(df, table_name):
                self.gui.display_message("Success!", f"✨ Image table '{table_name}' saved.", symbol="✅")
            else:
                self.gui.display_message("Error", f"😥 Failed to save image table '{table_name}'.", symbol="❌")
        else:
            self.gui.display_message("Error", "❌ Gemini Vision failed to extract a table.", symbol="💥")

    def _handle_paragraph_to_table(self):
        if not self.paragraph_handler:
            self.gui.display_message("Feature Unavailable", "Paragraph Handler is not ready. Check API key.", symbol="📝")
            return

        paragraph = self.gui.prompt_for_text_input("Paste or type your paragraph below:")
        if not paragraph: return

        self.gui.display_message("Processing", "Asking Gemini to analyze the paragraph...", symbol="🤖")
        df = self.paragraph_handler.paragraph_to_table(paragraph)

        if df is not None and not df.empty:
            self.gui.display_table(df, "Table Extracted from Paragraph")
            self.gui.root.update_idletasks()
            self._offer_download(df, "paragraph_extract")
            
            raw_table_name = self.gui.prompt_for_text_input("Enter table name for this data:")
            table_name = self._sanitize_table_name(raw_table_name, "paragraph_data")

            if self.db_mgr.load_df_to_table(df, table_name):
                self.gui.display_message("Success!", f"🎉 Paragraph data saved to table '{table_name}'.", symbol="✅")
            else:
                self.gui.display_message("Error", f"😥 Failed to save paragraph table '{table_name}'.", symbol="❌")
        else:
            self.gui.display_message("Error", "❌ Gemini could not create a structured table from the text.", symbol="💥")

    def _handle_custom_sql(self):
        custom_sql = self.gui.prompt_for_text_input("Enter your custom SQL query:")
        if not custom_sql: return

        self.gui.update_status("🚀 Executing your custom SQL...")
        sql_lower = custom_sql.lower().strip()
        is_select = sql_lower.startswith("select") or sql_lower.startswith("pragma")
        
        result_df = self.db_mgr.execute_query(custom_sql, fetch_all=is_select)

        if is_select and result_df is not None:
            
            self.gui.display_table(result_df, "Custom Query Result")
            self._offer_download(result_df, "custom_query_result")
            self.gui.update_status("🚀 Wait till 15 seconds .Till then see what you can do with it.")
            time.sleep(15)
        elif result_df is True:
            self.gui.display_message("Success", "✅ Your query was executed successfully.", symbol="👍")
        else:
            self.gui.display_message("Error", "❌ Your SQL query failed to execute. Check the console for database errors.", symbol="💥")
            
    def _handle_move_data(self):
        tables = self.db_mgr.list_tables(show_output=False)
        if len(tables) < 1:
            self.gui.display_message("Info", "You need at least one table to act as a source.", symbol="📂")
            return

        source_options = [{"value": t, "text": t} for t in tables]
        source_table = self.gui.prompt_for_menu_choice("Select Source Table", "Which table do you want to move data FROM?", source_options)
        if not source_table: return

        cols = self.db_mgr.get_table_columns(source_table)
        self.gui.display_message("Info", f"Columns in '{source_table}': {', '.join(cols)}", symbol="📜")
        self.gui.root.update_idletasks()
        
        cols_to_select = self.gui.prompt_for_text_input(f"Columns to select from '{source_table}' (e.g., col1, col2 or * for all):") or "*"
        where_clause = self.gui.prompt_for_text_input(f"Enter a WHERE clause for '{source_table}' (optional):")
        
        dest_table_name_raw = self.gui.prompt_for_text_input("Enter destination table name (can be new):")
        if not dest_table_name_raw: return
        dest_table_name = self._sanitize_table_name(dest_table_name_raw)

        select_query = f"SELECT {cols_to_select} FROM {source_table}"
        if where_clause: select_query += f" WHERE {where_clause}"

        preview_df = self.db_mgr.execute_query(f"{select_query} LIMIT 5;", fetch_all=True)
        if preview_df is None: 
            self.gui.display_message("Error", "Preview query failed. Check your syntax.", symbol="💥")
            return
        
        self.gui.display_table(preview_df, "Data to Move (Preview)")
        self.gui.root.update_idletasks()
        confirm = self.gui.prompt_for_menu_choice("Confirm Action", "Proceed with moving this data?", [{"value": "yes", "text": "Yes, Proceed"}, {"value": "no", "text": "No, Cancel"}])
        if confirm != "yes":
            self.gui.display_message("Cancelled", "Move operation cancelled.", symbol="🛑")
            return

        final_query = f"CREATE TABLE {dest_table_name} AS {select_query};"
        if dest_table_name in tables:
            final_query = f"INSERT INTO {dest_table_name} {select_query};"

        self.gui.update_status(f"Executing: {final_query}")
        if self.db_mgr.execute_query(final_query):
            self.gui.display_message("Success", f"✅ Data successfully moved/copied to '{dest_table_name}'.", symbol="🎉")
        else:
            self.gui.display_message("Error", "❌ The move/copy operation failed.", symbol="💥")

    def _handle_natural_language_query(self):
        tables = self.db_mgr.list_tables(show_output=True)
        if not tables:
            self.gui.display_message("Info", "No tables yet to chat about!", symbol="📂")
            self.gui.root.update_idletasks()
            self.gui.prompt_for_menu_choice("Action Complete", "Press button to return to Main Menu.", [{"value": "ok", "text": "Return to Menu"}])
            return

        table_options = [{"value": t, "text": t} for t in tables]
        table_name = self.gui.prompt_for_menu_choice("Select Table", "🗣️ Which table would you like to query?", table_options)
        if not table_name: return

        while True:
            natural_query = self.gui.prompt_for_text_input(f"What about '{table_name}'? (Type 'done' to exit)")
            if not natural_query or natural_query.lower() == 'done':
                break
            
            self.gui.update_status(f"Generating SQL for: {natural_query}")
            schema_str = f"Table '{table_name}' columns: {', '.join(self.db_mgr.get_table_columns(table_name))}"
            prompt = f"SQL generator for SQLite. Convert to SQL. Only SQL.\nContext:{schema_str}\nUser question for '{table_name}':\n\"{natural_query}\"\nSQL Query:"
            
            response = self.text_to_sql_model.generate_content(prompt)
            generated_sql = response.text.strip().replace("```sql", "").replace("```", "").strip()
            
            self.gui.display_message("Generated SQL", generated_sql, symbol="💡")
            self.gui.root.update_idletasks()
            time.sleep(1)

            result_df = self.db_mgr.execute_query(generated_sql, fetch_all=True)
            if result_df is not None:
                self.gui.display_table(result_df, f"Query Result for '{table_name}'")
                self._offer_download(result_df, f"{table_name}_query_result")
                self.gui.root.update_idletasks()