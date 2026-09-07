"""Accessible offline tabs with an all-content fallback independent of chart loading."""

TABS = (
    ("overview", "Overview"),
    ("arena", "Forecast Arena"),
    ("champion", "Champion Map"),
    ("diagnostics", "Forecast Diagnostics"),
    ("labor", "Labor Optimizer"),
    ("scenario", "Scenario Lab"),
    ("governance", "Governance / DRI"),
)
PROVENANCE = (
    "This portfolio prototype uses public M5 retail-demand data. "
    "Labor and inventory inputs are illustrative and are not intended "
    "to represent any specific company's production operations."
)
CSS = """
*{box-sizing:border-box}html{scroll-padding-top:110px}main{max-width:1280px;
min-width:0}
section,article,.cards,.brief,.overview-grid,.tab-panel,figure{min-width:0;
max-width:100%}
.cards,.brief,.overview-grid{display:grid;
grid-template-columns:repeat(2,minmax(0,1fr));
align-items:start}
.cards>*,.brief>*,.overview-grid>*{min-width:0;
overflow-wrap:anywhere;
height:auto}
nav{position:sticky;
top:0;
z-index:20;
display:flex;
flex-wrap:wrap;
gap:5px;

 background:#f4f7fb;
padding:12px 0;
border-bottom:1px solid #ccd7e1}
nav a{flex:0 1 auto;
white-space:normal;
text-decoration:none;
border-radius:8px;
padding:10px 12px}
nav a[aria-selected=true]{background:#15364e;
color:white}nav a:focus-visible{outline:3px solid #bd6509}
.tab-panel[hidden]{display:none}.tab-panel{scroll-margin-top:110px}
.visual-grid{display:grid;
grid-template-columns:minmax(0,1fr);
gap:24px;
margin:28px 0}
.visual-card{margin:0;
padding:24px;
background:white;
border:1px solid #d8e1e9;
border-radius:14px;
overflow:hidden}
.visual-card h3{font-size:22px;
margin:0 0 12px;
line-height:1.4;
overflow-wrap:anywhere}
.visual-card .chart{position:relative;
width:100%;
height:450px;
min-height:450px;
margin:0;
border:0;
overflow:hidden}
.visual-card p{margin:18px 0 0;
line-height:1.6}.visual-card small{overflow-wrap:anywhere}
img,svg{max-width:100%;
height:auto;
display:block}.scroll{width:100%;
max-width:100%;
overflow-x:auto}
table{width:max-content;
min-width:100%}td,th{max-width:36rem;
overflow-wrap:anywhere}
.timeline,.workload-flow{display:flex;
flex-wrap:wrap;
align-items:center;
gap:18px;
padding:24px;
background:#e5eef6}
.timeline>*,.workload-flow>*{flex:1 1 200px;
min-width:0}section{height:auto;
overflow:visible}
@media(max-width:760px){main{padding:12px}.cards,.brief,.overview-grid{grid-template-columns:minmax(0,1fr)}
nav{position:relative;
top:auto}html{scroll-padding-top:15px}.tab-panel{scroll-margin-top:15px}
.visual-card{padding:12px}.visual-card .chart{height:490px;
min-height:490px}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
"""

# A separate script: a failed chart library cannot prevent navigation initialization.
CONTROLLER = """
(function(){
 const tabs=Array.from(document.querySelectorAll('[data-tab]'));

 const panels=Array.from(document.querySelectorAll('[data-panel]'));

 function fallback(){panels.forEach(p=>p.hidden=false);
tabs.forEach(t=>t.tabIndex=0);
}
 function select(id,focus){
  const selected=tabs.find(t=>t.dataset.tab===id);
if(!selected)return;

  try {
   panels.forEach(p=>p.hidden=p.dataset.panel!==id);

   tabs.forEach(t=>{const active=t===selected;
t.setAttribute('aria-selected',String(active));
t.tabIndex=active?0:-1;
});

   if(focus)selected.focus();

   window.dispatchEvent(new Event('resize'));

  }catch(error){fallback();
}
 }
 try {
  tabs.forEach((tab,index)=>{
   tab.addEventListener('click',event=>{event.preventDefault();
select(tab.dataset.tab,false);
});

   tab.addEventListener('keydown',event=>{
    let next=index;

    if(event.key==='ArrowRight')next=(index+1)%tabs.length;

    else if(event.key==='ArrowLeft')next=(index+tabs.length-1)%tabs.length;

    else if(event.key==='Home')next=0;
else if(event.key==='End')next=tabs.length-1;
else return;

    event.preventDefault();
select(tabs[next].dataset.tab,true);

   });

  });

  select('overview',false);

 }catch(error){fallback();
}
})();

"""
