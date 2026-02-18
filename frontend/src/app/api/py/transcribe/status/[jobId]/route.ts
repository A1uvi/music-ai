import { NextRequest } from 'next/server'
import http from 'http'

export const dynamic = 'force-dynamic'
export const runtime = 'nodejs'

const BACKEND_HOST = 'localhost'
const BACKEND_PORT = 8000

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params
  const path = `/api/py/transcribe/status/${jobId}`

  const stream = new ReadableStream({
    start(controller) {
      const req = http.request(
        {
          hostname: BACKEND_HOST,
          port: BACKEND_PORT,
          path,
          method: 'GET',
          headers: {
            Accept: 'text/event-stream',
            'Cache-Control': 'no-cache',
          },
        },
        (res) => {
          res.on('data', (chunk: Buffer) => {
            controller.enqueue(chunk)
          })
          res.on('end', () => {
            controller.close()
          })
          res.on('error', (err) => {
            controller.error(err)
          })
        }
      )

      req.on('error', (err) => {
        controller.error(err)
      })

      req.end()
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
  })
}
