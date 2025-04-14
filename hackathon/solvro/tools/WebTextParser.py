import requests
from bs4 import BeautifulSoup

class WebTextParser:
    def __init__(self, url: str):
        self.url = url
        self.response = None
        self.soup = None

    def fetch(self):
        """Fetch the webpage content."""
        try:
            self.response = requests.get(self.url)
            self.response.raise_for_status()
            self.soup = BeautifulSoup(self.response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching the page: {e}")
            self.response = None
            self.soup = None

    def get_raw_text(self) -> str:
        """Return raw text from the page."""
        if self.soup:
            return self.soup.get_text()
        return ""

    def get_clean_text(self) -> str:
        """Return cleaned-up text (no extra whitespace)."""
        raw_text = self.get_raw_text()
        return ' '.join(raw_text.split())

    def print_clean_text(self):
        """Print cleaned-up text."""
        print(self.get_clean_text())


# Example usage
if __name__ == "__main__":
    url = "https://www.omim.org/help/api"
    parser = WebTextParser(url)
    parser.fetch()
    parser.print_clean_text()
