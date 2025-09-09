# ES-Viewer 打包、上传与使用说明

本文档描述了如何将 `es-viewer` 项目打包并上传到 Python 包索引 (PyPI)，以及用户如何通过 `pip` 进行安装和使用。

---

## 1. 环境准备

在开始之前，请确保您已经安装了 Python，并准备好您的 PyPI 账户。

### 安装打包工具

您需要 `setuptools`, `wheel` 和 `twine` 这三个核心工具来完成构建和上传。如果尚未安装，请运行以下命令：

```bash
pip install setuptools wheel twine
```

---

## 2. 打包项目

项目打包是通过 `setup.py` 脚本完成的。

### 构建分发文件

在项目的根目录下（即 `setup.py` 所在的目录），打开终端或命令提示符，运行以下命令：

```bash
python setup.py sdist bdist_wheel
```

这个命令会执行以下操作：
- `sdist`: 创建一个源码分发包 (例如 `es-viewer-1.2.0.tar.gz`)。
- `bdist_wheel`: 创建一个预编译的 wheel 包 (例如 `es-viewer-1.2.0-py3-none-any.whl`)。

命令成功执行后，您会在项目根目录下看到一个新建的 `dist` 文件夹，其中包含了这两个打包好的文件。

---

## 3. 上传到 PyPI

当您的包构建完成后，就可以使用 `twine` 将其上传到 PyPI。

### 执行上传命令

在终端中运行以下命令：

```bash
twine upload dist/*
```

- `twine` 会安全地将 `dist` 文件夹中的所有包文件上传到 PyPI。
- 运行时，系统会提示您输入在 [PyPI](https://pypi.org/) 注册的**用户名**和**密码**。

> **提示**: 建议先上传到 TestPyPI 进行测试，以避免污染主仓库。
>
> 1.  上传到 TestPyPI: `twine upload --repository testpypi dist/*`
> 2.  从 TestPyPI 安装: `pip install --index-url https://test.pypi.org/simple/ es-viewer`

上传成功后，您的包就正式发布了。

---

## 4. 用户安装与使用

一旦包成功发布到 PyPI，任何用户都可以通过 `pip` 轻松安装和使用。

### 通过 pip 安装

用户只需在终端中运行以下命令即可安装 `es-viewer`：

```bash
pip install es-viewer
```

`pip` 会自动从 PyPI 下载包并安装所有在 `setup.py` 中声明的依赖项（如 `PyQt6` 和 `requests`）。

### 启动应用

安装完成后，由于我们在 `setup.py` 中配置了入口点（entry point），`pip` 会在系统的可执行路径下创建一个名为 `es-viewer` 的命令。

用户可以直接在终端中输入以下命令来启动图形界面应用：

```bash
es-viewer
```

程序将像本地运行 `python es_gui.py` 一样启动。
