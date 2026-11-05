// AΩ | AI deterministic advisory action gate, v0.2.
// Open source educational prototype. It does NOT grant permission to act.
export const VERSION = "0.2.0";
const yesNo=["yes","no","unknown"];
const tri=["yes","no","unknown"];
const values={
  kind:["information","external"],authorization:tri,affected:["yes","no"],
  consent:tri,privacy:tri,autonomy:tri,harm:["low","medium","high"],
  benefit:["shared","concentrated","unknown"],oversight:["yes","no"],
  reversible:tri,evidence:["strong","reasonable","weak"],appeal:tri
};
export function evaluate(input){
  if(!input||typeof input!=="object"||Array.isArray(input)) throw Error("Expected an action declaration object.");
  if(typeof input.description!=="string"||!input.description.trim()||input.description.length>500) throw Error("A description between 1 and 500 characters is required.");
  for(const [field,allowed] of Object.entries(values)) if(!allowed.includes(input[field])) throw Error("Invalid or missing field: "+field);
  const blocks=[],reviews=[],notes=[];
  if(input.kind==="external"&&input.authorization!=="yes") blocks.push("External action lacks verified authorization.");
  if(input.privacy==="no") blocks.push("Declared privacy violation.");
  if(input.autonomy==="no") blocks.push("Declared restriction of human agency.");
  if(input.affected==="yes"&&input.consent==="no") blocks.push("Others are affected without consent or a documented lawful basis.");
  if(input.harm==="high"&&input.oversight==="no") blocks.push("Severe plausible harm without a human reviewer.");
  if(input.harm==="high"&&input.kind==="external") reviews.push("Severe foreseeable harm: independent safeguards and specialist review needed.");
  else if(input.harm==="high") reviews.push("Severe foreseeable harm: independent safeguards needed.");
  if(input.harm==="medium") reviews.push("Meaningful possible harm requires mitigation evidence.");
  if(input.privacy==="unknown") reviews.push("Privacy effects have not been established.");
  if(input.autonomy==="unknown") reviews.push("Effects on autonomy remain uncertain.");
  if(input.affected==="yes"&&input.consent==="unknown") reviews.push("Affected people's rights and legal basis need independent checking.");
  if(input.benefit==="concentrated") reviews.push("Benefits are concentrated: examine who bears the costs and whether alternatives distribute benefits more fairly.");
  if(input.benefit==="unknown") reviews.push("Distribution of benefits is not known.");
  if(input.oversight==="no"&&input.kind==="external") reviews.push("An external agent action must have human control and a safe interrupt path.");
  if(input.reversible!=="yes") reviews.push("Reversibility is not established.");
  if(input.evidence!=="strong") reviews.push(input.evidence==="weak"?"Claims have not been verified.":"Evidence remains incomplete or unverified independently.");
  if(input.affected==="yes"&&input.appeal!=="yes") reviews.push("Affected people lack a clear appeal or remedy path.");
  if(input.authorization!=="yes"&&input.kind==="information") reviews.push("Who may authorize this information release is unclear.");
  if(input.affected==="no"&&input.consent==="no") notes.push("Consent marked missing, but no other people were declared affected; re-check the declaration.");
  const status=blocks.length?"BLOCK":reviews.length?"REVIEW":"PROVISIONAL";
  const explanations=[...blocks,...reviews,...notes];
  if(!explanations.length) explanations.push("No listed gate was triggered by the submitted claims. This is not independent verification.");
  const mirror=input.benefit==="concentrated"?
   "If the people bearing the costs became the decision-makers, would this allocation still seem fair? What alternative shares the gains?":
   input.affected==="yes"?
   "Would you consent to this action if you were one of the people affected, with the same information and ability to object?":
   "Who could be affected indirectly, and would you accept the same risk if the roles were reversed?";
  const title=status==="BLOCK"?"Do not execute this action.":status==="REVIEW"?"Stop for human review.":"Provisionally clear for discussion.";
  const summary=status==="BLOCK"?"At least one declared hard safeguard is absent.":status==="REVIEW"?"No hard stop was declared, but material concerns require attention.":"The stated checks did not raise a flag. Facts are still unverified.";
  return {version:VERSION,status,title,summary,explanations,mirror,humanApprovalRequired:input.kind==="external"||status!=="PROVISIONAL",limitations:"Self-reported declarations only. No fact checking, impact prediction, legal determination, or model alignment guarantee. This output never authorizes real actions."};
}
