# DingTalk RichText Channel Plugin Example

这个示例展示如何以 `channel` 插件方式扩展 nanobot 的 DingTalk 通道。

能力点：

- 解析 DingTalk 入站消息里的 `richText` 内容并转成普通文本
- 识别附件下载链接并下载到本地 `/tmp`（可配置）
- 将下载后的本地文件路径放入 `InboundMessage.media`，便于后续工具链处理

## 前置条件

- Python >= 3.11
- 已安装并可运行 `nanobot`
- 你已经在钉钉开放平台创建了机器人应用，并拿到 `AppKey/AppSecret`
- 使用 `uv`（推荐）或 `pip` 安装本示例插件

## 目录结构

- `pyproject.toml`：插件包定义与 entry point
- `src/nanobot_plugin_dingtalk_richtext/channel_factory.py`：插件工厂 + 通道实现

## 安装（editable）

```bash
cd examples/channel-plugin-dingtalk-richtext
uv pip install -e .
```

安装后可通过命令确认插件是否被加载：

```bash
nanobot channels status
```

如果插件已被配置并启用，你会看到 `dingtalk_richtext (plugin)`。

## 配置 nanobot

将以下内容合并到 `~/.nanobot/config.json`：

```json
{
  "channels": {
    "plugins": {
      "dingtalk_richtext": {
        "enabled": true,
        "clientId": "YOUR_DINGTALK_APP_KEY",
        "clientSecret": "YOUR_DINGTALK_APP_SECRET",
        "allowFrom": ["*"],
        "downloadDir": "/tmp"
      }
    }
  }
}
```

说明：

- `downloadDir` 默认值是 `/tmp`
- 插件配置里可继续放你自己的扩展字段，插件会按需读取

配置字段说明：

| 字段 | 必填 | 说明 |
|------|------|------|
| `enabled` | 是 | 是否启用插件通道 |
| `clientId` | 是 | 钉钉机器人 AppKey |
| `clientSecret` | 是 | 钉钉机器人 AppSecret |
| `allowFrom` | 是 | 白名单，示例里 `[*]` 代表允许所有发送者 |
| `downloadDir` | 否 | 附件下载目录，默认 `/tmp` |

## 验证

```bash
nanobot channels status
nanobot run
```

在 `channels status` 中你应该看到 `dingtalk_richtext (plugin)`。

验证建议步骤：

1. 给机器人发一条纯文本消息，确认正常回复。
2. 给机器人发一条富文本消息（richText），确认机器人能提取文本内容。
3. 给机器人发一个带附件的消息，确认附件被下载到 `/tmp`。

你可以在本机查看下载结果：

```bash
ls -lah /tmp | grep -i -E "(png|jpg|jpeg|pdf|doc|docx|xlsx|txt|bin)"
```

插件行为说明：

- 若消息仅有附件无文本，插件会上报内容 `[Attachment message]`
- 下载后的本地绝对路径会进入 `InboundMessage.media`
- 如果附件文件名冲突，插件会自动追加时间戳避免覆盖

## 常见问题

1. `channels status` 看不到插件项

  - 检查是否在示例目录执行过 `uv pip install -e .`
  - 检查配置路径是否是当前实例使用的配置（多实例场景常见）

2. 插件已加载但消息无响应

  - 检查 `clientId/clientSecret` 是否正确
  - 检查 `allowFrom` 是否放行了当前发送者

3. 附件未下载到 `/tmp`

  - 检查进程是否有 `/tmp` 写权限
  - 检查消息里的附件 URL 是否可访问
  - 可将 `downloadDir` 改为其他可写目录

## 入口点说明

本示例使用 `nanobot.channel_factories` 入口点：

- 名称：`dingtalk-richtext`
- 工厂：`nanobot_plugin_dingtalk_richtext.channel_factory:create_channel`

nanobot 会把配置 `channels.plugins.dingtalk_richtext` 传给该工厂。
