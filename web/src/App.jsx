import React, { useState } from 'react'
import Chart, { ZONE_LABELS, SIDE_LABELS } from './Chart.jsx'

const SAMPLE = {
  target: '10',
  sigma: '2',
  readings: '10,11,10,17',
}

export default function App() {
  const [target, setTarget] = useState(SAMPLE.target)
  const [sigma, setSigma] = useState(SAMPLE.sigma)
  const [readings, setReadings] = useState(SAMPLE.readings)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setError(null)
    setData(null)
    setLoading(true)
    try {
      const nums = readings
        .split(/[\s,，、;；]+/)
        .map((s) => s.trim())
        .filter(Boolean)
        .map(Number)
      const payload = {
        target: Number(target),
        sigma: Number(sigma),
        readings: nums,
      }
      const res = await fetch('/api/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const body = await res.json()
      if (!res.ok) {
        const detail = Array.isArray(body.detail)
          ? body.detail
              .map((d) => {
                const loc = d.loc?.slice(1).join('.') || '输入'
                return `${loc}：${d.msg}`
              })
              .join('；')
          : String(body.detail ?? '请求被拒绝')
        setError(`HTTP ${res.status} — ${detail}`)
        return
      }
      setData(body)
    } catch (err) {
      setError(`请求失败：${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const evidenceIdx = new Set(data?.violation?.evidence_indices ?? [])

  return (
    <main className="page">
      <h1>SPC 控制图核验台</h1>
      <p className="sub">
        精确整数判定四条规则：一点越 3σ；三点中两点越同侧 2σ；
        五点中四点越同侧 1σ；八点严格位于中心线同侧。等于边界不算越过。
      </p>

      <form className="form" onSubmit={submit}>
        <label>
          target（整数中心线）
          <input
            data-testid="target"
            type="number"
            step="1"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            required
          />
        </label>
        <label>
          sigma（正整数）
          <input
            data-testid="sigma"
            type="number"
            step="1"
            min="1"
            value={sigma}
            onChange={(e) => setSigma(e.target.value)}
            required
          />
        </label>
        <label className="readings">
          readings（2–200 个整数，逗号/空白分隔）
          <input
            data-testid="readings"
            type="text"
            value={readings}
            onChange={(e) => setReadings(e.target.value)}
            required
          />
        </label>
        <button data-testid="submit" type="submit" disabled={loading}>
          {loading ? '核验中…' : '核验'}
        </button>
      </form>

      {error && (
        <div className="banner error" data-testid="error" role="alert">
          {error}
        </div>
      )}

      {data && (
        <section data-testid="result">
          {data.in_control ? (
            <div className="banner ok" data-testid="verdict">
              过程稳定：四条规则均未命中。
            </div>
          ) : (
            <div className="banner alarm" data-testid="verdict">
              <div>
                <strong>
                  失控 — 规则 {data.violation.rule}（结束下标{' '}
                  {data.violation.end_index}）
                </strong>
                <div className="rule-name">{data.violation.rule_name}</div>
                <div data-testid="evidence-label">
                  证据下标：{data.violation.evidence_indices.join(', ')}
                </div>
              </div>
            </div>
          )}

          <Chart data={data} />

          <table className="grid">
            <thead>
              <tr>
                <th>下标</th>
                <th>读数</th>
                <th>偏差</th>
                <th>侧别</th>
                <th>分区</th>
                <th>证据</th>
              </tr>
            </thead>
            <tbody>
              {data.points.map((p) => (
                <tr
                  key={p.index}
                  className={evidenceIdx.has(p.index) ? 'ev' : ''}
                  data-index={p.index}
                >
                  <td>{p.index}</td>
                  <td>{p.value}</td>
                  <td>{p.delta > 0 ? `+${p.delta}` : p.delta}</td>
                  <td>{SIDE_LABELS[p.side]}</td>
                  <td>{ZONE_LABELS[p.zone]}</td>
                  <td>{evidenceIdx.has(p.index) ? '●' : ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </main>
  )
}
