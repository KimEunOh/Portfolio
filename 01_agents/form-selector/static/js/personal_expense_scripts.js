(() => {
  console.log('[personal_expense_scripts.js] Script file parsing started.');

  // DOMContentLoaded 리스너 제거
  // document.addEventListener('DOMContentLoaded', () => { // 이 줄 삭제

  console.log('[personal_expense_scripts.js] Script logic executing.');

  const totalAmountHeaderField = document.getElementById('total_amount_header');
  const totalExpenseAmountField = document.getElementById('total_expense_amount');
  const itemsDataScript = document.getElementById('items-data');
  const fixedItemCount = 6; // HTML 템플릿에 설정된 항목 수에 맞게 조정

  console.log('[personal_expense_scripts.js] Initial elements: totalAmountHeaderField:', totalAmountHeaderField, 'totalExpenseAmountField:', totalExpenseAmountField, 'itemsDataScript:', itemsDataScript);
  if (itemsDataScript) {
      console.log('[personal_expense_scripts.js] itemsDataScript.textContent raw:', itemsDataScript.textContent);
  }

  // 경비 분류 (HTML의 <select> 옵션과 일치시킴) - 필요시 사용
  // const expenseCategories = {
  //     "traffic": "교통비",
  //     "accommodation": "숙박비",
  //     // ... 기타 등등
  // };

  // 전체 합계 금액을 계산하는 함수
  function calculateOverallTotal() {
      let overallTotal = 0;
      for (let i = 1; i <= fixedItemCount; i++) {
          const amountField = document.getElementById(`expense_amount_${i}`);
          if (amountField) {
              overallTotal += parseFloat(amountField.value) || 0;
          }
      }
      if (totalAmountHeaderField) totalAmountHeaderField.value = overallTotal.toFixed(0);
      if (totalExpenseAmountField) totalExpenseAmountField.value = overallTotal.toFixed(0);
      console.log('[personal_expense_scripts.js] Calculated overall total:', overallTotal);
  }

  // 고정된 항목 세트에 이벤트 리스너 추가
  for (let i = 1; i <= fixedItemCount; i++) {
      const amountInput = document.getElementById(`expense_amount_${i}`);
      if (amountInput) {
          amountInput.addEventListener('input', calculateOverallTotal);
      }
  }

  // 초기 데이터 로드 (items-data)
  if (itemsDataScript && itemsDataScript.textContent && itemsDataScript.textContent.trim() !== '' && itemsDataScript.textContent.trim() !== '{items_json}') {
      console.log('[personal_expense_scripts.js] Attempting to parse itemsDataScript.textContent:', itemsDataScript.textContent);
      try {
          let itemsToLoad = [];
          const parsedData = JSON.parse(itemsDataScript.textContent);
          console.log('[personal_expense_scripts.js] parsedData from items-data:', parsedData);

          // LLM 응답에서 expense_items 키로 내려오는 것을 우선으로 함.
          if (parsedData && typeof parsedData === 'object' && Array.isArray(parsedData.expense_items)) {
              itemsToLoad = parsedData.expense_items;
          } else if (Array.isArray(parsedData)) { // 루트가 바로 배열인 경우도 호환성 위해 처리
              itemsToLoad = parsedData;
          }
          console.log('[personal_expense_scripts.js] itemsToLoad for personal expenses:', itemsToLoad);

          if (itemsToLoad.length > 0) {
              itemsToLoad.forEach((item, index) => {
                  if (index < fixedItemCount) { // 고정된 항목 수만큼만 데이터 채우기
                      const itemIndex = index + 1;
                      console.log(`[personal_expense_scripts.js] Processing expense item ${itemIndex}:`, item);

                      const dateEl = document.getElementById(`expense_date_${itemIndex}`);
                      if (dateEl) dateEl.value = item.expense_date || '';
                      console.log(`[personal_expense_scripts.js] Filled expense_date_${itemIndex} with:`, item.expense_date || '');

                      const categoryEl = document.getElementById(`expense_category_${itemIndex}`);
                      if (categoryEl) categoryEl.value = item.expense_category || '';
                      console.log(`[personal_expense_scripts.js] Filled expense_category_${itemIndex} with:`, item.expense_category || '');

                      const descriptionEl = document.getElementById(`expense_description_${itemIndex}`);
                      if (descriptionEl) descriptionEl.value = item.expense_description || '';
                      console.log(`[personal_expense_scripts.js] Filled expense_description_${itemIndex} with:`, item.expense_description || '');

                      const amountEl = document.getElementById(`expense_amount_${itemIndex}`);
                      if (amountEl) amountEl.value = item.expense_amount || '';
                      console.log(`[personal_expense_scripts.js] Filled expense_amount_${itemIndex} with:`, item.expense_amount || '');

                      const notesEl = document.getElementById(`expense_notes_${itemIndex}`);
                      if (notesEl) notesEl.value = item.expense_notes || '';
                      console.log(`[personal_expense_scripts.js] Filled expense_notes_${itemIndex} with:`, item.expense_notes || '');
                  }
              });
          }
          calculateOverallTotal(); // 모든 항목 로드 후 전체 합계 계산
      } catch (e) {
          console.error('[personal_expense_scripts.js] Error parsing or loading items data:', e, 'Raw content:', itemsDataScript.textContent);
      }
  } else {
      const elseContent = itemsDataScript ? itemsDataScript.textContent.trim() : 'itemsDataScript_is_null';
      console.log(`[personal_expense_scripts.js] Condition for itemsDataScript failed or placeholder present. Content: "${elseContent}"`);
      calculateOverallTotal(); // 초기 데이터가 없거나 플레이스홀더인 경우 합계 초기화
  }

  // }); // DOMContentLoaded 리스너의 닫는 괄호 삭제

  console.log('[personal_expense_scripts.js] Script file parsing finished.'); 
})(); 

