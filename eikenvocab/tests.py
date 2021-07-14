import requests
from pathlib import Path


def download_file(url: str, path: str):
    try:
        with requests.get(url) as response:
            try:
                response.raise_for_status()
                print("Downloading file ...")
                with open(path, "wb") as f:
                    print("Writing file ...")
                    f.write(response.content)
                print("Done.")
            except requests.exceptions.HTTPError:
                print("No test")
    except requests.exceptions.ConnectionError:
        print("Cannot connect.")


def scrape_eiken_tests(grades: list[str], base_path: str):
    base_url = "https://www.eiken.or.jp/eiken/exam/"
    years = ["2021", "2020"]
    # Every year has three test sessions (Summer, Fall, Winter)
    sessions = ["1", "2", "3"]
    for grade in grades:
        download_path = base_path / f"grade_{grade}/"
        Path(download_path).mkdir(parents=True, exist_ok=True)
        print(f"Download Path: {download_path}")
        for year in years:
            for session in sessions:
                # https://www.eiken.or.jp/eiken/exam/grade_5/pdf/202101/2021-1-1ji-5kyu.pdf
                # https://www.eiken.or.jp/eiken/exam/grade_5/pdf/202101/2021-1-1ji-5kyu-script.pdf
                filenames = [
                    f"{year}-{session}-1ji-{grade}kyu.pdf",
                    f"{year}-{session}-1ji-{grade}kyu-script.pdf",
                ]
                for filename in filenames:
                    url = f"{base_url}/grade_{grade}/pdf/{year}0{session}/{filename}"
                    download_file(url=url, path=download_path / filename)


def main():
    # p2 and p1 are for Grades Pre-2 and Pre-1
    grades = ["5", "4", "3", "p2", "2", "p1", "1"]
    # grades = ["1"]
    base_path = Path(__file__).parent.parent.resolve() / "data"
    scrape_eiken_tests(grades=grades, base_path=base_path)


if __name__ == "__main__":
    main()
