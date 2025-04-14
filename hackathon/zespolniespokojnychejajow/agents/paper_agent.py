from typing import Any, Dict, Literal, Optional
import json
import os
from pathlib import Path
import re
import datetime
import numpy as np

from langchain.prompts import PromptTemplate
from loguru import logger

from ..llm.utils import get_model
from ..state import HypgenState
from ..utils import add_role

# Paper agent prompt
PAPER_PROMPT = """You are a research paper synthesizer.

Your task is to analyze the ontologist's output and create a comprehensive research paper summary that consolidates all the key concepts and relationships.

Based on the ontologist's analysis, create a single comprehensive research paper summary with the following structure:
1. Title: A clear, descriptive title that encompasses the main concepts
2. Authors: A list of potential authors (can be fictional but realistic)
3. Abstract: A detailed summary covering all the key concepts and relationships
4. Introduction: An introduction to the main topics and their significance
5. Key Concepts: A breakdown of each key concept defined in the ontologist's analysis
6. Relationships: An analysis of how these concepts interact, based on the relationships identified
7. Research Questions: A list of potential research questions that emerge from this analysis
8. Methodology: A proposed methodology for investigating these questions
9. Potential Findings: Hypothetical findings that might result from such research
10. Conclusion: The significance and implications of this research
11. Keywords: 5-7 keywords that capture the essence of the paper

Your output should be a well-structured JSON object containing all these sections.

Analyze the following ontologist output carefully:

{context}
"""

