from PIL import Image
import pytesseract
import fitz
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
from gspread.models import Cell
from oauth2client.service_account import ServiceAccountCredentials
from googletrans import Translator
from google.cloud import translate_v2 as translate  # type: ignore # pylance complains about this
import requests
from bs4 import BeautifulSoup
import pykakasi
import jaconv
from datetime import datetime


# 1 - Convert PDFs to images
# 2 - OCR images to text
# def pdfs_to_string(
#     input_path: str = pathlib.Path(__file__).parent.parent.absolute() / "data/",
#     drop_first_and_last_pages: bool = True,
# ) -> str:
#     print("Starting PDF reading and OCR extraction ...")
#     output_string = ""
#     filelist = input_path.glob("*.pdf")
#     for file in filelist:
#         with tempfile.TemporaryDirectory() as output_path:
#             pages = pdf2image.convert_from_path(
#                 file, dpi=500, output_folder=output_path
#             )
#             if drop_first_and_last_pages:
#                 # the first and last pages have no English, so drop them
#                 pages = pages[1:-1]
#             for page in pages:
#                 output_string += pytesseract.image_to_string(page)
#     print("Finished PDF reading and OCR extraction")
#     return output_string


# Try using the text layer in the PDF instead of OCR
def pdfs_to_string(
    input_path: str = pathlib.Path(__file__).parent.parent.absolute() / "data/",
    drop_first_and_last_pages: bool = True,
) -> str:
    # print("Starting PDF reading and text layer extraction ...")
    output_string = ""
    filelist = input_path.glob("*.pdf")
    for file in filelist:
        pages = fitz.open(file)
        if drop_first_and_last_pages:
            selection = list(range(1, pages.pageCount - 1))
            pages.select(selection)
        for page in pages:
            output_string += page.get_text()
    # print("Finished PDF reading and text layer extraction")
    return output_string


# 3 - Make list of all words
def string_to_words(string: str) -> list[str]:
    # the text results from the PDF often have a curly apostrophe, so replace it
    string = string.replace("’", "'")
    # include any words made of letters and the apostrophe, for contractions
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
def get_most_frequent_words(words: list, limit: int = 10000) -> list:
    words = Counter(words).most_common(limit)
    return words


# 6 - Transliterate English words with katakana pronunciation
def english_to_katakana(word: str) -> str:
    url = "https://freeenglish.jp/convertp.php"
    mydata = {"englishtext": word, "prontype": "kana"}

    try:
        response = requests.post(url, data=mydata)
        soup = BeautifulSoup(response.content, "html.parser")
        katakana_pronunciation = soup.select_one(".kana").text
    except AttributeError:
        katakana_pronunciation = "none"
    return katakana_pronunciation


# 7 - Translate English words to Japanese (google)
def english_to_japanese(word: str) -> str:
    # translator = Translator()
    # translation = translator.translate(word, src="en", dest="ja")
    # return translation.text
    # set environment variable to credentials file location
    # TODO - convert to pathlib path
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "translatecreds.json"
    translate_client = translate.Client()
    target_language = "ja"
    translation = translate_client.translate(word, target_language=target_language)
    return translation["translatedText"]


# 8 - Transliterate Japanese into hiragana, katakana, romaji
def japanese_to_hiragana(word: str) -> str:
    kks = pykakasi.kakasi()
    transliterationresult = kks.convert(word)
    # the above result is tokenized by what kakasi thinks are
    #  the words in the Japanese string, so we need to loop
    #  through the result and concatenate the words
    hiragana = ""
    for item in transliterationresult:
        hiragana = hiragana + item["hira"]
    return hiragana


