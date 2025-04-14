import os
import random
import time
import urllib.error
import urllib.request
from dotenv import load_dotenv
load_dotenv()
from langchain_community.tools.pubmed.tool import PubmedQueryRun
from langchain_community.utilities.pubmed import PubMedAPIWrapper


class PubMedAPIWrapperImproved(PubMedAPIWrapper):
    def retrieve_article(self, uid: str, webenv: str) -> dict:
        url = (
            self.base_url_efetch
            + "db=pubmed&retmode=xml&id="
            + uid
            + "&webenv="
            + webenv
        )
        if self.api_key != "":
            url += f"&api_key={self.api_key}"

        retry = 0
        while True:
            try:
                result = urllib.request.urlopen(url)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and retry < self.max_retry:
                    # Too Many Requests errors
                    sleep_time_random = random.uniform(0.5, 1.5)
                    sleep_time = self.sleep_time + sleep_time_random
                    print(f"Too Many Requests, waiting for {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                    self.sleep_time *= 2
                    retry += 1
                else:
                    raise e

        xml_text = result.read().decode("utf-8")
        text_dict = self.parse(xml_text)
        return self._parse_article(uid, text_dict)


# ✅ Ensure the API key is loaded correctly
api_key = os.getenv("PUBMED_API_KEY")
if not api_key:
    raise ValueError("Missing PUBMED_API_KEY! Please set it in your environment or .env file.")

# ✅ Create the PubMed tool
pubmed_tool = PubmedQueryRun(
    api_wrapper=PubMedAPIWrapperImproved(api_key=api_key)
)

if __name__ == "__main__":
    query = "PTPN22 AND rheumatoid arthritis"
    result = pubmed_tool.run(query)
    print(result)
