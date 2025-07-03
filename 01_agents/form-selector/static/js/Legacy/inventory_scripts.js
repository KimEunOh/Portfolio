(() => {
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
  // itemData가 제공되면 (초기 로드 시), item_total_price를 우선 사용
  function calculateItemTotal(itemIndex, itemData = null) {
    const quantityEl = document.getElementById(`item_quantity_${itemIndex}`);
    const unitPriceEl = document.getElementById(`item_unit_price_${itemIndex}`);
    const itemTotalPriceField = document.getElementById(`item_total_price_${itemIndex}`);

    if (!itemTotalPriceField) {
        console.warn(`[inventory_scripts.js] Element item_total_price_${itemIndex} not found.`);
        calculateOverallTotal(); // 그래도 전체 합계는 재계산
        return;
    }

    if (itemData && itemData.item_total_price !== null && itemData.item_total_price !== undefined) {
        itemTotalPriceField.value = parseFloat(itemData.item_total_price).toFixed(0);
        console.log(`[inventory_scripts.js] Used item_total_price from data for item ${itemIndex}:`, itemData.item_total_price);
    } else {
        const quantity = parseFloat(quantityEl ? quantityEl.value : 0) || 0;
        const unitPrice = parseFloat(unitPriceEl ? unitPriceEl.value : 0) || 0;
        itemTotalPriceField.value = (quantity * unitPrice).toFixed(0);
        console.log(`[inventory_scripts.js] Calculated item_total_price for item ${itemIndex}:`, itemTotalPriceField.value);
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
    const itemTotalPriceInput = document.getElementById(`item_total_price_${i}`); // 금액 필드

    if (quantityInput) {
        quantityInput.addEventListener('input', () => calculateItemTotal(i));
    }
    if (unitPriceInput) {
        unitPriceInput.addEventListener('input', () => calculateItemTotal(i));
    }
    if (itemTotalPriceInput) { // 금액 필드에 대한 이벤트 리스너 추가
        itemTotalPriceInput.addEventListener('input', calculateOverallTotal);
    }
  }

  // 초기 데이터 로드 (items-data)
  if (itemsDataScript && itemsDataScript.textContent && itemsDataScript.textContent.trim() !== '' && itemsDataScript.textContent.trim() !== '{items_json}') {
    console.log('[inventory_scripts.js] Attempting to parse itemsDataScript.textContent:', itemsDataScript.textContent);
    try {
        let itemsToLoad = [];
        const parsedData = JSON.parse(itemsDataScript.textContent);
        console.log('[inventory_scripts.js] parsedData from items-data:', parsedData);

        if (parsedData && typeof parsedData === 'object' && Array.isArray(parsedData.items)) {
            itemsToLoad = parsedData.items;
        } else if (Array.isArray(parsedData)) {
            itemsToLoad = parsedData;
        }
        console.log('[inventory_scripts.js] itemsToLoad for inventory:', itemsToLoad);

        if (itemsToLoad.length > 0) {
            itemsToLoad.forEach((item, index) => {
                if (index < fixedItemCount) {
                    const itemIndex = index + 1;
                    console.log(`[inventory_scripts.js] Processing item ${itemIndex} for inventory:`, item);

                    const itemNameEl = document.getElementById(`item_name_${itemIndex}`);
                    if(itemNameEl) itemNameEl.value = item.item_name || '';
                    console.log(`[inventory_scripts.js] Filled item_name_${itemIndex} with:`, item.item_name || '');

                    const itemQuantityEl = document.getElementById(`item_quantity_${itemIndex}`);
                    if(itemQuantityEl) itemQuantityEl.value = item.item_quantity || '';
                    console.log(`[inventory_scripts.js] Filled item_quantity_${itemIndex} with:`, item.item_quantity || '');
                    
                    const itemUnitPriceEl = document.getElementById(`item_unit_price_${itemIndex}`);
                    if(itemUnitPriceEl) itemUnitPriceEl.value = item.item_unit_price || '';
                    console.log(`[inventory_scripts.js] Filled item_unit_price_${itemIndex} with:`, item.item_unit_price || '');
                    
                    const itemPurposeEl = document.getElementById(`item_purpose_${itemIndex}`);
                    if(itemPurposeEl) itemPurposeEl.value = item.item_notes || ''; 
                    console.log(`[inventory_scripts.js] Filled item_purpose_${itemIndex} with:`, item.item_notes || '');
                    
                    // 데이터 로드 시에는 item 객체를 전달하여 item_total_price 우선 적용
                    calculateItemTotal(itemIndex, item); 
                }
            });
        }
        // calculateOverallTotal(); // calculateItemTotal 내부에서 호출되므로 중복 제거 가능, 단 모든 item 처리 후 최종 호출이 필요하면 유지
    } catch (e) {
        console.error('[inventory_scripts.js] Error parsing or loading items data:', e, 'Raw content:', itemsDataScript.textContent);
    }
  } else {
    const elseContent = itemsDataScript ? itemsDataScript.textContent.trim() : 'itemsDataScript_is_null';
    console.log(`[inventory_scripts.js] Condition for itemsDataScript failed or placeholder present. Content: "${elseContent}"`);
    for (let i = 1; i <= fixedItemCount; i++) {
        calculateItemTotal(i); // 초기 데이터 없을 시 기존 방식대로 계산
    }
    // calculateOverallTotal(); // 여기도 calculateItemTotal에서 호출됨
  }
  // 스크립트 로드 완료 후, 혹시 모를 초기 상태에 대해 전체 합계 한 번 더 보장 (선택 사항)
  calculateOverallTotal();

  console.log('[inventory_scripts.js] Script file parsing finished.');
})(); 