# standard library imports
from pathlib import Path
import itertools
import pprint

# third party imports
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import jinja2
from weasyprint import HTML
import fitz  # pyMuPDF - get text from PDFs


def get_data_for_grade(grade: str) -> list[list[str]]:
    """Get data for a grade level from a Google Sheet

    Args:
        grade (str): The grade level of the data to get.

    Returns:
        list[str]: The contents of the sheet in list form (two-dimensional).
    """
    # Fetch data from Google Sheet
    sheetname = "Eiken Vocabulary"
    credsfile = Path(__file__).parent.parent.resolve() / "creds.json"
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credsfile, scope)
    client = gspread.authorize(creds)
    try:
        sheet = client.open(sheetname).worksheet(f"grade_{grade}")
        return sheet.get_all_values()
    except FileNotFoundError as fnf_error:
        print(fnf_error)
        return []


def make_wordlist(data: list[list[str]]) -> list[dict]:
    """Create a list of dictionaries to hold the wordlist data.

    Args:
        data (list[str]): The content from a Google Sheet in list form (two-dimensional).

    Returns:
        list[dict]: A list of dictionaries containing the word and pronunciation, translation, etc.
    """
    wordlist = []
    # the first row of the data is the spreadsheet header, use as keys
    keys = data[0]
    # loop over the rest of the data, excluding the first row
    for word in data[1:]:
        wordlist.append(dict(zip(keys, word)))
    return wordlist


def render_template(grade: str, wordlist: list[dict]) -> str:
    """Render HTML from a jinja2 template.

    Args:
        grade (str): The grade level of the content.
        wordlist (list[dict]): The list of words and their pronunciations, translations, etc.

    Returns:
        str: The rendered HTML content.
    """
    template_loader = jinja2.FileSystemLoader(searchpath="./templates/")
    template_env = jinja2.Environment(loader=template_loader)
    TEMPLATE_FILE = "cards.html"
    template = template_env.get_template(TEMPLATE_FILE)
    template_path = Path(__file__).parent.resolve() / "templates/"
    static_path = Path(__file__).parent.resolve() / "static/"
    output_text = template.render(
        static_path=static_path, grade=grade, wordlist=wordlist
    )
    return output_text


def render_pdf(grade: str, content: str, output_path: str) -> str:
    """Render the PDF from the HTML contents.

    Args:
        grade (str): The grade level of the content.
        content (str): The HTML content.
        output_path (str): The path where the resulting PDF will be saved.

    Returns:
        str: Returns the filename of the output PDF.
    """
    output_path = Path(output_path).resolve()
    Path(output_path).mkdir(parents=True, exist_ok=True)
    filename = f"{output_path}/grade-{grade}.pdf"
    # Create Weasyprint HTML object
    html = HTML(string=content)
    # Output PDF via Weasyprint
    html.write_pdf(filename)
    return filename


def reorder_pdf(filename: str):
    """Reorder the pages in the flashcard PDF so we can print
    two per postcard page, duplex, while keeping the front
    and back aligned.

    Args:
        filename (str): The PDF file to be reordered.
    """
    doc = fitz.open(filename)
    # For the 2-per-page print format to work, the number of pages
    #  must be a multiple of 4
    if len(doc) % 4 != 0:
        # get the page dimensions from the first page
        width, height = doc[0].MediaBoxSize
        # add two new pages to the end of the document
        doc.new_page(pno=-1, width=width, height=height)
        doc.new_page(pno=-1, width=width, height=height)
    pagenums = list(range(len(doc)))
    # print(pagenums)
    # first, get separate lists of the even and odd page numbers,
    #  grouped into tuples of two at a time
    evens = []
    odds = []
    for pagenum in pagenums:
        if pagenum % 2 == 0:
            evens.append(pagenum)
        else:
            odds.append(pagenum)
    pairedevenlist = []
    for even1, even2 in zip(*[iter(evens)] * 2):
        # for even1, even2 in itertools.zip_longest(*[iter(evens)] * 2):
        pairedevenlist.append((even1, even2))
    pairedoddlist = []
    for odd1, odd2 in zip(*[iter(odds)] * 2):
        # for odd1, odd2 in itertools.zip_longest(*[iter(odds)] * 2):
        pairedoddlist.append((odd1, odd2))
    # next, zip the evens and odds together
    newpairedlist = list(zip(pairedevenlist, pairedoddlist))
    # newpairedlist = list(itertools.zip_longest(pairedevenlist, pairedoddlist))
    # then flatten the list, which is currently tuples within tuples
    flatlist = list(itertools.chain(*itertools.chain(*newpairedlist)))
    # set the new page order
    doc.select(flatlist)
    # save the result to a new file (overwriting is problematic)
    newfilename = str(Path(filename).stem) + "-reordered.pdf"
    newpath = Path(filename).parent / newfilename
    doc.save(newpath)


def main():
    # p2 and p1 are for Grades Pre-2 and Pre-1
    grades = ["5", "4", "3", "p2", "2", "p1", "1"]
    # grades = ["5"]
    output_path = Path(__file__).parent.parent.resolve() / "output/"
    for grade in grades:
        print(f"Starting Grade {grade} ...")
        data = get_data_for_grade(grade)
        # Use Pre-2, not p2 for flashcard labels
        long_grade = grade.replace("p", "Pre-")
        wordlist = make_wordlist(data)
        content = render_template(grade=long_grade, wordlist=wordlist)
        render_pdf(grade=grade, content=content, output_path=output_path)
        print(f"Finished Grade {grade}.")


if __name__ == "__main__":
    main()
