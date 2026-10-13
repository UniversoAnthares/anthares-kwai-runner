package main

import (
 "encoding/json"
 "net/http"
 "net/http/httptest"
 "strings"
 "sync"
 "testing"
)

func TestControlProtocolEndToEnd(t *testing.T) {
 var mu sync.Mutex
 calls := map[string]int{}
 var submitted Result
 server := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request) {
  mu.Lock(); calls[r.URL.Path]++; mu.Unlock()
  if r.Header.Get("Authorization")!="Bearer test-token" || r.Header.Get("X-Anthares-Device")!="test-device" {
   http.Error(w,"unauthorized",http.StatusUnauthorized); return
  }
  switch r.URL.Path {
  case "/v1/device/heartbeat":
   if r.Method!=http.MethodPost {t.Errorf("heartbeat method %s",r.Method)}
   w.WriteHeader(http.StatusOK)
  case "/v1/device/jobs/next":
   w.Header().Set("Content-Type","application/json")
   _,_=w.Write([]byte(`{"job":{"id":"test-job","type":"ping","args":{}}}`))
  case "/v1/device/jobs/test-job/result":
   if err:=json.NewDecoder(r.Body).Decode(&submitted);err!=nil {t.Errorf("result JSON: %v",err)}
   w.WriteHeader(http.StatusOK)
  default:
   http.NotFound(w,r)
  }
 }))
 defer server.Close()
 previous:=httpClient
 httpClient=server.Client()
 defer func(){httpClient=previous}()
 cfg:=Config{ControlURL:server.URL,DeviceToken:"test-token",DeviceID:"test-device"}
 if err:=heartbeat(cfg);err!=nil{t.Fatal(err)}
 job,err:=pollJob(cfg);if err!=nil{t.Fatal(err)}
 if job==nil||job.ID!="test-job"{t.Fatalf("invalid job: %#v",job)}
 result:=executeJob(cfg,*job)
 if !result.OK||result.Output!="pong"{t.Fatalf("execution failed: %#v",result)}
 if err:=postResult(cfg,result);err!=nil{t.Fatal(err)}
 if submitted.ID!=job.ID||!submitted.OK||submitted.Output!="pong"{t.Fatalf("result mismatch: %#v",submitted)}
 for _,p:=range []string{"/v1/device/heartbeat","/v1/device/jobs/next","/v1/device/jobs/test-job/result"} {
  if calls[p]!=1 {t.Errorf("expected one call to %s, got %d",p,calls[p])}
 }
}

func TestControlRejectsUnauthorizedDevice(t *testing.T) {
 server:=httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request) {
  if !strings.HasPrefix(r.Header.Get("Authorization"),"Bearer valid") {http.Error(w,"unauthorized",http.StatusUnauthorized);return}
  w.WriteHeader(http.StatusNoContent)
 }))
 defer server.Close()
 old:=httpClient;httpClient=server.Client();defer func(){httpClient=old}()
 cfg:=Config{ControlURL:server.URL,DeviceToken:"wrong",DeviceID:"test-device"}
 if _,err:=pollJob(cfg);err==nil{t.Fatal("unauthorized poll accepted")}
}
