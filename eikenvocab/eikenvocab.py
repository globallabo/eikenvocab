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
def pdfs_to_string(
    input_path: str = pathlib.Path(__file__).parent.parent.absolute() / "data/",
) -> str:
    print(input_path)
    output_str = ""
    filelist = input_path.glob("*.pdf")
    for file in filelist:
        # because path is object not string
        path_in_str = str(file)
        print(path_in_str)
        with tempfile.TemporaryDirectory() as output_path:
            pages = pdf2image.convert_from_path(
                file, dpi=500, output_folder=output_path
            )
            print(type(pages))
            # the first and last pages have no English, so drop them
            pages = pages[1:-1]
            pagenum = 1
            for page in pages:
                print(type(page))
                print(pagenum)
                pagenum += 1
                output_str += pytesseract.image_to_string(page)
    return output_str


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
    with open("output.txt", "w") as opened_file:
        opened_file.write(pdfs_to_string())
