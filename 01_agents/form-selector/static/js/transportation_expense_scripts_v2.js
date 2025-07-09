/**
 * 교통비 신청서 - 리팩토링된 버전
 * BaseFormProcessor를 상속받아 중복 코드를 제거하고 양식별 고유 로직만 유지
 */

(() => {
    console.log('[transportation_expense_scripts_v2.js] Script loaded - Refactored version');

    // BaseFormProcessor와 FormConfigs가 로드될 때까지 대기
    if (typeof BaseFormProcessor === 'undefined' || typeof getFormConfig === 'undefined') {
        console.error('[transportation_expense_scripts_v2.js] Dependencies not loaded. Waiting...');
        setTimeout(() => {
            if (typeof BaseFormProcessor !== 'undefined' && typeof getFormConfig !== 'undefined') {
                initTransportationExpenseProcessor();
            } else {
                console.error('[transportation_expense_scripts_v2.js] Dependencies still not available');
            }
        }, 100);
        return;
    }

    initTransportationExpenseProcessor();

    function initTransportationExpenseProcessor() {
        /**
         * 교통비 전용 프로세서 클래스
         */
        class TransportationExpenseProcessor extends BaseFormProcessor {
            constructor() {
                const config = getFormConfig('transportation_expense');
                if (!config) {
                    console.error('[TransportationExpenseProcessor] Configuration not found');
                    return;
                }
                
                super(config);
            }

            /**
             * 추가 초기화 - 교통비 특화 기능
             */
            onAfterInit() {
                this.setupTransportationSpecificFeatures();
            }

            /**
             * 교통비 특화 기능
             */
            setupTransportationSpecificFeatures() {
                // 교통비 특화 로직
                this.setupLocationValidation();
                this.setupAmountValidation();
                this.setupTransportDateDefault();
                console.log('[TransportationExpenseProcessor] Transportation-specific features initialized');
            }

            /**
             * 교통일 기본값 설정
             */
            setupTransportDateDefault() {
                const transportDateInput = this.form.querySelector('#transport_date');
                if (transportDateInput && !transportDateInput.value) {
                    transportDateInput.value = new Date().toISOString().split('T')[0];
                    console.log('[TransportationExpenseProcessor] Transport date set to today');
                }
            }

            /**
             * 출발지/도착지 유효성 검사
             */
            setupLocationValidation() {
                const departureInput = this.form.querySelector('#departure_location');
                const arrivalInput = this.form.querySelector('#arrival_location');
                
                if (departureInput && arrivalInput) {
                    const validateLocations = () => {
                        if (departureInput.value && arrivalInput.value) {
                            if (departureInput.value.trim() === arrivalInput.value.trim()) {
                                alert('출발지와 도착지가 같을 수 없습니다.');
                                arrivalInput.focus();
                                return false;
                            }
                            
                            console.log(`[TransportationExpenseProcessor] Route: ${departureInput.value} → ${arrivalInput.value}`);
                            return true;
                        }
                        return false;
                    };
                    
                    departureInput.addEventListener('blur', validateLocations);
                    arrivalInput.addEventListener('blur', validateLocations);
                }
            }

            /**
             * 교통비 금액 유효성 검사
             */
            setupAmountValidation() {
                const amountInput = this.form.querySelector('#transport_amount');
                
                if (amountInput) {
                    amountInput.addEventListener('input', (e) => {
                        const value = e.target.value;
                        
                        // 숫자가 아닌 문자 제거
                        const numericValue = value.replace(/[^0-9]/g, '');
                        if (numericValue !== value) {
                            e.target.value = numericValue;
                        }
                        
                        // 금액 유효성 검사
                        const amount = parseInt(numericValue);
                        if (amount > 1000000) {
                            alert('교통비는 100만원을 초과할 수 없습니다.');
                            e.target.focus();
                        }
                        
                        console.log(`[TransportationExpenseProcessor] Amount updated: ${amount}`);
                    });
                    
                    amountInput.addEventListener('blur', (e) => {
                        const amount = parseInt(e.target.value);
                        if (amount > 0 && amount < 1000) {
                            const confirmResult = confirm('교통비가 1,000원 미만입니다. 계속하시겠습니까?');
                            if (!confirmResult) {
                                e.target.focus();
                            }
                        }
                    });
                }
            }
        }

        // 프로세서 인스턴스 생성
        new TransportationExpenseProcessor();
    }

    console.log('[transportation_expense_scripts_v2.js] Script completed');
})();

