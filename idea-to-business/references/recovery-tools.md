# 发送恢复与五图导入

适用于中断恢复、下载超时及五个原件归档。以下是本地辅助工具，不是远程自动控制器。浏览器或连接器负责实际发送、下载；代理负责核对人类授权、普通 Chat 模式与原图内容。Python 3.10+；导入图像需要 Pillow。

## 从普通 Chat 取回原件

先定位当前交接编号对应回复，确认其五张独立版本。旧图、上传图和当前生成图可能在同一个查看器内混排，不能使用整个聊天的图片总数。

1. 打开本轮图片，检查下载控件的实际结果。有的界面先弹菜单，需继续选择“下载图片”或“下载本系列五张”；仅打开菜单不会产生下载事件。
2. 受支持下载接口未给路径时，检查本机下载目录是否已经落盘；观察超时不代表下载失败。结合当前操作、文件内容、版本标记和可用的原件哈希归属，不按最新五个文件猜测，也不重发生图任务。
3. 若查看器媒体地址是 blob 且媒体导出失败，可使用图片文件菜单中的“在资料库中打开”。从这个当前图片实际跳转的页面定位已显示原件；本次实测该处显示的是 HTTPS 原件，可用浏览器支持的媒体导出（如可见 img 的 downloadMedia）得到本地路径。
4. 若资料库出现本轮五个文件条目，逐个打开或导出已显示的原件，核对版本、完整解码和归属。相近时间/类似文件名只是定位线索；不能替代图片内容和本轮关联核对。不下载无关项目文件，不猜隐藏 API、拼接文件编号或提取凭据。
5. 取得五图后调用下方导入工具，填审核表。取图成功不等于图中文字正确。资料库路径未在当前环境验证时仍只是一种待尝试方案，不能提前承诺成功。

2026-10-17 的同一轮五图已通过此资料库原件导出路径全部自动取回；五个文件均与对应原件字节哈希一致。一张媒体导出观察超时但原件实际已落盘，通过目录与哈希核对接回，未再次点击下载。链路有明显延迟，不能据一次成功宣称长期稳定无人值守。人工用户选版和反馈确认仍是预期流程，不属于自动化故障。

## 发送前后

先用 build_handoff.py 准备交接包。点击发送前领取发送权，目标应为刚核对的同一聊天地址或受支持 ID：

```text
python scripts/handoff_state.py reserve handoff/handoff.json handoff/send-state.json --target CHAT_URL --authorization-ref HUMAN_MESSAGE_REF --mode-evidence CURRENT_CHAT_MODE_OBSERVATION
```

领取成功后只发送一次。若领取后崩溃而不知道是否已点击，保守地只读目标；脚本不会自动释放发送权。已有历史发送状态时不要重新领取或换路径再发送。

读到目标中的同交接编号消息后记录，再记录归属于该回复的五个图像块：

```text
python scripts/handoff_state.py observe handoff/handoff.json handoff/send-state.json --target CHAT_URL --event message-present --evidence MATCHING_MESSAGE_OBSERVATION
python scripts/handoff_state.py observe handoff/handoff.json handoff/send-state.json --target CHAT_URL --event five-generated --evidence FIVE_CURRENT_REPLY_IMAGES
python scripts/handoff_state.py status handoff/handoff.json handoff/send-state.json
```

下载失败记录 `retrieval-failed`，成功归档记录 `files-imported`。状态不是自动验证证据；`--evidence` 必须指向实际观察，不能凭空填写。观察超时先读目标；下载失败只恢复取图。残留 `.lock` 表示写入中断或仍有写入者，先核验，不自动清理。

## 五图归档

根据实际图片版本与回复关联生成 mapping.json。`handoff_id`、`content_hash`、`round` 必须逐字复制当前 handoff.json。每个 variant_id 恰好一次；不通过文件名或时间自动猜版本。

```json
{
  "handoff_id": "COPY_FROM_CURRENT_MANIFEST",
  "content_hash": "COPY_FROM_CURRENT_MANIFEST",
  "round": 1,
  "images": [
    {"variant_id":"V1","path":"downloads/v1.png","transport":"browser-download","source_evidence":"当前回复第一张已显示 V1，下载返回此路径"},
    {"variant_id":"V2","path":"downloads/v2.png","transport":"browser-download","source_evidence":"当前回复第二张已显示 V2，下载返回此路径"},
    {"variant_id":"V3","path":"downloads/v3.png","transport":"browser-download","source_evidence":"当前回复第三张已显示 V3，下载返回此路径"},
    {"variant_id":"V4","path":"downloads/v4.png","transport":"browser-download","source_evidence":"当前回复第四张已显示 V4，下载返回此路径"},
    {"variant_id":"V5","path":"downloads/v5.png","transport":"browser-download","source_evidence":"当前回复第五张已显示 V5，下载返回此路径"}
  ]
}
```

`path` 为绝对路径或相对 mapping.json 的路径。transport：接口实际自动下载为 `browser-download`，从下载目录读取为 `download-folder`，用户附回为 `user-upload`。下载目录拾取只证明本地收集自动完成，不能证明点击下载也自动完成；source_evidence 应说明哪一步由用户做。五图同时解码并排除相同像素后，整个批次才归档；不能用改元数据的重复图凑五张。

```text
python scripts/import_images.py handoff/handoff.json mapping.json originals
```

输出五个保留字节的原件和 import-receipt.json。既有输出只允许同一批次幂等核对；文件被改或来源变更即报错。失败时不留下可被误认为成功的半批次；临时文件在目标目录同级清理。调用者提供的目标与输入须在当前用户允许的项目范围内。

## 审核与接回

打开每个原图，按共同内容逐项核对，另填 image-review.csv 与 return-receipt.json。脚本默认 `pending`，不从图片大小、五个哈希或 OCR 无报错推定通过。疑似错字先放大核对；OCR 和视觉结果冲突时保留不确定性。记录用户当前轮选择和满意确认后再同步风格与阶段。原始失败记录保留，替换稿另编号，不覆盖失败原件。
