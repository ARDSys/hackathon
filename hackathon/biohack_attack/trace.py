import json
import threading
from typing import List, Union
from loguru import logger

from agents import Trace, Span
from agents.tracing.processor_interface import TracingExporter
from agents.tracing.processors import BatchTraceProcessor


class LocalFileExporter(TracingExporter):
    """A TracingExporter that writes traces and spans to a local file."""

    def __init__(self, filepath: str, format: str = 'json'):
        """
        Args:
            filepath: The path to the file where logs will be written.
            format: The output format ('json' or 'str'). JSON is recommended.
        """
        super().__init__()
        self.filepath = filepath
        self._file = None
        self._lock = threading.Lock()  # Protect file access if export called concurrently (shouldn't happen with BatchProcessor)
        self._format = format.lower()
        if self._format not in ['json', 'str']:
            raise ValueError("Invalid format. Choose 'json' or 'str'.")
        logger.info(f"LocalFileExporter initialized. Logging to: {self.filepath} in format: {self._format}")

    def _ensure_file_open(self):
        """Opens the file if it's not already open."""
        if self._file is None:
            try:
                # Open in append mode, create if doesn't exist, use utf-8 encoding
                self._file = open(self.filepath, 'a', encoding='utf-8')
                logger.info(f"Opened log file: {self.filepath}")
            except IOError as e:
                logger.error(f"Failed to open log file {self.filepath}: {e}")
                # You might want to raise the exception or handle it differently
                raise

    def export(self, items: List[Union[Trace, Span]]) -> None:
        """Exports a batch of traces or spans to the local file."""
        with self._lock:
            try:
                self._ensure_file_open()
                if self._file:  # Check if file opening succeeded
                    for item in items:
                        if self._format == 'json':
                            # Attempt to convert item to dict, then serialize as JSON
                            try:
                                if hasattr(item, 'to_dict') and callable(item.to_dict):
                                    log_line = json.dumps(item.to_dict())
                                else:
                                    # Fallback if no to_dict method
                                    log_line = json.dumps(item.__dict__)
                            except (TypeError, AttributeError) as e:
                                logger.warning(
                                    f"Could not serialize item to JSON, falling back to str(): {item}. Error: {e}")
                                log_line = str(item)  # Fallback to string representation
                        else:  # format == 'str'
                            log_line = str(item)

                        self._file.write(log_line + '\n')
                    self._file.flush()  # Ensure data is written to disk periodically
            except IOError as e:
                logger.error(f"Failed to write to log file {self.filepath}: {e}")
                # Attempt to close and reopen on next export might be an option here
                self.shutdown()  # Close the problematic file handle
            except Exception as e:
                logger.exception(f"An unexpected error occurred during export: {e}")

    def shutdown(self) -> None:
        """Closes the log file."""
        with self._lock:
            if self._file:
                try:
                    logger.info(f"Closing log file: {self.filepath}")
                    self._file.close()
                except IOError as e:
                    logger.error(f"Error closing log file {self.filepath}: {e}")
                finally:
                    self._file = None  # Ensure file handle is cleared


class LocalFilesystemTracingProcessor(BatchTraceProcessor):
    """
    A BatchTraceProcessor that serializes traces and spans as logs
    to a specified local file.
    """

    def __init__(
            self,
            filepath: str,
            log_format: str = 'json',  # Expose log format selection
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
