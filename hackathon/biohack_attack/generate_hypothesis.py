from datetime import datetime
from pathlib import Path

import dotenv
from agents import set_trace_processors
from langfuse.callback import CallbackHandler
from loguru import logger

from ard.hypothesis import Hypothesis
from ard.subgraph import Subgraph
from biohack_attack.hypothesis_generator import HypothesisGenerator
from biohack_attack.local_trace_processor import LocalFilesystemTracingProcessor

langfuse_callback = CallbackHandler()

dotenv.load_dotenv()


def main(file: str, output: str):
    output_dir = Path(output)
    if not output_dir.exists():
        output_dir.mkdir()
    log_file_path = output_dir / f"{datetime.now().strftime('%Y-%m-%d-%H-%M')}-traces.log"
    set_trace_processors([LocalFilesystemTracingProcessor(
        log_file_path.as_posix()
    )])
    source_file = Path(file)
    logger.info(f"Subgraph loaded from {source_file}")

    logger.info("Generating hypothesis...")
    hypothesis = Hypothesis.from_subgraph(
        subgraph=Subgraph.load_from_file(file),
        method=HypothesisGenerator(),
    )
    print(hypothesis)
    logger.info(f"Hypothesis generated for {source_file}")

    # Save hypothesis in json and md format
    hypothesis.save(backend_path=output, parser_type="json")
    hypothesis.save(backend_path=output, parser_type="md")

    logger.info(f"Hypothesis saved to {output_dir}")


if __name__ == "__main__":
    main(
        file=(Path(__file__).parent.parent / "sample_subgraph.json").as_posix(),
        output="out"
    )
