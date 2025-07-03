console.log('[purchase_approval_scripts.js] Script file parsing started.');

console.log('[purchase_approval_scripts.js] Script logic executing.');

const totalAmountField = document.getElementById('total_purchase_amount');
const itemsDataScript = document.getElementById('items-data');
const fixedItemCount = 3; // 고정된 항목 세트 수

console.log('[purchase_approval_scripts.js] itemsDataScript element:', itemsDataScript);
if (itemsDataScript) {
    console.log('[purchase_approval_scripts.js] itemsDataScript.textContent raw:', itemsDataScript.textContent);
}

function calculateItemTotal(itemIndex) {
    const quantityEl = document.getElementById(`item_quantity_${itemIndex}`);
    const unitPriceEl = document.getElementById(`item_unit_price_${itemIndex}`);
    const itemTotalPriceField = document.getElementById(`item_total_price_${itemIndex}`);
    
    const quantity = parseFloat(quantityEl ? quantityEl.value : 0) || 0;
    const unitPrice = parseFloat(unitPriceEl ? unitPriceEl.value : 0) || 0;
    
    if (itemTotalPriceField) {
        itemTotalPriceField.value = (quantity * unitPrice).toFixed(0);
    }
    calculateOverallTotal();
}

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
    }
}

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

if (itemsDataScript && itemsDataScript.textContent.trim() !== '' && itemsDataScript.textContent.trim() !== '{items_json}') {
    console.log('[purchase_approval_scripts.js] itemsDataScript.textContent (inside if): ', itemsDataScript.textContent);
    try {
        let itemsToLoad = [];
        const parsedData = JSON.parse(itemsDataScript.textContent);
        console.log('[purchase_approval_scripts.js] parsedData from items-data:', parsedData);

        if (Array.isArray(parsedData)) {
            itemsToLoad = parsedData;
        } else if (parsedData && typeof parsedData === 'object') {
            if (Array.isArray(parsedData.items)) {
            itemsToLoad = parsedData.items;
            } else if (parsedData.slots && Array.isArray(parsedData.slots.items)) {
                itemsToLoad = parsedData.slots.items;
            }
        }
        console.log('[purchase_approval_scripts.js] itemsToLoad:', itemsToLoad);

        if (itemsToLoad.length > 0) {
            itemsToLoad.forEach((item, index) => {
                console.log(`[purchase_approval_scripts.js] Processing item ${index + 1}:`, item);
                if (index < fixedItemCount) { 
                    const itemIndex = index + 1;
                    
                    const itemNameEl = document.getElementById(`item_name_${itemIndex}`);
                    if(itemNameEl) itemNameEl.value = item.item_name || '';
                    console.log(`[purchase_approval_scripts.js] Filled item_name_${itemIndex} with:`, item.item_name || '');

                    const itemSpecEl = document.getElementById(`item_spec_${itemIndex}`);
                    if(itemSpecEl) itemSpecEl.value = item.item_spec || '';
                    console.log(`[purchase_approval_scripts.js] Filled item_spec_${itemIndex} with:`, item.item_spec || '');

                    const itemQuantityEl = document.getElementById(`item_quantity_${itemIndex}`);
                    if(itemQuantityEl) itemQuantityEl.value = item.item_quantity || '';
                    console.log(`[purchase_approval_scripts.js] Filled item_quantity_${itemIndex} with:`, item.item_quantity || '');
                    
                    const itemUnitPriceEl = document.getElementById(`item_unit_price_${itemIndex}`);
                    if(itemUnitPriceEl) itemUnitPriceEl.value = item.item_unit_price || '';
                    console.log(`[purchase_approval_scripts.js] Filled item_unit_price_${itemIndex} with:`, item.item_unit_price || '');
                    
                    const itemDeliveryDateEl = document.getElementById(`item_delivery_date_${itemIndex}`);
                    if(itemDeliveryDateEl) itemDeliveryDateEl.value = item.item_delivery_date || item.item_delivery_request_date || ''; 
                    console.log(`[purchase_approval_scripts.js] Filled item_delivery_date_${itemIndex} with:`, (item.item_delivery_date || item.item_delivery_request_date || ''));

                    const itemSupplierEl = document.getElementById(`item_supplier_${itemIndex}`);
                    if(itemSupplierEl) itemSupplierEl.value = item.item_supplier || '';
                    console.log(`[purchase_approval_scripts.js] Filled item_supplier_${itemIndex} with:`, item.item_supplier || '');

                    const itemNotesEl = document.getElementById(`item_notes_${itemIndex}`);
                    if(itemNotesEl) itemNotesEl.value = item.item_notes || item.item_purpose || ''; 
                    console.log(`[purchase_approval_scripts.js] Filled item_notes_${itemIndex} with:`, (item.item_notes || item.item_purpose || ''));
                    
                    calculateItemTotal(itemIndex); 
                }
            });
        }
        calculateOverallTotal(); 
    } catch (e) {
        console.error('[purchase_approval_scripts.js] Error parsing or loading items data for purchase_approval_form:', e, 'Raw content:', itemsDataScript.textContent);
    }
} else {
    const elseContent = itemsDataScript ? itemsDataScript.textContent.trim() : 'itemsDataScript_is_null';
    console.log(`[purchase_approval_scripts.js] Condition for itemsDataScript failed. Content: "${elseContent}"`);
    for (let i = 1; i <= fixedItemCount; i++) {
        calculateItemTotal(i);
    }
    calculateOverallTotal();
}

console.log('[purchase_approval_scripts.js] Script file parsing finished.'); 