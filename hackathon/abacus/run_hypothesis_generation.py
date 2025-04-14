#!/usr/bin/env python3
# filepath: c:\Users\gopte\source\hackathon_beeard\hackathon\team_name\run_hypothesis_generation.py
# Main Script (run_hypothesis_generation.py)
import os
import sys
from pathlib import Path
import logging
import argparse
from dotenv import load_dotenv

from ard.subgraph import Subgraph
from ard.hypothesis import Hypothesis

# Import our hypothesis generator
from hypothesis_generator import MultiAgentHypothesisGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hypothesis_generation.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("hypothesis_generator")


def main():
    # Load environment variables from .env file
    load_dotenv()

    # Check if API keys are set
    required_keys = ["OPENAI_API_KEY"]  # Add other required keys
    missing_keys = [key for key in required_keys if not os.environ.get(key)]
    if missing_keys:
        logger.error(f"Missing required API keys: {', '.join(missing_keys)}")
        logger.error("Please add them to your .env file")
        sys.exit(1)

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Generate hypotheses from subgraphs")
    parser.add_argument('--input_dir', type=str, required=True,
                        help='Directory containing subgraph JSON files')
    parser.add_argument('--output_dir', type=str, required=True,
                        help='Directory to save generated hypotheses')
    args = parser.parse_args()

    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all JSON files in input directory
    input_dir = Path(args.input_dir)
    subgraph_files = list(input_dir.glob("*.json"))

    if not subgraph_files:
        logger.error(f"No JSON files found in {input_dir}")
        sys.exit(1)

    # Initialize our hypothesis generator
    logger.info("Initializing MultiAgentHypothesisGenerator")
    generator = MultiAgentHypothesisGenerator()

    # Process each subgraph file
    for subgraph_file in subgraph_files:
        logger.info(f"Processing subgraph file: {subgraph_file}")

        # Load subgraph
        subgraph = Subgraph.load_from_file(subgraph_file)
        logger.info(f"Loaded subgraph with ID: {subgraph.subgraph_id}")
        logger.info(f"Path: {subgraph.start_node} -> {subgraph.end_node}")

        # Generate hypothesis
        logger.info("Generating hypothesis...")
        hypothesis = Hypothesis.from_subgraph(subgraph, generator)
        logger.info(f"Generated hypothesis: {hypothesis.title}")

        # Save hypothesis in both JSON and Markdown formats
        logger.info(f"Saving hypothesis to {output_dir}")
        hypothesis.save(backend_path=output_dir, parser_type="json")
        hypothesis.save(backend_path=output_dir, parser_type="md")

        logger.info(f"Successfully processed {subgraph_file.name}")
        logger.info("-" * 50)

    logger.info(f"All subgraphs processed. Results saved to {output_dir}")


if __name__ == "__main__":
    main()
