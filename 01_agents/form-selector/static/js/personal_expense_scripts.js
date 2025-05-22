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