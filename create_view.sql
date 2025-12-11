-- Script para crear la vista vw_GLSource_daily
-- Ejecutar en SQL Server Management Studio o sqlcmd

USE AT2017_DEPLOY;
GO

-- Crear o reemplazar la vista
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

-- Verificar que la vista se creó correctamente
SELECT TOP 10 * FROM vw_GLSource_daily ORDER BY dtmDate DESC;
GO

