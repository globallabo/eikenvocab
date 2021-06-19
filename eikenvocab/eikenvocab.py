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
from googletrans import Translator
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pykakasi

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
def get_most_frequent_words(words: list, limit: int = 1000) -> list:
    words = Counter(words).most_common(limit)
    return words


# 6 - Transliterate English words with katakana
def english_to_katakana(word: str) -> str:
    # headers = {
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    # }
    # url = f"https://www.sljfaq.org/cgi/e2k.cgi?word={word}"
    # response = requests.get(url, headers=headers)
    # # print(response.content)
    # soup = BeautifulSoup(response.content, "html.parser")
    # katakana_pronunciation = soup.select_one("#katakana-string").text.strip()
    # headers = {
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    # }
    # url = f"https://japanga.com/name-converter#?q={word}"
    # response = requests.get(url, headers=headers)
    # # print(response.content)
    # soup = BeautifulSoup(response.content, "html.parser")
    # katakana_pronunciation = soup.select_one(".name-katakana").text.strip()
    url = f"https://japanga.com/name-converter#?q={word}"
    max_delay = 10
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-gpu")
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--window-size=1920,1080")
    # webdriver_path = "/usr/bin/chromedriver"
    driver = webdriver.Chrome(options=chrome_options)
    # driver.implicitly_wait(20)
    driver.get(url)
    try:
        katakana_pronunciation = (
            WebDriverWait(driver, max_delay)
            .until(EC.visibility_of_element_located((By.CLASS_NAME, "nc-katakana")))
            .text
        )
    finally:
        driver.quit()
    return katakana_pronunciation


# 7 - Translate English words to Japanese (google)
def english_to_japanese(word: str) -> str:
    translator = Translator()
    translation = translator.translate(word, src="en", dest="ja")
    return translation.text


# 8 - Transliterate Japanese into hiragana, katakana, romaji
def japanese_to_hiragana(word: str) -> str:
    kks = pykakasi.kakasi()
    transliterationresult = kks.convert(word)
    return transliterationresult[0]["hira"]


# 9 - Output to CSV?

# 10 - Output to Google Sheet (new worksheet)
# 10a - move "main" sheet to "backup-<date>"
# 10b - Create new "main" sheet to use for output


if __name__ == "__main__":
    # with open("output.txt", "w") as opened_file:
    #     opened_file.write(pdfs_to_string())

    # words = string_to_words(pdfs_to_string())
    # words = clean_wordlist(words)
    # words = get_most_frequent_words(words)
    words = [("mail", 1), ("sell", 1), ("something", 1), ("pet", 1), ("fever", 1)]
    print(len(words))
    print(type(words))
    for wordcount in words:
        print(wordcount)
        print(type(wordcount))
        word, count = wordcount
        transliteration = english_to_katakana(word)
        translation = english_to_japanese(word)
        hiragana = japanese_to_hiragana(translation)
        print(
            f"Word: {word}, Count: {count}, Transliteration: {transliteration}, Translation: {translation}, Hiragana: {hiragana}"
        )
    # print(*words, sep=", ")
    print(len(words))
