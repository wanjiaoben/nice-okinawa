# M1104-02 · A功能 / product · 首页语言修复与视觉探索

## 改了什么
- 视觉探索候选，等待任务 4 的视觉规定讨论后定稿。不得按本候选自动合并或生产发布。
- 三个首屏业务入口：旅游、语言教室、出口贸易；四语常驻选择器；修复浮潜附属链接占据网格的问题。
- 简中母版及繁中、日文、英文对齐文案。浏览器语言识别与手动保存遵循共享 resolver。
- Review 候选入口使用 `?lang=zh-Hans`；普通访客遵循 saved > URL > browser。支持列表以外的语言回退英文。无 JS 时提供完整简中 HTML。
- 新闻三卡保留，交通新闻标记 `TRAVEL-TRANSPORT-20261104-01` 保留。缺少对应语言的文章明确标注原文语言：培训日文、台风指南英文、旅游统计简中入口指向既有繁中、交通指南繁中入口指向既有简中。

## 修改文件
- `index.html`、`assets/home.css`、`assets/js/home.js`、`assets/js/home-copy.js`。
- `content/home/copy.json` 为简中母版及派生覆盖层（每行固定 zh-Hans / zh-Hant / ja / en）；`scripts/build_home.py` 生成首页与词典。
- `assets/js/ui-language-resolver.js` 原样采用 Mini 上 bjt 的既有共享实现；无产品私改。当前主站没有共享脚本，旧 Partners 有页面级判定。本次未照搬、未改 Partners。
- `tests/home.test.cjs`、`tests/home.browser.cjs`、`.github/workflows/home-checks.yml`、本记录、`PROGRESS.md`。

## 明确未改
- 原目录的未提交修改、main、生产、新闻正文、Partners 页面、付款、会员权益、预授权、后台和 Review 发布器均未改。
- 主站不包含付费学习、支付或预授权逻辑，diff 不涉及它们。未对真实账户、订单或客户发消息。
- 原根目录不存在 `.agents/skills` 和 `DEPLOY_GATE.md`；已读 AGENTS、CLAUDE v1.19、RULES、FREEZE、MERGE_GATE、PIPELINE、ANTI_PATTERNS 与语言 ADR。

## 自测结果
- Mini 本机 Chromium：390 / 1440 × 四语；320px；无横向溢出；三入口、五张旅游卡、三新闻卡；所有页内锚点与本地文章链接 200。
- 浏览器识别、手动选择压过 URL、URL 压过浏览器、存储不可用正常工作；无页面 JS 错误。
- 联系表单空值 / 无效邮箱校验通过；WhatsApp 调用被拦截核对，未发送。邮箱与微信保持原地址 / ID。
- 词典完整性、优先级映射、页面禁止自读 navigator、新闻保留自动测试通过。
- `WAN_RULES_LOCAL_PATH=... scripts/check_wan_constitution.sh` 通过 v1.19；`git diff --check` 通过。
- 桌面与手机截图已在 Mini 目检，证据保存在任务工作区的 evidence 目录。

## 风险点
- 这是探索版，不是批准版；等待任务 4 的视觉规定讨论。
- 正式托管仍是 GitHub Pages 的 main 根目录，未建立 Cloudflare Pages preview。本次 Review 为既有 `/tasks/` 静态候选，不伪造 Pages deployment。
- Review 的 `sites/nice.okinawa.json` 当前 repo=null、publisher_enabled=false、supported_languages=[en]；首页更新不具备已验证的一键发布契约。本任务不修改此注册，不绕过文章发布门禁。
- 后续新闻发布器需与首页母版/词典同步，不能只注入未翻译卡片后再运行构建器，否则会覆盖新卡片或重新引入混语。任务 3 需在集成前确认此契约。合并前必须重查 main / 最新新闻，保留近期变更。
- 共享 resolver 来源是 Mini 上的 bjt 既有文件（完整保留，支持 ja 等扩展语言），与旧 ADR 的三语映射表有年代差异；未改平台实现。
- 沿用原首页已有 Unsplash 图片地址，图片非公司实拍证明，未声称地点真实性。图片加载失败仍有海色背景，文字与入口可用。

## 回滚方式
候选分支直接关闭即可；生产未改，无需生产回滚。删除本任务独立的 Review 静态目录即可撤掉预览，不影响其他队列。
