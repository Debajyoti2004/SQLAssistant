import os
import pandas as pd
import json
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

class ImageHandler:
    def __init__(self, api_key=os.getenv("IMAGE_GOOGLE_API_KEY")):
        self.api_key=api_key
        if not self.api_key:
            raise ValueError("❌ Gemini API key not provided. Set it in the constructor or as environment variable 'GEMINI_API_KEY'.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro-vision')
        print("✅ GeminiTableExtractor initialized successfully.")

    def is_gemini_available(self):
        return self.api_key is not None

    def image_to_dataframe(self, image_path):
        if not self.is_gemini_available():
            print("❌ Gemini API key is missing. Cannot process image.")
            return None, None
        
        if not os.path.exists(image_path):
            print(f"❌ Error: Image file not found at {image_path}")
            return None, None

        try:
            print("📌 Processing image with Gemini Vision model...")

            with open(image_path, "rb") as f:
                image_bytes = f.read()

            prompt = (
                "Extract the table from this image and return it in JSON array format. "
                "Preserve all headers and rows. Do not include commentary or description. "
                "Only return valid JSON."
            )

            response = self.model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_bytes}
            ])

            text_output = response.text.strip()
            print("\n🔍 [RAW GEMINI OUTPUT PREVIEW (first 500 chars)]")
            print(text_output[:500] + "..." if len(text_output) > 500 else text_output)

            try:
                data = json.loads(text_output)
                if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
                    raise ValueError("⚠️ Invalid table format received from Gemini.")
                df = pd.DataFrame(data)
                print("✅ Table parsed successfully into DataFrame.")
            except Exception as e:
                print(f"❌ Error parsing Gemini response: {e}")
                return None, None

            base_name = os.path.splitext(os.path.basename(image_path))[0]
            suggested_table_name = base_name.strip().replace(' ', '_') + "_gemini_table"

            return df, suggested_table_name

        except Exception as e:
            print(f"❌ Error processing image with Gemini: {e}")
            return None, None
        
if __name__ == "__main__":
    image_path = "sample_table.png" 

    extractor = ImageHandler()
    extracted_text,table_name = extractor.image_to_dataframe(image_path)

    print("\n🔍 Extracted Table:")
    print(extracted_text)

