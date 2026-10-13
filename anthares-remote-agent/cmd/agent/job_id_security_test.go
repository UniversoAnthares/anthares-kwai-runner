package main

import (
 "net/http"
 "net/http/httptest"
 "testing"
)

func TestValidateJobID(t *testing.T) {
 for _,id:=range []string{"job-123","a_b","ABC123"} {
  if err:=validateJobID(id);err!=nil {t.Errorf("valid ID %q rejected: %v",id,err)}
 }
 for _,id:=range []string{"","../admin","x/y","x?y","x#y","x%2fy","with space","ä",string(make([]byte,129))} {
  if err:=validateJobID(id);err==nil {t.Errorf("unsafe ID %q accepted",id)}
 }
}

func TestPostResultRejectsUnsafeJobIDBeforeNetwork(t *testing.T) {
 calls:=0
 server:=httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request) {calls++;w.WriteHeader(http.StatusOK)}))
 defer server.Close()
 old:=httpClient;httpClient=server.Client();defer func(){httpClient=old}()
 cfg:=Config{ControlURL:server.URL,DeviceToken:"test",DeviceID:"test"}
 if err:=postResult(cfg,Result{ID:"../admin",OK:true});err==nil {t.Fatal("unsafe result ID accepted")}
 if calls!=0 {t.Fatalf("unexpected outbound requests: %d",calls)}
}
