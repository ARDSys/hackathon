from datetime import datetime
from pathlib import Path

import dotenv
from agents import set_trace_processors
from langfuse.callback import CallbackHandler
from loguru import logger

from ard.hypothesis import Hypothesis
from ard.subgraph import Subgraph
from biohack_attack.hypothesis_generator import HypothesisGenerator, ProcessConfig
from biohack_attack.local_trace_processor import LocalFilesystemTracingProcessor

langfuse_callback = CallbackHandler()

dotenv.load_dotenv()


def main(file: str, output: str):
    output_dir = Path(output) / f"{datetime.now().strftime('%Y-%m-%d-%H-%M')}"
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    log_file_path = output_dir / "traces.jsonl"
    debug_logs_file_path = output_dir / "debug.log"
    logger.add(
        debug_logs_file_path,
        level="DEBUG",
    )
    info_logs_file_path = output_dir / f"info.log"
    logger.add(
        info_logs_file_path,
        level="INFO",
    )

    set_trace_processors([LocalFilesystemTracingProcessor(log_file_path.as_posix())])
    source_file = Path(file)
    logger.info(f"Subgraph loaded from {source_file}")

    process_config = ProcessConfig(
        num_of_threads=16, num_of_hypotheses=5, out_dir_path=output_dir
    )
    logger.info("Generating hypothesis...")
    hypothesis = Hypothesis.from_subgraph(
        subgraph=Subgraph.load_from_file(file),
        method=HypothesisGenerator(process_config),
    )
    logger.info(f"Hypothesis generated for {source_file}")

    # Save hypothesis in json and md format
    hypothesis.save(backend_path=output, parser_type="json")
    hypothesis.save(backend_path=output, parser_type="md")

    logger.info(f"Hypothesis saved to {output_dir}")


if __name__ == "__main__":
    main(
        file=(
            Path(__file__).parent.parent.parent
            / "data/Antinuclear_Antibodies__ANA_.json"
        ).as_posix(),
        output="out",
    )
