"""
Sistema de detección de anomalías en cuentas contables usando Isolation Forest
y alertas mediante LLM local.
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
    """Clase principal para detectar anomalías en cuentas contables."""
    
    def __init__(self, config_path='config.json'):
        """Inicializa el detector con configuración."""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Configurar conexión a base de datos
        self._setup_database_connection()
        
        # Configurar Isolation Forest
        self._setup_isolation_forest()
        
        # Inicializar sistemas de alerta
        recipients_file = self.config.get('recipients_file', 'recipients.json')
        self.alert_system = AlertSystem(recipients_file)
        self.llm_generator = LLMAlertGenerator(self.config.get('llm', {}))
    
    def _setup_database_connection(self):
        """Configura la conexión a SQL Server."""
        db_config = self.config['database']
        
        if db_config.get('trusted_connection'):
            connection_string = (
                f"mssql+pyodbc://@{db_config['server']}/{db_config['database']}"
                f"?driver={db_config['driver'].replace(' ', '+')}"
                f"&trusted_connection=yes"
            )
        else:
            # Si necesitas autenticación por usuario/password
            # connection_string = f"mssql+pyodbc://{user}:{password}@{server}/{database}?driver={driver}"
            raise ValueError("Configura autenticación en config.json")
        
        self.engine = create_engine(connection_string)
        print("✓ Conexión a base de datos configurada")
    
    def _setup_isolation_forest(self):
        """Configura el modelo Isolation Forest."""
        if_config = self.config['isolation_forest']
        self.isolation_forest = IsolationForest(
            contamination=if_config.get('contamination', 0.02),
            random_state=if_config.get('random_state', 42),
            n_estimators=if_config.get('n_estimators', 100)
        )
        self.scaler = StandardScaler()
        print("✓ Isolation Forest configurado")
    
    def load_data(self):
        """Carga datos desde la vista SQL."""
        print("\n📊 Cargando datos desde la vista...")
        
        query = "SELECT * FROM vw_GLSource_daily ORDER BY accountID, dtmDate"
        
        try:
            df = pd.read_sql(query, self.engine)
            df['dtmDate'] = pd.to_datetime(df['dtmDate'])
            
            print(f"✓ Datos cargados: {len(df):,} registros")
            print(f"  - Cuentas únicas: {df['accountID'].nunique()}")
            print(f"  - Rango de fechas: {df['dtmDate'].min().date()} a {df['dtmDate'].max().date()}")
            
            return df
        except Exception as e:
            print(f"❌ Error al cargar datos: {e}")
            raise
    
    def prepare_features(self, df):
        """Prepara features para el modelo."""
        print("\n🔧 Preparando features...")
        
        # Calcular promedio anual por cuenta
        avg_year = df.groupby('accountID')['amount'].mean().rename('avg_year_amount')
        df = df.merge(avg_year, on='accountID', how='left')
        
        # Calcular ratio vs promedio anual
        df['ratio_vs_avg'] = df['amount'] / df['avg_year_amount'].replace(0, np.nan)
        
        # Calcular estadísticas adicionales por cuenta
        account_stats = df.groupby('accountID')['amount'].agg([
            'std', 'min', 'max', 'median'
        ]).add_prefix('amount_')
        
        df = df.merge(account_stats, on='accountID', how='left')
        
        # Feature: desviación estándar normalizada
        df['z_score'] = (df['amount'] - df['avg_year_amount']) / df['amount_std'].replace(0, np.nan)
        
        # Feature: diferencia porcentual vs mediana
        df['pct_diff_median'] = ((df['amount'] - df['amount_median']) / 
                                  df['amount_median'].replace(0, np.nan)) * 100
        
        print(f"✓ Features preparadas: {len(df.columns)} columnas")
        
        return df
    
    def detect_anomalies(self, df):
        """Detecta anomalías usando Isolation Forest y regla de negocio."""
        print("\n🔍 Detectando anomalías...")
        
        # Preparar features para Isolation Forest
        feature_cols = ['amount', 'avg_year_amount', 'ratio_vs_avg', 
                       'z_score', 'pct_diff_median']
        
        # Filtrar valores nulos e infinitos
        df_clean = df.dropna(subset=feature_cols)
        df_clean = df_clean.replace([np.inf, -np.inf], np.nan).dropna(subset=feature_cols)
        
        if len(df_clean) == 0:
            print("⚠️  No hay datos válidos para analizar")
            return pd.DataFrame()
        
        # Escalar features
        features_scaled = self.scaler.fit_transform(df_clean[feature_cols])
        
        # Aplicar Isolation Forest
        df_clean['if_prediction'] = self.isolation_forest.fit_predict(features_scaled)
        df_clean['if_score'] = self.isolation_forest.score_samples(features_scaled)
        
        # Regla de negocio: 3x el promedio anual
        threshold = self.config['alert_threshold']['ratio_multiplier']
        df_clean['business_rule_alert'] = df_clean['ratio_vs_avg'] >= threshold
        
        # Combinar ambas condiciones
        df_clean['is_anomaly'] = (
            (df_clean['if_prediction'] == -1) |  # Isolation Forest detecta anomalía
            (df_clean['business_rule_alert'])    # Regla de negocio: >= 3x promedio
        )
        
        anomalies = df_clean[df_clean['is_anomaly']].copy()
        
        print(f"✓ Anomalías detectadas: {len(anomalies):,}")
        print(f"  - Por Isolation Forest: {(df_clean['if_prediction'] == -1).sum()}")
        print(f"  - Por regla de negocio (≥{threshold}x): {df_clean['business_rule_alert'].sum()}")
        
        return anomalies
    
    def generate_alert_messages(self, anomalies):
        """Genera mensajes de alerta usando LLM local."""
        print("\n📝 Generando mensajes de alerta...")
        
        if len(anomalies) == 0:
            print("✓ No hay anomalías para alertar")
            return []
        
        alerts = []
        
        for idx, row in anomalies.iterrows():
            # Preparar datos para el LLM
            alert_data = {
                'account_number': str(row['accountNumber']),
                'account_name': str(row['account']),
                'date': row['dtmDate'].strftime('%Y-%m-%d'),
                'amount': float(row['amount']),
                'yearly_average': float(row['avg_year_amount']),
                'ratio': float(row['ratio_vs_avg']),
                'detection_method': 'Isolation Forest' if row['if_prediction'] == -1 else 'Business Rule',
                'isolation_score': float(row['if_score'])
            }
            
            # Generar mensaje con LLM
            try:
                message = self.llm_generator.generate_alert(alert_data)
                alerts.append({
                    'data': alert_data,
                    'message': message
                })
            except Exception as e:
                print(f"⚠️  Error generando mensaje LLM para cuenta {row['accountNumber']}: {e}")
                # Mensaje de respaldo sin LLM
                alerts.append({
                    'data': alert_data,
                    'message': self._generate_fallback_message(alert_data)
                })
        
        print(f"✓ {len(alerts)} mensajes generados")
        return alerts
    
    def _generate_fallback_message(self, data):
        """Genera mensaje de alerta sin LLM como respaldo."""
        return (
            f"🚨 ALERTA DE ANOMALÍA DETECTADA\n\n"
            f"Cuenta: {data['account_number']} - {data['account_name']}\n"
            f"Fecha: {data['date']}\n"
            f"Monto: ${data['amount']:,.2f}\n"
            f"Promedio anual: ${data['yearly_average']:,.2f}\n"
            f"Ratio: {data['ratio']:.2f}x\n"
            f"Método de detección: {data['detection_method']}\n\n"
            f"Este monto supera {data['ratio']:.1f} veces el promedio anual. "
            f"Se requiere revisión inmediata."
        )
    
    def send_alerts(self, alerts):
        """Envía alertas a los destinatarios configurados."""
        if not alerts:
            print("\n✓ No hay alertas para enviar")
            return
        
        print(f"\n📧 Enviando {len(alerts)} alertas...")
        
        for alert in alerts:
            try:
                self.alert_system.send_alert(alert['message'], alert['data'])
            except Exception as e:
                print(f"⚠️  Error enviando alerta: {e}")
        
        print("✓ Proceso de alertas completado")
    
    def run(self):
        """Ejecuta el proceso completo de detección."""
        print("=" * 60)
        print("🔍 SISTEMA DE DETECCIÓN DE ANOMALÍAS")
        print("=" * 60)
        
        try:
            # 1. Cargar datos
            df = self.load_data()
            
            # 2. Preparar features
            df = self.prepare_features(df)
            
            # 3. Detectar anomalías
            anomalies = self.detect_anomalies(df)
            
            # 4. Generar mensajes de alerta
            alerts = self.generate_alert_messages(anomalies)
            
            # 5. Enviar alertas
            self.send_alerts(alerts)
            
            # 6. Guardar reporte
            if len(anomalies) > 0:
                self._save_report(anomalies)
            
            print("\n" + "=" * 60)
            print("✅ PROCESO COMPLETADO")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error en el proceso: {e}")
            raise
    
    def _save_report(self, anomalies):
        """Guarda un reporte CSV con las anomalías detectadas."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"anomalies_report_{timestamp}.csv"
        
        # Seleccionar columnas relevantes para el reporte
        report_cols = [
            'accountID', 'accountNumber', 'account', 'dtmDate',
            'amount', 'avg_year_amount', 'ratio_vs_avg',
            'if_prediction', 'if_score', 'business_rule_alert'
        ]
        
        report = anomalies[report_cols].copy()
        report.to_csv(filename, index=False, encoding='utf-8-sig')
        
        print(f"\n📄 Reporte guardado: {filename}")


def main():
    """Función principal."""
    detector = AnomalyDetector()
    detector.run()


if __name__ == '__main__':
    main()

