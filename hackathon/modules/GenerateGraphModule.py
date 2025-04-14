import requests
import json
import logging
import os
import re
import time
import random
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

# Attempt to import your LLM Module
try:
    # Dostosuj ścieżkę importu do struktury Twojego projektu
    from hackathon.modules.LLMQueryModule import LLMQueryModule
except ImportError:
    logging.error("Could not import LLMQueryModule. Using dummy class.")
    class LLMQueryModule: # Dummy class na potrzeby działania skryptu
        def __init__(self, *args, **kwargs): logging.warning("Using dummy LLMQueryModule.")
        def __call__(self, prompt:str):
            logging.warning(f"Dummy LLM received prompt length: {len(prompt)}")
            return f"Placeholder summary for prompt starting with: {prompt[:100]}..."
        def forward(self, prompt:str): return self.__call__(prompt)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# Semantic Scholar API
SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
PAPERS_LIMIT_API = 30 # Request up to 100 papers initially
PAPER_FIELDS = "paperId,title,abstract,authors.authorId,authors.name,venue,year,citationCount,url,externalIds"
MAX_RETRIES = 50
RETRY_DELAY_SECONDS = 2
API_TIMEOUT = 180 # Increased timeout slightly

# Filtering & Grouping
TOP_N_PAPERS_BY_CITATION = 15
GROUP_SIZE = 5

# --- Module Definitions ---
class Module(ABC):
    def __init__(self): super().__init__()
    @abstractmethod
    def forward(self, *args, **kwargs) -> Any: pass
    def __call__(self, *args, **kwargs) -> Any: return self.forward(*args, **kwargs)

class GraphTripletExtractor(Module):
    """Extracts 'source - relation - target' triplet strings from graph data."""
    def __init__(self): super().__init__(); logging.info("GraphTripletExtractor initialized.")
    def forward(self, graph_json_data: Dict[str, Any]) -> Optional[List[str]]:
        triplet_strings = []; logging.info("Extracting triplets...")
        if not isinstance(graph_json_data, dict): logging.error("Input is not dict."); return None
        graph_data = graph_json_data.get("graph_data")
        if not isinstance(graph_data, dict): logging.error("Missing 'graph_data'."); return None
        edges = graph_data.get("edges")
        if not isinstance(edges, list): logging.error("Missing 'graph_data.edges'."); return triplet_strings
        logging.info(f"Found {len(edges)} edges.")
        for i, edge in enumerate(edges):
            if not isinstance(edge, dict): logging.warning(f"Skip edge {i}: not dict."); continue
            source = edge.get("source"); relation = edge.get("relation"); target = edge.get("target")
            if isinstance(source, str) and isinstance(relation, str) and isinstance(target, str):
                triplet_str = f"{source} - {relation} - {target}"; triplet_strings.append(triplet_str)
            else: logging.warning(f"Skip edge {i}: invalid components. {edge}")
        logging.info(f"Extracted {len(triplet_strings)} triplets."); return triplet_strings

class SemanticScholarQueryProcessor(Module):
    """Finds relevant papers using Semantic Scholar API, returns raw list."""
    def __init__(self, api_key: Optional[str] = None, api_url: str = SEMANTIC_SCHOLAR_API_URL, papers_limit: int = PAPERS_LIMIT_API, paper_fields: str = PAPER_FIELDS, timeout: int = API_TIMEOUT):
        super().__init__(); self.api_key = api_key or os.environ.get("SEMANTIC_SCHOLAR_API_KEY"); self.api_url = api_url; self.papers_limit = papers_limit; self.paper_fields = paper_fields; self.timeout = timeout; self.session = requests.Session()
        if self.api_key: self.session.headers.update({"x-api-key": self.api_key}); logging.info("S2 Query Processor initialized with API key.")
        else: logging.warning("S2 Query Processor initialized WITHOUT API key.")
        logging.info(f"API URL: {self.api_url}, Limit: {self.papers_limit}, Fields: '{self.paper_fields}'")
    def _call_semantic_scholar_api(self, query: str) -> Optional[List[Dict[str, Any]]]:
        if not query: logging.warning("API query empty."); return []
        params = {"query": query, "limit": self.papers_limit, "fields": self.paper_fields}; logging.info(f"Querying S2 API query='{query}' (limit={self.papers_limit})..."); last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(self.api_url, params=params, timeout=self.timeout); is_retryable = response.status_code == 429 or response.status_code >= 500; response.raise_for_status()
                response_json = response.json(); papers_data = response_json.get("data", []); total_found = response_json.get("total", len(papers_data)); logging.debug(f"API attempt {attempt+1} returned {len(papers_data)} papers (~{total_found} total).")
                if not isinstance(papers_data, list): logging.error("API 'data' not list"); return None
                return papers_data
            except requests.exceptions.Timeout as e: logging.warning(f"Attempt {attempt+1}/{MAX_RETRIES}: Timeout."); last_exception = e; is_retryable = True
            except requests.exceptions.HTTPError as e: logging.warning(f"Attempt {attempt+1}/{MAX_RETRIES}: HTTP Error {e.response.status_code}."); last_exception = e
            except requests.exceptions.RequestException as e: logging.warning(f"Attempt {attempt+1}/{MAX_RETRIES}: Request failed: {e}"); last_exception = e; is_retryable = True
            except json.JSONDecodeError as e: logging.warning(f"Attempt {attempt+1}/{MAX_RETRIES}: JSON Decode Error."); last_exception = e; is_retryable = True
            except Exception as e: logging.exception(f"Attempt {attempt+1}/{MAX_RETRIES}: Unexpected error: {e}"); last_exception = e; is_retryable = True
            if is_retryable and attempt < MAX_RETRIES-1: logging.info(f"Waiting {RETRY_DELAY_SECONDS}s..."); time.sleep(RETRY_DELAY_SECONDS)
            elif not is_retryable: logging.error(f"Non-retryable error received: {last_exception}"); break
        logging.error(f"API call failed after {MAX_RETRIES} attempts for query: '{query}'.");
        if last_exception: logging.error(f"Last error: {last_exception}")
        return None
    def forward(self, query_string: str) -> Optional[List[Dict[str, Any]]]:
        if not query_string or not isinstance(query_string, str): logging.error("Invalid query string."); return None
        search_query = query_string.strip(); papers_data = self._call_semantic_scholar_api(search_query)
        if papers_data is None: logging.error(f"Failed to retrieve papers for query: '{search_query}'"); return None
        return papers_data

