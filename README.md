# Sistema de Detección de Anomalías - Darwin Company

Sistema automatizado de detección de anomalías en transacciones contables basado en desviaciones del promedio por cuenta.

## 🎯 Características Principales

- ✅ **Detección basada en promedio**: Identifica transacciones que exceden el promedio de la cuenta por un porcentaje configurable
- ✅ **Configuración dinámica**: Lee el umbral de detección desde la tabla `config.setting` en la base de datos
- ✅ **Almacenamiento automático**: Guarda todas las anomalías detectadas en una tabla de base de datos
- ✅ **Alertas por email**: Envía emails HTML detallados con resumen y lista completa de anomalías
- ✅ **Adjuntos CSV**: Incluye archivo CSV con todos los detalles para análisis posterior
- ✅ **Empresa Darwin**: Sistema personalizado para Darwin Company

## 📋 Requisitos Previos

1. **SQL Server** con acceso a:
   - Tabla `rep_GLSource` (transacciones contables)
   - Tabla `glAccount` (catálogo de cuentas)
   - Tabla `config.setting` (configuración del sistema)
   - Tabla `AnomalyDetections` (para guardar anomalías - se crea con el script SQL incluido)

2. **Python 3.8+** instalado

3. **ODBC Driver 17 for SQL Server** instalado

4. **Servidor SMTP** configurado (puede ser local o externo como Gmail, Outlook, etc.)

## 🚀 Instalación

### 1. Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

### 2. Crear la tabla de anomalías en SQL Server

Ejecuta el script SQL incluido para crear la tabla donde se guardarán las anomalías:

```bash
sqlcmd -S localhost -d AT2017_DEPLOY -i create_anomaly_table.sql
```

O ejecuta el script `create_anomaly_table.sql` desde SQL Server Management Studio.

Este script:
- Crea la tabla `dbo.AnomalyDetections`
- Crea índices para mejor rendimiento
- Opcionalmente crea el setting `"percentage Anomalias"` en `config.setting` con valor por defecto de 50%

### 3. Configurar el sistema

Edita el archivo `config.json` con tus parámetros:

```json
{
  "database": {
    "server": "localhost",
    "database": "AT2017_DEPLOY",
    "driver": "ODBC Driver 17 for SQL Server",
    "trusted_connection": true
  },
  "anomaly_detection": {
    "setting_key": "percentage Anomalias",
    "anomaly_table": "AnomalyDetections",
    "lookback_days": 365
  },
  "email": {
    "enabled": true,
    "smtp_server": "localhost",
    "smtp_port": 25,
    "from_email": "anomaly-detector@darwin.com",
    "recipients": [
      "admin@darwin.com",
      "finance@darwin.com"
    ]
  }
}
```

### 4. Configurar el umbral de detección en la base de datos

El sistema lee el porcentaje de umbral desde la tabla `config.setting`. Asegúrate de tener este registro:

```sql
INSERT INTO config.setting (settingKey, settingValue, settingDescription)
VALUES ('percentage Anomalias', '50', 'Umbral de porcentaje para detección de anomalías');
```

**Ejemplo**: Si el valor es `50`, el sistema detectará transacciones que excedan el promedio de la cuenta en un 50% o más.

## 🏃 Uso

### Ejecución Manual

```bash
python main.py
```

### Ejecución Programada

**Windows Task Scheduler:**
```cmd
schtasks /create /tn "Darwin Anomaly Detection" /tr "python C:\ruta\al\proyecto\main.py" /sc daily /st 09:00
```

**Linux/Mac (Cron):**
```bash
# Ejecutar diariamente a las 9:00 AM
0 9 * * * cd /ruta/al/proyecto && python main.py >> logs/anomaly_detection.log 2>&1
```

## 📊 Cómo Funciona

### Proceso de Detección

1. **Carga de configuración**: Lee el umbral de porcentaje desde `config.setting`
2. **Extracción de datos**: Consulta transacciones de los últimos N días (configurable)
3. **Cálculo de promedios**: Calcula el promedio de transacciones por cada cuenta
4. **Detección de anomalías**: Identifica transacciones que exceden el promedio por el porcentaje configurado
5. **Almacenamiento**: Guarda las anomalías detectadas en la tabla `AnomalyDetections`
6. **Envío de alertas**: Envía email HTML con resumen y detalles + archivo CSV adjunto

### Fórmula de Detección

```
Anomalía detectada si:
((Monto - Promedio) / Promedio) * 100 >= Umbral%
```

**Ejemplo**:
- Promedio de la cuenta: $1,000
- Umbral configurado: 50%
- Transacción de $1,600
- Cálculo: ((1600 - 1000) / 1000) * 100 = 60%
- **Resultado**: ✅ Anomalía detectada (60% > 50%)

## 📁 Estructura del Proyecto

```
Darwin Anomaly Detection/
├── main.py                        # Script principal
├── anomaly_detector.py            # Módulo de detección de anomalías
├── email_alert.py                 # Sistema de alertas por email
├── config.json                    # Configuración del sistema
├── requirements.txt               # Dependencias Python
├── create_anomaly_table.sql       # Script SQL para crear tabla
└── README.md                      # Esta documentación
```

## 📧 Formato del Email de Alerta

El email incluye:

- **Encabezado**: Logo y título de Darwin Company
- **Resumen estadístico**:
  - Total de anomalías detectadas
  - Monto total involucrado
  - Desviación promedio
  - Fecha de detección
  - Umbral utilizado
- **Tabla detallada**: Lista de todas las anomalías con:
  - Número de cuenta
  - Nombre de cuenta
  - Fecha de transacción
  - Monto
  - Promedio de la cuenta
  - Porcentaje de desviación
- **Acciones recomendadas**: Pasos sugeridos para revisar las anomalías
- **Archivo CSV adjunto**: Datos completos para análisis en Excel

## 🔧 Ajuste de Parámetros

### Cambiar el umbral de detección

Actualiza el valor en la base de datos:

```sql
UPDATE config.setting 
SET settingValue = '75'  -- Nuevo umbral: 75%
WHERE settingKey = 'percentage Anomalias';
```

### Cambiar el período de análisis

Edita `config.json`:

```json
"anomaly_detection": {
  "lookback_days": 180  -- Analizar últimos 6 meses
}
```

## 👥 Soporte

Para problemas o preguntas, contactar al equipo de desarrollo de Darwin Company.

---

**Darwin Company** - Sistema de Detección de Anomalías v1.0

