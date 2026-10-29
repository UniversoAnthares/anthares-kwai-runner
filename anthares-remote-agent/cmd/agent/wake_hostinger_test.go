package main

import (
    "context"
    "errors"
    "io"
    "net/http"
    "net/url"
    "strings"
    "sync/atomic"
    "testing"
    "time"
)

type wakeRoundTrip func(*http.Request)(*http.Response,error)
func (fn wakeRoundTrip) RoundTrip(r *http.Request)(*http.Response,error){return fn(r)}
func testClient(fn wakeRoundTrip)*http.Client {
    return &http.Client{Transport:fn,Timeout:time.Second,
        CheckRedirect:func(*http.Request,[]*http.Request)error{return http.ErrUseLastResponse}}
}
const testListenerToken="TEST_ONLY_LISTENER_CREDENTIAL_0123456789___"
func TestWakeFlagAndSeparateListenerSecret(t *testing.T){
    cfg:=Config{ControlURL:"https://anthares-remote-primary.vercel.app",DeviceID:araHostingerDevice,
        WakeListenerToken:testListenerToken}
    if startWakeSubscriber(cfg)!=nil {t.Fatal("default-off must not start")}
    cfg.WakeEnabled=true;cfg.DeviceID="FOREIGN-DEVICE"
    if startWakeSubscriber(cfg)!=nil {t.Fatal("wrong device must not start")}
    cfg.DeviceID=araHostingerDevice;cfg.WakeListenerToken=""
    if startWakeSubscriber(cfg)!=nil {t.Fatal("missing listener token must not start")}
    cfg.WakeListenerToken=testListenerToken;cfg.ControlURL=""
    if startWakeSubscriber(cfg)!=nil {t.Fatal("queue-only must not create listener")}
    cfg.ControlURL="https://anthares-remote-primary.vercel.app";cfg.WakeOriginIP="127.0.0.1"
    if startWakeSubscriber(cfg)!=nil {t.Fatal("private origin IP must fail closed")}
}
func TestWakeHostingerFixedURLAndAuthentication(t *testing.T){
    var calls atomic.Int32
    client:=testClient(func(r *http.Request)(*http.Response,error){
        calls.Add(1)
        if r.URL.Scheme!="https" || r.URL.Host!="anthares.us" || r.URL.Path!="/ara-notify/index.php" {t.Errorf("untrusted URL %s",r.URL)}
        if r.Method!="GET" || r.Header.Get("X-Anthares-Notify-Key")!=testListenerToken || r.Header.Get("Authorization")!="" || r.Header.Get("X-Anthares-Device")!="" {t.Errorf("auth or method invalid")}
        q:=r.URL.Query()
        if q.Get("action")!="wait" || q.Get("device_id")!=araHostingerDevice || q.Get("since")!="13" || q.Get("seconds")!="20" {t.Errorf("wake query: %s",q.Encode())}
        if _,err:=url.Parse(r.URL.String());err!=nil {t.Error(err)}
        return &http.Response{StatusCode:200,Body:io.NopCloser(strings.NewReader(`{"ok":true,"wake":true,"sequence":14,"protocol":"ara-wake-v1"}`)),Header:http.Header{}},nil
    })
    seq,wake,err:=waitHostinger(context.Background(),client,testListenerToken,13)
    if err!=nil||seq!=14||!wake||calls.Load()!=1{t.Fatalf("seq=%d wake=%t err=%v calls=%d",seq,wake,err,calls.Load())}
}
func TestWakePayloadRejectsCommandInjection(t *testing.T){
    cases:=[]string{
        `{"wake":true,"sequence":2,"command":"shell"}`,
        `{"wake":true,"sequence":2,"job_id":"malicious"}`,
        `{"wake":true,"sequence":2,"url":"https://malicious"}`,
        `{"wake":true,"sequence":-1}`,
        `{"wake":true,"sequence":2,"device_id":"FOREIGN"}`,
        `{"wake":true,"sequence":2,"ok":false}`,
        `{"wake":"true","sequence":2}`,
        `{"wake":true}`,
        strings.Repeat("x",1025),
    }
    for _,payload:=range cases {if _,_,err:=decodeHostingerWake([]byte(payload),0);err==nil{t.Errorf("accepted malformed payload %s",payload)}}
    if _,_,err:=decodeHostingerWake([]byte(`{"wake":true,"sequence":4}`),5);err==nil {t.Fatal("sequence regression accepted")}
    seq,wake,err:=decodeHostingerWake([]byte(`{"wake":false,"sequence":7}`),7)
    if err!=nil||wake||seq!=7 {t.Fatal("valid idle response rejected",err)}
    seq,wake,err=decodeHostingerWake([]byte(`{"wake":false,"sequence":8}`),7)
    if err!=nil||!wake||seq!=8 {t.Fatal("advanced sequence should wake",err)}
}
func TestWakeOfflineFallbackAndCoalescing(t *testing.T){
    var s *wakeSubscriber
    if wakeWaitDuration(s)!=2*time.Second {t.Fatal("nil legacy fallback wrong")}
    s=newWakeSubscriber()
    if wakeWaitDuration(s)!=2*time.Second {t.Fatal("disconnected fallback wrong")}
    s.setOnline(true)
    if wakeWaitDuration(s)!=12*time.Second {t.Fatal("online reconciliation must be 12sec")}
    start:=time.Now();s.waitAfterEmpty()
    if time.Since(start)>150*time.Millisecond {t.Fatal("connecting must unblock idle HTTP scan")}
    s.signal();s.signal();s.signal()
    if len(s.events)>1 {t.Fatal("wake events not coalesced")}
    start=time.Now();s.waitAfterEmpty()
    if time.Since(start)>150*time.Millisecond {t.Fatal("wake did not unblock")}
    s.setOnline(false)
    if wakeWaitDuration(s)!=2*time.Second {t.Fatal("disconnection must restore 2sec legacy poll")}
    start=time.Now();s.waitAfterEmpty()
    if time.Since(start)>150*time.Millisecond {t.Fatal("disconnect must unblock immediately")}
}
func TestWakeHTTPFailureDoesNotClaimJobs(t *testing.T){
    client:=testClient(func(r *http.Request)(*http.Response,error){
        return &http.Response{StatusCode:401,Body:io.NopCloser(strings.NewReader(`{"error":"unauthorized"}`)),Header:http.Header{}},nil
    })
    _,_,err:=waitHostinger(context.Background(),client,testListenerToken,0)
    if err==nil || !strings.Contains(err.Error(),"wake_http_401") {t.Fatalf("auth failure not detected: %v",err)}
    client=testClient(func(*http.Request)(*http.Response,error){return nil,errors.New("hostinger_unavailable")})
    _,_,err=waitHostinger(context.Background(),client,testListenerToken,0)
    if err==nil {t.Fatal("network outage not detected")}
    if hostingerReconnectDelay(0)<2*time.Second || hostingerReconnectDelay(12)>34*time.Second {t.Fatal("unbounded reconnect backoff")}
}
func TestWakeOriginIPRejectsPrivateAddresses(t *testing.T){
    for _,v:=range []string{"127.0.0.1","10.0.0.1","192.168.0.1","172.16.0.1","169.254.1.1","100.64.1.2","203.0.113.3","::1","evil.example.org"}{
        if publicWakeOrigin(v){t.Errorf("origin accepted: %s",v)}
    }
    if !publicWakeOrigin("8.8.8.8"){t.Fatal("public IPv4 rejected")}
    client,err:=hostingerWakeClient("8.8.8.8")
    if err!=nil||client.CheckRedirect==nil {t.Fatal("direct origin client invalid",err)}
    if _,err:=hostingerWakeClient("192.168.0.1");err==nil {t.Fatal("private IP allowed")}
}
func TestWakeClientRejectsRedirect(t *testing.T){
    c,err:=hostingerWakeClient("")
    if err!=nil {t.Fatal(err)}
    if c.CheckRedirect(nil,nil)!=http.ErrUseLastResponse {t.Fatal("redirect must be rejected to protect bearer")}
}

