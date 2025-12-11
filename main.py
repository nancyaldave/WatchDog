"""
Darwin Company - Anomaly Detection System
Main script to detect anomalies in accounting transactions and send alerts.

This system:
1. Reads percentage threshold from config.setting table
2. Detects transactions that exceed the average by that percentage
3. Saves anomalies to a user-defined table
4. Sends detailed email alerts to configured recipients
"""

import json
import sys
from datetime import datetime
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')

from anomaly_detector import AnomalyDetector
from email_alert import EmailAlertSystem


class AnomalyDetectionSystem:
    """Main orchestrator for the anomaly detection system."""
    
    def __init__(self, config_path='config.json'):
        """
        Initialize the system.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.engine = self._setup_database()
        
    def _load_config(self) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✓ Configuration loaded from {self.config_path}")
            return config
        except FileNotFoundError:
            print(f"❌ Configuration file not found: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing configuration file: {e}")
            sys.exit(1)
    
    def _setup_database(self):
        """Setup database connection."""
        db_config = self.config['database']
        
        try:
            if db_config.get('trusted_connection'):
                connection_string = (
                    f"mssql+pyodbc://@{db_config['server']}/{db_config['database']}"
                    f"?driver={db_config['driver'].replace(' ', '+')}"
                    f"&trusted_connection=yes"
                )
            else:
                username = db_config.get('username', '')
                password = db_config.get('password', '')
                if not username or not password:
                    raise ValueError("Database username and password required when trusted_connection is false")
                
                connection_string = (
                    f"mssql+pyodbc://{username}:{password}@{db_config['server']}/{db_config['database']}"
                    f"?driver={db_config['driver'].replace(' ', '+')}"
                )
            
            engine = create_engine(connection_string)
            
            # Test connection
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            
            print(f"✓ Database connection established: {db_config['server']}/{db_config['database']}")
            return engine
            
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
            sys.exit(1)
    
    def run(self):
        """Execute the complete anomaly detection process."""
        print("=" * 80)
        print(f"🔍 {self.config['company']['name']} - ANOMALY DETECTION SYSTEM")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            # Initialize detector
            detector = AnomalyDetector(self.config, self.engine)
            
            # Run detection
            print("STEP 1: Running Anomaly Detection")
            print("-" * 80)
            anomalies, records_saved = detector.run_detection()
            
            # Send email alerts
            if len(anomalies) > 0:
                print("\nSTEP 2: Sending Email Alerts")
                print("-" * 80)
                email_system = EmailAlertSystem(self.config)
                email_sent = email_system.send_alert(
                    anomalies, 
                    detector.percentage_threshold
                )
                
                if email_sent:
                    print("✓ Email alert process completed")
                else:
                    print("⚠️  Email alert was not sent")
            else:
                print("\nSTEP 2: Email Alerts")
                print("-" * 80)
                print("✓ No anomalies detected - no alerts to send")
            
            # Summary
            print("\n" + "=" * 80)
            print("📊 EXECUTION SUMMARY")
            print("=" * 80)
            print(f"Anomalies Detected: {len(anomalies)}")
            print(f"Records Saved to Database: {records_saved}")
            print(f"Email Alerts Sent: {'Yes' if len(anomalies) > 0 else 'No'}")
            print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            print("✅ PROCESS COMPLETED SUCCESSFULLY")
            print("=" * 80)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Process interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n\n❌ CRITICAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            # Close database connection
            if hasattr(self, 'engine'):
                self.engine.dispose()
                print("\n✓ Database connection closed")


def main():
    """Main entry point."""
    system = AnomalyDetectionSystem()
    system.run()


if __name__ == '__main__':
    main()

