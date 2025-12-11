-- =============================================
-- Script: Create Anomaly Detection Table
-- Company: Darwin
-- Description: Creates table to store detected anomalies
-- =============================================

USE AT2017_DEPLOY;
GO

-- Drop table if exists (optional - comment out if you want to preserve existing data)
-- DROP TABLE IF EXISTS dbo.AnomalyDetections;
-- GO

-- Create the anomaly detection table
CREATE TABLE dbo.AnomalyDetections (
    -- Primary key
    anomaly_id INT IDENTITY(1,1) PRIMARY KEY,
    
    -- Account information
    accountID INT NOT NULL,
    accountNumber NVARCHAR(50) NOT NULL,
    account NVARCHAR(255) NOT NULL,
    
    -- Transaction details
    dtmDate DATETIME NOT NULL,
    amount DECIMAL(18, 2) NOT NULL,
    
    -- Statistical information
    avg_amount DECIMAL(18, 2) NOT NULL,
    pct_diff_from_avg DECIMAL(10, 2) NOT NULL,
    
    -- Detection metadata
    threshold_used DECIMAL(10, 2) NOT NULL,
    detection_date DATETIME NOT NULL DEFAULT GETDATE(),
    company NVARCHAR(100) NOT NULL DEFAULT 'Darwin',
    
    -- Audit fields
    created_at DATETIME NOT NULL DEFAULT GETDATE(),
    
    -- Indexes for better query performance
    INDEX IX_AnomalyDetections_AccountID (accountID),
    INDEX IX_AnomalyDetections_Date (dtmDate),
    INDEX IX_AnomalyDetections_DetectionDate (detection_date)
);
GO

-- Add description
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Stores detected anomalies in accounting transactions for Darwin company', 
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE',  @level1name = N'AnomalyDetections';
GO

-- Column descriptions
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Unique identifier for each anomaly record', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'AnomalyDetections', @level2type = N'COLUMN', @level2name = N'anomaly_id';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Account ID from glAccount table', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'AnomalyDetections', @level2type = N'COLUMN', @level2name = N'accountID';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Account number', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'AnomalyDetections', @level2type = N'COLUMN', @level2name = N'accountNumber';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Account description/name', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'AnomalyDetections', @level2type = N'COLUMN', @level2name = N'account';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Transaction date', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'AnomalyDetections', @level2type = N'COLUMN', @level2name = N'dtmDate';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Transaction amount (debit - credit)', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'AnomalyDetections', @level2type = N'COLUMN', @level2name = N'amount';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Average amount for this account', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'AnomalyDetections', @level2type = N'COLUMN', @level2name = N'avg_amount';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Percentage difference from average', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'AnomalyDetections', @level2type = N'COLUMN', @level2name = N'pct_diff_from_avg';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Threshold percentage used for detection', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'AnomalyDetections', @level2type = N'COLUMN', @level2name = N'threshold_used';
EXEC sys.sp_addextendedproperty @name = N'MS_Description', @value = N'Date when anomaly was detected', @level0type = N'SCHEMA', @level0name = N'dbo', @level1type = N'TABLE', @level1name = N'AnomalyDetections', @level2type = N'COLUMN', @level2name = N'detection_date';
GO

-- Sample query to view anomalies
-- SELECT TOP 100 * FROM dbo.AnomalyDetections ORDER BY detection_date DESC, pct_diff_from_avg DESC;

PRINT 'Table AnomalyDetections created successfully!';
GO

-- =============================================
-- Optional: Create setting in config.setting table
-- =============================================

-- Check if config.setting table exists and insert the percentage threshold
IF EXISTS (SELECT 1 FROM sys.tables WHERE name = 'setting' AND schema_id = SCHEMA_ID('config'))
BEGIN
    -- Insert or update the percentage threshold setting
    IF NOT EXISTS (SELECT 1 FROM config.setting WHERE settingKey = 'percentage Anomalias')
    BEGIN
        INSERT INTO config.setting (settingKey, settingValue, settingDescription)
        VALUES ('percentage Anomalias', '50', 'Percentage threshold for anomaly detection - transactions exceeding this % above average are flagged');
        
        PRINT 'Setting "percentage Anomalias" created with default value of 50%';
    END
    ELSE
    BEGIN
        PRINT 'Setting "percentage Anomalias" already exists';
    END
END
ELSE
BEGIN
    PRINT 'WARNING: config.setting table not found. Please create the setting manually:';
    PRINT 'INSERT INTO config.setting (settingKey, settingValue) VALUES (''percentage Anomalias'', ''50'')';
END
GO

