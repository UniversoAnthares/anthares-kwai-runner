package main

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

const testListenerToken = "TEST_ONLY_LISTENER_NOT_A_DEVICE_OR_PUBLISHER_000000"

func TestWakeFlagAndIdentityFailClosed(t *testing.T) {
	base := Config{ControlURL: "https://anthares-remote-primary.vercel.app",
		DeviceToken: "test-only-device-token", DeviceID: araWakeDevice}
	t.Setenv("ANTHARES_WAKE_LISTENER_TOKEN", testListenerToken)
	if startWakeSubscriber(base) != nil { t.Fatal("default off") }
	base.WakeEnabled = true
	base.DeviceID = "OTHER"
	if startWakeSubscriber(base) != nil { t.Fatal("foreign device") }
	base.DeviceID = araWakeDevice
	base.ControlURL = ""
	if startWakeSubscriber(base) != nil { t.Fatal("queue only") }
	base.ControlURL = "https://anthares-remote-primary.vercel.app"
	for _, token := range []string{"", "short", testListenerToken+"\r", base.DeviceToken} {
		t.Setenv("ANTHARES_WAKE_LISTENER_TOKEN", token)
		if startWakeSubscriber(base) != nil { t.Fatal("invalid/shared credential") }
	}
	if araWakeEndpoint != "https://anthares.us/ara-notify/index.php" {
		t.Fatal("unexpected trusted destination")
	}
}

func TestWakeIdleReconciliationPolicy(t *testing.T) {
	if wakeWaitDuration(nil) != 2*time.Second { t.Fatal("disabled fallback") }
	s := newWakeSubscriber()
	if wakeWaitDuration(s) != 2*time.Second { t.Fatal("offline fallback") }
	s.setOnline(true)
	<-s.events
	if wakeWaitDuration(s) != 12*time.Second { t.Fatal("safety scan") }
	s.signal()
	s.signal()
	if len(s.events) != 1 { t.Fatal("not coalesced") }
	start := time.Now()
	s.waitAfterEmpty()
	if time.Since(start) > 200*time.Millisecond { t.Fatal("wake did not bypass timer") }
	s.setOnline(false)
	<-s.events
	if wakeWaitDuration(s) != 2*time.Second { t.Fatal("failure fallback") }
}

func TestWakeReceiptsOnlyContainHints(t *testing.T) {
	for _, tc := range []struct{raw string; health, valid bool}{
		{`{"ok":true,"protocol":"ara-wake-v1","sequence":0,"role":"listener"}`,true,true},
		{`{"ok":true,"protocol":"ara-wake-v1","sequence":2,"wake":true}`,false,true},
		{`{"ok":true,"protocol":"ara-wake-v1","sequence":2,"wake":false}`,false,true},
		{`{"ok":false,"protocol":"ara-wake-v1","sequence":2,"wake":true}`,false,false},
		{`{"ok":true,"protocol":"other","sequence":2,"wake":true}`,false,false},
		{`{"ok":true,"protocol":"ara-wake-v1","sequence":-1,"wake":true}`,false,false},
		{`{"ok":true,"protocol":"ara-wake-v1","sequence":1.5,"wake":true}`,false,false},
		{`{"ok":true,"protocol":"ara-wake-v1","sequence":1000000000000000000,"wake":true}`,false,false},
		{`{"ok":true,"protocol":"ara-wake-v1","sequence":null,"wake":false}`,false,false},
		{`{"ok":true,"protocol":"ara-wake-v1","sequence":0,"wake":null}`,false,false},
		{`{"ok":true,"protocol":"ara-wake-v1","sequence":2,"role":"publisher"}`,true,false},
		{`{"ok":true,"protocol":"ara-wake-v1","sequence":2,"wake":true,"job_id":"evil"}`,false,false},
		{`{"ok":true,"protocol":"ara-wake-v1","sequence":2,"command":"evil"}`,false,false},
		{`{"ok":false,"ok":true,"protocol":"ara-wake-v1","sequence":2,"wake":true}`,false,false},
		{strings.Repeat("x",513),false,false},
		{"not json",false,false},
	} {
		_,_,err := parseWakeReceipt([]byte(tc.raw),tc.health)
		if (err == nil) != tc.valid { t.Fatalf("wrong acceptance: %s: %v",tc.raw,err) }
	}
}

