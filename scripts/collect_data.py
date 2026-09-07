import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.collectors.bunker_collector import BunkerCollector
from src.collectors.forex_collector import ForexCollector
from src.collectors.bdi_collector import BDICollector

# Attempt to load settings
try:
    from src.config.settings import DATA_RAW_DIR, START_DATE, END_DATE
except ImportError:
    DATA_RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
    START_DATE = "2020-01-01"
    END_DATE = "2026-09-07"

def main():
    parser = argparse.ArgumentParser(description="Collect data for SIH26006")
    parser.add_argument("--start-date", default=START_DATE, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", default=END_DATE, help="End date (YYYY-MM-DD)")
    parser.add_argument("--skip-bunker", action="store_true", help="Skip bunker data collection")
    parser.add_argument("--skip-forex", action="store_true", help="Skip forex data collection")
    parser.add_argument("--skip-bdi", action="store_true", help="Skip BDI data collection")
    
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("collect_data")
    
    # Ensure raw directory exists
    raw_dir = Path(DATA_RAW_DIR)
    raw_dir.mkdir(parents=True, exist_ok=True)

    collectors = []
    if not args.skip_bunker:
        collectors.append(BunkerCollector(output_dir=raw_dir))
    if not args.skip_forex:
        collectors.append(ForexCollector(output_dir=raw_dir))
    if not args.skip_bdi:
        collectors.append(BDICollector(output_dir=raw_dir))

    summary = []
    has_critical_failure = False

    for collector in collectors:
        try:
            df = collector.collect(start_date=args.start_date, end_date=args.end_date)
            if not df.empty:
                summary.append((collector.name, "SUCCESS", len(df)))
            else:
                summary.append((collector.name, "FAILED (Empty)", 0))
                has_critical_failure = True
        except Exception as e:
            logger.error(f"Collector {collector.name} failed with error: {e}")
            summary.append((collector.name, f"FAILED ({e})", 0))
            has_critical_failure = True

    logger.info("=== Collection Summary ===")
    for name, status, count in summary:
        logger.info(f"{name.ljust(15)}: {status} ({count} rows)")

    if has_critical_failure:
        logger.error("One or more collectors failed.")
        sys.exit(1)
    else:
        logger.info("All collectors succeeded.")
        sys.exit(0)

if __name__ == "__main__":
    main()
