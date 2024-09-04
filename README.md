# ai-conference-deadlines
中国计算机协会和中国人工智能协会推荐人工智能想会议的截止投稿日期：
1. [查询页面](https://www.aihomecaring.com/?conference/)
2. 展示说明
![ai-conference-dealines-demo.png](assets%2Fai-conference-dealines-demo.png)

## 贡献会议信息

非常欢迎贡献会议信息！

项目列出了根据**中国计算机协会**和**中国人工智能协会**推荐的AI会议。如果你没有看到你感兴趣的子领域或会议，欢迎维护一个独立的分支。

要添加或更新截止日期：

- Fork（克隆）该仓库
- 更新 data/conferences.yml
- 确保包括 title、year、id、link、deadline、timezone、date、place
   + timezone 需要转换为 UTC 格式（例如：UTC-12，UTC，UTC+9）。
- 可选添加sub，如果添加，sub可选范围为：[人工智能综合、 自然语言与语音处理、计算机视觉与图形、知识工程与数据挖掘、人机交互与智能应用、类脑智能与智能芯片、智能机器人机器学习]
- 可选地添加 note 和 abstract_deadline（如果会议有单独的强制摘要截止日期）
- 可选地添加 hindex（h5-index[查询位置](https://scholar.google.com/citations?view_op=top_venues&vq=eng)）
  - 示例：
  ```yaml
  - title: NAACL
    year: 2025
    id: naacl25
    link: https://2025.naacl.org
    deadline: '2024-10-15 23:59:59'
    abstract_deadline: 
    timezone: UTC-12
    place: Albuquerque, New Mexico, USA
    date: April 29- May 4, 2024
    start: 2025-04-29
    end: 2025-05-04
    hindex: 132
    sub: 
    note: All submissions must be done through ARR.
  ```
- 发送一个 pull request 请求

## 数据清洗说明
1. 进入程序位置
```shell
cd utils
```
2. 运行PDF读取和转换脚本
```python
# 运行说明参考脚本中main函数的说明
python pdf_parse.py
```
3. 运行数据更新和入库脚本
```python
# 运行说明参考脚本中main函数的说明
python process.py
```

## 参考链接
- [ai-deadlines](https://github.com/paperswithcode/ai-deadlines)
