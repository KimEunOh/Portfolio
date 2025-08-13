(function(){
  /*
   * 법인카드 지출내역서 어댑터
   * - 역할: 슬롯 값 자동 채움 → 퍼블리싱 DOM에서 카드 사용 내역 수집 → hidden `card_usage_items` JSON 유지 → 총액 필드 동기화 → 결재라인 렌더/조회
   * - 서버 연계: `form_selector/processors/corporate_card_processor.py` 및 service 변환 로직과 호환
   * - 중요: 퍼블리싱 템플릿의 필드 네이밍(usageAmount1, usageCategory1, usageDate1, merchantName1, ...)에 의존
   */
  // 법인카드: 슬롯 채움 + 항목 수집(hidden card_usage_items) + 총액 갱신
  var aliasMap = {
    card_number: ['cardNumber'],
    statement_date: ['statementDate'],
    expense_reason: ['expenseReason','description'],
    total_usage_amount: ['totalUsageAmount','totalAmount']
  };
  var normalizers = {
    total_usage_amount: function(v){ var n = Number(String(v||'').replace(/[^\d.-]/g,'')); return isNaN(n) ? 0 : n; }
  };

  // URL 경로에서 mstPid 추출 (결재라인 조회 시 사용)
  function getPidFromPath(){ try{ var m = window.location.pathname.match(/\/master\/(\d+)/); if(m&&m[1]) return Number(m[1]); }catch(e){} return null; }
  // 숫자 파싱 및 표시 유틸
  function parseNumber(value){ var n = Number(String(value||'').replace(/[^\d.-]/g,'')); return isNaN(n)?0:n; }
  function formatComma(n){ try{ var num = parseNumber(n); return num ? num.toLocaleString('ko-KR') : ''; }catch(_){ return String(n||''); } }

  // 퍼블리싱 DOM → card_usage_items 배열 수집
  function collectUsageItems(){
    var items = [];
    try{
      var maxScan = 12;
      for(var i=1;i<=maxScan;i++){
        var amountEl = document.getElementById('usageAmount'+i) || document.querySelector('[name="usageAmount'+i+'"]');
        var catEl = document.getElementById('usageCategory'+i) || document.querySelector('[name="usageCategory'+i+'"]');
        var dateEl = document.querySelector('[name="usageDate'+i+'"]');
        var descEl = document.getElementById('merchantName'+i) || document.querySelector('[name="merchantName'+i+'"]');
        var notesEl = document.getElementById('usageNotes'+i) || document.querySelector('[name="usageNotes'+i+'"]');
        if(!(amountEl || catEl || dateEl || descEl || notesEl)) continue;
        var item = {
          usage_date: dateEl ? dateEl.value : '',
          usage_category: catEl ? catEl.value : '',
          usage_description: descEl ? descEl.value : '',
          usage_amount: parseNumber(amountEl && amountEl.value),
          usage_notes: notesEl ? notesEl.value : ''
        };
        if(item.usage_date || item.usage_category || item.usage_description || item.usage_amount || item.usage_notes){ items.push(item); }
      }
    }catch(e){ try{ if(window.__FORM_DEBUG__){ console.warn('[CorporateCardAdapter] collect error', e); } }catch(_e){} }
    return items;
  }

  // hidden `card_usage_items` 유지 및 총액 필드 동기화
  function ensureHiddenItemsAndTotals(){
    try{
      var form = document.querySelector('.form_area form') || document.querySelector('form');
      if(!form) return;
      // hidden dedupe: 동일 name 중복 제거 및 1개만 유지
      var allHidden = form.querySelectorAll('input[name="card_usage_items"]');
      var hidden = allHidden && allHidden[0];
      if(!hidden){ hidden = document.createElement('input'); hidden.type='hidden'; hidden.name='card_usage_items'; form.appendChild(hidden); }
      if(allHidden && allHidden.length > 1){ Array.prototype.slice.call(allHidden,1).forEach(function(el){ try{ el.parentNode && el.parentNode.removeChild(el); }catch(_e){} }); }
      hidden.type = 'hidden';
      var items = collectUsageItems();
      hidden.value = JSON.stringify(items);
      // 총액 갱신
      var totalField = document.getElementById('totalUsageAmount') || form.querySelector('[name="totalUsageAmount"]') || form.querySelector('[name="totalAmount"]');
      if(totalField){
        var sum = 0; items.forEach(function(it){ sum += parseNumber(it.usage_amount); });
        totalField.value = sum.toLocaleString('ko-KR');
      }
      try{ if(window.__FORM_DEBUG__){ console.log('[CorporateCardAdapter] items updated, count=', items.length); } }catch(_){ }
    }catch(e){}
  }

  // 슬롯으로 전달된 card_usage_items를 폼에 반영 (행 수 보정 포함)
  function populateFromSlots(slots){
    if(!slots || !Array.isArray(slots.card_usage_items) || !slots.card_usage_items.length) return;
    try{
      var list = document.querySelector('.detail_area ul');
      if(!list) return;
      var need = slots.card_usage_items.length;
      ensureListItemCount(need);
      slots.card_usage_items.forEach(function(it, idx){
        var i = idx+1;
        var amountEl = document.getElementById('usageAmount'+i) || list.querySelector('[name="usageAmount'+i+'"]');
        var catEl = document.getElementById('usageCategory'+i) || list.querySelector('[name="usageCategory'+i+'"]');
        var dateEl = list.querySelector('[name="usageDate'+i+'"]');
        var descEl = document.getElementById('merchantName'+i) || list.querySelector('[name="merchantName'+i+'"]');
        var notesEl = document.getElementById('usageNotes'+i) || list.querySelector('[name="usageNotes'+i+'"]');
        if(amountEl){ amountEl.value = formatComma(it.usage_amount); }
        if(catEl){ catEl.value = it.usage_category || ''; try{ catEl.dispatchEvent(new Event('change',{bubbles:true})); }catch(_e){} }
        if(dateEl){ dateEl.value = it.usage_date || ''; try{ dateEl.dispatchEvent(new Event('change',{bubbles:true})); }catch(_e){} }
        if(descEl){ descEl.value = it.usage_description || ''; }
        if(notesEl){ notesEl.value = it.usage_notes || ''; }
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
          el.setAttribute(attr, v.replace(/(usageAmount|usageCategory|merchantName|usageNotes|usageDate)\d+/, function(m){ return m.replace(/\d+$/, String(nextIndex)); }));
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
    try{ console.log('[CorporateCardAdapter][DEBUG] bootstrap start'); }catch(_){ }
    if(window.ExternalSlots && window.ExternalSlots.fillSlots){
      window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers });
      setTimeout(function(){ window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers }); }, 200);
      setTimeout(function(){ window.ExternalSlots.fillSlots({ slots: slots||{}, aliasMap: aliasMap, normalizers: normalizers }); }, 800);
    }

    try{ if(document._corporateCardPopulated !== true){ populateFromSlots(slots||{}); document._corporateCardPopulated = true; } }catch(_){ }
    ensureHiddenItemsAndTotals();

    if(window.ApproverIntegration){
      try{ console.log('[CorporateCardAdapter][DEBUG] renderApprovalLine'); }catch(_){ }
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
      if(document._corporateCardListenersBound !== true){ document._corporateCardListenersBound = true;
        document.addEventListener('input', function(e){
          var t = e && e.target; if(!t) return;
          var re = /(usageAmount|usageCategory|merchantName|usageNotes|usageDate)\d+$/;
          if((t.name && re.test(t.name)) || (t.id && re.test(t.id))){
            ensureHiddenItemsAndTotals();
          }
        }, true);
        document.addEventListener('change', function(e){
          var t = e && e.target; if(!t) return;
          var re = /(usageAmount|usageCategory|merchantName|usageNotes|usageDate)\d+$/;
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
                el.setAttribute(attr, v.replace(/(usageAmount|usageCategory|merchantName|usageNotes|usageDate)\d+/, function(m){ return m.replace(/\d+$/, String(nextIndex)); }));
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

  window.CorporateCardStatementAdapter = { bootstrap: bootstrap };
})();


