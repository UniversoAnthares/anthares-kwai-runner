import assert from "node:assert/strict";
import test from "node:test";
import {validatePinterestTerminalErrorProof} from "../infra/neon-cortes-queue/index.mjs";

const NOW=Date.parse("2026-11-10T17:00:00Z");
const safe={
 id:"cortes-fanout-pinterest-23108d7fbcf6db56a713e806907be474",
 target_key:"pinterest:lucasyahn",
 remote_id:"6ad914067d80fe56e7308119",
 buffer_channel_id:"6ad8a46d778b240e2f79a40f",
 provider_status:"error",scheduling_type:"automatic",
 external_link:"",provider_link_present:false,
 provider_due_at_utc:"2026-10-21T20:58:00Z"
};

test("one old Buffer error yields fenced quarantine proof",()=>{
 const result=validatePinterestTerminalErrorProof(safe,NOW);
 assert.equal(result.id,safe.id);
 assert.equal(result.remote,safe.remote_id);
 assert.equal(result.provider_due_at_utc,"2026-10-21T20:58:00.000Z");
});

test("no scheduled, sent, public Pin or manual post can be quarantined",()=>{
 for(const fields of [
  {provider_status:"scheduled"},{provider_status:"sent"},
  {external_link:"https://www.pinterest.com/pin/819514463494611181",provider_link_present:true},
  {scheduling_type:"manual"},{provider_due_at_utc:"2026-11-10T16:50:00Z"}
 ])assert.equal(validatePinterestTerminalErrorProof({...safe,...fields},NOW),null);
});

test("wrong account or different remote channel fails",()=>{
 for(const fields of [
  {target_key:"pinterest:other"},{buffer_channel_id:"wrong"},
  {id:"cortes-fanout-pinterest-bad"},{remote_id:"../../breakout"}
 ])assert.equal(validatePinterestTerminalErrorProof({...safe,...fields},NOW),null);
});

test("old error receipt cannot invent a published public link",()=>{
 for(const fields of [
   {provider_link_present:true},{external_link:undefined},
   {provider_due_at_utc:"INVALID"},{provider_due_at_utc:"2020-01-01T00:00:00Z"}
 ])assert.equal(validatePinterestTerminalErrorProof({...safe,...fields},NOW),null);
});
