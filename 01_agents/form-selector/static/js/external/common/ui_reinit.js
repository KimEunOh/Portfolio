(function(){
  function tryReinitDatepickers(){
    try{
      if (typeof fn_setDatePicker === 'function'){
        fn_setDatePicker('#searchStDt', {});
        fn_setDatePicker('#searchEdDt', {});
        // 퍼블리싱에서 자주 쓰는 id 대응
        fn_setDatePicker('#workDate', {});
      } else if (window.jQuery && jQuery.fn && jQuery.fn.datetimepicker){
        try{ jQuery('#searchStDt').datetimepicker(); }catch(e){}
        try{ jQuery('#searchEdDt').datetimepicker(); }catch(e){}
        try{ jQuery('#workDate').datetimepicker(); }catch(e){}
      }
    }catch(e){}
  }

  function tryReinitNiceSelect(){
    try{
      if (window.jQuery && jQuery.fn && jQuery.fn.niceSelect){ jQuery('select').niceSelect('update'); }
    }catch(e){}
  }

  function tryReinitInputActive(){
    try{ if (typeof inputActive === 'function'){ inputActive('body'); } }catch(e){}
  }

  function run(){
    tryReinitNiceSelect();
    tryReinitInputActive();
    tryReinitDatepickers();
  }

  function schedule(){
    run();
    setTimeout(run, 150);
    setTimeout(run, 500);
    setTimeout(run, 1200);
    setTimeout(run, 2000);
  }

  window.UIReinit = { run: run, schedule: schedule };
})();

