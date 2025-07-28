# PDF报告生成指南

## 问题解决方案

### 1. 前端显示未结束的问题

**问题原因**: Streamlit应用的自动刷新机制导致状态更新延迟。

**已修复的内容**:
- ✅ 增加了分析完成状态的实时检测
- ✅ 优化了自动刷新频率（从1秒改为2秒）
- ✅ 添加了"🎉 分析完成！"日志的状态更新触发器

**使用建议**:
- 等待日志中出现"🎉 分析完成！"消息
- 页面会自动更新为"✅ 分析已完成"状态
- 如果状态未及时更新，可以手动刷新页面

### 2. PDF报告生成功能

#### 当前状态
- ✅ `pdfkit` 已安装
- ❌ `wkhtmltopdf` 需要手动安装
- ✅ 报告生成器代码已就绪

#### 安装 wkhtmltopdf (Windows)

1. **下载安装包**:
   - 访问: https://wkhtmltopdf.org/downloads.html
   - 下载 Windows 版本的安装包

2. **安装步骤**:
   - 运行下载的安装程序
   - 按照提示完成安装
   - 默认安装路径通常是: `C:\Program Files\wkhtmltopdf\bin\`

3. **配置环境变量**:
   - 打开"系统属性" → "高级" → "环境变量"
   - 在"系统变量"中找到"Path"
   - 添加 wkhtmltopdf 的安装路径到 Path 中
   - 例如: `C:\Program Files\wkhtmltopdf\bin\`

4. **验证安装**:
   ```bash
   # 重启命令行后运行
   wkhtmltopdf --version
   
   # 或者运行检查脚本
   python install_pdf_support.py
   ```

#### 使用PDF生成功能

1. **在Streamlit应用中**:
   - 完成交易分析后
   - 在左侧边栏的"📄 报告生成"部分
   - 选择格式为"pdf"
   - 输入报告标题
   - 点击"📊 生成报告"按钮

2. **下载报告**:
   - 生成成功后会显示"📥 下载 PDF 报告"按钮
   - 点击按钮下载PDF文件

#### 支持的报告格式

- **Markdown** (.md) - ✅ 已支持
- **Word文档** (.docx) - ✅ 已支持
- **PDF文档** (.pdf) - ⚠️ 需要安装 wkhtmltopdf

#### 报告内容包括

- 📋 用户查询
- 📊 市场技术分析
- 💭 市场情绪分析
- 📰 新闻事件分析
- 🏢 基本面分析
- 🎯 投资策略辩论
- 👔 投资决策
- 📈 交易执行计划
- ⚠️ 风险管理分析
- 🛡️ 最终风险决策

## 故障排除

### PDF生成失败

1. **检查依赖**:
   ```bash
   python install_pdf_support.py
   ```

2. **常见错误**:
   - `OSError: wkhtmltopdf reported an error` → wkhtmltopdf未正确安装
   - `FileNotFoundError: [Errno 2] No such file or directory: 'wkhtmltopdf'` → 环境变量未配置

3. **解决方案**:
   - 重新安装 wkhtmltopdf
   - 检查环境变量配置
   - 重启IDE和命令行

### 前端状态问题

1. **分析完成但显示仍在运行**:
   - 等待2-3秒让页面自动刷新
   - 手动刷新浏览器页面
   - 检查日志中是否有"🎉 分析完成！"消息

2. **分析卡住不动**:
   - 点击"⏹️ 停止分析"按钮
   - 刷新页面重新开始

## 快速测试

1. **测试PDF功能**:
   ```bash
   python install_pdf_support.py
   ```

2. **测试完整流程**:
   - 启动Streamlit应用: `streamlit run streamlit_app.py`
   - 输入分析问题
   - 等待分析完成
   - 生成PDF报告

## 技术细节

### 修复的文件
- `streamlit_app.py`: 优化状态管理和刷新逻辑
- `install_pdf_support.py`: 新增PDF依赖检查和安装脚本

### 报告生成器
- 位置: `src/report_generator.py`
- 支持多种格式输出
- 自动格式化分析结果
- 包含完整的样式和布局

---

**注意**: 完成 wkhtmltopdf 安装后，PDF生成功能将完全可用。如有问题，请参考故障排除部分或重新运行检查脚本。