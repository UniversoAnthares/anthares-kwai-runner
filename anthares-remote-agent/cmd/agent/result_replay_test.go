package main

import (
 "net/http"
 "net/http/httptest"
 "os"
 "path/filepath"
 "sync/atomic"
 "testing"
)
func TestReplayEncryptedResultsKeepsOnFailureAndRemovesOnAck(t *testing.T){
 var accept atomic.Bool
 var received atomic.Int32
 server:=httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){
  if r.URL.Path!="/v1/device/jobs/job_1/result"{t.Errorf("unexpected path %s",r.URL.Path);w.WriteHeader(404);return}
  received.Add(1)
  if !accept.Load(){w.WriteHeader(503);return}
  w.WriteHeader(200)
 }))
 defer server.Close()
 old:=httpClient
 httpClient=server.Client()
 defer func(){httpClient=old}()
 cfg:=Config{ControlURL:server.URL,DeviceToken:"spool-secret",DeviceID:"replay-test-device"}
 dir:=resultSpoolDir(cfg)
 defer os.RemoveAll(dir)
 if err:=saveEncryptedResult(dir,cfg.DeviceToken,Result{ID:"job_1",OK:true,Output:"done"});err!=nil{t.Fatal(err)}
 path:=filepath.Join(dir,"job_1.pending")
 if err:=replayEncryptedResults(cfg);err==nil{t.Fatal("expected upload failure")}
 if _,err:=os.Stat(path);err!=nil{t.Fatal("failed upload removed pending result")}
 accept.Store(true)
 if err:=replayEncryptedResults(cfg);err!=nil{t.Fatal(err)}
 if _,err:=os.Stat(path);!os.IsNotExist(err){t.Fatalf("acknowledged result not removed: %v",err)}
 if received.Load()<2{t.Fatal("result was not retried")}
}
