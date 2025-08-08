(function(){
  var DEFAULT_SELECTORS = {
    drafterName: '#drafterName, .approval_line .draft .name',
    approverList: '#approverList, .approval_line .lines ul',
    approverTableBody: '#approverTableBody'
  };

  function qsAny(selector){
    var parts = selector.split(',');
    for(var i=0;i<parts.length;i++){
      var el = document.querySelector(parts[i].trim());
      if(el) return el;
    }
    return null;
  }

  function renderApprovalLine(approverInfo, selectors){
    if(!approverInfo || typeof approverInfo !== 'object') return;
    var sel = Object.assign({}, DEFAULT_SELECTORS, selectors||{});

    try{
      // 항상 펼쳐보이도록 처리
      try{
        var line = document.querySelector('.approval_line');
        if(line) line.classList.add('active');
      }catch(e){}

      var drafterEl = qsAny(sel.drafterName);
      if(drafterEl && approverInfo.drafterName){
        // 버튼 보존하면서 이름만 갱신
        var btn = drafterEl.querySelector('.btn_arr');
        if(btn){
          // 텍스트 노드 찾아 갱신, 없으면 생성 후 버튼 앞에 삽입
          var textNode = null;
          for(var i=0;i<drafterEl.childNodes.length;i++){
            if(drafterEl.childNodes[i].nodeType===3){ textNode = drafterEl.childNodes[i]; break; }
          }
          if(!textNode){
            textNode = document.createTextNode('');
            drafterEl.insertBefore(textNode, btn);
          }
          textNode.nodeValue = String(approverInfo.drafterName) + ' ';
        } else {
          drafterEl.textContent = String(approverInfo.drafterName);
        }
      }

      var tableBody = qsAny(sel.approverTableBody);
      if(tableBody && Array.isArray(approverInfo.approvers)){
        tableBody.innerHTML = '';
        approverInfo.approvers.forEach(function(appr, idx){
          var tr = document.createElement('tr');
          var tdOrder = document.createElement('td'); tdOrder.textContent = String((appr && appr.ordr!=null) ? appr.ordr : (idx+1));
          var tdName = document.createElement('td'); tdName.textContent = String((appr && appr.aprvPsNm) || '-');
          var tdId = document.createElement('td'); tdId.textContent = String((appr && appr.aprvPsId) || '-');
          var tdType = document.createElement('td'); tdType.textContent = String((appr && appr.aprvDvTy) || '-');
          tr.appendChild(tdOrder); tr.appendChild(tdName); tr.appendChild(tdId); tr.appendChild(tdType);
          tableBody.appendChild(tr);
        });
        return;
      }

      var ul = qsAny(sel.approverList);
      if(ul && Array.isArray(approverInfo.approvers)){
        ul.innerHTML = '';
        var typeLabel = function(t){
          if(!t) return '결재';
          var up = String(t).toUpperCase();
          if(up==='AGREEMENT') return '합의';
          if(up==='APPROVAL') return '결재';
          if(up==='REFERENCE' || up==='CC' || up==='CONSENT') return '참조';
          return '결재';
        };
        approverInfo.approvers.forEach(function(appr){
          var li = document.createElement('li');
          var dl = document.createElement('dl');
          var dt = document.createElement('dt'); dt.textContent = typeLabel(appr && appr.aprvDvTy);
          var dd = document.createElement('dd');
          var nameDiv = document.createElement('div'); nameDiv.className='name'; nameDiv.textContent = String((appr && appr.aprvPsNm) || '-');
          var btn = document.createElement('button'); btn.type='button'; btn.className='btn'; btn.textContent='변경';
          dd.appendChild(nameDiv); dd.appendChild(btn);
          dl.appendChild(dt); dl.appendChild(dd);
          li.appendChild(dl);
          ul.appendChild(li);
        });
      }
    }catch(e){}
  }

  async function fetchApproverInfo(params){
    var endpoint = (params && params.endpoint) || '/myLine';
    var mstPid = params && params.mstPid;
    var drafterId = params && params.drafterId;
    if(!mstPid) return null;
    try{
      var body = JSON.stringify({ mstPid: Number(mstPid), drafterId: drafterId || '' });
      var resp = await fetch(endpoint, { method:'POST', headers:{'Content-Type':'application/json'}, body });
      if(!resp.ok) return null;
      var data = await resp.json();
      return (data && data.data) ? data.data : null;
    }catch(e){ return null; }
  }

  window.ApproverIntegration = { renderApprovalLine: renderApprovalLine, fetchApproverInfo: fetchApproverInfo };
})();

