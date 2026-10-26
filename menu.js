(function(){
  "use strict";
  // Phone menu: the menu button opens the header links and the language list; the language button next to
  // "Get the app" opens the same panel with only the language list. CSS shows both buttons at 820px and below.
  var h=document.querySelector(".site-header"),b=h&&h.querySelector(".menu-btn"),lb=h&&h.querySelector(".lang-btn");
  if(!b)return;
  var lang=h.querySelector("details.lang"),mq=window.matchMedia("(max-width:820px)");
  function isOpen(){return h.classList.contains("menu-open");}
  function isLang(){return h.classList.contains("menu-lang");}
  function set(o,langOnly){
    h.classList.toggle("menu-open",o);
    h.classList.toggle("menu-lang",o&&!!langOnly);
    b.setAttribute("aria-expanded",String(o&&!langOnly));
    if(lb)lb.setAttribute("aria-expanded",String(o&&!!langOnly));
    if(lang)lang.open=o;
  }
  b.hidden=false;
  if(lb)lb.hidden=false;
  b.addEventListener("click",function(){set(!(isOpen()&&!isLang()),false);});
  if(lb)lb.addEventListener("click",function(){
    var close=isOpen()&&isLang();
    set(!close,true);
    if(!close){var a=h.querySelector("details.lang [aria-current]")||h.querySelector("details.lang a");if(a)a.focus({preventScroll:true});}
  });
  h.addEventListener("click",function(e){if(isOpen()&&e.target.closest&&e.target.closest("nav a, details.lang li a"))set(false);});
  document.addEventListener("keydown",function(e){if(e.key==="Escape"&&isOpen()){var l=isLang();set(false);(l&&lb?lb:b).focus();}});
  document.addEventListener("click",function(e){if(isOpen()&&!h.contains(e.target))set(false);});
  var onMq=function(){if(!mq.matches&&isOpen())set(false);};
  if(mq.addEventListener)mq.addEventListener("change",onMq);else if(mq.addListener)mq.addListener(onMq);
})();
