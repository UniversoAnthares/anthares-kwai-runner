export const EXTERNAL_DEVICE = "ANTHARES-HOSTINGER";
export const EXTERNAL_PATH = "/anthares-independent/status.php";
export const EXTERNAL_URL = "https://anthares.us" + EXTERNAL_PATH;
const allowed = new Set(["system_info", "session_status", "capabilities"]);
export async function externalReadOnly(name, {sign, fetchImpl=fetch}={}) {
  if (!allowed.has(name)) throw new Error("external_executor_operation_not_supported");
  const signature = await sign("GET", EXTERNAL_PATH, "");
  const response = await fetchImpl(EXTERNAL_URL, {
    method:"GET", redirect:"manual", signal:AbortSignal.timeout(10000),
    headers:{"X-ARA-Signer":"anthares-remote-mcp","X-ARA-Timestamp":signature.timestamp,"X-ARA-Signature":signature.signature}
  });
  if (response.status===401 || response.status===403) throw new Error("external_executor_authorization_denied");
  if (!response.ok) throw new Error("external_executor_unavailable_http_"+response.status);
  const d = await response.json();
  if (d?.ok!==true || d.executor_id!==EXTERNAL_DEVICE || d.read_only!==true ||
      d.provider!=="hostinger" || !Array.isArray(d.supported_operations) ||
      d.supported_operations.some(x=>!allowed.has(x))) throw new Error("external_executor_invalid_contract");
  const common={ok:true,connected:true,device_id:EXTERNAL_DEVICE,backend:"hostinger-read-only",
    read_only:true,job_execution:"not_supported",observed_at:d.observed_at,
    capabilities:["system_info","session_status","capabilities"]};
  if(name==="capabilities") return {...common,protocol:"anthares-external-readonly/1.0",
    client_access:{granted_scopes:["ara.read"],remote_execution:"not_supported_on_this_executor"}};
  if(name==="session_status") return {...common,queue_state:"not_applicable_for_read_only_diagnostics",
    queued:null,leased:null,uncertain:null};
  return {...common,execution_site:"Hostinger",runtime:d.runtime,host_observations:d.host_observations,
    services:d.services,capacity_limits:"not_verified",inference:"not_tested"};
}