# 9 - Output to Google Sheet (new worksheet)
def write_gsheet(wordlist: list[dict], grade: str):
    max_rows = len(wordlist) + 10
    max_cols = len(wordlist[0]) + 2
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    client = gspread.authorize(creds)
    vocabsheet = client.open("Eiken Vocabulary")
    try:
        worksheet = vocabsheet.add_worksheet(
            title=f"grade_{grade}", rows=max_rows, cols=max_cols, index=0
        )
        print(f"Successfully added Grade {grade} sheet.")
    except gspread.exceptions.APIError:
        last_position = len(vocabsheet.worksheets()) - 1
        print(f"Grade {grade} worksheet exists; backing up before creating ...")
        backup_sheet_name = f"grade_{grade}-backup_" + datetime.now().strftime(
            "%Y-%m-%d_%H.%M.%S"
        )
        vocabsheet.duplicate_sheet(
            source_sheet_id=vocabsheet.worksheet(title=f"grade_{grade}").id,
            new_sheet_name=backup_sheet_name,
            insert_sheet_index=last_position,
        )
        vocabsheet.del_worksheet(vocabsheet.worksheet(title=f"grade_{grade}"))
        worksheet = vocabsheet.add_worksheet(
            title=f"grade_{grade}", rows=max_rows, cols=max_cols, index=0
        )
        print(f"Successfully added Grade {grade} sheet.")
    # Use the dictionary keys to create the header row
    for index, key in enumerate(wordlist[0]):
        worksheet.update_cell(row=1, col=index + 1, value=key)
    worksheet.format("1", {"textFormat": {"bold": True}, "wrapStrategy": "WRAP"})
    worksheet.freeze(rows=1)

    # use a list to contain gspread Cell objects, which can be batch written
    cells = []
    row = 2
    for word in wordlist:
        column = 1
        for value in word.values():
            # print(f"Row: {row}, Column: {column}, Value: {value}")
            # print(type(value))
            cells.append(Cell(row=row, col=column, value=value))
            # worksheet.update_cell(row, column, value)
            column += 1
        row += 1
    # write in a batch
    worksheet.update_cells(cells)


def main():
    # words = [
    #     ("mail", 1),
    #     ("sell", 1),
    #     ("something", 1),
    #     ("pet", 1),
    #     ("fever", 1),
    #     ("there", 1),
    #     ("father", 1),
    #     ("your", 1),
    #     ("here", 1),
    #     ("be", 1),
    #     ("is", 1),
    #     ("are", 1),
    #     ("was", 1),
    #     ("being", 1),
    #     ("been", 1),
    #     ("go", 1),
    #     ("goes", 1),
    #     ("going", 1),
    #     ("went", 1),
    #     ("gone", 1),
    #     ("have", 1),
    #     ("has", 1),
    #     ("having", 1),
    #     ("had", 1),
    #     ("walk", 1),
    #     ("walks", 1),
    #     ("walking", 1),
    #     ("walked", 1),
    #     ("work", 1),
    #     ("works", 1),
    #     ("working", 1),
    #     ("worked", 1),
    #     ("take", 1),
    #     ("takes", 1),
    #     ("taking", 1),
    #     ("took", 1),
    #     ("help", 1),
    #     ("helps", 1),
    #     ("helping", 1),
    #     ("helped", 1),
    # ]

    # p2 and p1 are for Grades Pre-2 and Pre-1
    grades = ["5", "4", "3", "p2", "2", "p1", "1"]
    # grades = ["5"]
    base_path = pathlib.Path(__file__).parent.parent.absolute() / "data"
    for grade in grades:
        print(f"Starting Grade {grade} ...")
        input_path = base_path / f"grade_{grade}"
        words = string_to_words(pdfs_to_string(input_path=input_path))
        words = clean_wordlist(words)
        words = get_most_frequent_words(words)
        wordlist = []
        for wordcount in words:
            word, count = wordcount
            pronunciation_kata = english_to_katakana(word)  # Katakana to Hiragana
            pronunciation_hira = jaconv.kata2hira(pronunciation_kata)
            translation_kanji = english_to_japanese(word)
            translation_hiragana = japanese_to_hiragana(translation_kanji)
            worddict = {
                "Word": word,
                "Frequency": count,
                "Pronunciation (katakana)": pronunciation_kata,
                "Pronunciation (hiragana)": pronunciation_hira,
                "Translation (kanji)": translation_kanji,
                "Translation (hiragana)": translation_hiragana,
            }
            wordlist.append(worddict)

            # print(
            #     f"Word: {word}, Count: {count}, pronunciation: {pronunciation}, Translation: {translation}, Hiragana: {hiragana}"
            # )
            # print(
            #     f"Word: {word}, pronunciation (Katakana): {pronunciation_kata}, pronunciation (Hiragana): {pronunciation_hira}, Translation (Kanji): {translation_kanji}, Translation (Hiragana): {translation_hiragana}"
            # )
            # Necessary to prevent rate-limiting by the Google translate API
            # time.sleep(5)
        # print(*words, sep=", ")
        write_gsheet(wordlist=wordlist, grade=grade)
        print(f"Finished Grade {grade}.")


if __name__ == "__main__":
    main()
