# 모든 양식 테스트 스크립트
Write-Host "=== 전체 양식 테스트 시작 ===" -ForegroundColor Green

$testFiles = @(
    @{Name = "Transportation Expense"; File = "test_transportation.json"},
    @{Name = "Dispatch Business Trip Report"; File = "test_dispatch_trip.json"},
    @{Name = "Inventory Purchase Report"; File = "test_inventory.json"},
    @{Name = "Purchase Approval Form"; File = "test_purchase_approval.json"},
    @{Name = "Personal Expense Report"; File = "test_personal_expense.json"},
    @{Name = "Corporate Card Statement"; File = "test_corporate_card.json"}
)

foreach ($test in $testFiles) {
    Write-Host "`n--- $($test.Name) 테스트 ---" -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/form-selector" -Method POST -ContentType "application/json" -InFile $test.File
        
        Write-Host "✅ 양식 분류: $($response.form_type)"
        Write-Host "✅ 키워드: $($response.keywords -join ', ')"
        Write-Host "✅ 추출된 슬롯 수: $($response.slots.PSObject.Properties.Count)"
        
        # 주요 슬롯 정보 출력
        if ($response.slots) {
            $response.slots.PSObject.Properties | ForEach-Object {
                if ($_.Value -and $_.Value -ne "") {
                    Write-Host "   - $($_.Name): $($_.Value)"
                }
            }
        }
        
        Write-Host "✅ 테스트 성공" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ 테스트 실패: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 1  # 서버 부하 방지
}

Write-Host "`n=== 전체 테스트 완료 ===" -ForegroundColor Green 