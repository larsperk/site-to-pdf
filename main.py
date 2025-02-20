import requests
from bs4 import BeautifulSoup
import pdfkit
import os
import re
from urllib.parse import urlparse
import tldextract

SITE_ROOT = "zushealth.com" # do not prefix with http:// or https:// or www
OUTPUT_FILE = "zushealth.txt"
SUBDIR = "txts"

MODE = "TEXT-BLOB"  # or "PDFS"


output_file = os.path.join(SUBDIR, OUTPUT_FILE)
if os.path.exists(output_file):
    os.remove(output_file)

excluded_url_strings = [
    "drive.google.com",
    "feeds",
    "audio",
    "podcast",
    ".jpeg",
    ".jpg",
    "undefined",
    "youtu.be",
    "pdf",
]

excluded_subdomains = [
]

def get_subdomain(url):
    if not url.startswith("http"):
        url = "https://" + url
    parsed_url = urlparse(url)
    extracted = tldextract.extract(parsed_url.netloc)
    path = parsed_url.path

    # Reconstruct subdomain
    subdomain = extracted.subdomain
    base_domain = f"{extracted.domain}.{extracted.suffix}"  # e.g., example.com

    return subdomain, base_domain, path

class WebsiteScraper:
    def __init__(self, start_url):
        self.visited_urls = set()
        self.start_url = start_url
        self.start_subdomain, _, _ = get_subdomain("https://" + start_url)
        self.current_subdomain = self.start_subdomain
        self.output_file = os.path.join(SUBDIR, OUTPUT_FILE)

        # use this for an entire website
        self.domain = start_url.split("//")[-1].split("/")[0]

        # use this for a specific subdomain
        # self.domain = start_url.split("//")[-1]

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
        if any([excluded_url_string in url for excluded_url_string in excluded_url_strings]):
            result = False
            print(f'ignoring link {url}')

        else:
            try:
                text = " " + text + " "
                text_file = open(self.output_file, "a")
                result = text_file.write(text)
                file_size = os.path.getsize(self.output_file)
                print(f"Saved {url} as {self.output_file} {file_size}")
                result = True

            except Exception as e:
                print(f"Error saving {url} as TXT: {e}")
                result = False

        return result

    def scrape(self, url):
        new_subdomain, base_domain, path = get_subdomain(url)
        new_subdomain = ""
        if self.current_subdomain != new_subdomain and new_subdomain:
            self.current_subdomain = new_subdomain
            print(f"Switching to subdomain {new_subdomain} for {url}")

        should_scrape = True
        if any([excluded_url_string in url for excluded_url_string in excluded_url_strings]):
            should_scrape = False
        if any([excluded_subdomain in url for excluded_subdomain in excluded_subdomains]):
            should_scrape = False

        if should_scrape:
            if self.current_subdomain:
                domain_prefix = self.current_subdomain + "."
                self.output_file = os.path.join(SUBDIR, self.current_subdomain + "_" + OUTPUT_FILE)
            else:
                domain_prefix = ""
                self.output_file = os.path.join(SUBDIR, OUTPUT_FILE)

            url = "https://" + domain_prefix + base_domain + path
            if url in self.visited_urls:
                return
            self.visited_urls.add(url)

            response = requests.get(url)
            if response.status_code != 200:
                print(f"Failed to fetch {url}")
                return

            soup_to_be_delinked = BeautifulSoup(response.text, 'html.parser')
            for a in soup_to_be_delinked.find_all('a'):
                a.decompose()  # Completely remove the <a> tag and its content
            delinked_text = soup_to_be_delinked.get_text(separator="\n", strip=True)
            delinked_text = "\n".join(line for line in delinked_text.splitlines() if line.strip())
            delinked_text = re.sub(r'\n+', '\n', delinked_text)

            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.getText(separator=' ')

            if MODE == "TEXT-BLOB":
                result = self.save_as_text(url, delinked_text)
            elif MODE == "PDFS":
                self.save_as_pdf(url)

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
    clean_url = SITE_ROOT.removeprefix("http://").removeprefix("https://").removeprefix("www.")
    scraper = WebsiteScraper(clean_url)

    # Create a directory to save the PDFs
    if MODE == "PDFS":
        if not os.path.exists("pdfs"):
            os.makedirs("pdfs")
        scraper.scrape(scraper.start_url)

    # or the TXTs
    elif MODE == "TEXT-BLOB":
        if not os.path.exists("txts"):
            os.makedirs("txts")
        scraper.scrape(scraper.start_url)

    else:
        printf(f"Invalid scrape mode {MODE}")
