# standard library imports
from pathlib import Path
from typing import Optional

# third party imports
import typer

# local imports
import tests
import flashcards
import wordlists


app = typer.Typer(help="Eiken Vocabulary Flashcard Generator")


@app.command()
def downloadtests(
    grades: list[str] = typer.Option(
        ["5", "4", "3", "p2", "2", "p1", "1"],
        "--grade",
        "-g",
        help="Specify a grade of test to download. Can be repeated for multiple grades.",
        show_default="all grades",
    ),
    downloadpath: str = typer.Option(
        Path(__file__).parent.parent.resolve() / "data",
        "--datapath",
        "-d",
        help="The path where the test PDFs should be saved.",
    ),
):
    """
    Download the test PDFs from the web.
    """
    tests.scrape_eiken_tests(grades=grades, path=downloadpath)


@app.command()
def makelists(
    grades: list[str] = typer.Option(
        ["5", "4", "3", "p2", "2", "p1", "1"],
        "--grade",
        "-g",
        help="Specify a grade to create a list for. Can be repeated for multiple grades.",
        show_default="all grades",
    ),
    datapath: str = typer.Option(
        Path(__file__).parent.parent.resolve() / "data",
        "--datapath",
        "-d",
        help="The path where the source PDFs are located.",
    ),
    wordlimit: Optional[int] = typer.Option(
        None,
        "--wordlimit",
        "-l",
        help="The maximum number of words per list.",
        show_default="no limit",
    ),
):
    """
    Make the wordlists in Google Sheets.
    """
    for grade in grades:
        print(f"Starting Grade {grade} ...")
        input_path = datapath / f"grade_{grade}"
        words = wordlists.string_to_words(
            wordlists.pdfs_to_string(input_path=input_path)
        )
        words = wordlists.clean_wordlist(words)
        words = wordlists.get_most_frequent_words(words=words, limit=wordlimit)
        wordlist = wordlists.make_wordlist(words=words)
        wordlists.write_gsheet(wordlist=wordlist, grade=grade)
        print(f"Finished Grade {grade}.")


@app.command()
def makecards(
    grades: list[str] = typer.Option(
        ["5", "4", "3", "p2", "2", "p1", "1"],
        "--grades",
        "-g",
        help="Specify a grade to create a list for. Can be repeated for multiple grades.",
        show_default="all grades",
    ),
    outputpath: str = typer.Option(
        Path(__file__).parent.parent.resolve() / "output",
        "--outputpath",
        "-o",
        help="The path where the PDF files will be saved.",
    ),
):
    """
    Make the flashcard PDFs from the data in Google Sheets.
    """
    for grade in grades:
        print(f"Starting Grade {grade} ...")
        data = flashcards.get_data_for_grade(grade)
        # Use Pre-2, not p2 for flashcard labels
        long_grade = grade.replace("p", "Pre-")
        wordlist = flashcards.make_wordlist(data)
        content = flashcards.render_template(grade=long_grade, wordlist=wordlist)
        outfilename = flashcards.render_pdf(
            grade=grade, content=content, output_path=outputpath
        )
        flashcards.reorder_pdf(outfilename)
        print(f"Finished Grade {grade}.")


if __name__ == "__main__":
    app()
