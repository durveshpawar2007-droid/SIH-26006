import io
import pandas as pd
from pathlib import Path
from src.collectors.base_collector import BaseCollector

class BunkerCollector(BaseCollector):
    """
    Collects daily bunker fuel prices from USDA AgTransport Socrata API.
    """

    def __init__(self, output_dir: Path):
        super().__init__(name="bunker", output_dir=output_dir)
        self.csv_url = "https://agtransport.usda.gov/api/views/4v3x-mj86/rows.csv?accessType=DOWNLOAD"
        self.json_url = "https://agtransport.usda.gov/resource/4v3x-mj86.json"

    def collect(self, start_date: str, end_date: str) -> pd.DataFrame:
        self.logger.info(f"Collecting bunker data from {start_date} to {end_date}")
        df = self._collect_csv()
        if df.empty:
            self.logger.info("CSV download failed or empty, falling back to JSON API")
            df = self._collect_json()

        if df.empty:
            self.logger.error("Failed to collect bunker data.")
            return pd.DataFrame()

        # Rename columns to standard names from both CSV headers and JSON API
        rename_map = {
            "vlsfo_fuel_oil_imo_2020_grade_0_5": "bunker_vlsfo",
            "VLSFO Fuel Oil, IMO 2020 Grade, 0.5%": "bunker_vlsfo",
            "marine_gas_oil": "bunker_mgo",
            "Marine Gas Oil": "bunker_mgo",
            "intermdiate_fuel_oil_380cst": "bunker_ifo380",
            "Intermdiate Fuel Oil, 380cSt": "bunker_ifo380",
            "intermdiate_fuel_oil_180cst": "bunker_ifo180",
            "Intermdiate Fuel Oil, 180cSt": "bunker_ifo180",
            "day": "date_raw",
            "Day": "date_raw"
        }
        df = df.rename(columns=rename_map)

        if "date_raw" in df.columns:
            # Parse date_raw (supports ISO or MM/DD/YYYY)
            df['date'] = pd.to_datetime(df['date_raw'], errors='coerce').dt.strftime('%Y-%m-%d')
        elif "date" in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        else:
            self.logger.error("Could not find date column in data.")
            return pd.DataFrame()

        # Add constant columns
        df['currency'] = 'USD'
        df['unit'] = 'USD/MT'
        df['source'] = 'USDA_AgTransport_ShipAndBunker'
        df['data_type'] = 'REAL'

        # Filter by start_date and end_date
        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        df = df.loc[mask].copy()

        # Select relevant columns
        cols_to_keep = ['date', 'bunker_vlsfo', 'bunker_mgo', 'bunker_ifo380', 'bunker_ifo180', 'currency', 'unit', 'source', 'data_type']
        
        # Add missing columns if they don't exist
        for col in cols_to_keep:
            if col not in df.columns:
                df[col] = pd.NA
                
        df = df[cols_to_keep]

        # Convert numerics
        numeric_cols = ['bunker_vlsfo', 'bunker_mgo', 'bunker_ifo380', 'bunker_ifo180']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df = df.sort_values('date').reset_index(drop=True)
        self._save_raw(df, "bunker_prices_raw.csv")
        return df

    def _collect_csv(self) -> pd.DataFrame:
        try:
            response = self._retry_request(self.csv_url)
            df = pd.read_csv(io.StringIO(response.text))
            return df
        except Exception as e:
            self.logger.warning(f"Error reading CSV: {e}")
            return pd.DataFrame()

    def _collect_json(self) -> pd.DataFrame:
        try:
            url = f"{self.json_url}?$limit=50000&$offset=0"
            response = self._retry_request(url)
            data = response.json()
            return pd.DataFrame(data)
        except Exception as e:
            self.logger.warning(f"Error reading JSON: {e}")
            return pd.DataFrame()
