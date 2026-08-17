# PM-PHAR-Tool 完整使用教程

本教程演示如何：准备一个可用的 `.phar` 文件 → 备份原文件 → 解压 → 修改内容 → 使用原始 Stub 重新打包。

---

## 📦 第一步：准备一个可用的 PHAR 文件

### 你需要什么
- 一个**完好无损**的 PocketMine 插件 `.phar` 或核心 `.phar` 文件
- 例如：`TestPlugin.phar`、`PocketMine-MP.phar`

### 验证 PHAR 是否可用
在终端执行以下命令：

```bash
php -d phar.readonly=0 -r "new Phar('TestPlugin.phar'); echo 'PHAR 可用\n';"
```

如果输出 `PHAR 可用`，说明文件完整，可以继续。

---

## 💾 第二步：备份原文件

**强烈建议**在操作前先备份原始文件，防止误操作导致数据丢失。

### 手动备份
```bash
cp TestPlugin.phar TestPlugin_backup.phar
```

### 或者用 Python
```python
import shutil
shutil.copy('TestPlugin.phar', 'TestPlugin_backup.phar')
print("✅ 已备份到 TestPlugin_backup.phar")
```

---

## 📂 第三步：解压 PHAR

### 使用本工具解压（方式一：交互式）

```bash
python 自定义编辑打包phar未加密插件.py
```

选择 **选项 1**，然后按提示输入：

```
> 请输入选项 (1-6): 1
> 请输入.phar文件路径: TestPlugin.phar
> 请输入解压目录（留空为当前目录）: ./TestPlugin_extracted
```

### 使用本工具解压（方式二：代码调用）

```python
from pm_phar_tool.phar import extract_phar

extract_phar("TestPlugin.phar", "./TestPlugin_extracted")
```

### 手动用 PHP 解压（验证用）

```bash
php -d phar.readonly=0 -r "
\$phar = new Phar('TestPlugin.phar');
\$phar->extractTo('./TestPlugin_extracted', null, true);
echo '解压完成\n';
"
```

解压后的目录结构示例：

```
TestPlugin_extracted/
├── plugin.yml          # 插件配置文件
├── src/
│   └── TestPlugin/
│       └── Main.php    # 主类文件
└── resources/
    └── config.yml      # 资源文件
```

---

## ✏️ 第四步：修改内容（可选）

现在你可以像编辑普通文件夹一样修改里面的文件。

### 常见修改场景

| 修改内容 | 操作示例 |
|----------|----------|
| 修改插件名称/版本 | 编辑 `plugin.yml` |
| 修改代码逻辑 | 编辑 `src/` 下的 `.php` 文件 |
| 添加新文件 | 直接复制文件到对应目录 |
| 删除不需要的文件 | 直接删除 |

### 示例：修改 plugin.yml

编辑前：
```yaml
name: TestPlugin
version: 1.0.0
main: TestPlugin\Main
api: [5.0.0]
```

编辑后：
```yaml
name: TestPlugin
version: 1.0.1
main: TestPlugin\Main
api: [5.0.0]
author: YourName
```

---

## 📤 第五步：使用原始 Stub 重新打包

这是最关键的一步。PHAR 文件的 **Stub** 是文件开头的启动代码，决定了 PHAR 如何被加载。使用错误的 Stub 会导致打包后的 PHAR 无法运行。

### 方式一：交互式打包（推荐）

```bash
python 自定义编辑打包phar未加密插件.py
```

选择 **选项 2**，然后按提示操作：

```
> 请输入选项 (1-6): 2
> 请输入插件文件夹路径: ./TestPlugin_extracted
> 请输入输出文件名（默认: TestPlugin_extracted.phar）: TestPlugin_v1.0.1.phar
> 是否使用自定义 Stub？（y/n，默认 n）: y
> 请输入原始的 .phar 文件（用于提取 Stub）: TestPlugin.phar
```

工具会自动：
1. 从原始 `TestPlugin.phar` 中提取 Stub
2. 将修改后的文件夹打包为新的 PHAR
3. 使用原始 Stub 作为启动入口
4. 清理临时文件

### 方式二：先提取 Stub，再手动打包

#### 步骤 A：提取 Stub

```bash
python 自定义编辑打包phar未加密插件.py
```

选择 **选项 5**：

```
> 请输入选项 (1-6): 5
> 请输入.phar文件路径: TestPlugin.phar
> 请输入Stub保存目录（留空为当前目录）: .
> 请输入Stub文件完整路径（默认: ./TestPlugin.phar.stub.php）: （直接回车）
```

Stub 会被保存为 `TestPlugin.phar.stub.php`。

#### 步骤 B：使用提取的 Stub 打包

```bash
python 自定义编辑打包phar未加密插件.py
```

选择 **选项 2**：

