import json
import threading
from typing import List, Union

from agents.tracing.processors import BatchTraceProcessor
from loguru import logger

from agents import Trace, Span  # Assuming these are the correct base types or Protocols
from agents.tracing.processor_interface import TracingExporter


class LocalFileExporter(TracingExporter):
    """A TracingExporter that writes traces and spans to a local file."""

    def __init__(self, filepath: str, format: str = "json"):
        """
        Args:
            filepath: The path to the file where logs will be written.
            format: The output format ('json' or 'str'). JSON is recommended.
        """
        super().__init__()
        self.filepath = filepath
        self._file = None
        self._lock = threading.Lock()  # Protect file access
        self._format = format.lower()
        if self._format not in ["json", "str"]:
            raise ValueError("Invalid format. Choose 'json' or 'str'.")
        logger.info(
            f"LocalFileExporter initialized. Logging to: {self.filepath} in format: {self._format}"
        )

    def _ensure_file_open(self):
        """Opens the file if it's not already open."""
        if self._file is None:
            try:
                # Open in append mode, create if doesn't exist, use utf-8 encoding
                self._file = open(self.filepath, "a", encoding="utf-8")
                logger.info(f"Opened log file: {self.filepath}")
            except IOError as e:
                logger.error(f"Failed to open log file {self.filepath}: {e}")
                raise

    def export(self, items: List[Union[Trace, Span]]) -> None:
        """Exports a batch of traces or spans to the local file."""
        with self._lock:
            try:
                self._ensure_file_open()
                if self._file:  # Check if file opening succeeded
                    for item in items:
                        log_line = ""
                        if self._format == "json":
                            if hasattr(item, "export") and callable(item.export):
                                try:
                                    exported_data = item.export()
                                    # Ensure export() actually returned something potentially serializable
                                    if exported_data is not None:
                                        log_line = json.dumps(exported_data)
                                    else:
                                        logger.warning(
                                            f"Item export() returned None, falling back to str(): {item}"
                                        )
                                        log_line = str(item)
                                except (TypeError, AttributeError) as e:
                                    logger.warning(
                                        f"Could not serialize item.export() to JSON, falling back to str(): {item}. Error: {e}"
                                    )
                                    log_line = str(item)
                            else:
                                # Fallback if no export() method (shouldn't happen for Trace/Span)
                                logger.warning(
                                    f"Item missing export() method, falling back to str(): {item}"
                                )
                                log_line = str(item)
                            # --- END OF CORE CHANGE ---
                        else:  # format == 'str'
                            log_line = str(item)

                        if log_line:  # Only write if we got a non-empty string
                            self._file.write(log_line + "\n")
                            logger.debug(log_line)

                    self._file.flush()  # Ensure data is written to disk periodically
            except IOError as e:
                logger.error(f"Failed to write to log file {self.filepath}: {e}")
                self.shutdown()
            except Exception as e:
                logger.exception(f"An unexpected error occurred during export: {e}")

    def shutdown(self) -> None:
        """Closes the log file."""
        with self._lock:
            if self._file:
                try:
                    logger.info(f"Closing log file: {self.filepath}")
                    # Ensure everything is written before closing
                    self._file.flush()
                    self._file.close()
                except IOError as e:
                    logger.error(f"Error closing log file {self.filepath}: {e}")
                finally:
                    self._file = None


class LocalFilesystemTracingProcessor(BatchTraceProcessor):
    """
    A BatchTraceProcessor that serializes traces and spans as logs
    to a specified local file.
    """

    def __init__(
        self,
        filepath: str,
        log_format: str = "json",  # Expose log format selection
        max_queue_size: int = 8192,
        max_batch_size: int = 128,
        schedule_delay: float = 5.0,
        export_trigger_ratio: float = 0.7,
    ):
        """
        Args:
            filepath: The path to the file where trace logs will be written.
            log_format: The format for logs ('json' or 'str'). Defaults to 'json'.
            max_queue_size: Max items in the internal queue before dropping.
            max_batch_size: Max items to write to the file in one batch.
            schedule_delay: Delay in seconds between periodic flushes.
            export_trigger_ratio: Queue fullness ratio triggering an immediate flush.
        """
        # Create the specific exporter for writing to a local file
        self._local_exporter = LocalFileExporter(filepath=filepath, format=log_format)

        # Initialize the parent BatchTraceProcessor with the file exporter
        super().__init__(
            exporter=self._local_exporter,
            max_queue_size=max_queue_size,
            max_batch_size=max_batch_size,
            schedule_delay=schedule_delay,
            export_trigger_ratio=export_trigger_ratio,
        )
        logger.info(f"LocalFilesystemTracingProcessor initialized for file: {filepath}")
