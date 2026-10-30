import {neon} from "@neondatabase/serverless";
const clients=new WeakMap();
export async function query(env,text,params=[]){let sql=clients.get(env);if(!sql){sql=neon(env.DATABASE_URL);clients.set(env,sql);}return sql.query(text,params,{fullResults:true,arrayMode:false});}