func TestHostingerSubscriptionHealthWakeIdleAndCancellation(t *testing.T) {
	var waits atomic.Int32
	ctx,cancel := context.WithCancel(context.Background())
	defer cancel()
	var server *httptest.Server
	server = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){
		if r.Method != "GET" || r.Header.Get("X-Anthares-Notify-Key") != testListenerToken ||
			r.Header.Get("Authorization") != "" || r.URL.Query().Get("device_id") != araWakeDevice {
			t.Error("wrong broker auth/protocol"); w.WriteHeader(401); return
		}
		w.Header().Set("Content-Type","application/json")
		if r.URL.Query().Get("action") == "health" {
			fmt.Fprint(w,`{"ok":true,"protocol":"ara-wake-v1","sequence":7,"role":"listener"}`)
			return
		}
		if r.URL.Query().Get("action") != "wait" || r.URL.Query().Get("seconds") != "20" {
			t.Error("not a bounded long poll")
		}
		n := waits.Add(1)
		if n == 1 {
			if r.URL.Query().Get("since") != "7" { t.Error("initial cursor lost") }
			fmt.Fprint(w,`{"ok":true,"protocol":"ara-wake-v1","sequence":8,"wake":true}`)
		} else if n == 2 {
			if r.URL.Query().Get("since") != "8" { t.Error("cursor not advanced") }
			fmt.Fprint(w,`{"ok":true,"protocol":"ara-wake-v1","sequence":8,"wake":false}`)
		} else { <-r.Context().Done() }
	}))
	defer server.Close()
	s := newWakeSubscriber()
	done := make(chan error,1)
	go func(){ done <- s.runLongPoll(ctx,server.Client(),server.URL,testListenerToken) }()
	deadline := time.After(2*time.Second)
	for waits.Load() < 3 {
		select { case <-deadline:t.Fatal("did not reach idle wait"); default:time.Sleep(time.Millisecond) }
	}
	if !s.online.Load() || len(s.events) != 1 { t.Fatal("no ready/wake coalesced hint") }
	cancel()
	select { case <-done: case <-time.After(time.Second):t.Fatal("cancel leaked request") }
	if s.online.Load() || wakeWaitDuration(s) != 2*time.Second { t.Fatal("no fallback") }
}

func TestBrokerErrorsRestoreFallbackAndQuotaStops(t *testing.T) {
	for _,status := range []int{401,402,403,429,503} {
		t.Run(fmt.Sprint(status),func(t *testing.T){
			var calls atomic.Int32
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){
				calls.Add(1);w.WriteHeader(status)
			}))
			defer server.Close()
			s:=newWakeSubscriber()
			ctx,cancel:=context.WithTimeout(context.Background(),time.Second)
			defer cancel()
			if status == 503 {
				err:=s.runLongPoll(ctx,server.Client(),server.URL,testListenerToken)
				if err==nil || terminalWakeError(err) { t.Fatal("wrong transient failure") }
			} else {
				done:=make(chan struct{})
				go func(){s.run(ctx,server.Client(),server.URL,testListenerToken);close(done)}()
				select{case <-done:case <-ctx.Done():t.Fatal("quota/auth attempt kept alive")}
				if calls.Load()!=1 {t.Fatal("repeated rejected request")}
			}
			if s.online.Load() || wakeWaitDuration(s)!=2*time.Second {t.Fatal("fallback not active")}
		})
	}
}

func TestWaitRejectsRegressedOrInconsistentSequence(t *testing.T) {
	for _,body:=range []string{
		`{"ok":true,"protocol":"ara-wake-v1","sequence":1,"wake":false}`,
		`{"ok":true,"protocol":"ara-wake-v1","sequence":2,"wake":true}`,
		`{"ok":true,"protocol":"ara-wake-v1","sequence":3,"wake":false}`,
	} {
		server:=httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){fmt.Fprint(w,body)}))
		_,_,err:=fetchWakeReceipt(context.Background(),server.Client(),server.URL,testListenerToken,false,2)
		server.Close()
		if err==nil {t.Fatal("inconsistent cursor accepted")}
	}
}

func TestRedirectNeverForwardsListenerCredential(t *testing.T) {
	var redirected atomic.Int32
	target:=httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){redirected.Add(1)}))
	defer target.Close()
	source:=httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){http.Redirect(w,r,target.URL,302)}))
	defer source.Close()
	client:=&http.Client{CheckRedirect:func(*http.Request,[]*http.Request)error{return http.ErrUseLastResponse}}
	_,_,err:=fetchWakeReceipt(context.Background(),client,source.URL,testListenerToken,true,0)
	if err==nil || redirected.Load()!=0 {t.Fatal("credential followed redirect")}
}

func TestWakeReconnectBackoffIsBounded(t *testing.T) {
	for _,n:=range []int{-1,0,1,4,100} {
		d:=wakeReconnectDelay(n,func(int64)int64{return 0})
		if d<2*time.Second || d>30*time.Second {t.Fatal("bad backoff")}
	}
}
