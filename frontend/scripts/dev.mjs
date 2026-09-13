import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import http from 'node:http'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const backendRoot = resolve(frontendRoot, '..', 'backend')
const python = resolve(backendRoot, '.venv', 'bin', 'python')
const processes = []

function health() {
  return new Promise((resolveHealth) => {
    const request = http.get('http://127.0.0.1:8001/api/health', (response) => {
      let body = ''
      response.on('data', (chunk) => { body += chunk })
      response.on('end', () => resolveHealth(response.statusCode === 200 && body.includes('"status":"ok"')))
    })
    request.on('error', () => resolveHealth(false))
    request.setTimeout(500, () => { request.destroy(); resolveHealth(false) })
  })
}

async function waitForHealth() {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    if (await health()) return
    await new Promise((resolveDelay) => setTimeout(resolveDelay, 250))
  }
  throw new Error('后端未能在 10 秒内通过 http://127.0.0.1:8001/api/health 健康检查。')
}

function start(command, args, cwd) {
  const child = spawn(command, args, { cwd, stdio: 'inherit' })
  processes.push(child)
  return child
}

function stop(exitCode = 0) {
  for (const child of processes) child.kill('SIGTERM')
  process.exit(exitCode)
}

for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => stop())

try {
  if (await health()) {
    console.log('AIPedia Hub API 已在 8001 就绪，复用现有服务。')
  } else {
    console.log('启动 AIPedia Hub API：8001')
    const backend = existsSync(python)
      ? start(python, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8001'], backendRoot)
      : start('uv', ['run', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8001'], backendRoot)
    backend.once('exit', (code) => { if (code !== 0) stop(code ?? 1) })
    await waitForHealth()
  }

  console.log('启动 AIPedia Hub 前端：5173')
  const frontend = start('pnpm', ['exec', 'vite', '--host', '127.0.0.1', '--port', '5173', '--strictPort'], frontendRoot)
  frontend.once('exit', (code) => stop(code ?? 0))
} catch (error) {
  console.error(error instanceof Error ? error.message : error)
  stop(1)
}