```
> 请输入插件文件夹路径: ./TestPlugin_extracted
> 请输入输出文件名（默认: TestPlugin_extracted.phar）: TestPlugin_new.phar
> 是否使用自定义 Stub？（y/n，默认 n）: y
> 请输入原始的 .phar 文件（用于提取 Stub）: TestPlugin.phar
```

### 方式三：纯 PHP 手动操作（高级）

```bash
# 1. 提取 Stub
php -d phar.readonly=0 -r "
\$phar = new Phar('TestPlugin.phar');
file_put_contents('stub.php', \$phar->getStub());
echo 'Stub 已提取\n';
"

# 2. 重新打包（使用提取的 Stub）
php -d phar.readonly=0 -r "
\$phar = new Phar('TestPlugin_new.phar');
\$phar->buildFromDirectory('./TestPlugin_extracted');
\$stub = file_get_contents('stub.php');
\$phar->setStub(\$stub);
\$phar->setSignatureAlgorithm(Phar::SHA1);
echo '打包完成\n';
"
```

---

## ✅ 第六步：验证新 PHAR

### 检查文件结构

```bash
php -d phar.readonly=0 -r "
\$phar = new Phar('TestPlugin_new.phar');
foreach (new RecursiveIteratorIterator(\$phar) as \$file) {
    echo \$file->getPathname() . PHP_EOL;
}
"
```

### 对比 Stub 是否一致

```bash
php -d phar.readonly=0 -r "
\$orig = new Phar('TestPlugin.phar');
\$new = new Phar('TestPlugin_new.phar');
echo '原始 Stub 长度: ' . strlen(\$orig->getStub()) . PHP_EOL;
echo '新 Stub 长度: ' . strlen(\$new->getStub()) . PHP_EOL;
echo 'Stub 一致: ' . (\$orig->getStub() === \$new->getStub() ? '是' : '否') . PHP_EOL;
"
```

### 放入 PocketMine 测试

将 `TestPlugin_new.phar` 放入 PocketMine 服务器的 `plugins/` 目录，启动服务器验证插件是否正常加载。

---

## 📋 完整流程速查表

```
┌─────────────────────────────────────────────────────────┐
│  1. 准备可用的 PHAR 文件（验证完整性）                    │
│  2. 备份原文件 → TestPlugin_backup.phar                  │
│  3. 解压 PHAR → ./TestPlugin_extracted/                  │
│  4. 修改文件夹中的内容（plugin.yml、代码等）              │
│  5. 使用原始 PHAR 提取 Stub 并打包                      │
│  6. 验证新 PHAR 的结构和 Stub 一致性                     │
│  7. 放入服务器测试                                       │
└─────────────────────────────────────────────────────────┘
```

---

## ⚠️ 常见问题

### Q1: 为什么必须使用原始 Stub？

**A:** PHAR 的 Stub 包含启动逻辑。PocketMine 核心 PHAR 的 Stub 通常包含版本检查、加载器初始化等关键代码。使用默认 Stub (`<?php __HALT_COMPILER(); ?>`) 会导致核心无法启动。

### Q2: 打包时提示 "Stub 文件不存在"？

**A:** 确保原始 PHAR 文件路径正确，且该 PHAR 未损坏。可以尝试先用选项 5 单独提取 Stub 验证。

### Q3: 修改后的 PHAR 比原来的大？

**A:** 本工具打包时不使用压缩（确保最大兼容性），所以文件会比原始压缩过的 PHAR 大。这是正常现象，不影响功能。

### Q4: 可以批量处理多个插件吗？

**A:** 当前版本为交互式 CLI，每次处理一个。可以编写简单的 shell 脚本批量调用：

```bash
#!/bin/bash
for phar in *.phar; do
    echo "处理: \$phar"
    python -c "
import sys
sys.path.insert(0, '.')
from pm_phar_tool.phar import extract_phar, build_phar
extract_phar('\$phar', '\$phar.extracted')
# 修改内容...
build_phar('\$phar.extracted', '\$phar.new', custom_stub_path='\$phar')
"
done
```

---

## 🎯 核心 PHAR 修复教程

如果你的 PocketMine 核心 PHAR 已损坏，按以下步骤修复：

```bash
python 自定义编辑打包phar未加密插件.py
```

选择 **选项 4**：

```
> 原始（损坏的）核心PHAR路径: PocketMine-MP.phar
> 请输入Stub文件保存目录（留空使用当前目录）: .
> 请输入Stub文件完整路径（默认: ./PocketMine-MP.phar.stub.php）: （回车）
```

工具会自动提取 Stub，然后解压文件。此时你可以：

1. **在另一个窗口**编辑 `./core_repair_temp/extracted/` 中的文件
2. 修改完成后，**回到工具窗口按回车**
3. 工具会使用原始 Stub 重新打包为 `PocketMine-MP_fixed.phar`

---

*教程版本: v1.0 | 适用工具版本: v3.1+*
