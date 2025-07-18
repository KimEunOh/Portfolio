// base-form-processor.js

/**
 * BaseFormProcessor - 모든 양식 JavaScript의 공통 기본 클래스
 * 
 * 이 클래스는 모든 양식에서 공통으로 사용되는 로직을 제공합니다:
 * - 총액 계산
 * - 데이터 로딩 (JSON 파싱)
 * - 이벤트 리스너 설정
 * - DOM 요소 조작
 * - 에러 처리
 */
class BaseFormProcessor {
    constructor(config) {
        this.config = config;
        this.form = document.getElementById(config.formId);
        this.itemsDataScript = document.getElementById('items-data');
        this.fixedItemCount = config.fixedItemCount || 6;
        
        console.log(`[${config.name}] BaseFormProcessor initialized`);
        
        if (!this.form) {
            console.error(`[${config.name}] Form with ID "${config.formId}" not found`);
            return;
        }
        
        this.init();
    }
    
    /**
     * 초기화 메서드
     */
    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.calculateOverallTotal();
        this.onAfterInit(); // 하위 클래스에서 추가 초기화
        
        console.log(`[${this.config.name}] Form processor initialized successfully`);
    }
    
    /**
     * 이벤트 리스너 설정
     */
    setupEventListeners() {
        for (let i = 1; i <= this.fixedItemCount; i++) {
            // 금액 필드들에 이벤트 리스너 추가
            this.config.amountFields.forEach(fieldPattern => {
                const fieldId = fieldPattern.replace('{index}', i);
                const element = document.getElementById(fieldId);
                
                if (element) {
                    element.addEventListener('input', () => this.onAmountFieldChange(i));
                }
            });
            
            // 수량/단가 필드가 있는 경우 (inventory, purchase_approval)
            if (this.config.quantityField && this.config.unitPriceField) {
                const quantityEl = document.getElementById(this.config.quantityField.replace('{index}', i));
                const unitPriceEl = document.getElementById(this.config.unitPriceField.replace('{index}', i));
                
                if (quantityEl) quantityEl.addEventListener('input', () => this.calculateItemTotal(i));
                if (unitPriceEl) unitPriceEl.addEventListener('input', () => this.calculateItemTotal(i));
            }
        }
    }
    
    /**
     * 금액 필드 변경 시 호출
     */
    onAmountFieldChange(itemIndex) {
        if (this.config.hasItemCalculation) {
            this.calculateItemTotal(itemIndex);
        } else {
            this.calculateOverallTotal();
        }
    }
    
    /**
     * 항목별 총액 계산 (inventory, purchase_approval에서 사용)
     */
    calculateItemTotal(itemIndex, itemData = null) {
        if (!this.config.hasItemCalculation) return;
        
        const quantityEl = document.getElementById(this.config.quantityField.replace('{index}', itemIndex));
        const unitPriceEl = document.getElementById(this.config.unitPriceField.replace('{index}', itemIndex));
        const totalEl = document.getElementById(this.config.itemTotalField.replace('{index}', itemIndex));
        
        if (!totalEl) {
            console.warn(`[${this.config.name}] Total field for item ${itemIndex} not found`);
            this.calculateOverallTotal();
            return;
        }
        
        // 초기 데이터에서 total이 제공된 경우 우선 사용
        if (itemData && itemData[this.config.itemTotalKey] !== null && itemData[this.config.itemTotalKey] !== undefined) {
            totalEl.value = parseFloat(itemData[this.config.itemTotalKey]).toFixed(0);
            console.log(`[${this.config.name}] Used provided total for item ${itemIndex}:`, itemData[this.config.itemTotalKey]);
        } else {
            const quantity = parseFloat(quantityEl ? quantityEl.value : 0) || 0;
            const unitPrice = parseFloat(unitPriceEl ? unitPriceEl.value : 0) || 0;
            totalEl.value = (quantity * unitPrice).toFixed(0);
            console.log(`[${this.config.name}] Calculated total for item ${itemIndex}:`, totalEl.value);
        }
        
        this.calculateOverallTotal();
    }
    
    /**
     * 전체 총액 계산 - 모든 양식에서 공통 사용
     */
    calculateOverallTotal() {
        let overallTotal = 0;
        
        for (let i = 1; i <= this.fixedItemCount; i++) {
            this.config.amountFields.forEach(fieldPattern => {
                const fieldId = fieldPattern.replace('{index}', i);
                const element = document.getElementById(fieldId);
                
                if (element) {
                    overallTotal += parseFloat(element.value) || 0;
                }
            });
        }
        
        // 총액 필드들에 값 설정
        this.config.totalFields.forEach(fieldId => {
            const element = document.getElementById(fieldId);
            if (element) {
                element.value = overallTotal.toFixed(0);
            }
        });
        
        console.log(`[${this.config.name}] Calculated overall total:`, overallTotal);
    }
    
    /**
     * 초기 데이터 로딩 - JSON 파싱 및 DOM 요소 채우기
     */
    loadInitialData() {
        if (!this.itemsDataScript || 
            !this.itemsDataScript.textContent || 
            this.itemsDataScript.textContent.trim() === '' || 
            this.itemsDataScript.textContent.trim() === '{items_json}') {
            
            const content = this.itemsDataScript ? this.itemsDataScript.textContent.trim() : 'script_not_found';
            console.log(`[${this.config.name}] No valid initial data. Content: "${content}"`);
            return;
        }
        
        console.log(`[${this.config.name}] Attempting to parse initial data:`, this.itemsDataScript.textContent);
        
        try {
            const parsedData = JSON.parse(this.itemsDataScript.textContent);
            console.log(`[${this.config.name}] Parsed data:`, parsedData);
            
            let itemsToLoad = this.extractItemsFromData(parsedData);
            console.log(`[${this.config.name}] Items to load:`, itemsToLoad);
            
            if (itemsToLoad.length > 0) {
                this.populateFormFields(itemsToLoad);
                this.calculateOverallTotal();
            }
            
        } catch (e) {
            console.error(`[${this.config.name}] Error parsing initial data:`, e, 'Raw content:', this.itemsDataScript.textContent);
        }
    }
    
    /**
     * 파싱된 데이터에서 항목 배열 추출
     */
    extractItemsFromData(parsedData) {
        // 우선순위: config에 지정된 키 > 배열 > 기본값
        if (parsedData && typeof parsedData === 'object' && Array.isArray(parsedData[this.config.itemsKey])) {
            return parsedData[this.config.itemsKey];
        } else if (Array.isArray(parsedData)) {
            return parsedData;
        }
        return [];
    }
    
    /**
     * 폼 필드에 데이터 채우기
     */
    populateFormFields(itemsToLoad) {
        itemsToLoad.forEach((item, index) => {
            if (index < this.fixedItemCount) {
                const itemIndex = index + 1;
                console.log(`[${this.config.name}] Processing item ${itemIndex}:`, item);
                
                // 필드 매핑에 따라 데이터 채우기
                this.config.fieldMappings.forEach(mapping => {
                    const fieldId = mapping.fieldPattern.replace('{index}', itemIndex);
                    const element = document.getElementById(fieldId);
                    
                    if (element) {
                        // 여러 소스 키 지원 (우선순위 순)
                        let value = '';
                        for (const key of mapping.dataKeys) {
                            if (item[key] !== undefined && item[key] !== null) {
                                value = item[key];
                                break;
                            }
                        }
                        
                        element.value = value || '';
                        console.log(`[${this.config.name}] Filled ${fieldId} with:`, value || '');
                    }
                });
                
                // 항목별 계산이 필요한 경우
                if (this.config.hasItemCalculation) {
                    this.calculateItemTotal(itemIndex, item);
                }
            }
        });
    }
    
    /**
     * 유틸리티: DOM 요소 안전하게 가져오기
     */
    getElement(id) {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`[${this.config.name}] Element with ID "${id}" not found`);
        }
        return element;
    }
    
    /**
     * 유틸리티: 숫자 값 안전하게 파싱
     */
    parseNumber(value) {
        return parseFloat(value) || 0;
    }
    
    /**
     * 확장 가능한 후크 메서드들 - 하위 클래스에서 오버라이드 가능
     */
    
    /**
     * 추가 초기화 로직 - 하위 클래스에서 구현
     */
    onAfterInit() {
        // 하위 클래스에서 필요시 구현
    }
    
    /**
     * 커스텀 검증 로직 - 하위 클래스에서 구현  
     */
    validateForm() {
        // 하위 클래스에서 필요시 구현
        return true;
    }
    
    /**
     * 커스텀 제출 전 처리 - 하위 클래스에서 구현
     */
    onBeforeSubmit() {
        // 하위 클래스에서 필요시 구현
    }
}

// 전역으로 노출
window.BaseFormProcessor = BaseFormProcessor;

console.log('[base-form-processor.js] BaseFormProcessor class loaded');
