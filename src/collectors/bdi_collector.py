import pandas as pd
import yfinance as yf
from pathlib import Path
from src.collectors.base_collector import BaseCollector

class BDICollector(BaseCollector):
    """
    Collects BDI data via yfinance BDRY ETF + manual CSV adapter.
    """

    def __init__(self, output_dir: Path):
        super().__init__(name="bdi", output_dir=output_dir)

    def collect(self, start_date: str, end_date: str) -> pd.DataFrame:
        self.logger.info(f"Collecting BDI/BDRY data from {start_date} to {end_date}")
        
        # 1. Download BDRY data
        try:
            end_date_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1)
            bdry = yf.download('BDRY', start=start_date, end=end_date_dt.strftime('%Y-%m-%d'), progress=False)
            bdry = bdry.reset_index()
            
            if isinstance(bdry.columns, pd.MultiIndex):
                bdry.columns = bdry.columns.droplevel(1)
            
            bdry['Date'] = pd.to_datetime(bdry['Date']).dt.strftime('%Y-%m-%d')
            bdry = bdry.rename(columns={
                'Date': 'date',
                'Open': 'bdry_open',
                'High': 'bdry_high',
                'Low': 'bdry_low',
                'Close': 'bdry_close',
                'Volume': 'bdry_volume'
            })
            
            avail_cols = ['date', 'bdry_open', 'bdry_high', 'bdry_low', 'bdry_close', 'bdry_volume']
            avail_cols = [c for c in avail_cols if c in bdry.columns]
            bdry = bdry[avail_cols]
        except Exception as e:
            self.logger.error(f"Failed to fetch BDRY data from yfinance: {e}")
            bdry = pd.DataFrame(columns=['date', 'bdry_close'])

        # 2. Manual BDI data
        manual_bdi_path = self.output_dir / "bdi_manual.csv"
        bdi_df = pd.DataFrame(columns=['date', 'bdi'])
        
        if manual_bdi_path.exists():
            self.logger.info(f"Found manual BDI file at {manual_bdi_path}")
            try:
                manual = pd.read_csv(manual_bdi_path)
                if 'Date' in manual.columns and 'Price' in manual.columns:
                    manual['date'] = pd.to_datetime(manual['Date']).dt.strftime('%Y-%m-%d')
                    if manual['Price'].dtype == object:
                        manual['Price'] = manual['Price'].str.replace(',', '').astype(float)
                    manual['bdi'] = manual['Price']
                    bdi_df = manual[['date', 'bdi']].copy()
                else:
                    self.logger.warning("Manual BDI file missing expected columns 'Date' and 'Price'.")
            except Exception as e:
                self.logger.error(f"Failed to read manual BDI file: {e}")
        else:
            self.logger.warning("No manual BDI CSV found at data/raw/bdi_manual.csv. 'bdi' will be NaN.")

        # 3. Merge
        if not bdry.empty and not bdi_df.empty:
            df = pd.merge(bdry, bdi_df, on='date', how='outer')
        elif not bdry.empty:
            df = bdry.copy()
            df['bdi'] = pd.NA
        elif not bdi_df.empty:
            df = bdi_df.copy()
            df['bdry_close'] = pd.NA
        else:
            self.logger.error("Both BDRY and BDI collections failed/empty.")
            return pd.DataFrame()

        if 'bdi' not in df.columns:
            df['bdi'] = pd.NA
        if 'bdry_close' not in df.columns:
            df['bdry_close'] = pd.NA
            
        df['source_bdi'] = 'Investing.com_Manual'
        df['source_bdry'] = 'Yahoo_Finance_BDRY'
        df['data_type'] = 'REAL'

        df = df.sort_values('date').reset_index(drop=True)
        
        # filter to requested range
        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        df = df.loc[mask].copy()

        self._save_raw(df, "bdi_raw.csv")
        return df