class Embedder:
    """
    A simple class for generating embeddings using sentence-transformers.
    """
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """Initialize the embedder with a model name."""
        self.model_name = model_name
        self._model = None
        
    def _load_model(self):
        """Lazy-load the embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                logger.error("The sentence-transformers package is required. Install with 'pip install sentence-transformers'")
                return None
            
            try:
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded sentence transformer model: {self.model_name}")
            except Exception as e:
                logger.error(f"Error loading model {self.model_name}: {str(e)}")
                return None
        
        return self._model
    
    def get_embedding(self, text):
        """Get embedding for a text string."""
        model = self._load_model()
        if model is None:
            logger.error("Could not load embedding model")
            return None
        
        try:
            embedding = model.encode(text, show_progress_bar=False)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None

def create_paper_agent(
    model: Optional[Literal["large", "small", "reasoning"]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Creates a paper agent that processes ontologist output and creates a comprehensive research summary."""

    prompt = PromptTemplate.from_template(PAPER_PROMPT)

    llm = get_model(model, **kwargs)
    chain = prompt | llm

    def agent(state: HypgenState) -> HypgenState:
        """Process the ontologist output and generate a comprehensive paper summary."""
        logger.info("Starting comprehensive paper summary generation")
        
        # Check if context from ontologist exists
        if "context" not in state or not state["context"]:
            logger.error("No ontologist context found in state")
            return state
        
        # Run the chain
        response = chain.invoke(state)
        
        # Create the papers directory if it doesn't exist
        papers_dir = Path("hackathon/zespolniespokojnychai/papers")
        papers_dir.mkdir(exist_ok=True, parents=True)
        
        # Generate timestamp here, outside the try/except blocks
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Try to parse the content as JSON
        try:
            # Extract JSON content from the response
            content = response.content
            # The model might wrap the JSON in markdown code blocks
            if "```json" in content:
                json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
            elif "```" in content:
                # Try to extract any code block
                json_match = re.search(r'```(?:\w*)\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
            
            # Parse the JSON summary
            paper_summary = json.loads(content)
            
            # Generate a filename based on the title if available
            filename = f"paper_summary_{timestamp}.json"
            if paper_summary.get("title"):
                # Clean the title for use as a filename
                title = paper_summary["title"].lower()
                title = ''.join(c if c.isalnum() else '_' for c in title)
                title = title[:50]  # Truncate to a reasonable length
                filename = f"{title}_{timestamp}.json"
            
            # Save the comprehensive paper summary
            paper_file = papers_dir / filename
            with open(paper_file, "w", encoding="utf-8") as f:
                json.dump(paper_summary, f, indent=2)
            
            logger.info(f"Saved comprehensive paper summary to {paper_file}")
            
            # Also save a markdown version for easier reading
            md_content = f"# {paper_summary.get('title', 'Research Paper Summary')}\n\n"
            
            # Add authors if available
            if paper_summary.get('authors'):
                if isinstance(paper_summary['authors'], list):
                    md_content += "**Authors:** " + ", ".join(paper_summary['authors']) + "\n\n"
                else:
                    md_content += f"**Authors:** {paper_summary['authors']}\n\n"
            
            # Add each section to the markdown file
            for section in ['abstract', 'introduction', 'key_concepts', 'relationships', 
                           'research_questions', 'methodology', 'potential_findings', 'conclusion']:
                if section in paper_summary:
                    section_title = section.replace('_', ' ').title()
                    section_content = paper_summary[section]
                    
                    md_content += f"## {section_title}\n\n"
                    if isinstance(section_content, list):
                        for item in section_content:
                            if isinstance(item, dict):
                                for k, v in item.items():
                                    md_content += f"### {k}\n{v}\n\n"
                            else:
                                md_content += f"- {item}\n"
                        md_content += "\n"
                    else:
                        md_content += f"{section_content}\n\n"
            
            # Add keywords if available
            if paper_summary.get('keywords'):
                if isinstance(paper_summary['keywords'], list):
                    md_content += "**Keywords:** " + ", ".join(paper_summary['keywords']) + "\n"
                else:
                    md_content += f"**Keywords:** {paper_summary['keywords']}\n"
            
            # Save the markdown version
            md_file = papers_dir / f"{filename.replace('.json', '.md')}"
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(md_content)
            
            logger.info(f"Saved markdown version to {md_file}")
            
            # Generate embeddings from the summary
            embedder = Embedder()
            
            # Create embeddings for key sections
            embeddings = {}
            try:
                # Add title embedding
                if paper_summary.get('title'):
                    title_embedding = embedder.get_embedding(paper_summary['title'])
                    if title_embedding is not None:
                        embeddings['title'] = title_embedding.tolist()
                
                # Add abstract embedding
                if paper_summary.get('abstract'):
                    abstract_embedding = embedder.get_embedding(paper_summary['abstract'])
                    if abstract_embedding is not None:
                        embeddings['abstract'] = abstract_embedding.tolist()
                
                # Combine keywords if available
                if paper_summary.get('keywords'):
                    keywords = paper_summary['keywords']
                    if isinstance(keywords, list):
                        keywords_text = " ".join(keywords)
                    else:
                        keywords_text = keywords
                    
                    keywords_embedding = embedder.get_embedding(keywords_text)
                    if keywords_embedding is not None:
                        embeddings['keywords'] = keywords_embedding.tolist()
                
                # Create a combined embedding from all text sections
                combined_text = []
                for section in ['title', 'abstract', 'introduction', 'conclusion']:
                    if paper_summary.get(section):
                        if isinstance(paper_summary[section], str):
                            combined_text.append(paper_summary[section])
                
                if combined_text:
                    combined_embedding = embedder.get_embedding(" ".join(combined_text))
                    if combined_embedding is not None:
                        embeddings['combined'] = combined_embedding.tolist()
                
                logger.info(f"Generated embeddings for {len(embeddings)} sections")
                
                # Save embeddings to a separate file
                embedding_file = papers_dir / f"{filename.replace('.json', '_embeddings.json')}"
                with open(embedding_file, "w", encoding="utf-8") as f:
                    json.dump(embeddings, f, indent=2)
                
                logger.info(f"Saved embeddings to {embedding_file}")
                
            except Exception as e:
                logger.error(f"Error generating embeddings: {str(e)}")
            
            # Add the response to the state
            return {
                "paper_summary": paper_summary,
                "paper_embeddings": embeddings,
                "messages": state.get("messages", []) + [add_role(response, "paper_agent")]
            }
        
        except json.JSONDecodeError:
            logger.error("Failed to parse paper agent output as JSON")
            # Still try to save the raw output
            error_file = papers_dir / f"paper_summary_error_{timestamp}.txt"
            with open(error_file, "w", encoding="utf-8") as f:
                f.write(response.content)
            
            return {
                "papers_error": "Failed to parse output as JSON",
                "messages": state.get("messages", []) + [add_role(response, "paper_agent")]
            }

    return {"agent": agent} 