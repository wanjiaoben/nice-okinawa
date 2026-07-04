# MERGE_GATE

所有优化分支 merge 到 `main` 前必须逐项执行本验收。禁止带 FAIL merge。

## 执行范围

- 目标分支与 `main` 的 diff。
- 受影响仓库的线上 URL、sitemap、canonical、hreflang。
- 如 diff 触及登录、鉴权、支付、KV/R2、Worker/API、构建产物，必须执行对应专项验收。

## 1. 兼容性

- 用现有老用户账号各 1 个：Pro、kiso、progress 付费账号。
- 走核心路径：登录 → 取题/取词 → 答题/建岛 → 查看付费内容。
- 任一 401、404、空数据、付费内容不可见 = FAIL。
- 无账号或无法自动登录时，标注：`需 Wan 人工确认`，并写明只需确认哪些账号/路径。

## 2. 鉴权与泄漏

- 免费账号请求 `/api/questions` 的 Pro 内容必须被拒。
- 前端构建产物 grep 不到答案字段和任何 secret。
- 重点 grep：`answer`、`correctAnswer`、`correct_answer`、`secret`、`apiKey`、`token`、`password`、`client_secret`。
- 若命中是普通展示文案，报告中注明为非泄漏命中。

## 3. URL

- 被移动/删除的 URL 必须有 301 到新 URL。
- sitemap 全量 curl，0 个 4xx/5xx。
- 任一 sitemap URL 返回 4xx/5xx = FAIL。

## 4. SEO

- `sitemap.xml` 与实际页面一致。
- 每语言至少抽 1 页验证：
  - 自指 canonical 正确。
  - hreflang 互指完整。
  - `x-default` 指向既定默认页。
- 多语言 sitemap 中列出的语言页必须线上可访问。

## 5. 支付

- PayPal plan ID、IAP 产品 ID、webhook 路由必须与 `main` 完全一致。
- 若本次需求就是支付变更，报告中单独说明变更点、测试账号、回滚方式。
- 未触及支付文件时，标注 `N/A：diff 未触及支付`。

## 6. KV/R2

- 如有 key 结构或 bucket 路径改动，必须附迁移脚本和回滚步骤。
- 必须用老数据实测读取。
- 未触及 KV/R2 文件时，标注 `N/A：diff 未触及 KV/R2`。

## 7. 报告格式

只报结论和失败项：

```txt
MERGE GATE: ALL PASS 可 merge
```

或：

```txt
MERGE GATE: FAIL 禁止 merge
- FAIL URL: activity sitemap 中 /en/、/ja/ 返回 404
- 需 Wan 人工确认: Pro/kiso/progress 老账号核心路径
```

## 8. Merge 规则

- `ALL PASS` 才能 merge。
- 有 `FAIL` 时禁止 merge。
- `需 Wan 人工确认` 不等于 PASS；必须由 Wan 确认后再更新报告结论。
