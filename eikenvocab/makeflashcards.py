# standard library imports
import pathlib
import pprint

# third party imports
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import jinja2
from weasyprint import HTML


# Get data from google Sheet (one grade at a time)
def get_data_for_grade(grade: str) -> list[str]:
    # Fetch data from Google Sheet
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("Eiken Vocabulary").worksheet(f"grade_{grade}")
        return sheet.get_all_values()
    except FileNotFoundError as fnf_error:
        print(fnf_error)
        return []


# create a list of dictionaries to loop over for each card
def make_wordlist(data: list[str]) -> list[dict]:
    wordlist = []
    # the first row of the data is the spreadsheet header, use as keys
    keys = data[0]
    # loop over the rest of the data, excluding the first row
    for word in data[1:]:
        wordlist.append(dict(zip(keys, word)))
    return wordlist


# use jinja2 to render an HTML template for the flashcards
def render_template(wordlist: list[dict]) -> str:
    template_loader = jinja2.FileSystemLoader(searchpath="./templates/")
    template_env = jinja2.Environment(loader=template_loader)
    TEMPLATE_FILE = "cards.html"
    template = template_env.get_template(TEMPLATE_FILE)
    template_path = pathlib.Path(__file__).parent.absolute() / "templates/"
    static_path = pathlib.Path(__file__).parent.absolute() / "static/"
    output_text = template.render(static_path=static_path, wordlist=wordlist)
    return output_text


# use weasyprint to render string of HTML into PDF
def render_pdf(content: str):
    filename = "card-test.pdf"
    # Create Weasyprint HTML object
    html = HTML(string=content)
    # Output PDF via Weasyprint
    html.write_pdf(filename)


def main():
    data = get_data_for_grade("5")
    wordlist = make_wordlist(data)
    content = render_template(wordlist)
    render_pdf(content)


if __name__ == "__main__":
    main()

# print(len(wordlist))
# pprint.pprint(wordlist[0:5])

# print("Keys:")
# print(data[0])
# print("Values:")
# print(data[1])
# worddict = dict(zip(data[0], data[1]))
# print("Dictionary:")
# print(worddict)

# templateLoader = jinja2.FileSystemLoader(searchpath="./templates/")
# templateEnv = jinja2.Environment(loader=templateLoader)
# TEMPLATE_FILE = "cards.html"
# template = templateEnv.get_template(TEMPLATE_FILE)
# template_path = pathlib.Path(__file__).parent.absolute() / "templates/"
# static_path = pathlib.Path(__file__).parent.absolute() / "static/"
# outputText = template.render(static_path=static_path, wordlist=wordlist)
# filename = "card-test.pdf"

# # print(outputText)
# # Create Weasyprint HTML object
# html = HTML(string=outputText)
# # Output PDF via Weasyprint
# html.write_pdf(filename)
