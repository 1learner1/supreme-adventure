# 港口锚地无人机协同调度专利稿

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
