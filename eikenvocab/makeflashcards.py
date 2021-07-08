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
def render_template(grade: str, wordlist: list[dict]) -> str:
    template_loader = jinja2.FileSystemLoader(searchpath="./templates/")
    template_env = jinja2.Environment(loader=template_loader)
    TEMPLATE_FILE = "cards.html"
    template = template_env.get_template(TEMPLATE_FILE)
    template_path = pathlib.Path(__file__).parent.absolute() / "templates/"
    static_path = pathlib.Path(__file__).parent.absolute() / "static/"
    output_text = template.render(
        static_path=static_path, grade=grade, wordlist=wordlist
    )
    return output_text


# use weasyprint to render string of HTML into PDF
def render_pdf(grade: str, content: str, output_path: str):
    filename = f"{output_path}/grade-{grade}.pdf"
    # Create Weasyprint HTML object
    html = HTML(string=content)
    # Output PDF via Weasyprint
    html.write_pdf(filename)


def main():
    # p2 and p1 are for Grades Pre-2 and Pre-1
    grades = ["5", "4", "3", "p2", "2", "p1", "1"]
    output_path = pathlib.Path(__file__).parent.parent.absolute() / "output/"
    for grade in grades:
        data = get_data_for_grade(grade)
        # Use Pre-2, not p2 for flashcard labels
        long_grade = grade.replace("p", "Pre-")
        wordlist = make_wordlist(data)
        content = render_template(grade=long_grade, wordlist=wordlist)
        render_pdf(grade=grade, content=content, output_path=output_path)


if __name__ == "__main__":
    main()
