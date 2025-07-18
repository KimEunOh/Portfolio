/**
 * Form Configurations - 모든 양식별 설정 데이터
 * 
 * 이 파일은 각 양식의 고유한 설정들을 중앙 집중식으로 관리합니다.
 * 새로운 양식을 추가할 때는 이 파일에 설정만 추가하면 됩니다.
 */

window.FormConfigs = {
    
    // 연차 신청서 설정
    annualLeave: {
        name: 'AnnualLeaveProcessor',
        formId: 'annual_leave_form',
        fixedItemCount: 1,  // 연차는 단일 항목
        itemsKey: null,     // 아이템 리스트 없음
        hasItemCalculation: false,
        
        amountFields: [],   // 금액 필드 없음
        totalFields: [],    // 총액 필드 없음
        
        fieldMappings: [
            {
                fieldPattern: 'leave_type',
                dataKeys: ['leave_type']
            },
            {
                fieldPattern: 'leave_start_date',
                dataKeys: ['leave_start_date']
            },
            {
                fieldPattern: 'leave_end_date',
                dataKeys: ['leave_end_date']
            },
            {
                fieldPattern: 'leave_reason',
                dataKeys: ['leave_reason']
            }
        ]
    },
    
    // 야근 식대 신청서 설정
    dinnerExpense: {
        name: 'DinnerExpenseProcessor',
        formId: 'dinner_expense_form',
        fixedItemCount: 1,  // 야근 식대는 단일 항목
        itemsKey: null,
        hasItemCalculation: false,
        
        amountFields: [
            'meal_amount'
        ],
        
        totalFields: [
            'meal_amount'
        ],
        
        fieldMappings: [
            {
                fieldPattern: 'work_date',
                dataKeys: ['work_date']
            },
            {
                fieldPattern: 'work_start_time',
                dataKeys: ['work_start_time']
            },
            {
                fieldPattern: 'work_end_time',
                dataKeys: ['work_end_time']
            },
            {
                fieldPattern: 'meal_amount',
                dataKeys: ['meal_amount']
            },
            {
                fieldPattern: 'work_reason',
                dataKeys: ['work_reason']
            }
        ]
    },
    
    // 교통비 신청서 설정
    transportationExpense: {
        name: 'TransportationExpenseProcessor',
        formId: 'transportation_expense_form',
        fixedItemCount: 1,  // 교통비는 단일 항목
        itemsKey: null,
        hasItemCalculation: false,
        
        amountFields: [
            'transport_amount'
        ],
        
        totalFields: [
            'transport_amount'
        ],
        
        fieldMappings: [
            {
                fieldPattern: 'transport_date',
                dataKeys: ['transport_date']
            },
            {
                fieldPattern: 'departure_location',
                dataKeys: ['departure_location']
            },
            {
                fieldPattern: 'arrival_location',
                dataKeys: ['arrival_location']
            },
            {
                fieldPattern: 'transport_amount',
                dataKeys: ['transport_amount']
            },
            {
                fieldPattern: 'transport_details',
                dataKeys: ['transport_details']
            }
        ]
    },
    
    // 파견 및 출장 보고서 설정
    dispatchReport: {
        name: 'DispatchReportProcessor',
        formId: 'dispatch_businesstrip_report_form',
        fixedItemCount: 1,  // 파견/출장은 단일 보고서
        itemsKey: null,
        hasItemCalculation: false,
        
        amountFields: [],   // 금액 필드 없음
        totalFields: [],    // 총액 필드 없음
        
        fieldMappings: [
            {
                fieldPattern: 'dispatch_start_date',
                dataKeys: ['dispatch_start_date']
            },
            {
                fieldPattern: 'dispatch_end_date',
                dataKeys: ['dispatch_end_date']
            },
            {
                fieldPattern: 'dispatch_duration_days',
                dataKeys: ['dispatch_duration_days']
            },
            {
                fieldPattern: 'dispatch_purpose',
                dataKeys: ['dispatch_purpose']
            },
            {
                fieldPattern: 'report_details',
                dataKeys: ['report_details']
            }
        ]
    },
    
    // 개인 경비 사용내역서 설정
    personalExpense: {
        name: 'PersonalExpenseProcessor',
        formId: 'personal_expense_form',
        fixedItemCount: 6,
        itemsKey: 'expense_items',
        hasItemCalculation: false,
        
        // 금액 필드 패턴들 (총액 계산에 사용)
        amountFields: [
            'expense_amount_{index}'
        ],
        
        // 총액이 표시될 필드들
        totalFields: [
            'total_amount_header',
            'total_expense_amount'
        ],
        
        // 필드 매핑 (LLM 데이터 → DOM 요소)
        fieldMappings: [
            {
                fieldPattern: 'expense_date_{index}',
                dataKeys: ['expense_date']
            },
            {
                fieldPattern: 'expense_category_{index}',
                dataKeys: ['expense_category']
            },
            {
                fieldPattern: 'expense_description_{index}',
                dataKeys: ['expense_description']
            },
            {
                fieldPattern: 'expense_amount_{index}',
                dataKeys: ['expense_amount']
            },
            {
                fieldPattern: 'expense_notes_{index}',
                dataKeys: ['expense_notes']
            }
        ]
    },
    
    // 법인카드 지출내역서 설정
    corporateCard: {
        name: 'CorporateCardProcessor',
        formId: 'corporate_card_form',
        fixedItemCount: 6,
        itemsKey: 'card_usage_items',
        hasItemCalculation: false,
        
        amountFields: [
            'usage_amount_{index}'
        ],
        
        totalFields: [
            'total_amount_header',
            'total_usage_amount'
        ],
        
        fieldMappings: [
            {
                fieldPattern: 'usage_date_{index}',
                dataKeys: ['usage_date']
            },
            {
                fieldPattern: 'usage_category_{index}',
                dataKeys: ['usage_category']
            },
            {
                fieldPattern: 'merchant_name_{index}',
                dataKeys: ['merchant_name', 'usage_description']
            },
            {
                fieldPattern: 'usage_amount_{index}',
                dataKeys: ['usage_amount']
            },
            {
                fieldPattern: 'usage_notes_{index}',
                dataKeys: ['usage_notes']
            }
        ]
    },
    
    // 비품/소모품 구입내역서 설정
    inventory: {
        name: 'InventoryProcessor',
        formId: 'inventory_purchase_form',
        fixedItemCount: 6,
        itemsKey: 'items',
        hasItemCalculation: true,
        
        // 수량 × 단가 = 총액 계산 필드들
        quantityField: 'item_quantity_{index}',
        unitPriceField: 'item_unit_price_{index}',
        itemTotalField: 'item_total_price_{index}',
        itemTotalKey: 'item_total_price',
        
        amountFields: [
            'item_total_price_{index}'
        ],
        
        totalFields: [
            'total_amount'
        ],
        
        fieldMappings: [
            {
                fieldPattern: 'item_name_{index}',
                dataKeys: ['item_name']
            },
            {
                fieldPattern: 'item_quantity_{index}',
                dataKeys: ['item_quantity']
            },
            {
                fieldPattern: 'item_unit_price_{index}',
                dataKeys: ['item_unit_price']
            },
            {
                fieldPattern: 'item_purpose_{index}',
                dataKeys: ['item_notes']
            }
        ]
    },
    
    // 구매 품의서 설정
    purchaseApproval: {
        name: 'PurchaseApprovalProcessor',
        formId: 'purchase_approval_form',
        fixedItemCount: 3,
        itemsKey: 'items',
        hasItemCalculation: true,
        
        quantityField: 'item_quantity_{index}',
        unitPriceField: 'item_unit_price_{index}',
        itemTotalField: 'item_total_price_{index}',
        itemTotalKey: 'item_total_price',
        
        amountFields: [
            'item_total_price_{index}'
        ],
        
        totalFields: [
            'total_purchase_amount'
        ],
        
        fieldMappings: [
            {
                fieldPattern: 'item_name_{index}',
                dataKeys: ['item_name']
            },
            {
                fieldPattern: 'item_spec_{index}',
                dataKeys: ['item_spec']
            },
            {
                fieldPattern: 'item_quantity_{index}',
                dataKeys: ['item_quantity']
            },
            {
                fieldPattern: 'item_unit_price_{index}',
                dataKeys: ['item_unit_price']
            },
            {
                fieldPattern: 'item_delivery_date_{index}',
                dataKeys: ['item_delivery_date', 'item_delivery_request_date']
            },
            {
                fieldPattern: 'item_supplier_{index}',
                dataKeys: ['item_supplier']
            },
            {
                fieldPattern: 'item_notes_{index}',
                dataKeys: ['item_notes', 'item_purpose']
            }
        ]
    }
};

/**
 * 양식 타입에 따른 설정 가져오기
 */
window.getFormConfig = function(formType) {
    const configMap = {
        'annual_leave': FormConfigs.annualLeave,
        'dinner_expense': FormConfigs.dinnerExpense,
        'transportation_expense': FormConfigs.transportationExpense,
        'dispatch_report': FormConfigs.dispatchReport,
        'personal_expense': FormConfigs.personalExpense,
        'corporate_card': FormConfigs.corporateCard,
        'inventory': FormConfigs.inventory,
        'purchase_approval': FormConfigs.purchaseApproval
    };
    
    return configMap[formType] || null;
};

/**
 * 지원되는 양식 목록
 */
window.getSupportedForms = function() {
    return Object.keys(FormConfigs);
};

console.log('[form-configs.js] Form configurations loaded:', Object.keys(FormConfigs));
