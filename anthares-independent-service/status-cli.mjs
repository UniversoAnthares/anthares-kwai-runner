import {readFile} from "node:fs/promises";
import {fileURLToPath} from "node:url";
import {dirname,join} from "node:path";
import {snapshot} from "./handler.mjs";
try {
  if(process.argv.length!==2)throw new Error("unsupported_arguments");
  const config=JSON.parse(await readFile(join(dirname(fileURLToPath(import.meta.url)),"config.json"),"utf8"));
  const data=await snapshot(config);
  process.stdout.write(JSON.stringify({...data,client:"anthares-operator-cli",
    auth_boundary:"owner OS session and private file permissions"})+"\n");
}catch {
  process.stdout.write(JSON.stringify({ok:false,error:"operator_diagnostic_unavailable"})+"\n");
  process.exitCode=1;
}
