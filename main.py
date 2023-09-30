import requests
from bs4 import BeautifulSoup
import pdfkit
import os


class WebsiteScraper:
    def __init__(self, start_url):
        self.visited_urls = set()
        self.start_url = start_url
        self.domain = start_url.split("//")[-1].split("/")[0]

    def is_internal(self, url):
        return self.domain in url

    def save_as_pdf(self, url):
        filename = url.replace("http://", "").replace("https://", "").replace("/", "_") + ".pdf"
        path = os.path.join("pdfs", filename)
        try:
            pdfkit.from_url(url, path)
            print(f"Saved {url} as {path}")
        except Exception as e:
            print(f"Error saving {url} as PDF: {e}")

    def save_as_text(self, url, text):

        if "drive.google.com" in url or "feeds" in url or "audio" in url or "podcast" in url:
            result = False
            print(f'ignoring link {url}')

        else:
            try:
                filename = url.replace("http://", "").replace("https://", "").replace("/", "_") + ".txt"
                path = os.path.join("txts", filename)
                text = " " + text + " "
                # text_file = open(path, "w")
                path = "txts/upenn-blob.txt"
                text_file = open(path, "a")
                result = text_file.write(text)
                print(f"Saved {url} as {path}")
                result = True

            except Exception as e:
                print(f"Error saving {url} as TXT: {e}")
                result = False

        return result

    def scrape(self, url):
        if "drive.google.com" not in url and "feeds" not in url and "audio" not in url and "podcast" not in url:

            url = "https://" + url.split("//")[-1]
            if url in self.visited_urls:
                return
            self.visited_urls.add(url)

            response = requests.get(url)
            if response.status_code != 200:
                print(f"Failed to fetch {url}")
                return

            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.getText(separator=' ')
            text = soup.getText()

            result = self.save_as_text(url, text)
            # self.save_as_pdf(url)

            links = [a['href'] for a in soup.find_all('a', href=True)]
            links = [link for link in links if "mailto" not in link]

            for link in links:
                # Normalize the link
                if link.startswith("/"):
                    link = self.start_url.rstrip("/") + link

                # Check if the link is internal to the website
                if self.is_internal(link) and link not in self.visited_urls:
                    self.scrape(link)
        else:
            print(f'not scraping {url}')


if __name__ == "__main__":
    scraper = WebsiteScraper("https://www.library.upenn.edu/")

    # Create a directory to save the PDFs
    if not os.path.exists("pdfs"):
        os.makedirs("pdfs")

    if not os.path.exists("txts"):
        os.makedirs("txts")

    scraper.scrape(scraper.start_url)
