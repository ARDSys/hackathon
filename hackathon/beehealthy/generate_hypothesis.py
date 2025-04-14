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
    logger.info(f"Hypothesis generated for {file_path}")

    # Save hypothesis in json and md format
    output_path.mkdir(parents=True, exist_ok=True)
    hypothesis.save(backend_path=output_path, parser_type="json")
    hypothesis.save(backend_path=output_path, parser_type="md")

    logger.info(f"Hypothesis saved to {output_path}")


if __name__ == "__main__":
    main()
