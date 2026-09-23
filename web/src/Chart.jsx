import React from 'react'

const ZONE_LABELS = {
  beyond_3sigma: '> 3σ（区外）',
  zone_a_2_3sigma: 'A 区 (2σ, 3σ]',
  zone_b_1_2sigma: 'B 区 (1σ, 2σ]',
  zone_c_0_1sigma: 'C 区 (0, 1σ]',
  center: '中心线',
}

const SIDE_LABELS = { above: '上侧', below: '下侧', on: '线上' }

// Band fill colors, symmetric above/below.
const BAND_FILL = {
  beyond: '#fde2e1',
  a: '#fdecd4',
  b: '#fdf7d4',
  c: '#e5f5d9',
}

const WIDTH = 920
const HEIGHT = 440
const M = { top: 30, right: 40, bottom: 56, left: 64 }

export default function Chart({ data }) {
  const { points, limits, violation } = data
  const evidenceIdx = new Set(violation?.evidence_indices ?? [])

  const allVals = points.map((p) => p.value)
  const rawMin = Math.min(...allVals, limits.minus_3sigma)
  const rawMax = Math.max(...allVals, limits.plus_3sigma)
  // Integer padding so out-of-band points stay visible.
  const span = Math.max(rawMax - rawMin, 1)
  const minV = rawMin - Math.max(1, Math.round(span * 0.08))
  const maxV = rawMax + Math.max(1, Math.round(span * 0.08))

  const plotW = WIDTH - M.left - M.right
  const plotH = HEIGHT - M.top - M.bottom
  const x = (i) => M.left + (points.length === 1
    ? plotW / 2
    : (i / (points.length - 1)) * plotW)
  const y = (v) => M.top + ((maxV - v) / (maxV - minV)) * plotH

  const bands = [
    { from: maxV, to: limits.plus_3sigma, fill: BAND_FILL.beyond, key: 'b3+' },
    { from: limits.plus_3sigma, to: limits.plus_2sigma, fill: BAND_FILL.a, key: 'a+' },
    { from: limits.plus_2sigma, to: limits.plus_1sigma, fill: BAND_FILL.b, key: 'b+' },
    { from: limits.plus_1sigma, to: limits.center, fill: BAND_FILL.c, key: 'c+' },
    { from: limits.center, to: limits.minus_1sigma, fill: BAND_FILL.c, key: 'c-' },
    { from: limits.minus_1sigma, to: limits.minus_2sigma, fill: BAND_FILL.b, key: 'b-' },
    { from: limits.minus_2sigma, to: limits.minus_3sigma, fill: BAND_FILL.a, key: 'a-' },
    { from: limits.minus_3sigma, to: minV, fill: BAND_FILL.beyond, key: 'b3-' },
  ]

  const lines = [
    { v: limits.plus_3sigma, label: '+3σ', dash: '6 4', color: '#c0392b' },
    { v: limits.plus_2sigma, label: '+2σ', dash: '6 4', color: '#e67e22' },
    { v: limits.plus_1sigma, label: '+1σ', dash: '4 4', color: '#b7950b' },
    { v: limits.center, label: `CL=${limits.center}`, dash: null, color: '#1b4f72' },
    { v: limits.minus_1sigma, label: '-1σ', dash: '4 4', color: '#b7950b' },
    { v: limits.minus_2sigma, label: '-2σ', dash: '6 4', color: '#e67e22' },
    { v: limits.minus_3sigma, label: '-3σ', dash: '6 4', color: '#c0392b' },
  ]

  const polyline = points.map((p, i) => `${x(i)},${y(p.value)}`).join(' ')
  const tickStep = Math.max(1, Math.ceil(points.length / 20))

  return (
    <svg
      className="chart"
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      role="img"
      aria-label="控制图：读数、中心线与 σ 分区"
    >
      {/* Zone bands */}
      {bands.map((b) => (
        <rect
          key={b.key}
          x={M.left}
          y={y(b.from)}
          width={plotW}
          height={Math.max(0, y(b.to) - y(b.from))}
          fill={b.fill}
        />
      ))}

      {/* Boundary / center lines */}
      {lines.map((l) => (
        <g key={l.label}>
          <line
            x1={M.left}
            x2={M.left + plotW}
            y1={y(l.v)}
            y2={y(l.v)}
            stroke={l.color}
            strokeWidth={l.dash ? 1.4 : 2}
            strokeDasharray={l.dash ?? undefined}
          />
          <text x={M.left + plotW + 4} y={y(l.v) + 4} fontSize="11" fill={l.color}>
            {l.label}
          </text>
        </g>
      ))}

      {/* Reading polyline */}
      <polyline
        points={polyline}
        fill="none"
        stroke="#5d6d7e"
        strokeWidth="1.2"
      />

      {/* Readings */}
      {points.map((p) => {
        const hit = evidenceIdx.has(p.index)
        return (
          <g key={p.index}>
            {hit && (
              <circle cx={x(p.index)} cy={y(p.value)} r="9"
                fill="none" stroke="#c0392b" strokeWidth="2" />
            )}
            <circle
              cx={x(p.index)}
              cy={y(p.value)}
              r={hit ? 5 : 3.4}
              fill={hit ? '#c0392b' : '#2874a6'}
              stroke="#fff"
              strokeWidth="0.8"
            >
              <title>{`#${p.index} 值=${p.value} ${SIDE_LABELS[p.side]} ${ZONE_LABELS[p.zone]}`}</title>
            </circle>
            {p.index % tickStep === 0 && (
              <text x={x(p.index)} y={M.top + plotH + 18}
                fontSize="10" fill="#555" textAnchor="middle">
                {p.index}
              </text>
            )}
          </g>
        )
      })}

      <text x={M.left} y={HEIGHT - 8} fontSize="11" fill="#555">
        下标（0 起）
      </text>
      {violation && (
        <text x={M.left} y={18} fontSize="13" fill="#c0392b" fontWeight="bold">
          {`失控证据：规则 ${violation.rule}，结束下标 ${violation.end_index}，证据 ${violation.evidence_indices.join(', ')}`}
        </text>
      )}
    </svg>
  )
}

export { ZONE_LABELS, SIDE_LABELS }
