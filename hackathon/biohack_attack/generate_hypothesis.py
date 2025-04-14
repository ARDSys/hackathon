import click
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import dotenv

# Assuming these imports are correct relative to your project structure
from agents import set_trace_processors
from langfuse.callback import CallbackHandler
from loguru import logger

from ard.hypothesis import Hypothesis
from ard.subgraph import Subgraph
from biohack_attack.hypothesis_generator import (
    HypothesisGenerator,
)  # Assuming ProcessConfig is defined here or imported separately
from biohack_attack.local_trace_processor import LocalFilesystemTracingProcessor


# If ProcessConfig is defined elsewhere, ensure it's imported.
# If it's defined as you showed, let's include it here for clarity:
@dataclass
class ProcessConfig:
    num_of_hypotheses: int = 5
    num_of_threads: int = 5
    top_k: int = 2
    max_iterations: int = 2
    out_dir_path: Optional[Path] = (
        None  # We'll populate this based on the output argument
    )


# --- Global Setup ---
# It's generally good practice to load dotenv early
dotenv.load_dotenv()

# Langfuse handler might be initialized here if needed globally,
# or within the command if its configuration depends on CLI args.
# For now, keeping it global as in the original script.
langfuse_callback = CallbackHandler()
# Note: You might want to make Langfuse integration configurable via CLI too (e.g., enable/disable)


# --- Core Processing Logic ---
def run_processing(
    input_file: Path,
    output_base_dir: Path,
    process_config: ProcessConfig,
    debug_log: bool,
    info_log: bool,
):
    """
    Runs the main hypothesis generation process.

    Args:
        input_file: Path to the source subgraph file.
        output_base_dir: The base directory for output. A timestamped subdir will be created.
        process_config: Configuration for the hypothesis generation process.
        debug_log: Whether to enable debug logging to a file.
        info_log: Whether to enable info logging to a file.
    """
    # --- Output Directory and Logging Setup ---
    timestamp_dir_name = datetime.now().strftime("%Y-%m-%d-%H-%M")
    output_dir = output_base_dir / timestamp_dir_name
    if not output_dir.exists():
        output_dir.mkdir(
            parents=True, exist_ok=True
        )  # exist_ok=True handles race conditions if needed
    logger.info(f"Output will be saved to: {output_dir}")

    log_file_path = output_dir / "traces.jsonl"  # For LocalFilesystemTracingProcessor

    if debug_log:
        debug_logs_file_path = output_dir / "debug.log"
        logger.add(
            debug_logs_file_path,
            level="DEBUG",
            format="{time} {level} {message}",  # Example format
        )
        logger.info(f"Debug logs enabled: {debug_logs_file_path}")

    if info_log:
        info_logs_file_path = output_dir / "info.log"
        logger.add(
            info_logs_file_path,
            level="INFO",
            format="{time} {level} {message}",  # Example format
        )
        logger.info(f"Info logs enabled: {info_logs_file_path}")

    # Set trace processor *after* output_dir is determined
    set_trace_processors([LocalFilesystemTracingProcessor(log_file_path.as_posix())])

    # Update process_config with the actual output directory path
    process_config.out_dir_path = output_dir

    # --- Load Subgraph ---
    logger.info(f"Loading subgraph from {input_file}")
    try:
        subgraph = Subgraph.load_from_file(input_file.as_posix())
    except Exception as e:
        logger.error(f"Failed to load subgraph from {input_file}: {e}")
        raise  # Re-raise after logging

    # --- Generate Hypothesis ---
    logger.info(f"Generating hypothesis with config: {process_config}")
    try:
        hypothesis = Hypothesis.from_subgraph(
            subgraph=subgraph,
            method=HypothesisGenerator(process_config),
            # If Langfuse integration is desired during generation:
            # callbacks=[langfuse_callback] # Assuming Hypothesis.from_subgraph accepts callbacks
        )
        logger.info(f"Hypothesis generated successfully for {input_file}")
    except Exception as e:
        logger.error(f"Failed during hypothesis generation: {e}")
        raise  # Re-raise after logging

    # --- Save Hypothesis ---
    output_base_name = input_file.stem  # Use input filename stem for output files
    json_output_path = output_dir / f"{output_base_name}_hypothesis.json"
    md_output_path = output_dir / f"{output_base_name}_hypothesis.md"

    try:
        logger.info(f"Saving hypothesis to JSON: {json_output_path}")
        # Assuming save takes the full path now, not just the directory
        hypothesis.save(
            backend_path=json_output_path.parent.as_posix(),
            parser_type="json",
        )

        logger.info(f"Saving hypothesis to Markdown: {md_output_path}")
        hypothesis.save(
            backend_path=md_output_path.parent.as_posix(),
            parser_type="md",
        )

        logger.info(f"Hypothesis saved successfully to {output_dir}")
    except Exception as e:
        logger.error(f"Failed to save hypothesis: {e}")
        # Decide if you want to raise here or just log the error


# --- Click CLI Definition ---
@click.command()
@click.argument(
    "input_file",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    # Note: 'file' argument from original main renamed to 'input_file' to avoid shadowing built-in
)
@click.option(
    "-o",
    "--output",
    "output_base_dir",  # Store the value in 'output_base_dir' variable
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    default="out",
    show_default=True,
    help="Base directory for output files. A timestamped subdirectory will be created inside.",
)
@click.option(
    "--num-hypotheses",
    type=int,
    default=5,
    show_default=True,
    help="Number of hypotheses to generate.",
)
@click.option(
    "--num-threads",
    type=int,
    default=5,  # Changed default from 16 in original main to 5 from ProcessConfig default
    show_default=True,
    help="Number of threads to use for processing.",
)
@click.option(
    "--top-k",
    type=int,
    default=2,
    show_default=True,
    help="Top K value for hypothesis generation process.",
)
@click.option(
    "--max-iterations",
    type=int,
    default=2,
    show_default=True,
    help="Maximum iterations for hypothesis generation process.",
)
@click.option(
    "--debug-log/--no-debug-log",
    default=True,
    show_default=True,
    help="Enable/disable saving debug logs to a file.",
)
@click.option(
    "--info-log/--no-info-log",
    default=True,
    show_default=True,
    help="Enable/disable saving info logs to a file.",
)
def cli(
    input_file: Path,
    output_base_dir: Path,
    num_hypotheses: int,
    num_threads: int,
    top_k: int,
    max_iterations: int,
    debug_log: bool,
    info_log: bool,
):
    """
    Generates hypotheses from a subgraph file using the ARD framework.
    """
    # Create the ProcessConfig object from CLI options
    # Note: out_dir_path is set inside run_processing after the timestamped dir is created
    process_config = ProcessConfig(
        num_of_hypotheses=num_hypotheses,
        num_of_threads=num_threads,
        top_k=top_k,
        max_iterations=max_iterations,
        # out_dir_path will be set later
    )

    # Call the main processing function
    try:
        run_processing(
            input_file=input_file,
            output_base_dir=output_base_dir,
            process_config=process_config,
            debug_log=debug_log,
            info_log=info_log,
        )
        click.echo(click.style("Processing finished successfully.", fg="green"))
    except Exception as e:
        # Loguru should have already logged the error details if configured
        # We raise a ClickException to ensure a non-zero exit code and user feedback
        raise click.ClickException(f"An error occurred during processing: {e}")


if __name__ == "__main__":
    cli()
