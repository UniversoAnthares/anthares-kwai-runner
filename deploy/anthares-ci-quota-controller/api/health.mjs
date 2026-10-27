import { neon } from "@neondatabase/serverless";

export default async function handler(req,res) {
  res.setHeader("Cache-Control","no-store");
  if (req.method !== "GET") return res.status(405).json({ok:false,code:"METHOD_NOT_ALLOWED"});
  if (!process.env.DATABASE_URL) return res.status(503).json({ok:false,code:"DATABASE_UNCONFIGURED"});
  try {
    const sql=neon(process.env.DATABASE_URL);
    const rows=await sql`SELECT current_user AS db_role, to_regclass('public.anthares_ci_quota_attempts')::text AS ledger`;
    if (rows[0]?.db_role !== "anthares_ci_quota_limited" || !rows[0]?.ledger) {
      return res.status(503).json({ok:false,code:"DB_ROLE_OR_SCHEMA_INVALID"});
    }
    return res.status(200).json({ok:true,version:"2026-10-27-cancel-first-v1",
      ledger:"READY",mode:process.env.CI_QUOTA_MODE==="ENABLED"?"ENABLED":"READ_ONLY"});
  } catch {
    return res.status(503).json({ok:false,code:"DATABASE_UNAVAILABLE"});
  }
}
