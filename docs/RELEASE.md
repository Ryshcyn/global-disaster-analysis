# 发布清单

本地项目已经按公开仓库用途去除姓名与课程分工信息。发布包仅由 `python tools/package.py` 的白名单生成，
原始 CSV、本地环境、缓存、Notebook 检查点和原课程报告不会打包。

## 本地验证

```bash
python -m unittest discover -s tests -v
python -m src.run
python tools/execute_notebook.py
python tools/package.py
```

`execute_notebook.py` 会从头执行 Notebook，再删除执行时间、临时路径和单元执行元数据。
原始 CSV 只留在 Git 忽略目录中。GitHub 不会自动渲染 Plotly HTML，下载后可离线打开；
静态图和已执行 Notebook 则可以直接阅读。

## 上传建议

建议新建名为 `global-disaster-analysis` 的仓库，上传公开 ZIP 的内容，而不是整个课程文件夹。
原始课程目录与本地原始 CSV 不应上传。
仓库用户名、Git 提交作者和 GitHub 账号资料由账号本身决定，不属于文件内容匿名化范围；
如需避免身份关联，发布时需自行选择对应账号和提交身份。

代码尚未指定开源许可；如需授权他人复用，可在发布前选择适合的代码许可。
第三方数据条款独立适用，不应把代码许可扩展到原始数据。
