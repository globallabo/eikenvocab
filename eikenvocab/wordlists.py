# standard library imports
from pathlib import Path
import os
import re
from collections import Counter
from datetime import datetime
from typing import Optional

# third party imports
import fitz  # pyMuPDF - get text from PDFs
import enchant
import gspread
from gspread.models import Cell
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import translate_v2 as translate
import requests
from bs4 import BeautifulSoup
import pykakasi
import jaconv


def pdfs_to_string(
    input_path: str = Path(__file__).parent.parent.resolve() / "data/",
    drop_first_and_last_pages: bool = True,
) -> str:
    """Extract the text layer of a PDF file.

    Args:
        input_path (str, optional): Path to the source PDF files. Defaults to Path(__file__).parent.parent.resolve()/"data/".
        drop_first_and_last_pages (bool, optional): Whether to remove the first and last pages, which often don't have any content. Defaults to True.

    Returns:
        str: A string containing all of the text from the PDF files.
    """
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


def string_to_words(string: str) -> list[str]:
    """Scrape all the individual words from a string of text.

    Args:
        string (str): The input string.

    Returns:
        list[str]: A list of all words, in lowercase.
    """
    # the text results from the PDF often have a curly apostrophe, so replace it
    string = string.replace("’", "'")
    # include any words made of letters and the apostrophe, for contractions
    words = re.findall(r"[A-Za-z']+", string.lower())
    return words


def remove_single_character_elements(words: list[str]) -> list[str]:
    """Remove all single-character elements from a list of words (e.g. "a" and "I").

    Args:
        words (list[str]): A list of words to process.

    Returns:
        list[str]: A filtered list of words.
    """
    words = [word for word in words if len(word) > 1]
    return words


def filter_by_spellcheck(words: list[str]) -> list[str]:
    """Filter out any words from a list that can't be found in a spellcheck dictionary, leaving only real English words.

    Args:
        words (list[str]): A list of words to process.

    Returns:
        list[str]: A filtered list of words.
    """
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


def clean_wordlist(words: list[str]) -> list[str]:
    """Clean up a list of words, to get a list of only real, useful English words.

    Args:
        words (list[str]): A list of words to process.

    Returns:
        list[str]: A filtered list of words.
    """
    words = remove_single_character_elements(words)
    words = filter_by_spellcheck(words)
    return words


def get_most_frequent_words(
    words: list[str], limit: Optional[int] = None
) -> list[tuple]:
    """Get a list of the most frequent words from a list of words.

    Args:
        words (list[str]): A list of words to process
        limit (Optional[int], optional): The maximum number of words per list. Defaults to None.

    Returns:
        list[tuple]: A tuple containing a word and its frequency within the input list.
    """
    words = Counter(words).most_common(limit)
    return words


def english_to_katakana(word: str) -> str:
    """Transliterate an English word into its katakana pronunciation equivalent.

    Args:
        word (str): An English word.

    Returns:
        str: A katakana transliteration of the English word.
    """
    url = "https://freeenglish.jp/convertp.php"
    mydata = {"englishtext": word, "prontype": "kana"}

    try:
        response = requests.post(url, data=mydata)
        soup = BeautifulSoup(response.content, "html.parser")
        katakana_pronunciation = soup.select_one(".kana").text
    except AttributeError:
        katakana_pronunciation = "none"
    return katakana_pronunciation


def english_to_japanese(word: str) -> str:
    """Translate an English word into Japanese.

    Args:
        word (str): An English word.

    Returns:
        str: A Japanese translation of the English word.
    """
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(
        Path(__file__).parent.parent.resolve() / "translatecreds.json"
    )
    translate_client = translate.Client()
    target_language = "ja"
    translation = translate_client.translate(word, target_language=target_language)
    return translation["translatedText"]


def japanese_to_hiragana(word: str) -> str:
    """Transliterate a Japanese string which may contain kanji into one which only contains hiragana.

    Args:
        word (str): A string of Japanese text.

    Returns:
        str: A string with all kanji transliterated into hiragana.
    """
    kks = pykakasi.kakasi()
    transliterationresult = kks.convert(word)
    # the above result is tokenized by what kakasi thinks are
    #  the words in the Japanese string, so we need to loop
    #  through the result and concatenate the words
    hiragana = ""
    for item in transliterationresult:
        hiragana = hiragana + item["hira"]
    return hiragana


def make_wordlist(words: list[tuple]) -> list[dict]:
    """Make a list of words along with their associated pronunciations, translations, etc.

    Args:
        words (list[tuple]): A list of tuples containing words and their frequencies in the source material.

    Returns:
        list[dict]: A list of dictionaries containing the vocabulary words, their frequencies, pronunciations and translations.
    """
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
    return wordlist


def write_gsheet(wordlist: list[dict], grade: str):
    """Create a worksheet within a Google Sheets document and write to it a list of words and their pronunciations and translations. Any existing worksheet with the same name will first be backed up.

    Args:
        wordlist (list[dict]): A list of words, which are each a dictionary containing the fields like pronunciation and translation.
        grade (str): The grade level of the word list.
    """
    # sheetname = "Eiken Vocabulary"
    sheetname = "Eiken Vocabulary (testing)"
    max_rows = len(wordlist) + 10
    max_cols = len(wordlist[0]) + 2
    credsfile = Path(__file__).parent.parent.resolve() / "creds.json"
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credsfile, scope)
    client = gspread.authorize(creds)
    vocabsheet = client.open(sheetname)
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
