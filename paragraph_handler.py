import pandas as pd
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv
load_dotenv()

class ParagraphHandler:
    def __init__(self,api_key = os.getenv("GOOGLE_API_KEY")):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def paragraph_to_table(self, paragraph):
        prompt = f"""
You are an expert data extractor.
Extract a structured table from the paragraph below. Return ONLY the table in valid Markdown format (starting and ending with a table).

Paragraph:
\"\"\"
{paragraph}
\"\"\"
"""
        print("\n--- Sending request to Gemini Pro ---")
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            print("\n--- Gemini Response ---")
            print(response_text)

            df = self._markdown_to_dataframe(response_text)
            return df
        except Exception as e:
            print(f"Error using Gemini Pro: {e}")
            return None

    def _markdown_to_dataframe(self, markdown_table):
        lines = [line.strip() for line in markdown_table.split("\n") if line.strip()]
        if len(lines) < 2 or '|' not in lines[0]:
            print("Markdown parsing failed. Not a valid table.")
            return None

        headers = [h.strip() for h in lines[0].strip('|').split('|')]
        data_rows = []
        for line in lines[2:]:
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            if len(cells) == len(headers):
                data_rows.append(cells)

        df = pd.DataFrame(data_rows, columns=headers)
        return df
    

if __name__ == "__main__":
    paragraph = """
    Elon Musk is the CEO of SpaceX and Tesla. He is 52 years old and lives in Texas.
    Sundar Pichai is the CEO of Google. He is 51 years old and resides in California.
    """

    handler = ParagraphHandler()
    df = handler.paragraph_to_table(paragraph)

    if df is not None:
        print("\n--- Final DataFrame ---")
        print(df)
    else:
        print("Failed to extract structured data.")