/**
 * 개인경비 사용내역서 양식의 동적 기능을 초기화합니다.
 * - 기안일 자동 설정
 * - 경비 항목 동적 추가 (+) 버튼 기능
 * - 총액 자동 계산
 * 이 함수는 `personal_expense_form`이 DOM에 로드되었을 때 호출되어야 합니다.
 */
(() => {
    console.log('[personal_expense_scripts.js] Script loaded and executing...');

    const form = document.getElementById('personal_expense_form');
    if (!form) {
        console.error('[personal_expense_scripts.js] Form with ID "personal_expense_form" not found. Aborting initialization.');
        return;
    }

    // --- 기안일 자동 설정 ---
    const draftDateInput = form.querySelector('#draft_date');
    if (draftDateInput) {
        // 값이 비어있을 경우에만 오늘 날짜로 설정
        if (!draftDateInput.value) {
            draftDateInput.value = new Date().toISOString().split('T')[0];
        }
    }

    // --- 항목 추가 기능 ---
    const container = form.querySelector('#personal-expense-items-container');
    const addButton = form.querySelector('#add-personal-expense-item');
    
    if (!container || !addButton) {
        console.error('[personal_expense_scripts.js] Required elements for item addition (container or button) not found.');
        return;
    }

    let expenseItemCounter = container.querySelectorAll('.item-set').length;

    addButton.addEventListener('click', () => {
        expenseItemCounter++;
        const newItemHtml = `
            <div class="item-set">
                <h4>경비 항목 ${expenseItemCounter}</h4>
                <div class="item-fields-grid">
                    <div class="form-group"><label for="expense_date_${expenseItemCounter}">사용일자:</label><input type="date" id="expense_date_${expenseItemCounter}" name="expense_date_${expenseItemCounter}" class="form-control"></div>
                    <div class="form-group"><label for="expense_category_${expenseItemCounter}">분류:</label><select id="expense_category_${expenseItemCounter}" name="expense_category_${expenseItemCounter}" class="form-control"><option value="">선택</option><option value="traffic">교통비</option><option value="accommodation">숙박비</option><option value="meals">식대</option><option value="entertainment">접대비</option><option value="education">교육훈련비</option><option value="supplies">소모품비</option><option value="other">기타</option></select></div>
                    <div class="form-group"><label for="expense_description_${expenseItemCounter}">사용내역:</label><input type="text" id="expense_description_${expenseItemCounter}" name="expense_description_${expenseItemCounter}" class="form-control"></div>
                    <div class="form-group"><label for="expense_amount_${expenseItemCounter}">금액:</label><input type="number" id="expense_amount_${expenseItemCounter}" name="expense_amount_${expenseItemCounter}" class="form-control expense-amount-calc"></div>
                    <div class="form-group"><label for="expense_notes_${expenseItemCounter}">비고:</label><input type="text" id="expense_notes_${expenseItemCounter}" name="expense_notes_${expenseItemCounter}" class="form-control"></div>
                </div>
            </div>`;
        container.insertAdjacentHTML('beforeend', newItemHtml);
        console.log(`[personal_expense_scripts.js] Item ${expenseItemCounter} added.`);
    });

    // --- 총액 자동 계산 ---
    const totalHeader = form.querySelector('#total_amount_header');
    const totalFooter = form.querySelector('#total_expense_amount');

    function calculateTotal() {
        const amounts = container.querySelectorAll('.expense-amount-calc');
        let total = 0;
        amounts.forEach(input => {
            total += Number(input.value) || 0;
        });
        if (totalHeader) totalHeader.value = total;
        if (totalFooter) totalFooter.value = total;
    }

    // 동적으로 추가된 항목에도 이벤트가 적용되도록 컨테이너에 이벤트 리스너 설정
    container.addEventListener('input', (e) => {
        if (e.target.classList.contains('expense-amount-calc')) {
            calculateTotal();
        }
    });

    // 초기 총액 계산
    calculateTotal();
    console.log('[personal_expense_scripts.js] Form functionalities initialized successfully.');
})(); 