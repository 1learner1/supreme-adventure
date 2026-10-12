# 港口锚地无人机协同调度专利稿


## 最新聚焦版：2026年10月12日

本轮以“每次调整任务或访问顺序，都完整重排周转时间轴并判断可执行性”为主线，将船舶窗口及有限工位作为海事新增设计单独说明。

- [完整Word审阅稿](port-dispatch_20261012105818.docx)及[Markdown正文](port-dispatch_20261012105818.md)。
- [权利要求书](port-dispatch_20261012105818-claims.docx)及[说明书](port-dispatch_20261012105818-specification.docx)。
- [本轮修改、来源边界及验证说明](port-dispatch_20261012105818-revision-notes.md)。
- [机制检查结果](port-dispatch_20261012105818-checks.json)及[可重复原型](port-dispatch_20261012105818-scheduler.py)。
- [来源与权项映射](port-dispatch_20261012105818-evidence.json)、[结构化稿](port-dispatch_20261012105818-draft.json)、[检查报告](port-dispatch_20261012105818-validation.txt)。
- [海事扩展查新状态](port-dispatch_20261012105818-prior-art-status.md)。

说明书为9项方法权利要求的对应技术披露，包含13个可编辑公式和3张中文黑白附图。人工5船小例验证三个机制以及41个邻域候选的完整重排；这不等于已完成真实港口仿真、实飞或新颖性判断。原论文山区结果与本轮海事新增设计没有混用。

从仓库根目录重复示例检查：

```bash
python3 docs/patents/port-anchor-drone-dispatch/port-dispatch_20261012105818-scheduler.py --output /tmp/port-mechanism-checks.json
```

## 此前版本（保留）

本目录保存港口锚地应急物资配送的异构无人机与共享电池协同调度专利修订稿。

- [Word 修订稿](patent-disclosure.docx)：依据 Markdown 于2026年10月12日重新生成，包含3张附图、13个可编辑公式和4张表格。
- [Markdown 修订稿](patent-disclosure.md)：正文、公式和可继续编辑的 Mermaid 图源。
- [修订说明及待确认事项](revision-notes.md)。
- [修订记录](revision-history.md)。
- [查新证据状态](prior-art-status.md)：本轮未重新检索，不作新颖性或创造性结论。
- [原稿 Markdown](original/patent-disclosure.md)及[原稿 Word](original/patent-disclosure.docx)：用户上传原稿的保留副本。

## 阅读与下载

在 GitHub 打开 Word 文件后，使用 **Download raw file** 或 **Raw** 下载到本机，再用 Word 或兼容软件打开。Markdown 可直接在 GitHub 阅读；附图位于 `figures/`，文档中保留 Mermaid 图源。

## 数值复算

```bash
python3 docs/patents/port-anchor-drone-dispatch/recalculate-example.py
```

脚本仅依赖 Python 标准库，重新计算原稿固定架次的航时、能耗与充电时刻，并更新 `example-results.json`。这不代表全局最优性、实飞性能或真实设备参数已验证。
