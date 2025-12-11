"""
Anomaly detection system for accounting accounts using Isolation Forest
and alerts via local LLM.
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from sqlalchemy import create_engine
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from alert_system import AlertSystem
from llm_generator import LLMAlertGenerator


class AnomalyDetector:
    """Main class for detecting anomalies in accounting accounts."""
    
    def __init__(self, config_path='config.json'):
        """Initialize the detector with configuration."""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Setup database connection
        self._setup_database_connection()
        
        # Setup Isolation Forest
        self._setup_isolation_forest()
        
        # Initialize alert systems
        recipients_file = self.config.get('recipients_file', 'recipients.json')
        self.alert_system = AlertSystem(recipients_file)
        self.llm_generator = LLMAlertGenerator(self.config.get('llm', {}))
    
    def _setup_database_connection(self):
        """Configure SQL Server connection."""
        db_config = self.config['database']
        
        # Construir servidor con puerto si está especificado
        server = db_config['server']
        port = db_config.get('port')
        if port:
            server = f"{server},{port}"
        
        if db_config.get('trusted_connection'):
            # Autenticación Windows (Trusted Connection)
            connection_string = (
                f"mssql+pyodbc://@{server}/{db_config['database']}"
                f"?driver={db_config['driver'].replace(' ', '+')}"
                f"&trusted_connection=yes"
            )
        else:
            # Autenticación con usuario y contraseña
            username = db_config.get('username', '')
            password = db_config.get('password', '')
            
            if not username or not password:
                raise ValueError(
                    "Para autenticación SQL Server, configura 'username' y 'password' "
                    "en config.json o usa 'trusted_connection': true para autenticación Windows"
                )
            
            # Escapar caracteres especiales en la contraseña para URL
            from urllib.parse import quote_plus
            password_encoded = quote_plus(password)
            username_encoded = quote_plus(username)
            
            connection_string = (
                f"mssql+pyodbc://{username_encoded}:{password_encoded}@{server}/{db_config['database']}"
                f"?driver={db_config['driver'].replace(' ', '+')}"
            )
        
        self.engine = create_engine(connection_string)
        print(f"✓ Conexión a base de datos configurada: {server}/{db_config['database']}")
    
    def _setup_isolation_forest(self):
        """Configure the Isolation Forest model."""
        if_config = self.config['isolation_forest']
        self.isolation_forest = IsolationForest(
            contamination=if_config.get('contamination', 0.02),
            random_state=if_config.get('random_state', 42),
            n_estimators=if_config.get('n_estimators', 100)
        )
        self.scaler = StandardScaler()
        print("✓ Isolation Forest configured")
    
    def load_data(self):
        """Load data from SQL view."""
        print("\n📊 Loading data from view...")
        
        query = "SELECT * FROM vw_GLSource_daily ORDER BY accountID, dtmDate"
        
        try:
            df = pd.read_sql(query, self.engine)
            df['dtmDate'] = pd.to_datetime(df['dtmDate'])
            
            print(f"✓ Data loaded: {len(df):,} records")
            print(f"  - Unique accounts: {df['accountID'].nunique()}")
            print(f"  - Date range: {df['dtmDate'].min().date()} to {df['dtmDate'].max().date()}")
            
            return df
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            raise
    
    def prepare_features(self, df):
        """Prepare features for the model."""
        print("\n🔧 Preparing features...")
        
        # Calculate yearly average per account
        avg_year = df.groupby('accountID')['amount'].mean().rename('avg_year_amount')
        df = df.merge(avg_year, on='accountID', how='left')
        
        # Calculate ratio vs yearly average
        df['ratio_vs_avg'] = df['amount'] / df['avg_year_amount'].replace(0, np.nan)
        
        # Calculate additional statistics per account
        account_stats = df.groupby('accountID')['amount'].agg([
            'std', 'min', 'max', 'median'
        ]).add_prefix('amount_')
        
        df = df.merge(account_stats, on='accountID', how='left')
        
        # Feature: normalized standard deviation
        df['z_score'] = (df['amount'] - df['avg_year_amount']) / df['amount_std'].replace(0, np.nan)
        
        # Feature: percentage difference vs median
        df['pct_diff_median'] = ((df['amount'] - df['amount_median']) / 
                                  df['amount_median'].replace(0, np.nan)) * 100
        
        print(f"✓ Features prepared: {len(df.columns)} columns")
        
        return df
    
    def detect_anomalies(self, df):
        """Detecta anomalías usando Isolation Forest."""
        print("\n🔍 Detectando anomalías...")
        
        # Prepare features for Isolation Forest
        feature_cols = ['amount', 'avg_year_amount', 'ratio_vs_avg', 
                       'z_score', 'pct_diff_median']
        
        # Filter null and infinite values
        df_clean = df.dropna(subset=feature_cols)
        df_clean = df_clean.replace([np.inf, -np.inf], np.nan).dropna(subset=feature_cols)
        
        if len(df_clean) == 0:
            print("⚠️  No valid data to analyze")
            return pd.DataFrame()
        
        # Scale features
        features_scaled = self.scaler.fit_transform(df_clean[feature_cols])
        
        # Apply Isolation Forest
        df_clean['if_prediction'] = self.isolation_forest.fit_predict(features_scaled)
        df_clean['if_score'] = self.isolation_forest.score_samples(features_scaled)
        
        # Detectar anomalías solo con Isolation Forest
        df_clean['is_anomaly'] = (df_clean['if_prediction'] == -1)
        
        anomalies = df_clean[df_clean['is_anomaly']].copy()
        
        print(f"✓ Anomalías detectadas: {len(anomalies):,}")
        print(f"  - Método: Isolation Forest")
        
        return anomalies
    
    def generate_alert_messages(self, anomalies):
        """Generate alert messages using local LLM."""
        print("\n📝 Generating alert messages...")
        
        if len(anomalies) == 0:
            print("✓ No anomalies to alert")
            return []
        
        alerts = []
        
        for idx, row in anomalies.iterrows():
            # Prepare data for LLM
            alert_data = {
                'account_number': str(row['accountNumber']),
                'account_name': str(row['account']),
                'date': row['dtmDate'].strftime('%Y-%m-%d'),
                'amount': float(row['amount']),
                'yearly_average': float(row['avg_year_amount']),
                'ratio': float(row['ratio_vs_avg']),
                'detection_method': 'Isolation Forest',
                'isolation_score': float(row['if_score'])
            }
            
            # Generate message with LLM
            try:
                message = self.llm_generator.generate_alert(alert_data)
                alerts.append({
                    'data': alert_data,
                    'message': message
                })
            except Exception as e:
                print(f"⚠️  Error generating LLM message for account {row['accountNumber']}: {e}")
                # Fallback message without LLM
                alerts.append({
                    'data': alert_data,
                    'message': self._generate_fallback_message(alert_data)
                })
        
        print(f"✓ {len(alerts)} messages generated")
        return alerts
    
    def _generate_fallback_message(self, data):
        """Generate alert message without LLM as fallback."""
        return (
            f"🚨 ANOMALY ALERT DETECTED\n\n"
            f"Account: {data['account_number']} - {data['account_name']}\n"
            f"Date: {data['date']}\n"
            f"Amount: ${data['amount']:,.2f}\n"
            f"Yearly average: ${data['yearly_average']:,.2f}\n"
            f"Ratio: {data['ratio']:.2f}x\n"
            f"Método de detección: {data['detection_method']}\n"
            f"Score de anomalía: {data['isolation_score']:.4f}\n\n"
            f"Una anomalía ha sido detectada mediante Isolation Forest. "
            f"Se requiere revisión inmediata."
        )
    
    def send_alerts(self, alerts):
        """Send alerts to configured recipients."""
        if not alerts:
            print("\n✓ No alerts to send")
            return
        
        print(f"\n📧 Sending {len(alerts)} alerts...")
        
        for alert in alerts:
            try:
                self.alert_system.send_alert(alert['message'], alert['data'])
            except Exception as e:
                print(f"⚠️  Error sending alert: {e}")
        
        print("✓ Alert process completed")
    
    def run(self):
        """Execute the complete detection process."""
        print("=" * 60)
        print("🔍 ANOMALY DETECTION SYSTEM")
        print("=" * 60)
        
        try:
            # 1. Load data
            df = self.load_data()
            
            # 2. Prepare features
            df = self.prepare_features(df)
            
            # 3. Detect anomalies
            anomalies = self.detect_anomalies(df)
            
            # 4. Generate alert messages
            alerts = self.generate_alert_messages(anomalies)
            
            # 5. Send alerts
            self.send_alerts(alerts)
            
            # 6. Save report
            if len(anomalies) > 0:
                self._save_report(anomalies)
            
            print("\n" + "=" * 60)
            print("✅ PROCESS COMPLETED")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error in process: {e}")
            raise
    
    def _save_report(self, anomalies):
        """Save a CSV report with detected anomalies."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"anomalies_report_{timestamp}.csv"
        
        # Select relevant columns for report
        report_cols = [
            'accountID', 'accountNumber', 'account', 'dtmDate',
            'amount', 'avg_year_amount', 'ratio_vs_avg',
            'if_prediction', 'if_score'
        ]
        
        report = anomalies[report_cols].copy()
        report.to_csv(filename, index=False, encoding='utf-8-sig')
        
        print(f"\n📄 Report saved: {filename}")


def main():
    """Main function."""
    detector = AnomalyDetector()
    detector.run()


if __name__ == '__main__':
    main()

