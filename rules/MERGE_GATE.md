# MERGE_GATE

所有优化分支 merge 到 `main` 前必须逐项执行本验收。禁止带本分支引入的 FAIL merge。

## 执行范围

- 目标分支与 `main` 的 diff。
- 受影响仓库的线上 URL、sitemap、canonical、hreflang。
- Gate 条目按改动类型适用。未触及的系统记 `N/A：本次未触及`，不要求人工补测。
- 如 diff 触及登录、鉴权、支付、KV/R2、Worker/API、构建产物，必须执行对应专项验收。
- 区分「本分支引入的回归」与「存量线上问题」：
  - 本分支引入的回归 = FAIL，禁止 merge。
  - 存量线上问题不阻塞本分支 merge，但必须自动记录到主站仓库 `audit/ISSUES.md`，包含发现日期、影响范围、证据、后续动作。

## 1. 兼容性

- 仅当 diff 触及付费产品代码、登录、鉴权、会员状态、题库/词库读取、progress/kiso/pro 路由、Worker/API 或相关构建产物时执行。
- 用现有老用户账号各 1 个：Pro、kiso、progress 付费账号。
- 走核心路径：登录 → 取题/取词 → 答题/建岛 → 查看付费内容。
- 任一 401、404、空数据、付费内容不可见 = FAIL。
- 未触及付费产品代码的分支，自动记 `N/A：本次未触及付费产品代码`。
- 触及但无账号或无法自动登录时，标注：`需 Wan 人工确认`，并写明只需确认哪些账号/路径。

## 2. 鉴权与泄漏

- 仅当 diff 触及鉴权、API、题库/词库、会员逻辑或构建产物时执行免费账号 API 拒绝测试。
- 免费账号请求 `/api/questions` 的 Pro 内容必须被拒。
- 所有前端代码或构建产物 grep 不到答案字段和任何 secret。
- 重点 grep：`answer`、`correctAnswer`、`correct_answer`、`secret`、`apiKey`、`token`、`password`、`client_secret`。
- 若命中是普通展示文案，报告中注明为非泄漏命中。

## 3. URL

- 本分支移动/删除的 URL 必须有 301 到新 URL。
- 受影响站点 sitemap 全量 curl。
- 本分支新增或修改的 sitemap URL 返回 4xx/5xx = FAIL。
- 未被本分支修改、但线上已存在的 sitemap URL 返回 4xx/5xx，记为存量线上问题，写入 `audit/ISSUES.md`，不阻塞当前分支。

## 4. SEO

- 受影响站点的 `sitemap.xml` 与实际页面一致。
- 每语言至少抽 1 页验证：
  - 自指 canonical 正确。
  - hreflang 互指完整。
  - `x-default` 指向既定默认页。
- 本分支新增或修改的多语言 sitemap URL 必须线上可访问。存量不可访问 URL 写入 `audit/ISSUES.md`。

## 5. Contact

- 面向用户的页面必须至少命中 1 次标准 WhatsApp 正链：wa.me/817089523968。
- 跳转页、错误页、纯重定向兼容页豁免。
- 若删除占位联系方式但未补标准正链 = FAIL。

## 6. 支付

- PayPal plan ID、IAP 产品 ID、webhook 路由必须与 `main` 完全一致。
- 若本次需求就是支付变更，报告中单独说明变更点、测试账号、回滚方式。
- 未触及支付文件时，标注 `N/A：diff 未触及支付`。

## 7. KV/R2

- 如有 key 结构或 bucket 路径改动，必须附迁移脚本和回滚步骤。
- 必须用老数据实测读取。
- 未触及 KV/R2 文件时，标注 `N/A：diff 未触及 KV/R2`。

## 8. 报告格式

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

## 9. Merge 规则

- `ALL PASS` 或 `PASS + N/A + 已记录存量问题` 才能 merge。
- 有本分支引入的 `FAIL` 时禁止 merge。
- `需 Wan 人工确认` 不等于 PASS；必须由 Wan 确认后再更新报告结论。
