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
def string_to_words(string: str) -> list[str]:
    words = re.findall(r"[A-Za-z']+", string.lower())
    return words


# 4 - Clean up list of words
# 4a - Remove single-character elements from the list
def remove_single_character_elements(words: list) -> str:
    words = [word for word in words if len(word) > 1]
    return words


# 4b - Check against English spellcheck dictionaries
#       to remove elements which are not words
def filter_by_spellcheck(words: list) -> list:
    en_dictionary = enchant.Dict("en")
    us_dictionary = enchant.Dict("en_US")
    gb_dictionary = enchant.Dict("en_GB")
    ca_dictionary = enchant.Dict("en_CA")
    au_dictionary = enchant.Dict("en_AU")
    words = [
        word
        for word in words
        if en_dictionary.check(word)
        or us_dictionary.check(word)
        or gb_dictionary.check(word)
        or ca_dictionary.check(word)
        or au_dictionary.check(word)
    ]
    return words


def clean_wordlist(words: list) -> list:
    words = remove_single_character_elements(words)
    words = filter_by_spellcheck(words)
    return words


# 5 - Make list of most frequent words

# 6 - Transliterate English words with katakana

# 7 - Translate English words to Japanese (google)

# 8 - Transliterate Japanese into hiragana, katakana, romaji

# 9 - Output to CSV?

# 10 - Output to Google Sheet (new worksheet)
# 10a - move "main" sheet to "backup-<date>"
# 10b - Create new "main" sheet to use for output


if __name__ == "__main__":
    # with open("output.txt", "w") as opened_file:
    #     opened_file.write(pdfs_to_string())

    words = string_to_words(pdfs_to_string())
    words = clean_wordlist(words)
    print(*words, sep=", ")
