import json
from pathlib import Path

import click
import dotenv
from langfuse.callback import CallbackHandler
from loguru import logger

from ard.hypothesis import Hypothesis
from ard.subgraph import Subgraph

from .hypothesis_generator import HypothesisGenerator

langfuse_callback = CallbackHandler()

dotenv.load_dotenv()


@click.command()
@click.option(
    "--file", "-f", type=click.Path(exists=True), help="Path to the json file"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(exists=True, file_okay=False),
    help="Path to the output directory",
    default=".",
)
def main(file: str, output: str):
    file_path = Path(file)
    output_path = Path(output)
    logger.info(f"Subgraph loaded from {file_path}")

    logger.info("Generating hypothesis...")
    hypothesis = Hypothesis.from_subgraph(
        subgraph=Subgraph.load_from_file(file_path),
        method=HypothesisGenerator(),
    )
    logger.info(f"Hypothesis generated successfully for {file_path}")
    
    logger.info(f"Saving mechanistic summaries to {output_path}")
    with open(output_path / "paths.json", "w") as f:
        json.dump(hypothesis.metadata["mechanistic_summaries"], f, indent=4)

    # Save hypothesis in json and md format
    logger.info(f"Saving hypothesis to {output_path}")
    output_path.mkdir(parents=True, exist_ok=True)
    hypothesis.save(backend_path=output_path, parser_type="json")
    hypothesis.save(backend_path=output_path, parser_type="md")


if __name__ == "__main__":
    main()
