/**
 * The Kwai posting clock is the independently verified public-video timestamp.
 * DB updated_at describes bookkeeping and MUST NOT anchor publication spacing.
 *
 * Equal slots: remaining video slots plus one trailing safety slot before 23h.
 * This gives constant intervals until the next verified publication or change
 * in the effective queue, while keeping the final start strictly before 23h.
 * Account-specific daily cap and delivery deadlines are hard fences.
 */
export const KWAI_PACING_VERSION='kwai-public-post-proportional-06to23-v3';

const date=v=>v==null?null:new Date(v);
const stamp=v=>v instanceof Date&&Number.isFinite(v.getTime());
export function deriveKwaiPacing(input){
 const {target_key,now,window_open_at,deadline,pending,used,confirmed_today,
        first_confirmed_at,last_confirmed_at,daily_limit=100}=input;
 if(!['kwai:lucasrosalem','kwai:universoanthares'].includes(target_key)
    ||![pending,used,confirmed_today,daily_limit].every(Number.isSafeInteger)
    ||pending<0||used<0||confirmed_today<0||used<confirmed_today
    ||daily_limit<1||daily_limit>100)
    throw Error('KWAI_PACING_INVALID_COUNTERS_OR_ACCOUNT');
 const time=date(now),open=date(window_open_at),end=date(deadline),first=date(first_confirmed_at),last=date(last_confirmed_at);
 if(!stamp(time)||!stamp(open)||!stamp(end)||open>=end)throw Error('KWAI_PACING_CLOCK_UNVERIFIED');
 const remaining=Math.min(pending,Math.max(0,daily_limit-used));
 const result={pacing_version:KWAI_PACING_VERSION,target_key,daily_limit,
    pending,confirmed_today,started_today:used,remaining_today:remaining,
    excess_over_limit:Math.max(0,pending-remaining),
    first_confirmed_at:first?first.toISOString():null,
    last_confirmed_at:last?last.toISOString():null,
    server_now:time.toISOString(),window_open_at:open.toISOString(),deadline_at:end.toISOString(),
    next_due_at:null,interval_seconds:null,status:'IDLE'};
 if(!pending)return result;
 // Production's 06:00 start is a hard server-side fence, including the
 // first publication (which otherwise becomes immediately DUE at midnight).
 if(time<open){result.status='WAIT_OPEN';result.next_due_at=open.toISOString();return result;}
 if(time>=end){result.status='BLOCKED_SAME_DAY_CAPACITY';return result;}
 if(!remaining){result.status='BLOCKED_PLATFORM_LIMIT';return result;}
 if(!!first!==!!last||confirmed_today>0&&!last||confirmed_today===0&&last){
    result.status='BLOCKED_UNVERIFIED_POST_CLOCK';return result;
 }
 if(!last){result.status='DUE';result.next_due_at=result.server_now;return result;}
 if(!stamp(first)||!stamp(last)||first>last||last>time||last>=end){
    result.status='BLOCKED_INVALID_PUBLICATION_CLOCK';return result;
 }
 // N remaining posts occupy N of N+1 identically spaced slots. The last
 // spare slot ends exactly at 23:00, so no actual upload starts at the cutoff.
 const interval=(end.getTime()-last.getTime())/(remaining+1);
 if(!Number.isFinite(interval)||interval<=0){result.status='BLOCKED_INVALID_INTERVAL';return result;}
 const next=new Date(Math.floor(last.getTime()+interval));
 if(next>=end||next<=last){result.status='BLOCKED_INVALID_INTERVAL';return result;}
 result.interval_seconds=interval/1000;
 result.next_due_at=next.toISOString();
 result.status=time>=next?'DUE':'WAIT';
 return result;
}
