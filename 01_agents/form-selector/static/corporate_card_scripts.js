console.log('[corporate_card_scripts.js] Script file parsing started.');

// DOMContentLoaded 리스너 제거
// document.addEventListener('DOMContentLoaded', () => { // 이 줄 삭제

console.log('[corporate_card_scripts.js] Script logic executing.');

const totalAmountHeaderField = document.getElementById('total_amount_header');
const totalUsageAmountField = document.getElementById('total_usage_amount');
const itemsDataScript = document.getElementById('items-data');
const fixedItemCount = 6; // HTML 템플릿에 설정된 항목 수에 맞게 조정

console.log('[corporate_card_scripts.js] Initial elements: totalAmountHeaderField:', totalAmountHeaderField, 'totalUsageAmountField:', totalUsageAmountField, 'itemsDataScript:', itemsDataScript);
if (itemsDataScript) {
    console.log('[corporate_card_scripts.js] itemsDataScript.textContent raw:', itemsDataScript.textContent);
}

// 법인카드 사용 분류 (HTML의 <select> 옵션과 일치시킴) - 필요시 사용
// const usageCategories = {
//     "meals": "식대/회식비",
//     // ... 기타 등등
// };

// 전체 합계 금액을 계산하는 함수
function calculateOverallTotal() {
    let overallTotal = 0;
    for (let i = 1; i <= fixedItemCount; i++) {
        const amountField = document.getElementById(`usage_amount_${i}`);
        if (amountField) {
            overallTotal += parseFloat(amountField.value) || 0;
        }
    }
    if (totalAmountHeaderField) totalAmountHeaderField.value = overallTotal.toFixed(0);
    if (totalUsageAmountField) totalUsageAmountField.value = overallTotal.toFixed(0);
    console.log('[corporate_card_scripts.js] Calculated overall total:', overallTotal);
}

// 고정된 항목 세트에 이벤트 리스너 추가
for (let i = 1; i <= fixedItemCount; i++) {
    const amountInput = document.getElementById(`usage_amount_${i}`);
    if (amountInput) {
        amountInput.addEventListener('input', calculateOverallTotal);
    }
}

// 초기 데이터 로드 (items-data)
if (itemsDataScript && itemsDataScript.textContent && itemsDataScript.textContent.trim() !== '' && itemsDataScript.textContent.trim() !== '{items_json}') {
    console.log('[corporate_card_scripts.js] Attempting to parse itemsDataScript.textContent:', itemsDataScript.textContent);
    try {
        let itemsToLoad = [];
        const parsedData = JSON.parse(itemsDataScript.textContent);
        console.log('[corporate_card_scripts.js] parsedData from items-data:', parsedData);

        // LLM 응답에서 card_usage_items 키로 내려오는 것을 우선으로 함.
        if (parsedData && typeof parsedData === 'object' && Array.isArray(parsedData.card_usage_items)) {
            itemsToLoad = parsedData.card_usage_items;
        } else if (Array.isArray(parsedData)) { // 루트가 바로 배열인 경우도 호환성 위해 처리
            itemsToLoad = parsedData;
        }
        console.log('[corporate_card_scripts.js] itemsToLoad for corporate card usage:', itemsToLoad);

        if (itemsToLoad.length > 0) {
            itemsToLoad.forEach((item, index) => {
                if (index < fixedItemCount) { // 고정된 항목 수만큼만 데이터 채우기
                    const itemIndex = index + 1;
                    console.log(`[corporate_card_scripts.js] Processing card usage item ${itemIndex}:`, item);

                    const dateEl = document.getElementById(`usage_date_${itemIndex}`);
                    if (dateEl) dateEl.value = item.usage_date || '';
                    console.log(`[corporate_card_scripts.js] Filled usage_date_${itemIndex} with:`, item.usage_date || '');

                    const categoryEl = document.getElementById(`usage_category_${itemIndex}`);
                    if (categoryEl) categoryEl.value = item.usage_category || '';
                    console.log(`[corporate_card_scripts.js] Filled usage_category_${itemIndex} with:`, item.usage_category || '');

                    // HTML의 merchant_name ID를 사용. LLM 슬롯은 merchant_name 또는 usage_description 일 수 있음
                    const merchantNameEl = document.getElementById(`merchant_name_${itemIndex}`);
                    if (merchantNameEl) merchantNameEl.value = item.merchant_name || item.usage_description || ''; 
                    console.log(`[corporate_card_scripts.js] Filled merchant_name_${itemIndex} with:`, item.merchant_name || item.usage_description || '');

                    const amountEl = document.getElementById(`usage_amount_${itemIndex}`);
                    if (amountEl) amountEl.value = item.usage_amount || '';
                    console.log(`[corporate_card_scripts.js] Filled usage_amount_${itemIndex} with:`, item.usage_amount || '');

                    const notesEl = document.getElementById(`usage_notes_${itemIndex}`);
                    if (notesEl) notesEl.value = item.usage_notes || '';
                    console.log(`[corporate_card_scripts.js] Filled usage_notes_${itemIndex} with:`, item.usage_notes || '');
                }
            });
        }
        calculateOverallTotal(); // 모든 항목 로드 후 전체 합계 계산
    } catch (e) {
        console.error('[corporate_card_scripts.js] Error parsing or loading items data:', e, 'Raw content:', itemsDataScript.textContent);
    }
} else {
    const elseContent = itemsDataScript ? itemsDataScript.textContent.trim() : 'itemsDataScript_is_null';
    console.log(`[corporate_card_scripts.js] Condition for itemsDataScript failed or placeholder present. Content: "${elseContent}"`);
    calculateOverallTotal(); // 초기 데이터가 없거나 플레이스홀더인 경우 합계 초기화
}

// }); // DOMContentLoaded 리스너의 닫는 괄호 삭제

console.log('[corporate_card_scripts.js] Script file parsing finished.'); 