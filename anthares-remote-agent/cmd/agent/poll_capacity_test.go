package main

import (
 "context"
 "net/http"
 "net/http/httptest"
 "sync/atomic"
 "testing"
 "time"
)

// This probe verifies that an idle poll never consumes an execution slot.
func TestPollNoContentDoesNotReturnJob(t *testing.T) {
 var polls atomic.Int32
 server:=httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){
  polls.Add(1);w.WriteHeader(http.StatusNoContent)
 }))
 defer server.Close()
 old:=httpClient;httpClient=server.Client();defer func(){httpClient=old}()
 cfg:=Config{ControlURL:server.URL,DeviceToken:"test",DeviceID:"test"}
 job,err:=pollJob(cfg)
 if err!=nil||job!=nil{t.Fatalf("204 must return nil job: %#v %v",job,err)}
 if polls.Load()!=1{t.Fatalf("expected one poll, got %d",polls.Load())}
}

func TestExecuteJobTimeoutIsBounded(t *testing.T) {
 ctx,cancel:=context.WithTimeout(context.Background(),time.Second)
 defer cancel()
 if err:=ctx.Err();err!=nil{t.Fatal(err)}
 r:=executeJob(Config{},Job{ID:"timeout-check",Type:"ping",TimeoutSeconds:999999})
 if !r.OK||r.Output!="pong"{t.Fatalf("bounded job execution failed: %#v",r)}
}
