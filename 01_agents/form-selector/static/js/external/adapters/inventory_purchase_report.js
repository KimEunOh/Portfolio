(function(){
  /*
   * 비품/소모품 구입내역서 어댑터
   * - 역할: 슬롯 값 자동 채움 → 퍼블리싱 DOM에서 품목 수집 → hidden `items` JSON 유지 → 총액 필드 동기화 → 결재라인 렌더/조회
   * - 서버 연계: `form_selector/processors/inventory_purchase_processor.py` 및 Legacy 변환과 호환
   * - 중요: 퍼블리싱 템플릿의 항목 네이밍(itemName1, itemUnitPrice1, itemTotalPrice1, ...)에 의존
   */
  // 비품/소모품: 슬롯 채움 + 항목 수집(hidden items) + 총액 갱신
  var aliasMap = {
      request_date: ['requestDate'],
      payment_method: ['paymentMethod'],
      total_amount: ['totalAmount']
  };
  var normalizers = {
      total_amount: function(v){ var n = Number(String(v||'').replace(/[^\d.-]/g,'')); return isNaN(n) ? 0 : n; }
  };

  // URL 경로에서 mstPid 추출 (결재라인 조회 시 사용)
  function getPidFromPath(){ try{ var m = window.location.pathname.match(/\/master\/(\d+)/); if(m&&m[1]) return Number(m[1]); }catch(e){} return null; }
  // 숫자 파싱 및 표시 유틸
  function parseNumber(value){ var n = Number(String(value||'').replace(/[^\d.-]/g,'')); return isNaN(n)?0:n; }
  function formatComma(n){ try{ var num = parseNumber(n); return num ? num.toLocaleString('ko-KR') : ''; }catch(_){ return String(n||''); } }

  // 입력 요소가 비어 있거나 플레이스홀더일 때만 값을 채우고 input/change 이벤트를 발생시킴
  function setIfEmpty(selector, value){
      try{
          var el = document.querySelector(selector);
          if(!el) return;
          var cur = (el.value==null? '' : String(el.value).trim());
          var isPlaceholder = /^\{[^}]*\}$/.test(cur) || /SLOT_NOT_FOUND/i.test(cur);
          if(cur === '' || isPlaceholder){
              el.value = value != null ? value : '';
              try{ el.dispatchEvent(new Event('input',{bubbles:true})); }catch(_){ }
              try{ el.dispatchEvent(new Event('change',{bubbles:true})); }catch(_){ }
          }
      }catch(_){ }
  }

  // 오늘 날짜(YYYY-MM-DD) 생성 유틸
  function getTodayYmd(){
      try{
          var d = new Date();
          var y = d.getFullYear();
          var m = String(d.getMonth()+1).padStart(2,'0');
          var day = String(d.getDate()).padStart(2,'0');
          return y + '-' + m + '-' + day;
      }catch(_){ return ''; }
  }

  // 요청일 필드 보강
  function ensureRequestDateField(slots){
      if(!slots) return;
      var rd = slots.request_date || slots.requestDate || '';
      // 슬롯에 날짜가 없을 때도 UI에 오늘 날짜 기본값 반영
      if(!rd){ rd = getTodayYmd(); }
      if(!rd) return;
      setIfEmpty('input[name="requestDate"]', rd);
      setIfEmpty('#date', rd);
      // change 이벤트만 트리거하여 위젯과 동기화
      try{ if(window.jQuery){ jQuery('#date').trigger('change'); } }catch(_){ }
      try{ if(window.UIReinit && window.UIReinit.schedule){ window.UIReinit.schedule(); } }catch(_){ }
  }

  // items 배열 수집
  function collectItems(){
      var items = [];
      try{
          var maxScan = 12;
          for(var i=1;i<=maxScan;i++){
              var nameEl = document.getElementById('itemName'+i) || document.querySelector('[name="itemName'+i+'"]');
              var specEl = document.getElementById('itemSpec'+i) || document.querySelector('[name="itemSpec'+i+'"]');
              var qtyEl = document.getElementById('itemQuantity'+i) || document.querySelector('[name="itemQuantity'+i+'"]');
              var unitPriceEl = document.getElementById('itemUnitPrice'+i) || document.querySelector('[name="itemUnitPrice'+i+'"]');
              var totalPriceEl = document.getElementById('itemTotalPrice'+i) || document.querySelector('[name="itemTotalPrice'+i+'"]');
              var deliDateEl = document.querySelector('[name="itemDeliveryDate'+i+'"]');
              var supplierEl = document.getElementById('itemSupplier'+i) || document.querySelector('[name="itemSupplier'+i+'"]');
              var notesEl = document.getElementById('itemNotes'+i) || document.querySelector('[name="itemNotes'+i+'"]');
              var purposeEl = document.getElementById('itemPurpose'+i) || document.querySelector('[name="itemPurpose'+i+'"]');
              if(!(nameEl || specEl || qtyEl || unitPriceEl || totalPriceEl || deliDateEl || supplierEl || notesEl)) continue;
              var item = {
                  item_name: nameEl ? nameEl.value : '',
                  item_spec: specEl ? specEl.value : '',
                  item_quantity: parseNumber(qtyEl && qtyEl.value),
                  item_unit_price: parseNumber(unitPriceEl && unitPriceEl.value),
                  item_total_price: parseNumber(totalPriceEl && totalPriceEl.value),
                  item_delivery_date: deliDateEl ? deliDateEl.value : '',
                  item_supplier: supplierEl ? supplierEl.value : '',
                  item_notes: notesEl ? notesEl.value : '',
                  item_purpose: purposeEl ? purposeEl.value : ''
              };
              if(item.item_name || item.item_total_price || item.item_quantity){ items.push(item); }
          }
      }catch(e){ try{ if(window.__FORM_DEBUG__){ console.warn('[InventoryPurchaseAdapter] collect error', e); } }catch(_e){} }
      return items;
  }

  // hidden `purchase_items` 유지 및 총액 필드 동기화
  function ensureHiddenItemsAndTotals(){
      try{
          var form = document.querySelector('.form_area form') || document.querySelector('form');
          if(!form) return;
          var hidden = form.querySelector('input[name="purchase_items"]');
          if(!hidden){ hidden = document.createElement('input'); hidden.type='hidden'; hidden.name='purchase_items'; form.appendChild(hidden); }
          var items = collectItems();
          hidden.value = JSON.stringify(items);
          var totalField = document.getElementById('totalAmount') || form.querySelector('[name="totalAmount"]');
          if(totalField){ var sum = 0; items.forEach(function(it){ sum += parseNumber(it.item_total_price); }); totalField.value = sum.toLocaleString('ko-KR'); }
          try{ if(window.__FORM_DEBUG__){ console.log('[InventoryPurchaseAdapter] items updated, count=', items.length); } }catch(_){ }
      }catch(e){}
  }

  // 슬롯으로 전달된 items를 폼에 반영 (행 수 보정 포함)
  function populateFromSlots(slots){
      if(!slots || !Array.isArray(slots.items) || !slots.items.length) return;
      try{
          var list = document.querySelector('.detail_area ul');
          if(!list) return;
          var need = slots.items.length;
          ensureListItemCount(need);
          slots.items.forEach(function(it, idx){
              var i = idx+1;
              var nameEl = document.getElementById('itemName'+i) || list.querySelector('[name="itemName'+i+'"]');
              var specEl = document.getElementById('itemSpec'+i) || list.querySelector('[name="itemSpec'+i+'"]');
              var qtyEl = document.getElementById('itemQuantity'+i) || list.querySelector('[name="itemQuantity'+i+'"]');
              var unitPriceEl = document.getElementById('itemUnitPrice'+i) || list.querySelector('[name="itemUnitPrice'+i+'"]');
              var totalPriceEl = document.getElementById('itemTotalPrice'+i) || list.querySelector('[name="itemTotalPrice'+i+'"]');
              var deliDateEl = list.querySelector('[name="itemDeliveryDate'+i+'"]');
              var supplierEl = document.getElementById('itemSupplier'+i) || list.querySelector('[name="itemSupplier'+i+'"]');
              var notesEl = document.getElementById('itemNotes'+i) || list.querySelector('[name="itemNotes'+i+'"]');
              var purposeEl = document.getElementById('itemPurpose'+i) || list.querySelector('[name="itemPurpose'+i+'"]');
              if(nameEl){ nameEl.value = it.item_name || ''; }
              if(specEl){ specEl.value = it.item_spec || ''; }
              if(qtyEl){ qtyEl.value = it.item_quantity != null ? String(it.item_quantity) : ''; }
              if(unitPriceEl){ unitPriceEl.value = formatComma(it.item_unit_price); }
              if(totalPriceEl){ totalPriceEl.value = formatComma(it.item_total_price); }
              if(deliDateEl){ deliDateEl.value = it.item_delivery_date || ''; try{ deliDateEl.dispatchEvent(new Event('change',{bubbles:true})); }catch(_e){} }
              if(supplierEl){ supplierEl.value = it.item_supplier || ''; }
              if(notesEl){ notesEl.value = it.item_notes || ''; }
              if(purposeEl){ purposeEl.value = it.item_purpose || it.item_notes || ''; }
              try{ var p = (nameEl && nameEl.closest('li')) ? nameEl.closest('li').querySelector('.box_head .tit p') : null; if(p){ p.textContent = nameEl.value || ''; } }catch(_e){}
          });
      }catch(e){}
  }

  // 현재 최상위 항목 li 개수 계산
  function existingItemCount(){
      var list = document.querySelector('.detail_area ul');
      if(!list) return 0;
      return Array.prototype.filter.call(list.children||[], function(el){ return el && el.tagName==='LI'; }).length;
  }

  // 목록(li) 개수를 target까지 확보 (퍼블리싱 add 버튼 또는 폴백 복제)
  function ensureListItemCount(target){
      var list = document.querySelector('.detail_area ul');
      if(!list) return;
      var getTopItems = function(ul){ return Array.prototype.filter.call((ul && ul.children)||[], function(el){ return el && el.tagName === 'LI'; }); };
      var addBtn = document.querySelector('.btn_add');
      var maxTarget = Math.min(Number(target)||0, 30);
      var current = getTopItems(list).length;
      for(var step=0; current < maxTarget && step < 40; step++){
          var before = current;
          if(addBtn){ addBtn.click(); }
          current = getTopItems(list).length;
          if(current > before){ continue; }
          // fallback: 직접 복제
          var itemsEls = getTopItems(list);
          var last = itemsEls[itemsEls.length-1];
          if(!last) break;
          var clone = last.cloneNode(true);
          Array.prototype.forEach.call(clone.querySelectorAll('.nice-select'), function(el){ if(el.parentNode){ el.parentNode.removeChild(el); } });
          Array.prototype.forEach.call(clone.querySelectorAll('select'), function(sel){ sel.removeAttribute('style'); sel.classList.remove('nice-initialized'); });
          var nextIndex = itemsEls.length + 1;
          clone.querySelectorAll('input, select, textarea, label').forEach(function(el){
              ['id','name','for'].forEach(function(attr){
                  var v = el.getAttribute && el.getAttribute(attr);
                  if(!v) return;
                  el.setAttribute(attr, v.replace(/(itemName|itemSpec|itemQuantity|itemUnitPrice|itemTotalPrice|itemDeliveryDate|itemSupplier|itemNotes|itemPurpose)\d+/, function(m){ return m.replace(/\d+$/, String(nextIndex)); }));
              });
              if(el.tagName==='INPUT' || el.tagName==='TEXTAREA'){ el.value = ''; }
              if(el.tagName==='SELECT'){ el.value = ''; try{ el.dispatchEvent(new Event('change',{bubbles:true})); }catch(_){} }
          });
          try{ var tp = clone.querySelector('.box_head .tit p'); if(tp){ tp.textContent = ''; } }catch(_e){}
          list.appendChild(clone);
          current = getTopItems(list).length;
          try{ if(window.UIReinit && window.UIReinit.schedule){ window.UIReinit.schedule(); } }catch(_e){}
      }
  }

  // 부트스트랩: 슬롯 채움 → 항목 반영 → hidden/총액 동기화 → 결재라인 렌더/조회 → 이벤트 바인딩
  async function bootstrap(slots, approverInfo){
      try{ console.log('[InventoryPurchaseAdapter][DEBUG] bootstrap start'); }catch(_){ }
      if(window.ExternalSlots && window.ExternalSlots.fillSlots){
          window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers });
          setTimeout(function(){ window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers }); }, 200);
          setTimeout(function(){ window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers }); }, 800);
      }

      try{ if(!document._inventoryPurchasePopulated){ populateFromSlots(slots||{}); document._inventoryPurchasePopulated = true; } }catch(_){ }
      try{ ensureRequestDateField(slots||{}); }catch(_){ }
      ensureHiddenItemsAndTotals();

      if(window.ApproverIntegration){
          try{ console.log('[InventoryPurchaseAdapter][DEBUG] renderApprovalLine'); }catch(_){ }
          window.ApproverIntegration.renderApprovalLine(approverInfo||{});
          if(!approverInfo || !approverInfo.approvers || !approverInfo.approvers.length){
              var pid = (slots && (slots.mst_pid || slots.mstPid)) || getPidFromPath();
              var drafterId = (slots && (slots.drafter_id || slots.drafterId)) || null;
              if(pid && window.ApproverIntegration.fetchApproverInfo){
                  var info = await window.ApproverIntegration.fetchApproverInfo({ mstPid: pid, drafterId: drafterId });
                  if(info){ window.ApproverIntegration.renderApprovalLine(info); }
              }
          }
      }

      try{
          if(document._inventoryPurchaseListenersBound === true){ /* already bound */ } else { document._inventoryPurchaseListenersBound = true;
          document.addEventListener('input', function(e){
              var t = e && e.target; if(!t) return;
              var re = /(itemName|itemSpec|itemQuantity|itemUnitPrice|itemTotalPrice|itemDeliveryDate|itemSupplier|itemNotes|itemPurpose)\d+$/;
              if((t.name && re.test(t.name)) || (t.id && re.test(t.id))){
                  ensureHiddenItemsAndTotals();
                  try{
                      var isName = (t.name && /^itemName\d+$/.test(t.name)) || (t.id && /^itemName\d+$/.test(t.id));
                      if(isName){
                          var li = t.closest('li');
                          if(li){
                              var tp = li.querySelector('.box_head .tit p');
                              if(tp){ tp.textContent = (t.value || ''); }
                          }
                      }
                  }catch(_e){}
              }
          }, true);
          document.addEventListener('change', function(e){
              var t = e && e.target; if(!t) return;
              var re = /(itemName|itemSpec|itemQuantity|itemUnitPrice|itemTotalPrice|itemDeliveryDate|itemSupplier|itemNotes|itemPurpose)\d+$/;
              if((t.name && re.test(t.name)) || (t.id && re.test(t.id))){
                  ensureHiddenItemsAndTotals();
                  try{
                      var isName = (t.name && /^itemName\d+$/.test(t.name)) || (t.id && /^itemName\d+$/.test(t.id));
                      if(isName){
                          var li = t.closest('li');
                          if(li){
                              var tp = li.querySelector('.box_head .tit p');
                              if(tp){ tp.textContent = (t.value || ''); }
                          }
                      }
                  }catch(_e){}
              }
          }, true);

          // 퍼블리싱 DOM의 행 추가/삭제 버튼 처리
          document.addEventListener('click', function(e){
              var btn = e.target; if(!btn) return;
              var list = document.querySelector('.detail_area ul');
              if(!list) return;
              // 행 추가
              if(btn.classList && btn.classList.contains('btn_add')){
                  var itemsEls = Array.prototype.filter.call((list && list.children)||[], function(el){ return el && el.tagName === 'LI'; });
                  var last = itemsEls[itemsEls.length-1];
                  if(!last) return;
                  var clone = last.cloneNode(true);
                  Array.prototype.forEach.call(clone.querySelectorAll('.nice-select'), function(el){ if(el.parentNode){ el.parentNode.removeChild(el); } });
                  Array.prototype.forEach.call(clone.querySelectorAll('select'), function(sel){ sel.removeAttribute('style'); sel.classList.remove('nice-initialized'); });
                  // 다음 인덱스 계산
                  var nextIndex = itemsEls.length + 1;
                  // id/name/for 속성의 숫자 인덱스를 갱신하고 값 초기화
                  clone.querySelectorAll('input, select, textarea, label').forEach(function(el){
                      ['id','name','for'].forEach(function(attr){
                          var v = el.getAttribute && el.getAttribute(attr);
                          if(!v) return;
                           el.setAttribute(attr, v.replace(/(itemName|itemSpec|itemQuantity|itemUnitPrice|itemTotalPrice|itemDeliveryDate|itemSupplier|itemNotes|itemPurpose)\d+/, function(m){ return m.replace(/\d+$/, String(nextIndex)); }));
                      });
                      if(el.tagName==='INPUT' || el.tagName==='TEXTAREA'){ el.value = ''; }
                      if(el.tagName==='SELECT'){ el.value = ''; try{ el.dispatchEvent(new Event('change',{bubbles:true})); }catch(_){} }
                  });
                  list.appendChild(clone);
                  try{ var titleEl = clone.querySelector('.box_head .tit p'); if(titleEl){ titleEl.textContent = ''; } }catch(_e){}
                  try{ if(window.UIReinit && window.UIReinit.schedule){ window.UIReinit.schedule(); } }catch(_e){}
                  setTimeout(ensureHiddenItemsAndTotals, 0);
                  e.preventDefault();
                  return;
              }
              // 행 삭제
              if(btn.classList && btn.classList.contains('btn_remove')){
                  var li = btn.closest('li');
                  var itemsEls2 = Array.prototype.filter.call((list && list.children)||[], function(el){ return el && el.tagName === 'LI'; });
                  if(li && itemsEls2.length > 1){ li.remove(); setTimeout(ensureHiddenItemsAndTotals, 0); }
                  e.preventDefault();
                  return;
              }
          }, true);
          }
      }catch(_){ }

      try{ if(window.UIReinit && window.UIReinit.schedule){ window.UIReinit.schedule(); } }catch(_){ }
  }

  window.InventoryPurchaseReportAdapter = { bootstrap: bootstrap };
})();


