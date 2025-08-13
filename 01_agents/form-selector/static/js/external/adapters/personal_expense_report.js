(function(){
  /*
   * 개인 경비 사용내역서 어댑터
   * - 역할: 슬롯 값 자동 채움 → 퍼블리싱 DOM에서 항목 수집 → hidden `expense_items` JSON 유지 → 총액 필드 동기화 → 결재라인 렌더/조회
   * - 서버 연계: `form_selector/processors/personal_expense_processor.py` 및 service의 V2/Legacy 변환 로직과 호환
   * - 중요: 퍼블리싱 템플릿의 항목 입력 네이밍 규칙(expenseAmount1, expenseCategory1, expenseDate1, ...)에 의존
   */
  // 개인 경비: 슬롯 채움 + 항목 수집(hidden expense_items) + 총액 갱신
  var aliasMap = {
    usage_status: ['usageStatus'],
    expense_reason: ['expenseReason','description'],
    total_expense_amount: ['totalExpenseAmount']
  };
  var normalizers = {
    total_expense_amount: function(v){ var n = Number(String(v||'').replace(/[^\d.-]/g,'')); return isNaN(n) ? 0 : n; }
  };

  // URL 경로에서 mstPid 추출 (결재라인 조회 시 사용)
  function getPidFromPath(){ try{ var m = window.location.pathname.match(/\/master\/(\d+)/); if(m&&m[1]) return Number(m[1]); }catch(e){} return null; }
  // 금액/수량 등 숫자 파싱 유틸
  function parseNumber(value){ var n = Number(String(value||'').replace(/[^\d.-]/g,'')); return isNaN(n)?0:n; }
  function formatComma(n){ try{ var num = parseNumber(n); return num ? num.toLocaleString('ko-KR') : ''; }catch(_){ return String(n||''); } }

  // 퍼블리싱 DOM → expense_items 배열 수집
  function collectExpenseItems(){
    var items = [];
    try{
      var maxScan = 30;
      for(var i=1;i<=maxScan;i++){
        var amountEl = document.getElementById('expenseAmount'+i) || document.querySelector('[name="expenseAmount'+i+'"]');
        var catEl = document.getElementById('expenseCategory'+i) || document.querySelector('[name="expenseCategory'+i+'"]');
        var dateEl = document.querySelector('[name="expenseDate'+i+'"]');
        var descEl = document.getElementById('expenseDescription'+i) || document.querySelector('[name="expenseDescription'+i+'"]');
        var notesEl = document.getElementById('expenseNotes'+i) || document.querySelector('[name="expenseNotes'+i+'"]');
        if(!(amountEl || catEl || dateEl || descEl || notesEl)) continue;
        var item = {
          expense_date: dateEl ? dateEl.value : '',
          expense_category: catEl ? catEl.value : '',
          expense_description: descEl ? descEl.value : '',
          expense_amount: parseNumber(amountEl && amountEl.value),
          expense_notes: notesEl ? notesEl.value : ''
        };
        if(item.expense_date || item.expense_category || item.expense_description || item.expense_amount || item.expense_notes){ items.push(item); }
      }
    }catch(e){ try{ if(window.__FORM_DEBUG__){ console.warn('[PersonalExpenseAdapter] collect error', e); } }catch(_e){} }
    return items;
  }

  // hidden `expense_items` 유지 및 총액 필드 동기화
  function ensureHiddenItemsAndTotals(){
    try{
      var form = document.querySelector('.form_area form') || document.querySelector('form');
      if(!form) return;
      // hidden dedupe: 동일 name 중복 제거 및 1개만 유지
      var allHidden = form.querySelectorAll('input[name="expense_items"]');
      var hidden = allHidden && allHidden[0];
      if(!hidden){ hidden = document.createElement('input'); hidden.type='hidden'; hidden.name='expense_items'; form.appendChild(hidden); }
      if(allHidden && allHidden.length > 1){ Array.prototype.slice.call(allHidden,1).forEach(function(el){ try{ el.parentNode && el.parentNode.removeChild(el); }catch(_e){} }); }
      hidden.type = 'hidden';
      var items = collectExpenseItems();
      hidden.value = JSON.stringify(items);
      // 총액 갱신
      var totalField = document.getElementById('totalExpenseAmount') || form.querySelector('[name="totalExpenseAmount"]') || form.querySelector('[name="total_expense_amount"]');
      if(totalField){
        var sum = 0; items.forEach(function(it){ sum += parseNumber(it.expense_amount); });
        totalField.value = sum.toLocaleString('ko-KR');
      }
      try{ if(window.__FORM_DEBUG__){ console.log('[PersonalExpenseAdapter] items updated, count=', items.length); } }catch(_){ }
    }catch(e){}
  }

  // 슬롯으로 전달된 expense_items를 폼에 반영 (행 수 보정 포함)
  function populateFromSlots(slots){
    if(!slots || !Array.isArray(slots.expense_items) || !slots.expense_items.length) return;
    try{
      var list = document.querySelector('.detail_area ul');
      if(!list) return;
      var need = slots.expense_items.length;
      ensureListItemCount(need);
      slots.expense_items.forEach(function(it, idx){
        var i = idx+1;
        var amountEl = document.getElementById('expenseAmount'+i) || list.querySelector('[name="expenseAmount'+i+'"]');
        var catEl = document.getElementById('expenseCategory'+i) || list.querySelector('[name="expenseCategory'+i+'"]');
        var dateEl = list.querySelector('[name="expenseDate'+i+'"]');
        var descEl = document.getElementById('expenseDescription'+i) || list.querySelector('[name="expenseDescription'+i+'"]');
        var notesEl = document.getElementById('expenseNotes'+i) || list.querySelector('[name="expenseNotes'+i+'"]');
        if(amountEl){ amountEl.value = formatComma(it.expense_amount); }
        if(catEl){ catEl.value = it.expense_category || ''; try{ catEl.dispatchEvent(new Event('change',{bubbles:true})); }catch(_e){} }
        if(dateEl){ dateEl.value = it.expense_date || ''; try{ dateEl.dispatchEvent(new Event('change',{bubbles:true})); }catch(_e){} }
        if(descEl){ descEl.value = it.expense_description || ''; }
        if(notesEl){ notesEl.value = it.expense_notes || ''; }
      });
      try{ if(window.UIReinit && window.UIReinit.schedule){ window.UIReinit.schedule(); } }catch(_e){}
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
          el.setAttribute(attr, v.replace(/(expenseAmount|expenseCategory|expenseDescription|expenseNotes|expenseDate)\d+/, function(m){ return m.replace(/\d+$/, String(nextIndex)); }));
        });
        if(el.tagName==='INPUT' || el.tagName==='TEXTAREA'){ el.value = ''; }
        if(el.tagName==='SELECT'){ el.value = ''; try{ el.dispatchEvent(new Event('change',{bubbles:true})); }catch(_){} }
      });
      list.appendChild(clone);
      current = getTopItems(list).length;
      try{ if(window.UIReinit && window.UIReinit.schedule){ window.UIReinit.schedule(); } }catch(_e){}
    }
  }

  // 부트스트랩: 슬롯 채움 → 항목 반영 → hidden/총액 동기화 → 결재라인 렌더/조회 → 이벤트 바인딩
  async function bootstrap(slots, approverInfo){
    try{ console.log('[PersonalExpenseAdapter][DEBUG] bootstrap start'); }catch(_){ }
    if(window.ExternalSlots && window.ExternalSlots.fillSlots){
      window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers });
      setTimeout(function(){ window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers }); }, 200);
      setTimeout(function(){ window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers }); }, 800);
    }

    try{ if(document._personalExpensePopulated !== true){ populateFromSlots(slots||{}); document._personalExpensePopulated = true; } }catch(_){ }
    ensureHiddenItemsAndTotals();

    if(window.ApproverIntegration){
      try{ console.log('[PersonalExpenseAdapter][DEBUG] renderApprovalLine'); }catch(_){ }
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
      if(document._personalExpenseListenersBound !== true){ document._personalExpenseListenersBound = true;
        document.addEventListener('input', function(e){
          var t = e && e.target; if(!t) return;
          var re = /(expenseAmount|expenseCategory|expenseDescription|expenseNotes|expenseDate)\d+$/;
          if((t.name && re.test(t.name)) || (t.id && re.test(t.id))){
            ensureHiddenItemsAndTotals();
          }
        }, true);
        document.addEventListener('change', function(e){
          var t = e && e.target; if(!t) return;
          var re = /(expenseAmount|expenseCategory|expenseDescription|expenseNotes|expenseDate)\d+$/;
          if((t.name && re.test(t.name)) || (t.id && re.test(t.id))){
            ensureHiddenItemsAndTotals();
          }
        }, true);
        // 퍼블리싱 DOM의 행 추가/삭제 버튼 처리
        document.addEventListener('click', function(e){
          var btn = e.target; if(!btn) return;
          var list = document.querySelector('.detail_area ul'); if(!list) return;
          // 행 추가
          if(btn.classList && btn.classList.contains('btn_add')){
            var itemsEls = Array.prototype.filter.call((list && list.children)||[], function(el){ return el && el.tagName === 'LI'; });
            var last = itemsEls[itemsEls.length-1]; if(!last) return;
            var clone = last.cloneNode(true);
            Array.prototype.forEach.call(clone.querySelectorAll('.nice-select'), function(el){ if(el.parentNode){ el.parentNode.removeChild(el); } });
            Array.prototype.forEach.call(clone.querySelectorAll('select'), function(sel){ sel.removeAttribute('style'); sel.classList.remove('nice-initialized'); });
            var nextIndex = itemsEls.length + 1;
            clone.querySelectorAll('input, select, textarea, label').forEach(function(el){
              ['id','name','for'].forEach(function(attr){
                var v = el.getAttribute && el.getAttribute(attr);
                if(!v) return;
                el.setAttribute(attr, v.replace(/(expenseAmount|expenseCategory|expenseDescription|expenseNotes|expenseDate)\d+/, function(m){ return m.replace(/\d+$/, String(nextIndex)); }));
              });
              if(el.tagName==='INPUT' || el.tagName==='TEXTAREA'){ el.value = ''; }
              if(el.tagName==='SELECT'){ el.value = ''; try{ el.dispatchEvent(new Event('change',{bubbles:true})); }catch(_){} }
            });
            list.appendChild(clone);
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

  window.PersonalExpenseReportAdapter = { bootstrap: bootstrap };
})();


