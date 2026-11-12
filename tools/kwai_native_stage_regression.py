#!/usr/bin/env python3
"""Offline regression guards for the Kwai Android MediaStore staging path."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
import kwai_native_cortes as k

class Result:
 def __init__(self,rc=0,stdout=''):
  self.returncode=rc;self.stdout=stdout;self.stderr=''

def run():
 digest='a'*64
 k.JOB='kwai-cortes-test-content-addressed-20261112'
 name='anthares-'+k.safe()[-70:]+'-'+digest[:12]+'.mp4'
 calls=[]
 old=k.adb
 def reuse(serial,*args,**kw):
  calls.append(args)
  if args[:2]==('shell','sha256sum'):return Result(0,digest+' '+args[-1])
  if args[:2]==('shell','content'):
   return Result(0,'Row: 0 _id=29, _display_name='+name+', duration=4200')
  return Result()
 try:
  k.adb=reuse
  _,uri=k.stage('test','media-unused',digest)
  assert uri.endswith('/29')
  assert not any(x[0]=='push' for x in calls)
  assert not any(x[:3]==('shell','am','broadcast') for x in calls)
  print('STAGING_HASHED_REUSE_NO_REPUSH_PASS')
  def wrong(serial,*args,**kw):
   if args[:2]==('shell','sha256sum'):return Result(0,'b'*64+' x')
   return Result()
  k.adb=wrong
  try:k.stage('test','unused',digest)
  except k.E as exc:assert 'different_sha256' in str(exc)
  else:raise AssertionError('wrong media SHA accepted')
  print('STAGING_HASH_MISMATCH_BLOCKED_PASS')
  calls=[];seen=[0]
  def new(serial,*args,**kw):
   calls.append(args)
   if args[:2]==('shell','sha256sum'):
    seen[0]+=1
    return Result(1) if seen[0]==1 else Result(0,digest+' x')
   if args[:2]==('shell','content'):
    return Result(0,'Row: 0 _id=41, _display_name='+name+', duration=4200')
   return Result()
  k.adb=new
  _,uri=k.stage('test','unused',digest)
  assert uri.endswith('/41')
  assert len([x for x in calls if x[0]=='push'])==1
  assert not any(x[:3]==('shell','am','broadcast') for x in calls)
  print('STAGING_NEW_PUSH_SHA256_AND_MEDIASTORE_PASS')
 finally:k.adb=old

if __name__=='__main__':run()
