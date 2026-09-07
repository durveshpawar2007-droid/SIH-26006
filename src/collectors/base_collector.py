import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
import requests


class BaseCollector(ABC):
    """
    Abstract base class for all data collectors.
    """

    def __init__(self, name: str, output_dir: Path):
        self.name = name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger(f"collector.{self.name}")
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    @abstractmethod
    def collect(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Collect data from the source and return as a DataFrame.
        """
        pass

    def _save_raw(self, df: pd.DataFrame, filename: str) -> Path:
        """
        Save the raw DataFrame to a CSV file.
        """
        if df.empty:
            self.logger.warning(f"DataFrame is empty. Not saving {filename}")
            return self.output_dir / filename

        output_path = self.output_dir / filename
        try:
            df.to_csv(output_path, index=False)
            self.logger.info(f"Saved {len(df)} rows to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save data to {output_path}: {e}")
            raise
        return output_path

    def _retry_request(self, url: str, max_retries: int = 3, backoff: float = 1.0) -> requests.Response:
        """
        Make an HTTP request with exponential backoff retries.
        """
        retries = 0
        while retries <= max_retries:
            try:
                self.logger.info(f"Requesting URL (Attempt {retries + 1}/{max_retries + 1}): {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                self.logger.warning(f"Request failed: {e}")
                if retries == max_retries:
                    self.logger.error(f"Max retries reached for {url}")
                    raise
                sleep_time = backoff * (2 ** retries)
                self.logger.info(f"Sleeping for {sleep_time} seconds before retry...")
                time.sleep(sleep_time)
                retries += 1
