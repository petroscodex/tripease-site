/* Tripveller home: hero mode tiles (Air / Land / Ferries). Crossfades every 5 s; static with reduced motion. */
(function(){
  var hero=document.querySelector(".tv-hero"); if(!hero)return;
  var slides=hero.querySelectorAll(".tv-slide"), tiles=hero.querySelectorAll(".tv-tile"), modes=["air","land","ferry"], i=0, t=null;
  function show(m){ i=modes.indexOf(m);
    slides.forEach(function(s){s.classList.toggle("on",s.getAttribute("data-mode")===m);});
    tiles.forEach(function(b){var on=b.getAttribute("data-mode")===m;b.classList.toggle("on",on);b.setAttribute("aria-pressed",on?"true":"false");}); }
  tiles.forEach(function(b){b.addEventListener("click",function(){ if(t){clearInterval(t);t=null;} show(b.getAttribute("data-mode")); });});
  show("air");
  if(!(window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches)){
    t=setInterval(function(){ show(modes[(i+1)%modes.length]); },5000);
  }
})();
