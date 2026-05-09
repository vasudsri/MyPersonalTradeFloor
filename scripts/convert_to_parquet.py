import pandas as pd
import os
import glob
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "extensions", "momentum_trading", "data", "raw")
FINE_DATA_DIR = os.path.join(BASE_DIR, "extensions", "momentum_trading", "data", "fine")

def convert_csv_to_parquet():
    """Converts all CSV files in the raw folder into Parquet format in the fine folder."""
    csv_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.csv"))
    
    if not csv_files:
        logger.warning(f"No CSV files found in {RAW_DATA_DIR}. Drop your raw backtest data there.")
        return

    logger.info(f"Found {len(csv_files)} CSV files for conversion.")

    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        parquet_filename = filename.replace(".csv", ".parquet")
        target_path = os.path.join(FINE_DATA_DIR, parquet_filename)

        try:
            logger.info(f"Reading {filename}...")
            # Using low_memory=False for large datasets
            df = pd.read_csv(csv_file, low_memory=False)
            
            # Identify and convert common datetime columns
            date_cols = ['date', 'Date', 'timestamp', 'Timestamp', 'datetime', 'DateTime']
            for col in date_cols:
                if col in df.columns:
                    try:
                        df[col] = pd.to_datetime(df[col])
                        logger.info(f"Converted '{col}' column to datetime.")
                    except Exception as date_err:
                        logger.warning(f"Failed to convert column '{col}' to datetime: {date_err}")

            logger.info(f"Saving to Parquet: {parquet_filename}...")
            df.to_parquet(target_path, index=False, engine='pyarrow')
            logger.info(f"Successfully processed: {target_path}")
            
        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")

if __name__ == "__main__":
    os.makedirs(FINE_DATA_DIR, exist_ok=True)
    convert_csv_to_parquet()
