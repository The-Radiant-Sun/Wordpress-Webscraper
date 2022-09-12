import requests
from bs4 import BeautifulSoup
from ebooklib import epub

urlTOC = "https://practicalguidetoevil.wordpress.com/table-of-contents/"  # url to table of contents
title = "A Practical Guide to Evil"
author = "ErraticErrata"
cover = "cover.jpg"  # Root to cover image if found

sectionSplit = "h2"  # Use "-" in front of split text if the split is within the section "-h1" as an example
sectionGroup = "ul"
sectionItem = "li"

currentSectionTitle = ""
currentSectionNumber = 0
book = epub.EpubBook()
spine = ["nav"]
subsections = ()  # Table of Contents subsections, filled as (Title, Content)
x = 0


def initializeEpubMetadata():
    """Set up Ebook Metadata"""
    global book
    book.set_title(title)
    book.add_author(author)
    book.set_cover(content=cover, file_name=cover)


def main():
    """For a provided book, extract information on all chapters"""
    global book, currentSectionTitle, currentSectionNumber

    input(f"Press enter to begin book scraping of {title}")

    initializeEpubMetadata()
    # Access Table of Contents
    page = requests.get(urlTOC)

    soup = BeautifulSoup(page.content, "html.parser")  # Table of Contents

    entryResults = soup.find("div", class_="entry-content")

    for child in entryResults.find_all(recursive=False):
        if child.name == sectionSplit and sectionSplit[0] != "-":  # Split in entries indicating new section
            currentSectionNumber += 1
            currentSectionTitle = child.text
        elif child.name == sectionGroup:
            iterateChapters(child)  # Get all connected chapters, then extract the content

    generateBook()
    print("Epub file has been generated")


def iterateChapters(chapters):
    """For each part within the section, identify if it is a chapter or a title, then add or extract respectively"""
    global currentSectionTitle, currentSectionNumber

    chaptersSoup = BeautifulSoup(str(chapters), "html.parser")  # Contains a list of chapters of a given book number

    for chapter in chaptersSoup.find_all(sectionItem):
        chapterSoup = BeautifulSoup(str(chapter), "html.parser")

        if sectionSplit[0] == "-":
            sections = chapterSoup.findAll(sectionSplit[1:])
            if sections:
                currentSectionNumber += 1
                currentSectionTitle = sections[0].text if len(chapterSoup.findAll(sectionSplit[1:])) == 1 else sections[currentSectionNumber].text

        else:
            currentChapterTitle = currentSectionTitle + " - " + chapterSoup.find("a").text  # Get Chapter Title
            url = chapterSoup.find("a")["href"]  # Get URL of Chapter
            extractChapter(url, currentChapterTitle)  # Extract content


def extractChapter(url, currentChapterTitle):
    global book
    chapterPage = requests.get(url)  # Visit the Chapter page
    chapterSoup = BeautifulSoup(chapterPage.content, "html.parser")  # Chapter page HTML content

    # Proceed to extract the text of the chapter
    content = chapterSoup.find("div", class_="entry-content")  # Chapter main text body
    [s.extract() for s in chapterSoup.select("div", id="jp-post-flair")]  # Remove footer buttons
    appendChapterToBook(content, currentChapterTitle)


def appendChapterToBook(content, currentChapterTitle):
    global x, book, spine, subsections, currentSectionTitle
    epubChapter = epub.EpubHtml(title=currentChapterTitle, file_name=str(x) + ".xhtml", lang='hr')
    epubChapter.content = "<h2>" + currentChapterTitle + "</h2>" + str(content).replace('<div class="entry-content">\n', "").replace('\n </div>', "")

    book.add_item(epubChapter)
    spine.append(epubChapter)
    subsections += (currentSectionTitle, epubChapter),

    x += 1
    print("Scraped " + currentChapterTitle)


def generateBook():
    global book
    print("Generating EPUB file")

    toc = ()

    for section in subsections:
        toc += (epub.Section(section[0]), section[1])

    book.toc = toc
    book.spine = spine

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    epub.write_epub(f'{title}.epub', book, {})


if __name__ == "__main__":
    main()
