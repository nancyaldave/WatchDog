"""
Anomaly Detection Module for Darwin Company
Detects anomalies based on average behavior per account using percentage threshold from settings.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, text
from typing import Dict, Any, List, Tuple
import warnings
warnings.filterwarnings('ignore')


class AnomalyDetector:
    """Detects anomalies in accounting transactions based on average behavior."""
    
    def __init__(self, config: Dict[str, Any], engine):
        """
        Initialize the anomaly detector.
        
        Args:
            config: Configuration dictionary
            engine: SQLAlchemy database engine
        """
        self.config = config
        self.engine = engine
        self.anomaly_config = config['anomaly_detection']
        self.company_name = config['company']['name']
        self.percentage_threshold = None
        
    def get_percentage_threshold(self) -> float:
        """
        Get the percentage threshold from config.setting table.
        
        Returns:
            Percentage threshold value
        """
        setting_key = self.anomaly_config['setting_key']
        
        query = text("""
            SELECT settingValue 
            FROM config.setting 
            WHERE settingKey = :setting_key
        """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query, {"setting_key": setting_key})
                row = result.fetchone()
                
                if row is None:
                    raise ValueError(f"Setting '{setting_key}' not found in config.setting table")
                
                percentage = float(row[0])
                print(f"✓ Percentage threshold loaded from settings: {percentage}%")
                return percentage
                
        except Exception as e:
            print(f"❌ Error loading percentage threshold: {e}")
            raise
    
    def load_transaction_data(self) -> pd.DataFrame:
        """
        Load transaction data from the database view.
        
        Returns:
            DataFrame with transaction data
        """
        lookback_days = self.anomaly_config.get('lookback_days', 365)
        
        query = f"""
        SELECT  
            A.accountID,
            A.accountNumber,
            B.[description] AS account,
            A.dtmDate,
            ISNULL(A.curDebit,0) - ISNULL(A.curCredit,0) AS amount
        FROM    rep_GLSource AS A WITH (NOLOCK) 
        INNER JOIN glAccount AS B WITH(NOLOCK) ON A.accountID = B.accountID 
        WHERE   dtmDate >= DATEADD(DAY, -{lookback_days}, GETDATE())
        AND     ISNULL(A.curDebit,0) - ISNULL(A.curCredit,0) > 0
        ORDER BY A.accountID, A.dtmDate
        """
        
        try:
            print(f"\n📊 Loading transaction data (last {lookback_days} days)...")
            df = pd.read_sql(query, self.engine)
            df['dtmDate'] = pd.to_datetime(df['dtmDate'])
            
            print(f"✓ Data loaded: {len(df):,} transactions")
            print(f"  - Unique accounts: {df['accountID'].nunique()}")
            print(f"  - Date range: {df['dtmDate'].min().date()} to {df['dtmDate'].max().date()}")
            
            return df
            
        except Exception as e:
            print(f"❌ Error loading transaction data: {e}")
            raise
    
    def calculate_averages_and_detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate average per account and detect anomalies.
        
        Args:
            df: DataFrame with transaction data
            
        Returns:
            DataFrame with detected anomalies
        """
        print(f"\n🔍 Calculating averages and detecting anomalies...")
        
        # Calculate average amount per account
        account_averages = df.groupby('accountID')['amount'].agg([
            ('avg_amount', 'mean'),
            ('std_amount', 'std'),
            ('min_amount', 'min'),
            ('max_amount', 'max'),
            ('count_transactions', 'count')
        ]).reset_index()
        
        # Merge averages back to original data
        df = df.merge(account_averages, on='accountID', how='left')
        
        # Calculate percentage difference from average
        df['pct_diff_from_avg'] = ((df['amount'] - df['avg_amount']) / df['avg_amount']) * 100
        
        # Detect anomalies: transactions that exceed the threshold percentage
        df['is_anomaly'] = df['pct_diff_from_avg'] >= self.percentage_threshold
        
        # Filter only anomalies
        anomalies = df[df['is_anomaly']].copy()
        
        # Add detection metadata
        anomalies['detection_date'] = datetime.now()
        anomalies['threshold_used'] = self.percentage_threshold
        anomalies['company'] = self.company_name
        
        print(f"✓ Anomalies detected: {len(anomalies):,} out of {len(df):,} transactions")
        print(f"  - Threshold used: {self.percentage_threshold}%")
        print(f"  - Anomaly rate: {(len(anomalies)/len(df)*100):.2f}%")
        
        return anomalies
    
    def save_anomalies_to_database(self, anomalies: pd.DataFrame) -> int:
        """
        Save detected anomalies to the database table.
        
        Args:
            anomalies: DataFrame with detected anomalies
            
        Returns:
            Number of records saved
        """
        if len(anomalies) == 0:
            print("\n✓ No anomalies to save")
            return 0
        
        table_name = self.anomaly_config['anomaly_table']
        
        # Prepare data for insertion
        save_columns = [
            'accountID', 'accountNumber', 'account', 'dtmDate', 'amount',
            'avg_amount', 'pct_diff_from_avg', 'threshold_used', 
            'detection_date', 'company'
        ]
        
        anomalies_to_save = anomalies[save_columns].copy()
        
        try:
            print(f"\n💾 Saving {len(anomalies_to_save)} anomalies to table '{table_name}'...")
            
            anomalies_to_save.to_sql(
                name=table_name,
                con=self.engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=1000
            )
            
            print(f"✓ Successfully saved {len(anomalies_to_save)} records to {table_name}")
            return len(anomalies_to_save)
            
        except Exception as e:
            print(f"❌ Error saving anomalies to database: {e}")
            raise
    
    def run_detection(self) -> Tuple[pd.DataFrame, int]:
        """
        Run the complete anomaly detection process.
        
        Returns:
            Tuple of (anomalies DataFrame, number of records saved)
        """
        # Get threshold from settings
        self.percentage_threshold = self.get_percentage_threshold()
        
        # Load transaction data
        df = self.load_transaction_data()
        
        if len(df) == 0:
            print("⚠️  No transaction data found")
            return pd.DataFrame(), 0
        
        # Detect anomalies
        anomalies = self.calculate_averages_and_detect(df)
        
        # Save to database
        records_saved = self.save_anomalies_to_database(anomalies)
        
        return anomalies, records_saved

