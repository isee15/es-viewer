# PyQt Elasticsearch Viewer
Elasticsearch ES可视化客户端工具

[下载地址](https://pan.quark.cn/s/ed38a68328eb)

*一个简单、轻量级、跨平台的桌面GUI工具，用于浏览和管理Elasticsearch集群。*

该工具是使用Python和PyQt6构建的独立桌面应用程序。它提供了一个用户友好的界面，用于执行常见的Elasticsearch操作，如搜索、文档管理、索引创建和API调用。它的设计目标是最小化和便携，仅依赖`requests`库与Elasticsearch通信，不依赖官方的`elasticsearch-py`客户端。

<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/743b6d3d-63a3-4526-80f2-5b274e982485" />


---

## ✨ 功能

*   **灵活的连接**: 通过HTTP或HTTPS连接到任何Elasticsearch集群。
*   **安全选项**:
    *   支持用户名/密码（Basic）认证。
    *   可选择禁用SSL证书验证，以连接使用自签名证书的集群。
*   **强大的搜索 (Search Tab)**: 一个专门用于编写和执行复杂JSON格式Query DSL搜索的标签页。
*   **文档编辑器 (Document Editor Tab)**: 集中管理单个文档的CRUD操作：
    *   **Get**: 按ID检索文档。
    *   **Create/Update**: 创建或完整更新一个文档。支持用户自定义ID和自动生成ID。
    *   **Partial Update**: 使用`_update` API对文档进行部分更新。
    *   **Delete**: 按ID删除文档。
*   **索引创建器 (Create Index Tab)**:
    *   通过直观的表单界面创建新索引。
    *   可配置分片、副本、设置、映射和别名。
    *   提供预定义的索引模板（如日志、文档、时间序列等）。
*   **API控制台 (API Console Tab)**:
    *   **常用API**: 通过双击快速执行常用的集群和索引命令（如健康检查、获取映射等）。
    *   **自定义请求**: 能够执行任何HTTP方法（GET, POST, PUT, DELETE等）和自定义端点，提供完整的API灵活性。
*   **交互式结果显示**:
    *   可在清晰的**树状视图**或格式化的**JSON文本视图**之间切换。
    *   优雅地处理嵌套的JSON结构。
*   **用户友好**:
    *   **复制粘贴**: 使用`Ctrl+C`或右键菜单轻松复制结果树中的键、值或完整的键值对。
    *   **会话持久化**: 自动保存您上次成功的连接和查询配置，在下次启动时加载。
*   **轻量级与跨平台**:
    *   最小依赖: `PyQt6` 和 `requests`。
    *   可在Windows、macOS和Linux上运行。

---

## 🛠️ 安装

您可以通过PyPI直接安装 `es-viewer`。

1.  **使用pip安装:**
    确保您已安装Python 3和pip，然后运行：
    ```bash
    pip install es-viewer
    ```

2.  **运行应用:**
    安装后，您可以从终端运行该应用：
    ```bash
    es-viewer
    ```

### 备选方案: 从源码运行

如果您希望直接从源代码运行：

1.  **克隆仓库:**
    ```bash
    git clone https://github.com/isee15/es-viewer
    cd es-viewer
    ```

2.  **安装依赖:**
    ```bash
    pip install PyQt6 requests
    ```

3.  **运行应用:**
    ```bash
    python es_gui.py
    ```

---

## 🚀 使用方法

1.  **运行应用:**
    如果您通过pip安装，请在终端中运行 `es-viewer`。如果从源码运行，请使用 `python es_gui.py`。

2.  **连接面板:**
    *   填写 `Host`、`Port` 和目标 `Index`。
    *   如果您的集群使用SSL/TLS，请勾选 **Use HTTPS**。
    *   如果使用HTTPS但证书是自签名的，您可能需要取消勾选 **Verify SSL Certificate**。
    *   如果您的集群需要认证，请勾选 **Enable Authentication** 并填写您的凭据。

3.  **功能标签页:**
    *   **Search**: 在JSON编辑器中编写您的Elasticsearch Query DSL，然后点击 **Search**。
    *   **Document Editor**:
        *   **Document ID**: 对于`Get`、`Partial Update`和`Delete`是必需的。对于`Create/Update`是可选的（如果留空，ES会自动生成ID）。
        *   **Document Source**: 为`Create/Update`输入完整的文档JSON，或为`Partial Update`输入更新载荷（例如 `{"doc": {"field": "new_value"}}`）。
    *   **Create Index**: 填写表单并使用子标签页定义设置、映射和别名，然后点击 **Create Index**。
    *   **API Console**: 在上半部分的树中双击常用API，或在下半部分构建并执行您自己的自定义请求。

4.  **结果视图:**
    *   操作结果将显示在右侧面板中。
    *   您可以在 **JSON Text** 和 **Tree View** 模式之间切换以获得最佳可读性。

---

## ⚙️ 配置

应用会在成功执行搜索操作后自动保存您的设置。

*   **文件位置**: 文件名为 `.es_viewer_config.json`，存储在您的用户主目录中（例如，Windows上的 `C:\Users\YourUser` 或Linux上的 `/home/youruser`）。
*   **功能**: 它存储了上次使用的连接详情、认证状态和搜索查询，因此您不必每次打开应用都重新输入。
*   **安全提示**: 密码在此文件中以明文形式保存。在生产环境中使用存在安全风险，请谨慎使用。

---

## 📜 许可证

本项目根据MIT许可证授权。详情请参阅 `LICENSE` 文件。
