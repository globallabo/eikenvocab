from PIL import Image
import pytesseract
import sys
import pathlib
import tempfile
from pdf2image import convert_from_path
import os
import re
from collections import Counter
import csv
import enchant
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1 - Convert PDFs to images
def convert_pdfs(
    input_path: str = pathlib.Path(__file__).parent.parent.absolute() / "data/",
) -> str:
    print(input_path)
    filelist = input_path.glob("*.pdf")
    for file in filelist:
        # because path is object not string
        path_in_str = str(file)
        print(path_in_str)


# 2 - OCR images to text

# 3 - Make list of all words

# 4 - Clean up list of words

# 5 - Count word frequency

# 6 - Transliterate English words with katakana

# 7 - Translate English words to Japanese (google)

# 8 - Transliterate Japanese into hiragana, katakana, romaji

# 9 - Output to CSV?

# 10 - Output to Google Sheet (new worksheet)


if __name__ == "__main__":
    convert_pdfs()
