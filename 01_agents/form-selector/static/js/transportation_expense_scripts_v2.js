/**
 * 교통비 신청서 - 리팩토링된 버전
 * BaseFormProcessor를 상속받아 중복 코드를 제거하고 양식별 고유 로직만 유지
 */

(function() {
    // 총액 계산 및 업데이트 함수
    function calculateTotal() {
        const totalAmountField = document.getElementById('total_amount');
        if (!totalAmountField) {
            console.error('Total amount field not found.');
        return;
    }

        let total = 0;
        document.querySelectorAll('#transportation_table .item-calc').forEach(input => {
            const value = parseFloat(input.value) || 0;
            total += value;
        });

        // 숫자를 쉼표가 있는 통화 형식으로 변환
        totalAmountField.value = new Intl.NumberFormat('ko-KR').format(total);
    }

    // JSON 데이터로 폼 채우기
    function populateFormWithData(data) {
        if (!data || !Array.isArray(data) || data.length === 0) {
            console.log("No items data to populate.");
                    return;
                }
                
        const table = document.getElementById('transportation_table');
        const templateItem = table.querySelector('tbody');
        if (!templateItem) {
            console.error("Template item not found in the table.");
            return;
        }

        // 기존의 모든 tbody (아이템) 삭제
        while (table.firstChild) {
            table.removeChild(table.firstChild);
        }
        
        data.forEach((itemData, index) => {
            const newItem = templateItem.cloneNode(true);
            const newItemIndex = index + 1;

            // ID와 name 속성 업데이트
            newItem.querySelectorAll('input, select, textarea').forEach(input => {
                if (input.id) input.id = input.id.replace(/_\d+$/, `_${newItemIndex}`);
                if (input.name) input.name = input.name.replace(/_\d+$/, `_${newItemIndex}`);
            });
            
            // 새 아이템에 데이터 채우기
            const transportType = newItem.querySelector(`[name="transport_type_${newItemIndex}"]`);
            if (transportType) {
                // transport_type 값과 일치하는 옵션을 찾아 선택된 상태로 만듭니다.
                const option = Array.from(transportType.options).find(opt => opt.value === itemData.transport_type);
                if (option) {
                    option.selected = true;
                } else if (itemData.transport_type) { // 일치하는 옵션이 없고 값이 존재할 경우 '기타'를 선택
                    const otherOption = Array.from(transportType.options).find(opt => opt.value === '기타');
                    if (otherOption) otherOption.selected = true;
                }
            }

            const origin = newItem.querySelector(`[name="origin_${newItemIndex}"]`);
            if (origin) origin.value = itemData.origin || '';
            
            const destination = newItem.querySelector(`[name="destination_${newItemIndex}"]`);
            if (destination) destination.value = itemData.destination || '';
            
            const amount = newItem.querySelector(`[name="amount_${newItemIndex}"]`);
            if (amount) amount.value = itemData.amount || '';

            const notes = newItem.querySelector(`[name="notes_${newItemIndex}"]`);
            if (notes) notes.value = itemData.notes || '';
            
            table.appendChild(newItem);
        });
    }

    // DOM이 로드되면 실행
    // document.addEventListener('DOMContentLoaded', function() {
        // 동적 테이블 초기화
        if (window.initializeDynamicTable) {
            window.initializeDynamicTable('transportation_table', 'add_row_btn', 'remove_row_btn');
        }

        // 이벤트 위임을 사용하여 금액 입력 변경 감지
        const table = document.getElementById('transportation_table');
        if (table) {
            table.addEventListener('input', function(e) {
                if (e.target && e.target.classList.contains('item-calc')) {
                    calculateTotal();
                }
            });
        }
        
        // 아이템 데이터 로드 및 폼 채우기
        const itemsDataElement = document.getElementById('items-data');
        if (itemsDataElement && itemsDataElement.textContent.trim()) {
            try {
                const itemsJson = itemsDataElement.textContent;
                // 플레이스홀더가 아닌 실제 JSON 데이터인지 확인
                if (itemsJson !== '{items_json}') {
                    const items = JSON.parse(itemsJson);
                    populateFormWithData(items);
                }
            } catch (e) {
                console.error('Error parsing items JSON:', e);
            }
        }
        
        // 초기 총액 계산
        calculateTotal();
        
        // 행 추가/삭제 시 총액 재계산
        const addBtn = document.getElementById('add_row_btn');
        const removeBtn = document.getElementById('remove_row_btn');

        if(addBtn) addBtn.addEventListener('click', calculateTotal);
        if(removeBtn) removeBtn.addEventListener('click', calculateTotal);
    // });
})(); 