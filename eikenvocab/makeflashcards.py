# standard library imports
import pathlib

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

data = get_data_for_grade("5")
print(data)
