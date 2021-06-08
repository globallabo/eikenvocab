from PIL import Image
import pytesseract
import sys
import pathlib
import tempfile
import pdf2image
import os
import re
from collections import Counter
import csv
import enchant
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1 - Convert PDFs to images
# 2 - OCR images to text
def pdfs_to_string(
    input_path: str = pathlib.Path(__file__).parent.parent.absolute() / "data/",
    drop_first_and_last_pages: bool = True,
) -> str:
    output_string = ""
    filelist = input_path.glob("*.pdf")
    for file in filelist:
        with tempfile.TemporaryDirectory() as output_path:
            pages = pdf2image.convert_from_path(
                file, dpi=500, output_folder=output_path
            )
            if drop_first_and_last_pages:
                # the first and last pages have no English, so drop them
                pages = pages[1:-1]
            for page in pages:
                output_string += pytesseract.image_to_string(page)
    return output_string


# 3 - Make list of all words

# 4 - Clean up list of words

# 5 - Count word frequency

# 6 - Transliterate English words with katakana

# 7 - Translate English words to Japanese (google)

# 8 - Transliterate Japanese into hiragana, katakana, romaji

# 9 - Output to CSV?

# 10 - Output to Google Sheet (new worksheet)


if __name__ == "__main__":
    with open("output.txt", "w") as opened_file:
        opened_file.write(pdfs_to_string())