# --- Orchestrator Module ---
class GraphPaperLinkerWithLLMSummary(Module):
    """
    Orchestrates loading graph, extracting triplets, using LLM for queries,
    finding papers, filtering/grouping, using LLM for summarizing groups,
    and saving/returning the final enriched data.
    """
    def __init__(self,
                 s2_api_key: Optional[str] = None,
                 llm_model_name: str = "small",
                 llm_query_agent_name: str = "query_shortener",
                 llm_summary_agent_name: str = "paper_summarizer",
                 output_filename_template: str = "enriched_{graph_name}_triplets_with_summaries.json"):
        super().__init__()
        self.triplet_extractor = GraphTripletExtractor()
        # Initialize LLM modules AFTER potential env var setting in main block
        # Store config, initialize later or handle potential errors
        self.llm_model_name = llm_model_name
        self.llm_query_agent_name = llm_query_agent_name
        self.llm_summary_agent_name = llm_summary_agent_name
        self.llm_query_module = None # Initialize lazily in forward
        self.llm_summarizer_module = None # Initialize lazily in forward

        self.paper_finder = SemanticScholarQueryProcessor(api_key=s2_api_key)
        self.output_filename_template = output_filename_template
        logging.info("GraphPaperLinkerWithLLMSummary initialized.")

    def _initialize_llm_modules(self):
        """Initializes LLM modules if not already done."""
        if self.llm_query_module is None:
            self.llm_query_module = LLMQueryModule(
                model_name=self.llm_model_name,
                agent_name=self.llm_query_agent_name,
                 system_message="You are an expert research assistant. Generate a concise keyword search query (max 5-6 words) for academic databases based on the core scientific concept in the provided triplet string. Focus on key entities and their interaction." # Added query system prompt
            )
        if self.llm_summarizer_module is None:
             summarizer_system_message = (
                "You are a highly knowledgeable biomedical research assistant. "
                "Your task is to synthesize information from a group of paper abstracts related to a specific biological relationship triplet. "
                "Focus on summarizing the key findings, agreements, contradictions, or knowledge gaps presented in the abstracts regarding the stated 'Context Relationship'. "
                "The summary should highlight insights useful for generating novel scientific hypotheses. "
                "Crucially, you MUST cite the source for each piece of information by mentioning the paper's title in parentheses, like (Paper Title Example). "
                "If multiple papers support a point, cite them all, e.g., (Title A; Title B). "
                "Do NOT include information not present in the provided abstracts. "
                "Keep the summary concise and focused on the relationship."
             )
             self.llm_summarizer_module = LLMQueryModule(
                 model_name=self.llm_model_name,
                 agent_name=self.llm_summary_agent_name,
                 system_message=summarizer_system_message
             )

    def _filter_and_select_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filters out null abstracts and selects top N by citation count."""
        # ... (no changes needed) ...
        if not papers: return []
        valid = [p for p in papers if p.get('abstract')]; logging.info(f"Filtered {len(papers)}->{len(valid)} with abstracts.")
        if not valid: return []
        valid.sort(key=lambda p: p.get('citationCount', 0) or 0, reverse=True)
        top = valid[:TOP_N_PAPERS_BY_CITATION]; logging.info(f"Selected top {len(top)} by citation (max {TOP_N_PAPERS_BY_CITATION})."); return top

    def _group_papers(self, papers: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Randomly groups papers into lists of specified size."""
        # ... (no changes needed) ...
        if not papers: return []
        random.shuffle(papers); groups = [];
        for i in range(0, len(papers), GROUP_SIZE): groups.append(papers[i : i + GROUP_SIZE])
        logging.info(f"Grouped {len(papers)} papers->{len(groups)} groups (size<={GROUP_SIZE})."); return groups

    def _generate_summary_prompt(self, triplet_string: str, paper_group: List[Dict[str, Any]]) -> str:
        """Constructs the detailed prompt for the LLM summarizer."""
        # ... (no changes needed) ...
        prompt = f"Context Relationship: {triplet_string}\n\nPapers Provided (Abstracts):\n"
        for i, paper in enumerate(paper_group):
            title = paper.get('title', f'Unknown Title {i+1}'); abstract = paper.get('abstract', 'No Abstract Provided.'); authors = paper.get('authors', []); venue = paper.get('venue', 'Unknown Venue'); year = paper.get('year', 'Unknown Year'); citation_count = paper.get('citationCount', 0); url = paper.get('url', 'No URL Provided.')
            if authors: authors = [a.get('name', 'Unknown Author') for a in authors]; authors = ', '.join(authors)
            if abstract is None: abstract = 'No Abstract Provided.'
            prompt += f"--- Paper {i+1}: {title} ---\n{abstract}\n\n"
            prompt += f"Authors: {authors}\n"
            prompt += f"Venue: {venue}, Year: {year}, Citations: {citation_count}, URL: {url}\n\n"
        prompt += ("Task: Based ONLY on the provided abstracts and the context relationship, synthesize the key findings, conflicts, or gaps in research related to "
                   f"'{triplet_string}'. Your summary should highlight insights useful for generating novel hypotheses. IMPORTANT: For every piece of information or claim "
                   "you include in the summary, you MUST cite the corresponding paper title(s) it came from in parentheses, like (Paper Title). Do not invent information "
                   "not present in the abstracts. Focus on the connection between the elements of the triplet as represented in these papers. Keep the summary concise and focused. You should mention at least a few papers. Do it all in about 6 sentences MENTION SOME PAPERS, MENTION SOME PAPERS OR YOU WILL GO TO JAIL. mention papers in this way: Chen, J. & Wong, T. (2021). Microglial Activation in Alzheimer's Disease. Nature Reviews Neuroscience, 22(4), 210-228 WHILE MENTIONING PAPERS MENTION TITLE AUTHORS AND VENUE. MENTION AT LEAST 3 PAPERS OR YOU WILL GO TO JAIL")
        return prompt

    def _sanitize_filename(self, name: str, default: str = "output") -> str:
        """Sanitizes a name string for use in a filename."""
        # ... (no changes needed) ...
        name = str(name).strip(); name = re.sub(r'[\s\\/:*?"<>|]+', '_', name); name = re.sub(r'[^\w\-_\. ]', '', name); return name[:60]

    def _save_to_json(self, data: List[Dict[str, Any]], filename: str):
        """Saves the final enriched data to a JSON file."""
        # ... (no changes needed) ...
        if not data: logging.warning("No data to save."); return False
        logging.info(f"Attempting to save {len(data)} enriched triplets to {filename}")
        try:
            output_dir = os.path.dirname(filename);
            if output_dir and not os.path.exists(output_dir): os.makedirs(output_dir)
            with open(filename, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)
            logging.info(f"Successfully saved data to {filename}"); return True
        except Exception as e: logging.error(f"Failed to save to JSON '{filename}': {e}"); return False

    def forward(self, graph_json_filepath: str) -> Optional[List[Dict[str, Any]]]:
        """
        Main workflow: Load graph -> Extract triplets -> LLM Query Gen -> Find Papers -> Filter -> Group -> LLM Summarize Groups -> Save -> Return.
        """
        # Ensure LLM modules are initialized (needed because API key might be set in main)
        try:
            self._initialize_llm_modules()
        except Exception as e:
            logging.error(f"Failed to initialize LLM modules: {e}")
            return None

        # 1. Load Graph
        loaded_data = None
        if not os.path.exists(graph_json_filepath): logging.error(f"Input file not found: {graph_json_filepath}"); return None
        try:
            with open(graph_json_filepath, 'r', encoding='utf-8') as f: loaded_data = json.load(f)
        except Exception as e: logging.error(f"Failed to load/parse '{graph_json_filepath}': {e}"); return None

        # 2. Extract Triplets
        triplet_strings = self.triplet_extractor(graph_json_data=loaded_data)
        if triplet_strings is None: logging.error("Triplet extraction failed."); return None
        if not triplet_strings: logging.warning("No triplets extracted."); return []

        # 3. Process Each Triplet
        final_results_data = []
        total_triplets = len(triplet_strings)
        logging.info(f"\n" + "="*30 + f" Processing {total_triplets} Triplets " + "="*30)

        for i, triplet_str in enumerate(triplet_strings):
            logging.info(f"\n--- Processing Triplet {i+1}/{total_triplets}: {triplet_str} ---")

            # 3a. LLM Query Generation
            llm_prompt_query = f"Summarize the core scientific concept or relationship described in the following triplet into a concise keyword phrase suitable for searching academic paper databases like Semantic Scholar. Focus on the key entities and their interaction. Triplet: '{triplet_str}'"
            shortened_query = self.llm_query_module(prompt=llm_prompt_query)
            if not shortened_query: logging.warning(f"LLM failed query gen (triplet {i+1})."); shortened_query = ""
            else: logging.info(f"LLM generated query: '{shortened_query}'")

            # 3b. Find Papers
            raw_papers = [];
            if shortened_query:
                raw_papers_result = self.paper_finder(query_string=shortened_query)
                if raw_papers_result is not None: raw_papers = raw_papers_result
                else: logging.warning(f"S2 query failed for triplet {i+1}.")
            else: logging.warning(f"Skipping S2 search for triplet {i+1} (empty LLM query).")

            # 3c. Filter and Select Papers
            selected_papers = self._filter_and_select_papers(raw_papers)

            # 3d. Group Papers
            paper_groups = self._group_papers(selected_papers)

            # 3e. LLM Summarization for Each Group
            group_analyses = [];
            if not paper_groups: logging.warning(f"No paper groups to summarize for triplet {i+1}.")
            else:
                 for group_idx, paper_group in enumerate(paper_groups):
                     summary_prompt = self._generate_summary_prompt(triplet_str, paper_group)
                     group_summary = self.llm_summarizer_module(prompt=summary_prompt)
                     print("-----------------")
                     print("-----------------")
                     print("-----------------")
                     print("-----------------")
                     print(group_summary)
                     print("-----------------")
                     print("-----------------")
                     print("-----------------")
                     print("-----------------")
                     if not group_summary: logging.warning(f"LLM summarizer failed for group {group_idx+1}, triplet {i+1}."); group_summary = "LLM summary generation failed."
                     group_analyses.append({"llm_summary": group_summary})
                     # Optional delay between LLM summary calls
            # 3f. Store Final Result for this Triplet
            final_results_data.append({"triplet_string": triplet_str,"paper_analysis": group_analyses})
            if i < total_triplets - 1: time.sleep(0.5)

        # 4. Determine Output Filename and Save
        graph_basename = self._sanitize_filename(os.path.splitext(os.path.basename(graph_json_filepath))[0], "graph")
        output_filename = self.output_filename_template.format(graph_name=graph_basename)
        self._save_to_json(final_results_data, output_filename)

        # 5. Return Final Data
        return final_results_data