(function () {
    const tableElement = document.getElementById('transportation_table');
    if (!tableElement) return;

    const tableBody = tableElement.querySelector('tbody');
    const addRowBtn = document.getElementById('add_transport_row_btn');
    const totalAmountInput = document.getElementById('total_amount');

    if (!tableBody || !addRowBtn || !totalAmountInput) {
        return;
    }

    let rowCount = 0;

    function createRow() {
        rowCount++;
        
        const row = document.createElement('tr');
        row.classList.add('item-row');
        row.setAttribute('data-row-id', rowCount);
        
        row.innerHTML = `
            <td style="width: 15%;">
                <select id="transport_type_${rowCount}" name="transport_type_${rowCount}" class="form-control transport-type">
                    <option value="subway">지하철</option>
                    <option value="bus">버스</option>
                    <option value="train">기차</option>
                    <option value="airplane">비행기</option>
                    <option value="other">기타</option>
                </select>
            </td>
            <td style="width: 20%;">
                <input type="text" id="origin_${rowCount}" name="origin_${rowCount}" class="form-control" placeholder="출발지">
            </td>
            <td style="width: 20%;">
                <input type="text" id="destination_${rowCount}" name="destination_${rowCount}" class="form-control" placeholder="도착지">
            </td>
            <td style="width: 20%;">
                <input type="date" id="boarding_date_${rowCount}" name="boarding_date_${rowCount}" class="form-control">
            </td>
            <td style="width: 15%;">
                <input type="number" id="amount_${rowCount}" name="amount_${rowCount}" class="form-control amount" placeholder="금액" min="0" step="100">
            </td>
            <td style="width: 10%; text-align: center;">
                <button type="button" class="btn-remove remove-row-btn" style="background-color: #dc3545; color: white; border: none; border-radius: 5px; cursor: pointer; width: 36px; height: 36px; font-size: 1.2rem; line-height: 1;">&times;</button>
            </td>
        `;
        
        tableBody.appendChild(row);
    }

    function updateTotalAmount() {
        let total = 0;
        const amountInputs = document.querySelectorAll('#transportation_table .amount');
        amountInputs.forEach(input => {
            const value = parseFloat(input.value) || 0;
            total += value;
        });
        totalAmountInput.value = total.toLocaleString();
    }

    addRowBtn.addEventListener('click', createRow);

    tableElement.addEventListener('click', function (e) {
        if (e.target && e.target.classList.contains('remove-row-btn')) {
            const row = e.target.closest('.item-row');
            if (row) {
                row.remove();
                updateTotalAmount();
            }
        }
    });

    tableElement.addEventListener('input', function (e) {
        if (e.target && e.target.classList.contains('amount')) {
            updateTotalAmount();
        }
    });
    
    // 초기 행 생성
    createRow();

    // LLM 추출 데이터로 첫 번째 행 채우기
    function populateInitialData() {
        const slotsDataElement = document.getElementById('form-slots-data');
        if (!slotsDataElement) return;

        try {
            const slots = JSON.parse(slotsDataElement.textContent);
            if (!slots || Object.keys(slots).length === 0) return;

            Object.keys(slots).forEach(key => {
                let elementId;
                if (key === 'type') { // 'type' 키를 'transport_type'으로 매핑
                    elementId = 'transport_type_1';
                } else {
                    elementId = `${key}_1`;
                }
                
                const element = document.getElementById(elementId);
                if (element) {
                    if (element.tagName === 'SELECT') {
                        for (let i = 0; i < element.options.length; i++) {
                            if (element.options[i].value === slots[key] || element.options[i].text === slots[key]) {
                                element.selectedIndex = i;
                                break;
                            }
                        }
                    } else {
                        element.value = slots[key];
                    }
                }
            });
            updateTotalAmount(); // 데이터 채운 후 합계 업데이트
        } catch (e) {
            console.error('슬롯 데이터를 파싱하는 중 오류 발생:', e);
        }
    }

    populateInitialData();
})(); 