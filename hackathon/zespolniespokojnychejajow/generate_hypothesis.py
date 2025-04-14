from pathlib import Path
import os
import json
import shutil

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
@click.option(
    "--copy-files",
    is_flag=True,
    help="Copy JSON and MD files to output directory in addition to saving inside hypothesis folder",
)
def main(file: str, output: str, copy_files: bool):
    file_path = Path(file)
    output_path = Path(output)
    logger.info(f"Subgraph loaded from {file_path}")

    logger.info("Generating hypothesis...")
    hypothesis_generator = HypothesisGenerator()
    hypothesis = Hypothesis.from_subgraph(
        subgraph=Subgraph.load_from_file(file_path),
        method=hypothesis_generator,
    )
    logger.info(f"Hypothesis generated for {file_path}")

    # Get the hypothesis output directory from metadata
    hypothesis_dir = hypothesis.metadata.get("output_dir")
    if hypothesis_dir:
        logger.info(f"Hypothesis saved in folder: {hypothesis_dir}")
        
        # Copy files to output directory if requested
        if copy_files:
            # Save hypothesis in json and md format to the output path as well
            hypothesis.save(backend_path=output_path, parser_type="json")
            hypothesis.save(backend_path=output_path, parser_type="md")
            logger.info(f"Hypothesis files also copied to {output_path}")
    else:
        # Fallback to old behavior if no output_dir in metadata
        hypothesis.save(backend_path=output_path, parser_type="json")
        hypothesis.save(backend_path=output_path, parser_type="md")
        logger.info(f"Hypothesis saved to {output_path}")


if __name__ == "__main__":
    main()
