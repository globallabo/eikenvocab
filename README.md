# eikenvocab

![Example flashcard output](/eikenvocab.png "Example flashcard output")

eikenvocab is a project whose goal is to automatically generate flashcards based on the most frequently occurring words in an English test. It will allow you to download tests from the web, scrape them for the most frequent English words, get Japanese pronunciation and translations for those words, export that data to a Google Sheet and then use that data to create PDFs of your final flashcards.

## Usage

### Download Tests

First, you will need some test PDFs as a data source to scrape. To automatically download those tests, run:

```bash
python eikenvocab/eikenvocab.py downloadtests
```

By default, this will download all available grades of test. And it will save them into a folder named "data" at the root of the package.

If you wish to only download specific grades, use the `--grade / -g` option. For example, if you want to only download tests for Grade 5:

```bash
python eikenvocab/eikenvocab.py downloadtests --grade 5
```

To download tests of multiple grades, repeat the option. For example, to download tests for both Grades 3 and 4:

```bash
python eikenvocab/eikenvocab.py downloadtests -g 3 -g 4
```

If you wish to download to another directory, use the `--datapath / -d` option. For example, to download to your home directory:

```bash
python eikenvocab/eikenvocab.py downloadtests -d ~/
```

### Scrape Tests and Make Word Lists

After you have some test data, you will need to scrape that data, create your word lists and export them to Google Sheets. To do that, run:

```bash
python eikenvocab/eikenvocab.py makelists
```

By default, this will scrape all available grades of test. And it will look for them in a folder named "data" at the root of the package.

If you wish to only process specific grades, use the `--grade / -g` option. For example, if you want to only make a list for Grade 5:

```bash
python eikenvocab/eikenvocab.py makelists --grade 5
```

To make lists for multiple grades, repeat the option. For example, to make lists for both Grades 3 and 4:

```bash
python eikenvocab/eikenvocab.py makelists -g 3 -g 4
```

If you downloaded your test PDFs to another directory, use the `--datapath / -d` option. For example, to read from your home directory:

```bash
python eikenvocab/eikenvocab.py makelists -d ~/
```

### Create Flashcards

After you have processed the test data and created your word lists, you will need to use the resulting data in Google Sheets to create PDF flashcards. To do that, run:

```bash
python eikenvocab/eikenvocab.py makecards
```

By default, this will make flashcards for all available grades of test. And it will save them to a folder named "output" at the root of the package.

If you wish to only process specific grades, use the `--grade / -g` option. For example, if you want to only make flashcards for Grade 5:

```bash
python eikenvocab/eikenvocab.py makelists --grade 5
```

To make flashcards for multiple grades, repeat the option. For example, to make flashcards for both Grades 3 and 4:

```bash
python eikenvocab/eikenvocab.py makelists -g 3 -g 4
```

If you wish to save your flashcard PDFs to another directory, use the `--outputpath / -o` option. For example, to save to your home directory:

```bash
python eikenvocab/eikenvocab.py makelists -d ~/
```
