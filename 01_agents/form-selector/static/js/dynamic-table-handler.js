(function() { // IIFE for encapsulation
    /**
     * 동적 아이템 컨테이너 추가/삭제를 처리하는 공통 함수
     * @param {string} tableId - 대상 테이블의 ID
     * @param {string} addButtonId - 아이템 추가 버튼의 ID
     * @param {string} removeButtonId - 아이템 삭제 버튼의 ID
     */
    function initializeDynamicTable(tableId, addButtonId, removeButtonId) {
        console.log(`[Debug] initializeDynamicTable called with: tableId=${tableId}, addButtonId=${addButtonId}`);

        const table = document.getElementById(tableId);
        if (!table) {
            console.error(`[Debug] Table with ID '${tableId}' not found.`);
            return;
        }
        console.log(`[Debug] Table element found:`, table);

        const addButton = document.getElementById(addButtonId);
        if (!addButton) {
            console.error(`[Debug] Add button with ID '${addButtonId}' not found.`);
            return;
        }
        console.log(`[Debug] Add button element found:`, addButton);
        
        const removeButton = document.getElementById(removeButtonId);
        if (removeButton) {
            console.log(`[Debug] Remove button element found:`, removeButton);
        }

        function updateRemoveButtonState() {
            if (removeButton) {
                const itemCount = table.querySelectorAll('tbody').length;
                removeButton.disabled = itemCount <= 1; // 최소 1개는 남김
            }
        }

        addButton.addEventListener('click', () => {
            console.log(`[Debug] Add button clicked.`);
            const lastItem = table.querySelector('tbody:last-of-type');
            if (!lastItem) {
                console.error('[Debug] No item container (tbody) found to clone.');
                return;
            }
            console.log(`[Debug] Cloning item:`, lastItem);

            const newItem = lastItem.cloneNode(true);
            const newItemIndex = table.querySelectorAll('tbody').length + 1;
            console.log(`[Debug] New item index will be: ${newItemIndex}`);

            newItem.querySelectorAll('input, select, textarea').forEach(input => {
                const id = input.id || '';
                const name = input.name || '';
                
                if (id) input.id = id.replace(/_\\d+$/, `_${newItemIndex}`);
                if (name) input.name = name.replace(/_\\d+$/, `_${newItemIndex}`);

                if (input.tagName === 'SELECT') {
                    input.selectedIndex = 0;
                } else if (input.type === 'checkbox' || input.type === 'radio') {
                    input.checked = false;
                } else {
                    input.value = '';
                }
            });
            
            console.log('[Debug] Appending new item to the table.');
            table.appendChild(newItem);
            updateRemoveButtonState();
        });

        if (removeButton) {
            removeButton.addEventListener('click', () => {
                console.log(`[Debug] Remove button clicked.`);
                const itemCount = table.querySelectorAll('tbody').length;
                if (itemCount > 1) {
                    table.querySelector('tbody:last-of-type').remove();
                    console.log(`[Debug] Last item removed.`);
                }
                updateRemoveButtonState();
            });
        }
        
        console.log('[Debug] Initializing remove button state.');
        updateRemoveButtonState();
    }
    
    window.initializeDynamicTable = initializeDynamicTable;
})(); 