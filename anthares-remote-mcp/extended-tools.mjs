import { z } from 'zod';

export function registerExtendedTools(server, { execute, text, defaultDevice }) {
  server.registerTool('process_start', {
    description: 'Start an executable on the authorized Windows device.',
    inputSchema: {
      path: z.string().min(1),
      args: z.string().default(''),
      device_id: z.string().default(defaultDevice),
    },
  }, async ({ path, args, device_id }) => text(await execute('process_start', { path, args }, 30, device_id)));

  server.registerTool('process_kill', {
    description: 'Terminate a process by PID on the authorized Windows device.',
    inputSchema: {
      pid: z.number().int().positive(),
      device_id: z.string().default(defaultDevice),
    },
  }, async ({ pid, device_id }) => text(await execute('process_kill', { pid: String(pid) }, 30, device_id)));

  server.registerTool('service_status', {
    description: 'Read the status of a Windows service.',
    inputSchema: {
      name: z.string().min(1),
      device_id: z.string().default(defaultDevice),
    },
  }, async ({ name, device_id }) => text(await execute('service_status', { name }, 30, device_id)));

  server.registerTool('service_start', {
    description: 'Start an authorized Windows service.',
    inputSchema: {
      name: z.string().min(1),
      device_id: z.string().default(defaultDevice),
    },
  }, async ({ name, device_id }) => text(await execute('service_start', { name }, 45, device_id)));

  server.registerTool('service_stop', {
    description: 'Stop an authorized Windows service.',
    inputSchema: {
      name: z.string().min(1),
      device_id: z.string().default(defaultDevice),
    },
  }, async ({ name, device_id }) => text(await execute('service_stop', { name }, 45, device_id)));

  server.registerTool('file_mkdir', {
    description: 'Create a directory inside an agent allowlisted root.',
    inputSchema: {
      path: z.string().min(1),
      device_id: z.string().default(defaultDevice),
    },
  }, async ({ path, device_id }) => text(await execute('file_mkdir', { path }, 30, device_id)));

  server.registerTool('file_remove', {
    description: 'Remove a file or directory inside an agent allowlisted root.',
    inputSchema: {
      path: z.string().min(1),
      recursive: z.boolean().default(false),
      device_id: z.string().default(defaultDevice),
    },
  }, async ({ path, recursive, device_id }) => text(await execute('file_remove', { path, recursive: recursive ? '1' : '0' }, 30, device_id)));

  server.registerTool('file_rename', {
    description: 'Rename or move a path between locations allowed by the agent.',
    inputSchema: {
      src: z.string().min(1),
      dst: z.string().min(1),
      device_id: z.string().default(defaultDevice),
    },
  }, async ({ src, dst, device_id }) => text(await execute('file_rename', { src, dst }, 30, device_id)));

  server.registerTool('file_copy', {
    description: 'Copy a file between locations allowed by the agent.',
    inputSchema: {
      src: z.string().min(1),
      dst: z.string().min(1),
      device_id: z.string().default(defaultDevice),
    },
  }, async ({ src, dst, device_id }) => text(await execute('file_copy', { src, dst }, 45, device_id)));

  server.registerTool('file_sha256', {
    description: 'Calculate the SHA-256 digest of a file inside an agent allowlisted root.',
    inputSchema: {
      path: z.string().min(1),
      device_id: z.string().default(defaultDevice),
    },
  }, async ({ path, device_id }) => text(await execute('file_sha256', { path }, 45, device_id)));

  server.registerTool('file_write_atomic', {
    description: 'Atomically replace a file from base64 data inside an agent allowlisted root.',
    inputSchema: {
      path: z.string().min(1),
      base64: z.string(),
      device_id: z.string().default(defaultDevice),
    },
  }, async ({ path, base64, device_id }) => text(await execute('file_write_atomic', { path, base64 }, 45, device_id)));
}