# --- Main Execution ---
if __name__ == "__main__":
    INPUT_GRAPH_FILE = "data/Bridge_Therapy.json" # Your graph structure file
    OUTPUT_FILE_TEMPLATE = "Dzejson.json" # Template for output

    # !!! IMPORTANT: Provide API Keys !!!
    # Option 1 (Recommended): Set environment variables:
    #   SEMANTIC_SCHOLAR_API_KEY=your_s2_key
    #   OPENAI_API_KEY=your_openai_key (or relevant key for your LLM config)
    # Option 2: Assign S2 key directly here (less secure)
    SEMANTIC_SCHOLAR_API_KEY = None
    # Option 3: Set OpenAI key directly *here* (VERY UNSAFE FOR SHARING)
    # This makes it available for os.getenv called during LLM module init
    # *** REMOVE THIS LINE BEFORE SHARING/COMMITTING ***


    # --- Instantiate the Orchestrator ---
    # Pass the S2 key if not using env var
    # Adjust llm_model_name if needed
    linker = GraphPaperLinkerWithLLMSummary(
        s2_api_key=SEMANTIC_SCHOLAR_API_KEY,
        llm_model_name="small",
        output_filename_template=OUTPUT_FILE_TEMPLATE
    )

    logging.info(f"\n" + "="*30 + f" STARTING GRAPH ENRICHMENT + SUMMARIZATION " + "="*30)

    # --- Run the forward method ---
    final_enriched_data = linker(graph_json_filepath=INPUT_GRAPH_FILE) # Use __call__

    logging.info(f"\n" + "="*30 + f" SCRIPT COMPLETE " + "="*30)