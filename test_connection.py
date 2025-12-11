"""
Script para probar la conexión a la base de datos SQL Server en Docker
"""

import json
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus


def test_database_connection():
    """Prueba la conexión a la base de datos."""

    # Cargar configuración
    print("📋 Cargando configuración desde config.json...")
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    db_config = config['database']

    # Mostrar configuración (sin mostrar la contraseña completa)
    print("\n🔧 Configuración de conexión:")
    print(f"  - Servidor: {db_config['server']}")
    print(f"  - Puerto: {db_config.get('port', 'default')}")
    print(f"  - Base de datos: {db_config['database']}")
    print(f"  - Usuario: {db_config.get('username', 'N/A')}")
    print(f"  - Contraseña: {'*' * len(db_config.get('password', ''))}")

    # Construir connection string usando pymssql (no requiere drivers ODBC)
    server = db_config['server']
    port = db_config.get('port', 1433)
    username = db_config.get('username', '')
    password = db_config.get('password', '')
    database = db_config['database']

    # Usar pymssql en lugar de pyodbc para evitar problemas con drivers ODBC
    connection_string = f"mssql+pymssql://{username}:{quote_plus(password)}@{server}:{port}/{database}"

    print(f"\n🔗 Connection string: mssql+pymssql://***:***@{server}:{port}/{database}")
    
    # Intentar conectar
    print("\n🔌 Intentando conectar a la base de datos...")
    try:
        engine = create_engine(connection_string)
        
        # Probar la conexión ejecutando una query simple
        with engine.connect() as connection:
            print("✅ ¡Conexión exitosa!")
            
            # Obtener versión de SQL Server
            result = connection.execute(text("SELECT @@VERSION AS version"))
            version = result.fetchone()[0]
            print(f"\n📊 Versión de SQL Server:")
            print(f"  {version.split('\\n')[0]}")
            
            # Obtener nombre de la base de datos actual
            result = connection.execute(text("SELECT DB_NAME() AS current_db"))
            current_db = result.fetchone()[0]
            print(f"\n💾 Base de datos actual: {current_db}")
            
            # Verificar si existe la vista vw_GLSource_daily
            print("\n🔍 Verificando vista vw_GLSource_daily...")
            result = connection.execute(text("""
                SELECT COUNT(*) as exists_view
                FROM INFORMATION_SCHEMA.VIEWS 
                WHERE TABLE_NAME = 'vw_GLSource_daily'
            """))
            view_exists = result.fetchone()[0]
            
            if view_exists:
                print("✅ La vista vw_GLSource_daily existe")
                
                # Contar registros en la vista
                result = connection.execute(text("SELECT COUNT(*) as total FROM vw_GLSource_daily"))
                total_records = result.fetchone()[0]
                print(f"  - Total de registros: {total_records:,}")
                
                if total_records > 0:
                    # Mostrar algunos registros de ejemplo
                    result = connection.execute(text("""
                        SELECT TOP 5 
                            accountID,
                            accountNumber,
                            account,
                            dtmDate,
                            amount
                        FROM vw_GLSource_daily 
                        ORDER BY dtmDate DESC
                    """))
                    
                    print("\n📋 Primeros 5 registros (más recientes):")
                    print("-" * 80)
                    for row in result:
                        print(f"  ID: {row[0]} | Cuenta: {row[1]} | {row[2][:30]:<30} | Fecha: {row[3]} | Monto: ${row[4]:,.2f}")
                    print("-" * 80)
            else:
                print("⚠️  La vista vw_GLSource_daily NO existe")
                print("   Ejecuta el script create_view.sql para crearla")
            
            print("\n" + "=" * 80)
            print("✅ PRUEBA DE CONEXIÓN COMPLETADA EXITOSAMENTE")
            print("=" * 80)
            
    except Exception as e:
        print(f"\n❌ Error al conectar a la base de datos:")
        print(f"   {str(e)}")
        print("\n💡 Posibles soluciones:")
        print("   1. Verifica que el contenedor Docker esté corriendo: docker ps")
        print("   2. Verifica las credenciales en config.json")
        print("   3. Verifica que el puerto esté mapeado correctamente")
        print("   4. Verifica que el driver ODBC esté instalado")
        return False
    
    return True


if __name__ == '__main__':
    print("=" * 80)
    print("🧪 PRUEBA DE CONEXIÓN A BASE DE DATOS SQL SERVER")
    print("=" * 80)
    test_database_connection()