func TestWakeLongPollDrivesEventLoopAndStopsCleanly(t *testing.T){
    ctx,cancel:=context.WithCancel(context.Background())
    defer cancel()
    var calls atomic.Int32
    client:=testClient(func(r *http.Request)(*http.Response,error){
        if calls.Add(1)==1 {
            return &http.Response{StatusCode:200,Header:http.Header{},Body:io.NopCloser(strings.NewReader(`{"ok":true,"wake":true,"sequence":41}`))},nil
        }
        <-r.Context().Done()
        return nil,r.Context().Err()
    })
    s:=newWakeSubscriber()
    done:=make(chan struct{})
    go func(){s.runHostinger(ctx,testListenerToken,client);close(done)}()
    select {
    case <-s.events:
    case <-time.After(time.Second):t.Fatal("first valid long poll did not schedule HTTP lease")
    }
    if !s.online.Load(){t.Fatal("listener not marked online")}
    if wakeWaitDuration(s)!=12*time.Second {t.Fatal("connected recheck wrong")}
    cancel()
    select {
    case <-done:
    case <-time.After(time.Second):t.Fatal("listener did not stop on cancel")
    }
    if s.online.Load(){t.Fatal("online flag stale after stop")}
    if wakeWaitDuration(s)!=2*time.Second {t.Fatal("legacy polling not restored")}
}
