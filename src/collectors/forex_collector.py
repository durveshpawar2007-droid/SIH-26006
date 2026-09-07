import io
import pandas as pd
from pathlib import Path
from src.collectors.base_collector import BaseCollector

class ForexCollector(BaseCollector):
    """
    Collects daily USD/INR from FRED.
    """

    def __init__(self, output_dir: Path):
        super().__init__(name="forex", output_dir=output_dir)
        self.base_url = "https://fred.stlouisfed.org/graph/fredgraph.csv"

    def collect(self, start_date: str, end_date: str) -> pd.DataFrame:
        self.logger.info(f"Collecting forex data from {start_date} to {end_date}")
        url = f"{self.base_url}?id=DEXINUS&cosd={start_date}&coed={end_date}"
        
        try:
            response = self._retry_request(url)
            df = pd.read_csv(io.StringIO(response.text), na_values=".")
        except Exception as e:
            self.logger.error(f"Failed to fetch forex data: {e}")
            return pd.DataFrame()

        if df.empty:
            self.logger.warning("No data retrieved from FRED.")
            return pd.DataFrame()

        df.columns = ['date', 'usd_inr']
        
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        df['usd_inr'] = pd.to_numeric(df['usd_inr'], errors='coerce')
        
        df['source'] = 'FRED_DEXINUS'
        df['data_type'] = 'REAL'

        df = df.sort_values('date').reset_index(drop=True)
        self._save_raw(df, "usd_inr_raw.csv")
        return df
