console.log('[inventory_scripts.js] Script file parsing started.');

console.log('[inventory_scripts.js] Script logic executing.');

const totalAmountField = document.getElementById('total_amount');
const itemsDataScript = document.getElementById('items-data');
const fixedItemCount = 6; // HTML 템플릿에 맞게 조정 필요할 수 있음

console.log('[inventory_scripts.js] Initial elements: totalAmountField:', totalAmountField, 'itemsDataScript:', itemsDataScript);
if (itemsDataScript) {
    console.log('[inventory_scripts.js] itemsDataScript.textContent raw:', itemsDataScript.textContent);
}

// 각 항목 세트의 금액을 계산하고 전체 합계를 업데이트하는 함수
function calculateItemTotal(itemIndex) {
    // 해당 ID의 요소가 없을 경우를 대비하여 null 체크 추가
    const quantityEl = document.getElementById(`item_quantity_${itemIndex}`);
    const unitPriceEl = document.getElementById(`item_unit_price_${itemIndex}`);
    const itemTotalPriceField = document.getElementById(`item_total_price_${itemIndex}`);

    const quantity = parseFloat(quantityEl ? quantityEl.value : 0) || 0;
    const unitPrice = parseFloat(unitPriceEl ? unitPriceEl.value : 0) || 0;

    if (itemTotalPriceField) {
        itemTotalPriceField.value = (quantity * unitPrice).toFixed(0);
    } else {
        console.warn(`[inventory_scripts.js] Element item_total_price_${itemIndex} not found.`);
    }
    calculateOverallTotal();
}

// 전체 합계 금액을 계산하는 함수
function calculateOverallTotal() {
    let overallTotal = 0;
    for (let i = 1; i <= fixedItemCount; i++) {
        const itemTotalPriceField = document.getElementById(`item_total_price_${i}`);
        if (itemTotalPriceField) {
            overallTotal += parseFloat(itemTotalPriceField.value) || 0;
        }
    }
    if (totalAmountField) {
        totalAmountField.value = overallTotal.toFixed(0);
    } else {
        console.warn("[inventory_scripts.js] Element total_amount not found for overall total.");
    }
}

// 고정된 항목 세트에 이벤트 리스너 추가
for (let i = 1; i <= fixedItemCount; i++) {
    const quantityInput = document.getElementById(`item_quantity_${i}`);
    const unitPriceInput = document.getElementById(`item_unit_price_${i}`);

    if (quantityInput) {
        quantityInput.addEventListener('input', () => calculateItemTotal(i));
    }
    if (unitPriceInput) {
        unitPriceInput.addEventListener('input', () => calculateItemTotal(i));
    }
}

// 초기 데이터 로드 (items-data)
if (itemsDataScript && itemsDataScript.textContent && itemsDataScript.textContent.trim() !== '' && itemsDataScript.textContent.trim() !== '{items_json}') {
    console.log('[inventory_scripts.js] Attempting to parse itemsDataScript.textContent:', itemsDataScript.textContent);
    try {
        let itemsToLoad = [];
        const parsedData = JSON.parse(itemsDataScript.textContent);
        console.log('[inventory_scripts.js] parsedData from items-data:', parsedData);

        // items 키가 있는지, 있다면 배열인지 확인하여 itemsToLoad 설정
        if (parsedData && typeof parsedData === 'object' && Array.isArray(parsedData.items)) {
            itemsToLoad = parsedData.items;
        } else if (Array.isArray(parsedData)) { // 루트가 바로 배열인 경우도 처리 (일관성을 위해 parsedData.items 선호)
            itemsToLoad = parsedData;
        }
        console.log('[inventory_scripts.js] itemsToLoad for inventory:', itemsToLoad);

        if (itemsToLoad.length > 0) {
            itemsToLoad.forEach((item, index) => {
                if (index < fixedItemCount) { // 고정된 항목 수만큼만 데이터 채우기
                    const itemIndex = index + 1;
                    console.log(`[inventory_scripts.js] Processing item ${itemIndex} for inventory:`, item);

                    // HTML 템플릿의 ID와 슬롯의 키 이름을 일치시켜야 함
                    // 예: item.item_name, item.item_quantity 등
                    const itemNameEl = document.getElementById(`item_name_${itemIndex}`);
                    if(itemNameEl) itemNameEl.value = item.item_name || '';
                    console.log(`[inventory_scripts.js] Filled item_name_${itemIndex} with:`, item.item_name || '');

                    const itemQuantityEl = document.getElementById(`item_quantity_${itemIndex}`);
                    if(itemQuantityEl) itemQuantityEl.value = item.item_quantity || '';
                    console.log(`[inventory_scripts.js] Filled item_quantity_${itemIndex} with:`, item.item_quantity || '');
                    
                    const itemUnitPriceEl = document.getElementById(`item_unit_price_${itemIndex}`);
                    if(itemUnitPriceEl) itemUnitPriceEl.value = item.item_unit_price || '';
                    console.log(`[inventory_scripts.js] Filled item_unit_price_${itemIndex} with:`, item.item_unit_price || '');
                    
                    // inventory_purchase_report.html 템플릿에 맞는 필드 ID와 슬롯 키 사용
                    // 예시로 item_purpose를 사용. 실제 템플릿의 필드명으로 변경 필요
                    const itemPurposeEl = document.getElementById(`item_purpose_${itemIndex}`); // 또는 item_remarks, item_notes 등
                    if(itemPurposeEl) itemPurposeEl.value = item.item_purpose || item.item_notes || ''; 
                    console.log(`[inventory_scripts.js] Filled item_purpose_${itemIndex} with:`, item.item_purpose || item.item_notes || '');
                    
                    calculateItemTotal(itemIndex);
                }
            });
        }
        calculateOverallTotal(); // 모든 항목 로드 후 전체 합계 다시 계산
    } catch (e) {
        console.error('[inventory_scripts.js] Error parsing or loading items data:', e, 'Raw content:', itemsDataScript.textContent);
    }
} else {
    const elseContent = itemsDataScript ? itemsDataScript.textContent.trim() : 'itemsDataScript_is_null';
    console.log(`[inventory_scripts.js] Condition for itemsDataScript failed or placeholder present. Content: "${elseContent}"`);
    // 초기 데이터가 없거나 items_json 플레이스홀더인 경우, 모든 금액 필드 초기 계산
    for (let i = 1; i <= fixedItemCount; i++) {
        calculateItemTotal(i);
    }
    calculateOverallTotal();
}

console.log('[inventory_scripts.js] Script file parsing finished.'); 