# 港口锚地无人机协同调度专利稿


## 最新纠正版：2026年10月12日

沿用“任务调整后完整重排机体、电池和工位时间轴”的主线，补齐实施细节与可追溯证据。

- [完整Word审阅稿](port-dispatch_20261012113350.docx)及[Markdown正文](port-dispatch_20261012113350.md)。
- [权利要求书](port-dispatch_20261012113350-claims.docx)、[说明书](port-dispatch_20261012113350-specification.docx)、[摘要](port-dispatch_20261012113350-abstract.docx)。
- [独立审核材料Word](port-dispatch_20261012113350-review.docx)及[来源、公式、代码和运行证据索引](port-dispatch_20261012113350-source-index.md)。
- [可重复原型](port-dispatch_20261012113350-scheduler.py)、[测试输入和完整资源记录](port-dispatch_20261012113350-checks.json)、[真实运行日志](port-dispatch_20261012113350-run-log.txt)、[选择提交与回滚事件](port-dispatch_20261012113350-trace.jsonl)。
- [结构化稿](port-dispatch_20261012113350-draft.json)、[证据映射](port-dispatch_20261012113350-evidence.json)、[原论文技术摘录及公式XML](port-dispatch_20261012113350-source-excerpts.json)。
- [结构与溯源检查](port-dispatch_20261012113350-validation.txt)、[交付检查](port-dispatch_20261012113350-delivery-checks.json)、[本轮修订说明](port-dispatch_20261012113350-revision-notes.md)。

本轮区分拆卸冷却完成、充电结束与满电再次可用；明确排序键、设备组合比较、状态提交和失败回滚。说明书含15个显示公式、可编辑行内上下标、3张带循环或反馈关系的中文附图和6个实施例。审核材料表格设置重复表头及禁止拆行。

已实际执行并重复运行代码。旧版基准、反向访问和共享工位结果保持一致，新增120秒工位外处理延迟的电池复用检查。人工5船及41个邻域候选检查不代表真实港口仿真、实飞或新颖性结论。

从仓库根目录运行（仅需Python标准库）：

```bash
python3 docs/patents/port-anchor-drone-dispatch/port-dispatch_20261012113350-scheduler.py --output /tmp/port-checks.json --trace-output /tmp/port-trace.jsonl
```

### 上一聚焦版（保留）

[port-dispatch_20261012105818.docx](port-dispatch_20261012105818.docx)及[对应Markdown](port-dispatch_20261012105818.md)。

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
