# HORUS AI Anomaly Detection Test Script
Write-Host "🚀 Testing HORUS AI Anomaly Detection System" -ForegroundColor Green
Write-Host "=============================================`n" -ForegroundColor Green

$baseUrl = "http://localhost:3000"

# Function to send transaction and display results
function Test-Transaction {
    param(
        [string]$TestName,
        [object]$TransactionData
    )
    
    Write-Host "🧪 Testing: $TestName" -ForegroundColor Yellow
    Write-Host "Transaction Data: $($TransactionData | ConvertTo-Json -Compress)" -ForegroundColor Gray
    
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/analyze/transaction" -Method Post -Body (
            @{
                transaction_data = $TransactionData
            } | ConvertTo-Json
        ) -ContentType "application/json"
        
        # Display results with color coding based on risk level
        $color = switch ($response.explanation.risk_level) {
            "HIGH" { "Red" }
            "MEDIUM" { "Yellow" }
            "LOW" { "Green" }
            default { "White" }
        }
        
        Write-Host "✅ Analysis Result:" -ForegroundColor Green
        Write-Host "   Anomaly Score: $($response.anomaly_score)" -ForegroundColor $color
        Write-Host "   Risk Level: $($response.explanation.risk_level)" -ForegroundColor $color
        Write-Host "   Confidence: $($response.explanation.confidence)" -ForegroundColor $color
        Write-Host "   Recommendation: $($response.explanation.recommendation)" -ForegroundColor $color
        
        if ($response.explanation.triggering_factors.Count -gt 0) {
            Write-Host "   Triggering Factors:" -ForegroundColor Cyan
            foreach ($factor in $response.explanation.triggering_factors) {
                Write-Host "     - $factor" -ForegroundColor Cyan
            }
        }
        
    } catch {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host "`n" + ("-" * 50) + "`n"
}

# Test 1: LOW RISK - Transaksi Normal
Write-Host "1. LOW RISK SCENARIO - Normal Business Transaction" -ForegroundColor Green
Test-Transaction -TestName "Normal Business Payment" @{
    id = 1001
    amount = 500000
    sender = "corporate_account"
    receiver = "verified_vendor"
    timestamp = [int][double]::Parse((Get-Date -Hour 14 -Minute 30 -Second 0 -Millisecond 0 -Date (Get-Date)).ToUniversalTime().Subtract((Get-Date "1970-01-01")).TotalSeconds)
    department = "keuangan"
    transaction_type = "pembayaran"
}

# Test 2: LOW-MEDIUM RISK - Transaksi Agak Besar tapi Normal
Write-Host "2. LOW-MEDIUM RISK - Large but Legitimate Transaction" -ForegroundColor Green
Test-Transaction -TestName "Large Legitimate Transfer" @{
    id = 1002
    amount = 1500000
    sender = "company_treasury"
    receiver = "bank_loan_account"
    timestamp = [int][double]::Parse((Get-Date -Hour 11 -Minute 0 -Second 0 -Millisecond 0 -Date (Get-Date)).ToUniversalTime().Subtract((Get-Date "1970-01-01")).TotalSeconds)
    department = "keuangan"
    transaction_type = "transfer"
}

# Test 3: MEDIUM RISK - Transaksi Mencurigakan
Write-Host "3. MEDIUM RISK - Suspicious Transaction" -ForegroundColor Yellow
Test-Transaction -TestName "Suspicious After-Hours Transfer" @{
    id = 1003
    amount = 800000
    sender = "employee_123"
    receiver = "external_personal"
    timestamp = [int][double]::Parse((Get-Date -Hour 23 -Minute 45 -Second 0 -Millisecond 0 -Date (Get-Date)).ToUniversalTime().Subtract((Get-Date "1970-01-01")).TotalSeconds)
    department = "pengadaan"
    transaction_type = "transfer"
}

# Test 4: HIGH RISK - Transaksi Sangat Mencurigakan
Write-Host "4. HIGH RISK - Highly Suspicious Transaction" -ForegroundColor Red
Test-Transaction -TestName "High-Risk Anomaly Pattern" @{
    id = 1004
    amount = 3000000
    sender = "unknown_sender"
    receiver = "offshore_account"
    timestamp = [int][double]::Parse((Get-Date -Hour 3 -Minute 30 -Second 0 -Millisecond 0 -Date (Get-Date)).ToUniversalTime().Subtract((Get-Date "1970-01-01")).TotalSeconds)
    department = "unknown"
    transaction_type = "transfer"
}

# Test 5: HIGH RISK - Self Transfer Pattern
Write-Host "5. HIGH RISK - Self Transfer Anomaly" -ForegroundColor Red
Test-Transaction -TestName "Self-Transfer Red Flag" @{
    id = 1005
    amount = 1200000
    sender = "suspicious_user"
    receiver = "suspicious_user"  # Self-transfer
    timestamp = [int][double]::Parse((Get-Date -Hour 4 -Minute 15 -Second 0 -Millisecond 0 -Date (Get-Date)).ToUniversalTime().Subtract((Get-Date "1970-01-01")).TotalSeconds)
    department = "unknown"
    transaction_type = "transfer"
}

# Test 6: EXTREME RISK - Multiple Red Flags
Write-Host "6. EXTREME RISK - Multiple Anomaly Indicators" -ForegroundColor DarkRed
Test-Transaction -TestName "Multiple Red Flags" @{
    id = 1006
    amount = 5000000
    sender = "compromised_account"
    receiver = "compromised_account"  # Self-transfer
    timestamp = [int][double]::Parse((Get-Date -Hour 2 -Minute 0 -Second 0 -Millisecond 0 -Date (Get-Date)).ToUniversalTime().Subtract((Get-Date "1970-01-01")).TotalSeconds)
    department = "unknown"
    transaction_type = "unknown"
}

Write-Host "🎯 Testing Complete! Summary:" -ForegroundColor Magenta
Write-Host "• 2 LOW risk scenarios (should pass)" -ForegroundColor Green
Write-Host "• 1 MEDIUM risk scenario (needs review)" -ForegroundColor Yellow  
Write-Host "• 3 HIGH risk scenarios (should be flagged)" -ForegroundColor Red