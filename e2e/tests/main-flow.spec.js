import { test, expect } from '@playwright/test'

// The only browser verification: one happy-path run end to end.
test.describe.configure({ mode: 'serial' })

test('主流程：提交读数 -> 唯一失控证据在 SVG 与表格中一致呈现', async ({ page }) => {
  await page.goto('/')

  await page.getByTestId('target').fill('10')
  await page.getByTestId('sigma').fill('2')
  await page.getByTestId('readings').fill('10,11,10,17')
  await page.getByTestId('submit').click()

  // Verdict: rule 1 at end index 3, single evidence point.
  await expect(page.getByTestId('verdict')).toContainText('规则 1')
  await expect(page.getByTestId('verdict')).toContainText('结束下标 3')
  await expect(page.getByTestId('evidence-label')).toHaveText('证据下标：3')

  // Table: exactly one row is evidence, showing the beyond-3sigma zone.
  const evRows = page.locator('table.grid tr.ev')
  await expect(evRows).toHaveCount(1)
  const row = page.locator('table.grid tr[data-index="3"]')
  await expect(row).toHaveClass(/ev/)
  await expect(row).toContainText('17')
  await expect(row).toContainText('> 3σ')

  // SVG: one highlighted point (halo circle) and the chart annotation.
  const svg = page.locator('svg.chart')
  await expect(svg).toBeVisible()
  await expect(svg.locator('circle[r="9"]')).toHaveCount(1)
  await expect(svg).toContainText('失控证据：规则 1，结束下标 3，证据 3')

  // Table and SVG share the same response: 4 rows / 4 reading points.
  await expect(page.locator('table.grid tbody tr')).toHaveCount(4)
  await expect(svg.locator('circle[fill="#2874a6"], circle[fill="#c0392b"]'))
    .toHaveCount(4)
})
