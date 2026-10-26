(function(){
  "use strict";
  // Phone menu: opens the header links and the language list (CSS shows the button at 820px and below).
  var h=document.querySelector(".site-header"),b=h&&h.querySelector(".menu-btn");
  if(!b)return;
  var lang=h.querySelector("details.lang"),mq=window.matchMedia("(max-width:820px)");
  function isOpen(){return h.classList.contains("menu-open");}
  function set(o){
    h.classList.toggle("menu-open",o);
    b.setAttribute("aria-expanded",String(o));
    if(lang)lang.open=o;
  }
  b.hidden=false;
  b.addEventListener("click",function(){set(!isOpen());});
  h.addEventListener("click",function(e){if(isOpen()&&e.target.closest&&e.target.closest("nav a, details.lang li a"))set(false);});
  document.addEventListener("keydown",function(e){if(e.key==="Escape"&&isOpen()){set(false);b.focus();}});
  document.addEventListener("click",function(e){if(isOpen()&&!h.contains(e.target))set(false);});
  var onMq=function(){if(!mq.matches&&isOpen())set(false);};
  if(mq.addEventListener)mq.addEventListener("change",onMq);else if(mq.addListener)mq.addListener(onMq);
})();
