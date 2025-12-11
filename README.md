# Sistema de Detección de Anomalías en Cuentas Contables

Sistema que detecta anomalías en montos de cuentas contables usando **Isolation Forest** y envía alertas automáticas mediante **LLM local**.

## 🎯 Características

- ✅ Detección de anomalías usando **Isolation Forest** (machine learning)
- ✅ Regla de negocio: alerta si el monto supera **3x el promedio anual**
- ✅ Generación de mensajes inteligentes usando **LLM local** (Ollama)
- ✅ Envío de alertas por **Email**, **Microsoft Teams** y **Slack**
- ✅ Reportes CSV con anomalías detectadas

## 📋 Requisitos Previos

1. **SQL Server** con la vista `vw_GLSource_daily` creada
2. **Python 3.8+**
3. **Ollama** instalado y ejecutándose (opcional, para LLM)
4. **ODBC Driver 17 for SQL Server** instalado

## 🚀 Instalación

1. **Clonar o descargar el proyecto**

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configurar la conexión a la base de datos en `config.json`**

4. **Configurar destinatarios de alertas en `recipients.json`**

## 📝 Configuración

### 1. Configuración principal (`config.json`)

Edita el archivo `config.json`:

```json
{
  "database": {
    "server": "localhost",
    "database": "AT2017_DEPLOY",
    "driver": "ODBC Driver 17 for SQL Server",
    "trusted_connection": true
  },
  "recipients_file": "recipients.json",
  "isolation_forest": {
    "contamination": 0.02,
    "random_state": 42,
    "n_estimators": 100
  },
  "alert_threshold": {
    "ratio_multiplier": 3.0
  },
  "llm": {
    "model": "llama3",
    "base_url": "http://localhost:11434",
    "enabled": true
  }
}
```

### 2. Destinatarios de alertas (`recipients.json`)

Edita el archivo `recipients.json` para agregar o modificar destinatarios:

```json
{
  "people": [
    {
      "name": "Administrador del Sistema",
      "email": "admin@example.com",
      "role": "Administrator",
      "enabled": true
    },
    {
      "name": "Gerente de Finanzas",
      "email": "finance@example.com",
      "role": "Finance Manager",
      "enabled": true
    },
    {
      "name": "Contador Principal",
      "email": "accountant@example.com",
      "role": "Senior Accountant",
      "enabled": false
    }
  ],
  "channels": {
    "teams_webhook": "https://outlook.office.com/webhook/...",
    "slack_webhook": "https://hooks.slack.com/services/..."
  },
  "email_settings": {
    "from_email": "anomaly-detector@accounttech.com",
    "from_name": "Sistema de Detección de Anomalías",
    "smtp_server": "localhost",
    "smtp_port": 25,
    "use_tls": false,
    "use_authentication": false,
    "smtp_username": "",
    "smtp_password": ""
  }
}
```

**Campos de cada persona:**
- `name`: Nombre completo de la persona
- `email`: Dirección de email para recibir alertas
- `role`: Rol o cargo (opcional, para referencia)
- `enabled`: `true` para recibir alertas, `false` para deshabilitar temporalmente

**Canales:**
- `teams_webhook`: URL del webhook de Microsoft Teams (opcional)
- `slack_webhook`: URL del webhook de Slack (opcional)

**Configuración de email:**
- `from_email`: Email del remitente
- `from_name`: Nombre del remitente
- `smtp_server`: Servidor SMTP (ej: `smtp.gmail.com`, `smtp-mail.outlook.com`, `localhost`)
- `smtp_port`: Puerto SMTP (25 para servidor local, 587 para TLS, 465 para SSL)
- `use_tls`: `true` para habilitar TLS/STARTTLS (requerido para Gmail, Outlook)
- `use_authentication`: `true` para usar autenticación SMTP
- `smtp_username`: Usuario SMTP (si `use_authentication` es `true`)
- `smtp_password`: Contraseña SMTP (si `use_authentication` es `true`)

**Ejemplos de configuración SMTP:**

Para Gmail:
```json
"smtp_server": "smtp.gmail.com",
"smtp_port": 587,
"use_tls": true,
"use_authentication": true,
"smtp_username": "tu-email@gmail.com",
"smtp_password": "tu-contraseña-de-aplicacion"
```

Para servidor local (sin autenticación):
```json
"smtp_server": "localhost",
"smtp_port": 25,
"use_tls": false,
"use_authentication": false
```

### Parámetros importantes:

- **database**: Configuración de conexión SQL Server
- **recipients_file**: Ruta al archivo JSON con destinatarios (por defecto: `recipients.json`)
- **isolation_forest.contamination**: Porcentaje esperado de anomalías (0.02 = 2%)
- **alert_threshold.ratio_multiplier**: Multiplicador para regla de negocio (3.0 = 3x)
- **llm**: Configuración del LLM local (Ollama)

## 🗄️ Vista SQL Requerida

