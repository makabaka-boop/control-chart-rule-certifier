# SPC 控制图核验台

从空仓库建立的轻量全栈核验台，供过程工程师复核控制图。单点未越过 3σ
不等于过程稳定——本台按固定证据精确判定四条规则，并给出**唯一可复核的
失控证据**，表格与 SVG 共用同一响应。

## 判定规则（精确整数比较，等于边界不算越过）

| 规则 | 判据 |
|----|----|
| R1 | 一点严格越过 3σ（`|x − target| > 3·sigma`） |
| R2 | 连续三点中至少两点严格越过**同侧** 2σ |
| R3 | 连续五点中至少四点严格越过**同侧** 1σ |
| R4 | 连续八点严格位于中心线同侧（恰在中心线上即打断） |

分区为半开区间：`|Δ| > 3σ` 为区外；`2σ < |Δ| ≤ 3σ` 为 A 区；
`1σ < |Δ| ≤ 2σ` 为 B 区；`0 < |Δ| ≤ 1σ` 为 C 区；`|Δ| = 0` 为中心线。

命中多个规则时，裁决键依次为：

1. **结束下标最小**（窗口右端，0 基，含）；
2. **规则顺序** R1 → R2 → R3 → R4；
3. **证据下标序列字典序最小**。

响应包含：首个违规的规则与结束下标、证据点、以及**每个点**的侧别
（above/below/on）与分区。

## 接口

`POST /api/evaluate`

```json
{ "target": 10, "sigma": 2, "readings": [10, 11, 10, 17] }
```

- `target`：整数；`sigma`：正整数；`readings`：2–200 个整数。
- 未知字段、`sigma ≤ 0`、读数数量越界、类型不符一律 **422**。

响应骨架：

```json
{
  "target": 10, "sigma": 2, "in_control": false,
  "violation": {
    "rule": 1, "rule_name": "一点严格越过 3σ",
    "end_index": 3, "evidence_indices": [3],
    "evidence": [ { "index": 3, "value": 17, "delta": 7,
                    "side": "above", "zone": "beyond_3sigma" } ]
  },
  "points": [ /* 每点 index/value/delta/side/zone */ ],
  "limits": { "center": 10, "plus_1sigma": 12, "minus_1sigma": 8,
              "plus_2sigma": 14, "minus_2sigma": 6,
              "plus_3sigma": 16, "minus_3sigma": 4 }
}
```

## 运行（Docker Compose）

```bash
docker compose up --build
# web: http://localhost:8080 （nginx 托管静态产物并代理 /api）
# api: http://localhost:8000 （/docs 可用）
```

## 本地开发

```bash
# api
pip install -r api/requirements.txt
uvicorn api.main:app --reload --port 8000

# web（vite 已把 /api 代理到 8000）
cd web && npm install && npm run dev   # http://localhost:5173
```

## 测试

```bash
# 后端：朴素窗口扫描对拍（3000 组随机用例）+ 手算边界/裁决 + 422
python3 -m pytest

# 浏览器：全项目仅这一个主流程用例
cd e2e && npm install && npx playwright install chromium && npx playwright test
```

`tests/test_rules.py` 中的 `naive_first` 是与引擎独立编写的朴素嵌套循环
扫描器，随机对拍验证结束下标、规则号、证据序列三者完全一致。

## 目录

```
api/                 FastAPI：models 校验(422) + rules.py 规则引擎
web/                 React + Vite：SVG 控制图（读数/中心线/分区）+ 证据表格
e2e/                 Playwright 单一主流程验证
docker-compose.yml   web(nginx) + api 两服务
```
