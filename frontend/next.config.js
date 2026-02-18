/** @type {import('next').NextConfig} */
const path = require('path')
const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const nextConfig = {
  webpack(config) {
    // Force webpack to use the CJS build of VexFlow instead of the ESM build.
    // The ESM entry point causes a chunk-loading failure in Next.js App Router
    // because webpack tries to split it into a separate async chunk that 404s.
    config.resolve.alias['vexflow'] = path.resolve(
      __dirname,
      'node_modules/vexflow/build/cjs/vexflow.js'
    )
    return config
  },
  async rewrites() {
    // Proxy all /api/py/* paths to the FastAPI backend, EXCEPT the SSE status
    // endpoint which is handled by the Next.js streaming API route so that
    // server-sent events are not buffered by the rewrite proxy.
    return [
      { source: '/api/py/health', destination: `${BACKEND}/api/py/health` },
      { source: '/api/py/transcribe/url', destination: `${BACKEND}/api/py/transcribe/url` },
      { source: '/api/py/transcribe/upload', destination: `${BACKEND}/api/py/transcribe/upload` },
      { source: '/api/py/transcribe/result/:jobId', destination: `${BACKEND}/api/py/transcribe/result/:jobId` },
    ]
  },
}

module.exports = nextConfig
