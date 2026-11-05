import {evaluate,VERSION} from "./core.mjs";
const scenarios={
access:{description:"Draft an accessible public information guide so more people can use essential services.",kind:"information",authorization:"yes",affected:"no",consent:"yes",privacy:"yes",autonomy:"yes",harm:"low",benefit:"shared",oversight:"yes",reversible:"yes",evidence:"strong",appeal:"yes"},
wealth:{description:"Deploy an automated hiring and profit-allocation policy that increases owner profits while excluding worker participation.",kind:"external",authorization:"yes",affected:"yes",consent:"unknown",privacy:"yes",autonomy:"unknown",harm:"medium",benefit:"concentrated",oversight:"yes",reversible:"unknown",evidence:"reasonable",appeal:"no"},
private:{description:"Send identifiable patient records to a third-party service without permission to make a product demo.",kind:"external",authorization:"no",affected:"yes",consent:"no",privacy:"no",autonomy:"no",harm:"high",benefit:"concentrated",oversight:"no",reversible:"no",evidence:"weak",appeal:"no"}
};
const form=document.querySelector("#assessmentForm"),trace=document.querySelector("#resultTrace");
let lastReport=null;
function setExample(name){
 const src=scenarios[name];if(!src)return;
 for(const [key,val] of Object.entries(src)){const field=form.elements.namedItem(key);if(field)field.value=val;}
 document.querySelectorAll(".scenario").forEach(el=>{const active=el.dataset.example===name;el.classList.toggle("active",active);el.setAttribute("aria-pressed",String(active));});
 render();
}
function render(){
 try{
  const data={};new FormData(form).forEach((value,key)=>data[key]=value);
  const res=evaluate(data);lastReport={declaration:data,assessment:res};
  const tag=document.querySelector("#resultClass");tag.className="outcome-tag "+res.status.toLowerCase();
  tag.textContent=res.status==="PROVISIONAL"?"PROVISIONAL · NOT PERMISSION":res.status==="REVIEW"?"HUMAN REVIEW REQUIRED":"BLOCK · DO NOT ACT";
  document.querySelector("#resultSymbol").textContent=res.status==="BLOCK"?"×":res.status==="REVIEW"?"!":"◎";
  document.querySelector("#resultTitle").textContent=res.title;document.querySelector("#resultSummary").textContent=res.summary;
  document.querySelector("#mirrorText").textContent=res.mirror;
  trace.replaceChildren();res.explanations.forEach(reason=>{const li=document.createElement("li");li.textContent=reason;trace.appendChild(li);});
  document.querySelector("#copyMessage").textContent="";
 }catch(e){lastReport=null;document.querySelector("#resultTitle").textContent="Check your declaration.";document.querySelector("#resultSummary").textContent=e.message;}
}
form.addEventListener("submit",event=>{event.preventDefault();render();});
form.addEventListener("change",()=>{document.querySelectorAll(".scenario").forEach(el=>{el.classList.remove("active");el.setAttribute("aria-pressed","false")});render();});
document.querySelectorAll(".scenario").forEach(button=>button.addEventListener("click",()=>setExample(button.dataset.example)));
document.querySelector("#copyResult").addEventListener("click",async()=>{
 const message=document.querySelector("#copyMessage");
 if(!lastReport){message.textContent="No valid assessment to copy.";return;}
 const text="AΩ | AI action assessment / "+VERSION+"\n"+JSON.stringify(lastReport,null,2);
 try{await navigator.clipboard.writeText(text);message.textContent="Assessment copied. Review before sharing.";}
 catch{message.textContent="Copy unavailable here. Open the browser clipboard permissions.";}
});
setExample("access");