import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import git from 'isomorphic-git';
import {candidate,authorized,validRef} from '../lib/mirror.mjs';

const author={name:'Mirror fixture',email:'fixture@anthares.invalid'};
async function fixture(t){
 const dir=await fs.promises.mkdtemp(path.join(os.tmpdir(),'anthares-mirror-test-'));const options={fs,dir};
 t.after(async()=>{assert.equal(path.dirname(path.resolve(dir)),path.resolve(os.tmpdir()));assert(path.basename(dir).startsWith('anthares-mirror-test-'));await fs.promises.rm(dir,{recursive:true,force:true});});
 await git.init({...options,defaultBranch:'main'});
 const commit=async(branch,files)=>{await git.checkout({...options,ref:branch});for(const [name,contents] of Object.entries(files)){await fs.promises.writeFile(path.join(dir,name),contents);await git.add({...options,filepath:name});}return git.commit({...options,author,message:'fixture'});};
 await fs.promises.writeFile(path.join(dir,'shared.txt'),'baseline\n');await git.add({...options,filepath:'shared.txt'});const base=await git.commit({...options,author,message:'baseline'});
 await git.branch({...options,ref:'source'});await git.branch({...options,ref:'destination'});
 return{dir,options,base,commit};
}
test('authorization fails closed and branch names are narrowly scoped',()=>{
 const secret='s'.repeat(48);assert(authorized('Bearer '+secret,secret));assert(!authorized('',secret));assert(!authorized('Bearer '+secret,'short'));assert(!authorized('Bearer '+'x'.repeat(48),secret));
 assert(validRef('main'));assert(validRef('validation/mirror-20261018-e2e'));assert(!validRef('../main'));assert(!validRef('other-production'));
});
test('merges preserve GitLab-only content and both histories',async t=>{
 const f=await fixture(t);const source=await f.commit('source',{'source.txt':'source-only\n'});const destination=await f.commit('destination',{'.gitlab-ci.yml':'fallback-only\n'});
 const result=await candidate(f.dir,source,destination);assert.equal(result.kind,'MERGED_PRESERVING_BOTH');
 for(const [file,expected]of [['source.txt','source-only\n'],['.gitlab-ci.yml','fallback-only\n']]){const {blob}=await git.readBlob({...f.options,oid:result.oid,filepath:file});assert.equal(Buffer.from(blob).toString(),expected);}
 assert(await git.isDescendent({...f.options,oid:result.oid,ancestor:source}));assert(await git.isDescendent({...f.options,oid:result.oid,ancestor:destination}));
 const again=await candidate(f.dir,source,result.oid);assert.equal(again.oid,result.oid);assert.equal(again.kind,'IN_SYNC_PRESERVING_DESTINATION');
});
test('conflicting content aborts without replacing destination branch',async t=>{
 const f=await fixture(t);const source=await f.commit('source',{'shared.txt':'source change\n'});const destination=await f.commit('destination',{'shared.txt':'destination change\n'});
 await assert.rejects(candidate(f.dir,source,destination),e=>e.code==='CONTENT_CONFLICT');assert.equal(await git.resolveRef({...f.options,ref:'destination'}),destination);
});
test('fast-forward and unchanged destination remain idempotent',async t=>{
 const f=await fixture(t);const source=await f.commit('source',{'source.txt':'new\n'});const ff=await candidate(f.dir,source,f.base);assert.equal(ff.kind,'FAST_FORWARD');assert.equal(ff.oid,source);const same=await candidate(f.dir,source,source);assert.equal(same.kind,'IN_SYNC');
});