Asegúrate de tener creada la vista `vw_GLSource_daily` en SQL Server:

```sql
USE AT2017_DEPLOY;
GO

CREATE OR ALTER VIEW vw_GLSource_daily AS
SELECT  
    A.accountID,
    A.accountNumber,
    B.[description] AS account,
    A.dtmDate,
    SUM(ISNULL(A.curDebit,0) - ISNULL(A.curCredit,0)) AS amount
FROM    rep_GLSource AS A WITH (NOLOCK) 
INNER JOIN glAccount AS B WITH(NOLOCK) ON A.accountID = B.accountID 
WHERE   dtmDate >= DATEADD(YEAR, -1, GETDATE())
GROUP BY A.accountID,
        A.accountNumber,
        B.[description],
        A.dtmDate;
GO
```

## 🏃 Uso

### Ejecución básica:

```bash
python main.py
```

### Ejecución programada (Windows Task Scheduler / Cron):

**Windows:**
```cmd
schtasks /create /tn "Anomaly Detection" /tr "python C:\ruta\al\proyecto\main.py" /sc daily /st 09:00
```

**Linux/Mac (Cron):**
```bash
# Ejecutar diariamente a las 9:00 AM
0 9 * * * cd /ruta/al/proyecto && python main.py >> logs/anomaly_detection.log 2>&1
```

## 📊 Cómo Funciona

1. **Carga de datos**: Lee datos desde `vw_GLSource_daily`
2. **Preparación de features**:
   - Calcula promedio anual por cuenta
   - Calcula ratio vs promedio
   - Genera estadísticas adicionales (z-score, desviaciones)
3. **Detección de anomalías**:
   - Aplica **Isolation Forest** para detectar outliers
   - Aplica regla de negocio: **monto ≥ 3x promedio anual**
   - Combina ambas condiciones
4. **Generación de alertas**:
   - Usa **LLM local** para generar mensajes profesionales
   - Si LLM no está disponible, usa mensaje de respaldo
5. **Envío de alertas**:
   - Envía a emails configurados
   - Envía a Teams/Slack si están configurados
6. **Generación de reporte**: Guarda CSV con anomalías detectadas

## 📁 Estructura del Proyecto

```
Py WhatDog/
├── main.py                 # Script principal
├── alert_system.py         # Sistema de envío de alertas
├── llm_generator.py        # Generador de mensajes con LLM
├── config.json             # Configuración del sistema
├── recipients.json         # Lista de destinatarios de alertas
├── create_view.sql         # Script SQL para crear la vista
├── requirements.txt        # Dependencias Python
└── README.md              # Este archivo
```

## 🔧 Configuración de Ollama (LLM Local)

1. **Instalar Ollama**: https://ollama.ai/

2. **Descargar modelo**:
```bash
ollama pull llama3
```

3. **Verificar que Ollama esté corriendo**:
```bash
ollama serve
```

4. **Probar el modelo**:
```bash
ollama run llama3 "Hola, ¿cómo estás?"
```

Si no quieres usar LLM, configura `"enabled": false` en `config.json` bajo `llm`.

## 📧 Configuración de Email

Para enviar emails, configura tu servidor SMTP en `recipients.json` bajo la sección `email_settings`. 

El sistema ahora envía emails realmente (el código SMTP está implementado y funcional). Configura los siguientes parámetros según tu servidor:

- **Servidor local**: Usa `localhost` con puerto `25`, sin TLS ni autenticación
- **Gmail**: Requiere TLS y autenticación con contraseña de aplicación
- **Outlook/Office365**: Requiere TLS y autenticación

Ver la sección de configuración de `recipients.json` arriba para ejemplos completos.

## 🐛 Solución de Problemas

### Error de conexión a SQL Server:
- Verifica que el driver ODBC esté instalado
- Verifica credenciales en `config.json`
- Prueba la conexión con `sqlcmd` o SQL Server Management Studio

### Error con Ollama:
- Verifica que Ollama esté corriendo: `ollama serve`
- Verifica que el modelo esté descargado: `ollama list`
- Si no quieres usar LLM, configura `"enabled": false`

### No se detectan anomalías:
- Ajusta `contamination` en `config.json` (valores más altos = más anomalías)
- Verifica que haya datos en la vista `vw_GLSource_daily`
- Revisa los logs de ejecución

## 📈 Ajuste de Parámetros

- **contamination**: Porcentaje esperado de anomalías
  - 0.01 = 1% de los datos son anomalías
  - 0.05 = 5% de los datos son anomalías
  
- **ratio_multiplier**: Umbral para regla de negocio
  - 3.0 = alerta si monto ≥ 3x promedio
  - 2.5 = alerta si monto ≥ 2.5x promedio

## 📝 Licencia

Este proyecto es de uso interno de Accounttech.

## 👥 Soporte

Para problemas o preguntas, contactar al equipo de desarrollo.

