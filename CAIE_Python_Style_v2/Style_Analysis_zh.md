# 剑桥评分方案（MS）如何书写代码，以及这对 Python 项目意味着什么

第 2.0 版（重新分析），2026 年 10 月 11 日。范围：2016–2025 年剑桥 IGCSE 计算机科学 0478 与
AS & A Level 计算机科学 9608 / 9618 已公布的全部评分方案（mark scheme，MS），共 399 份。
本文是 `Style_Analysis.md` 的中文版；两者内容一致，如有出入以英文版为准。

## 1. 摘要

1. **标识符几乎都用 PascalCase**（`TotalWeight`、`NumberOfItems`、`ThisChar`）。在 2023–2025
   年 IGCSE 评分方案和 9618 AS/A Level 评分方案中，88–98 % 的不同标识符是 PascalCase；其余是
   惯用的单字母（`i`、`X`、`Y`）和首字母大写的简短缩写（`DD`、`MM`）。全小写、camelCase 和
   snake_case 名称主要出现在旧版 IGCSE 评分方案（2016–2022）以及 2021 年一份过渡期的 A Level
   评分方案中。0478 考纲（2023 年起）规定必须使用 PascalCase，并禁止使用下划线。
2. **剑桥自己的 Python 采用同样的命名。** 在 9618 Paper 4（2021–2025）的 Python 答案中，89 %
   的被赋值名称和 94 % 的函数名是 PascalCase，属性写作 `self.__PascalCase`，方法写作
   `GetX` / `SetX`。
3. **风格随考纲改变，所谓"不一致"大多是时代差异。** 旧版 IGCSE（2016–2022）允许 `PRINT`、
   用 `=` 赋值、`CASE x OF`、`WHILE … DO`、不声明变量，并在 2019–2021 年使用从 0 开始的循环；
   2023 年起的 IGCSE 使用 `OUTPUT`、`DECLARE`、`ARRAY[1:n]` 和 `FOR … NEXT Count`。9608 把
   `THEN` 单独写在下一行、用 `ENDFOR` 结束循环；9618 把 `IF … THEN` 写在同一行，并写 `NEXT Index`。
4. **伪代码数组从 1 开始。** 在起始值为 0 或 1 的 `FOR` 循环中，AS 和 2023 年后 IGCSE 答案里
   89–98 % 从 1 开始；9618 指南写道 "Generally, a lower bound of 1 will be used"（一般使用下界 1）。
   只有当下标本身有含义（0–23 点钟）时，以及在 Paper 4 的上机语境中，才使用 0。
5. **剑桥的 Python 数组从 0 开始**，循环写作带显式起点的 `for X in range(0, N):`
   （9618 Paper 4 的 131 个 `for` 循环中有 83 个如此）。
6. **算法一步一步写出来。** 没有任何评分方案的 Python 答案使用 `sorted`、`.sort`、`sum`、`min`、
   `max`、`map`、`filter`、`lambda`、`enumerate`、`zip`、f-string、`.format` 或 `with open`。
   查找、求和、求最值和排序都是带计数器、标志和临时变量的显式循环（仅有的捷径是三份 2016 年答案
   中的 `in` 和一份 2025 年答案中的 `random.sample`）。
7. **标志变量通常显式比较。** AS 伪代码写 `WHILE Found = FALSE` 的次数约为 `NOT Found` 的六倍
   （99 比 16）；9618 Paper 4 的 Python 写 `while Valid == False:` 33 次，写 `not` 2 次。
   2023 年后的 IGCSE 答案是例外：它们更常写 `UNTIL NOT Swap` / `IF NOT Booked`（12 比 1）。
8. **Paper 4 的 Python 依赖全局状态。** 数组和指针是模块级变量，每个子程序里都有 `global` 语句
   （共 148 条 `global` 语句）。多个结果以元组返回，以模仿 BYREF
   （`return (True, Queue, Head, Tail, NumItems)`）。
9. **声明注释是剑桥的习惯。** AS 的 Python 答案在子程序开头写 `# DECLARE Index : INTEGER` 或
   `## Count As Integer`（92 个代码块中共 137 行），9618 Paper 4 则在变量后面加类型注释
   （`Queue = [] #string 50 elements`）。
10. **列表推导式只用于创建数组。** `[0 for I in range(100)]` 和
    `[[0 for X in range(3)] for Y in range(20)]` 与 `append` 循环并存；推导式从不用于筛选或计算。
11. **评分方案不是 Python 范本。** 许多 Python 答案有错误（`FALSE`、`Return`、`<>`、缺冒号、
    Python 2 的 `print`），有两份答案建立的二维列表各行是同一个共享列表（`[['*'] * 2] * 100`），
    还有一份在每一行中重复同一个记录对象。应照搬结构，而不是照搬错误。
12. **之前的分析（v1.0）有些地方不可靠。** 其提取器把含旋转页面的 108 份文档的文字打乱了，并把
    Java、Pascal 和 VB 标成了 Python。它还夸大了从 0 开始的数组出现的频率，并禁止了一些剑桥自己的
    Python 也在使用的写法。详见 `Audit_of_v1.md`。

根据这些证据得出的规则见 `AGENTS.md`（供 AI 编程助手使用）和 `AI_Coding_Prompt.txt`
（可粘贴到对话中的简短版）。

## 2. 资料来源与方法

### 2.1 文档

| 层级（本报告） | 试卷 | 评分方案数 |
|---|---|---:|
| IG | 0478 Paper 1 和 Paper 2 | 138 |
| AS | 9608 和 9618 Paper 1 和 Paper 2 | 132 |
| AL | 9608 和 9618 Paper 3 和 Paper 4 | 129 |

全部 399 份 PDF 都按 v1 清单中记录的 URL 重新下载，每个文件都与记录的 SHA-256 哈希值一致
（`tools/ms_manifest.csv`、`tools/download_ms.py`）。官方参考资料：0478 考纲 2023–2025
（伪代码部分）、9618 考纲 2024–2025 和 9618 教师伪代码指南（Pseudocode Guide for Teachers，
2026 年版），均取自 v1 压缩包。

### 2.2 提取

评分方案用等宽字体排版代码（Courier New、Courier，或 2016 年使用的字形宽度统一为 0.6 em 的
嵌入子集字体），因此可以按字体把代码与评分说明文字分开。提取器（`tools/extract_code.py`）：

- 读取每个字符及其字体和位置（PyMuPDF）；
- 对含有以页面旋转方式存储的横向页面的 108 份文档做坐标变换（否则各列文字会交错在一起）；
- 把用 Symbol 或 Wingdings 字体绘制的赋值箭头（`←`、`U+F0AC`、`Å`、`\x04`）还原为 `←`；
- 去除以微小偏移打印两次的"伪粗体"字形（`AAlarmmState` → `AlarmState`）；
- 恢复五份 2023–2025 年 Paper 4 评分方案中被画成短线而不是字符的下划线。这些 PDF 显示的是单个
  下划线（`def _init_(self, …)`、`self._ID`），而原意的 Python 是 `__init__` 和 `self.__ID`；
  语料保留 PDF 所显示的内容；
- 根据 x 坐标和每个代码块实测的字符宽度重建缩进；
- 把 PDF 在表格单元格内折行的行接回去，并把被分页拆开的代码块合并；
- 记录每个代码块正上方的评分文字，包括语言标签（"Python"、"VB.NET"、"Java"、"Pascal"）。

`tools/classify.py` 根据标签和关键字证据判定语言，然后去除重复（同一考季的第 1 和第 3 套试卷
常常相同）。我们也查找过扫描成图片的代码：编程试卷评分方案中的图片是流程图、树形图和程序输出的
截图，而不是代码清单。

### 2.3 语料

| 层级 | 语言 | 不重复代码块 | 行数 | MS 文件数 |
|---|---|---:|---:|---:|
| IG | 伪代码 | 294 | 3 734 | 66 |
| AS | 伪代码 | 472 | 5 666 | 68 |
| AS | Python（9608 Paper 2 附录） | 92 | 983 | 31 |
| AL | 伪代码 | 155 | 1 756 | 56 |
| AL | Python（9608 / 9618 Paper 4） | 478 | 3 625 | 43 |
| AS + AL | Visual Basic、Java、Pascal | 1 170 | 13 164 | — |

可阅读的语料文件：`corpus/IG_pseudocode.txt`、`AS_pseudocode.txt`、`AL_pseudocode.txt`、
`AS_python.txt`、`AL_python.txt`。全部 6 750 个代码块（所有语言，含页码、坐标、上下文和重复项
链接）在 `corpus/blocks.jsonl` 中。每个代码块的标题行给出来源 PDF 和物理页码。

### 2.4 统计分组

统计按考纲时代、对编程试卷中的不重复代码块进行：

| 组 | 内容 |
|---|---|
| IG-old | 0478 Paper 2，2016–2022 |
| IG-new | 0478 Paper 2，2023–2025（新考纲） |
| AS-9608 | 9608 Paper 2，2016–2021 |
| AS-9618 | 9618 Paper 2，2021–2025 |
| AL-9608 | 9608 Paper 3–4，2016–2021 |
| AL-9618 | 9618 Paper 3–4，2021–2025 |

这些计数是描述性的。同一考季的不同套卷彼此相关，提取仍可能拆开或合并少数代码块，正则表达式计数
也可能把某行归错类。完整表格：`stats/pseudocode_counts.csv`、`stats/python_counts.csv`、
`stats/*_identifier_styles.csv`、`stats/style_statistics.json`、
`stats/algorithm_patterns.txt`。

## 3. 官方约定与评分方案的实际做法

| 主题 | 官方文件 | 评分方案的实际做法 |
|---|---|---|
| 标识符大小写 | 0478："mixed case using Pascal case, e.g. FirstName … must start with a capital letter … the underscore should not be used"（使用 Pascal 式大小写混合，如 FirstName……必须以大写字母开头……不应使用下划线）。9618："mixed case … for example NumberOfPlayers" | PascalCase 占主导（第 4 节）。评分方案把它称为 "Camel Case"："Sensible / meaningful variable names // use of Camel Case"、"Capitalised keywords"（9618_s23_ms_22、9608_w19_ms_22） |
| 大小写敏感 | 两者：标识符不区分大小写；`Countdown` 和 `CountDown` 不得作为两个变量 | 遵守 |
| 单字母 | 两者：在惯用场合允许（下标用 `i`、`j`，坐标用 `X`、`Y`） | 9608 循环中用 `i`、`j`、`n`；9618 Paper 4 的 Python 中用 `X`、`Y` |
| 关键字 | 大写 | 大写；IGCSE 答案偶尔写成 `Print`、`For`、`Next`、`Repeat` |
| 缩进 | 0478：四个空格，`THEN`/`ELSE` 和 `CASE` 分支缩进两个。9618：通常三个空格 | IG：先写 `IF … `，`THEN` 在下一行并缩进两格。9618：`IF … THEN` 写在同一行 |
| 数组 | 9618："Generally, a lower bound of 1 will be used"。0478："The first index can be zero or one"（第一个下标可以是 0 或 1） | 大多数伪代码从 1 开始；Python 中从 0 开始 |
| 参数 | 9618：除非写明 `BYREF`，否则按值传递 | `BYREF` 出现在 13 个 AS 子程序头中 |
| 声明 | 9618：声明是良好习惯 | IG-new 和 AS 答案都声明；有几份评分方案注明 "declarations are not required"（不要求声明）（0478_s25_ms_22 p6、0478_w25_ms_21） |

IGCSE 的 15 分题（2023 年起）用分级评分表评分，其最高档要求 "Suitable identifiers with names
meaningful to their purpose"（标识符恰当、名称能表达用途）和 "All of the data structures used
have meaningful names"（所用的所有数据结构都有有意义的名称）（如 0478_s23_ms_21、0478_m24_ms_22）。

## 4. 标识符

### 4.1 变量、常量和参数名的大小写风格

统计被赋值、被声明、用作循环变量或用作参数的不同名称，每份评分方案中每个名称只计一次：

| 风格 | IG-old | IG-new | AS-9608 | AS-9618 | AL-9608 | AL-9618 |
|---|---:|---:|---:|---:|---:|---:|
| PascalCase，多个单词（`TotalWeight`） | 86 | 95 | 246 | 210 | 121 | 76 |
| 首字母大写的单个单词（`Count`） | 44 | 85 | 102 | 88 | 55 | 45 |
| 带下划线的 Pascal（`Ticket_Number`） | 12 | 0 | 0 | 1 | 0 | 0 |
| snake_case（`total_weight`） | 3 | 0 | 0 | 5 | 0 | 0 |
| camelCase（`foundProc`） | 8 | 0 | 0 | 0 | 7 | 0 |
| 全小写（`total`） | 7 | 0 | 1 | 6 | 6 | 0 |
| 全大写（`MM`、`EOL`） | 1 | 0 | 2 | 16 | 1 | 0 |
| 单字母（`i`、`X`） | 3 | 9 | 11 | 11 | 5 | 2 |
| **PascalCase 占比** | **79 %** | **95 %** | **96 %** | **88 %** | **90 %** | **98 %** |

少数派分别是什么：

- **IG-old**（2016–2022）在同一份答案中混用多种风格：`num_sand_ordered`、`total_weight`
  （0478_s16_ms_22 p2–3），`Ticket_Number`、`Order_Complete`（0478_s18_ms_23、0478_w18_ms_21），
  `foundProc`、`posCount`、`count`（0478_s18_ms_21）。这些形式在 IG-new 中都不再出现。
- **AS-9618** 的全大写名称是简短缩写（时钟过程中的 `DD`、`MM`、`HH`、`SS`，以及 `EOL`、`P1`、
  `F1`），全小写名称是 9618_s24_ms_21 中的坐标 `x1, y1, x2, y2`。带下划线的名称是带编号的字段名或
  模块名（`Club_1`、`Limit_1`、`Stage_1`、`Report_1`）。
- **AL-9608** 的 camelCase 来自 2021 年 6 月的 Paper 4 评分方案（`binaryTree`、`topOfStack`、
  `searchValue`、`preOrder`，9608_s21_ms_41）。同一考季的 9618 Paper 4 评分方案（9618_s21_ms_41）
  的 Python 也是 camelCase（`linearSearch`、`bubbleSort`、`outputNodes`）。之后的评分方案又回到了
  PascalCase。

### 4.2 常用词汇

最常见的赋值目标显示了剑桥如何给状态命名：

| 作用 | 最常见的名称 |
|---|---|
| 循环下标 / 位置 | `Index`（在 AS 和 9618 中远多于其他），`Count`、`Counter`、`Row`、`Column`、`Col`，冒泡排序中的 `J`，`i`、`j`、`n`（仅 9608），`X`、`Y`（Paper 4 Python） |
| 总和与计数 | `Total`、`Count`、`Sum`、`NumberOfItems`、`NumFound`、`CountA`、`TotalWeight` |
| 标志 | `Found`、`Valid`、`NoSwaps`、`Swap`、`Swapped`、`Flag`、`Done`、`Finished`、`Continue`、`IsPal`、`EndOfGeoCode`、`Placed` |
| 当前项 | `ThisChar`、`NextChar`、`ThisLine`、`ThisNum`、`ThisValue`、`CurrentValue`、`CurrentNode`、`CurrentPointer` |
| 逐步构建的结果 | `OutString`、`NewString`、`MyString`、`Result`、`RetVal`、`ReturnValue`、`ReturnFlag`、`DataToReturn` |
| 文件 | `FileData`、`FileLine`、`ThisLine`、`Line`、`FileName`、`File`（Python 文件句柄） |
| 临时变量 | `Temp`、`TempString`、`TempInt`、`Temp1`、`Temp2` |
| 边界与大小 | `Boundary`、`Lower`、`Upper`、`First`、`Last`、`Low`、`High`、`Mid`、`Middle`、`MaxSize`、`ArrayLength` |
| 指针 | `HeadPointer`、`TailPointer`、`TopOfStack`、`TopPointer`、`FreePointer`、`FreeNode`、`RootPointer`、`StartPointer`、`FirstNode`、`FirstEmpty`、`NullPointer` |

系统使用的前缀：`This…` 表示正在处理的项，`Next…` 表示即将读取的项，`New…` 表示正在构建的值，
`Num…` / `NumberOf…` 表示计数，`Is…` 用于布尔函数。拼写采用英式（`Initialise`、`Colour`、
`Centre`）。

### 4.3 常量

伪代码用 `CONSTANT` 声明常量。全大写单词（`CONSTANT COMMA = ','`、`HASH`、`SPACE`、`EMPTY`、
`SPACECHAR`、`ASTERISK`）和 PascalCase（`CONSTANT MaxSize = 60`、`Capacity`、`TreeCount`、
`Unused`、`Terminator`）都有出现；9618 在 Paper 2 中使用 `CONSTANT` 33 次。9608 的 Python 用大写
书写常量（`COMMA = ','`、`TREECOUNT = 20`、`SAFELIMIT = 36`）。

### 4.4 过程、函数和类

| 组 | 子程序头数 | PascalCase 占比 | 示例 |
|---|---:|---:|---|
| AS-9608 | 130 | 100 % | `CalculateCustomerID`、`ValidatePassword`、`BubbleSort`、`SearchFile`、`GetAverageScore` |
| AS-9618 | 141 | 95 % | `IsPalindrome`、`GetStart`、`FindPassword`、`CheckFile`、`AddError`、`Stage_1` |
| IG-new | 10 | 100 % | `CheckDetails`、`Balance`、`Deposit`、`Odds`、`Same`、`NewData` |
| AL（伪代码） | 67 | 88 % | `InsertRecord`、`SearchHashTable`、`AddToList`、`FindValue`、`Enqueue`、`Pop` |

名称是"动词 + 宾语"（`AddNewScores`、`FindRepeats`、`OutputLowestScore`），标准操作则用单个动词
（`Push`、`Pop`、`Enqueue`、`Dequeue`、`Initialise`、`Search`、`Sort`、`Hash`）。回答"是/否"
问题的函数以 `Is`、`Check` 或 `Validate` 开头。类名是 PascalCase 的单数名词（`Vehicle`、
`Employee`、`Node`、`TreeClass`、`Balloon`）。

## 5. 语句与排版

各组计数（不重复代码块中的行数）：

| 特征 | IG-old | IG-new | AS-9608 | AS-9618 | AL-9608 | AL-9618 |
|---|---:|---:|---:|---:|---:|---:|
| 用 `←` 赋值 / 用 `=` 赋值 | 433 / 14 | 463 / 4 | 784 / 13 | 767 / 3 | 257 / 4 | 156 / 0 |
| `OUTPUT` / `PRINT` 行 | 188 / 101 | 243 / 4 | 106 / 0 | 113 / 0 | 16 / 0 | 32 / 0 |
| `THEN` 与 `IF` 同行 / 全部 `IF` | 36 / 155 | 0 / 99 | 14 / 189 | 187 / 205 | 2 / 86 | 47 / 51 |
| `NEXT Var` / 单独的 `NEXT` / `ENDFOR` | 23 / 14 / 0 | 84 / 6 / 0 | 0 / 1 / 88 | 84 / 1 / 1 | 2 / 0 / 18 | 6 / 0 / 0 |
| `WHILE … DO` / 全部 `WHILE` | 28 / 41 | 24 / 35 | 0 / 66 | 0 / 58 | 0 / 19 | 0 / 11 |
| `REPEAT` 循环 | 59 | 46 | 23 | 28 | 10 | 2 |
| `CASE OF x` / `CASE x OF` | 5 / 17 | 6 / 0 | 9 / 0 | 9 / 0 | 0 / 0 | 0 / 0 |
| `DECLARE` 行 | 0 | 103 | 363 | 289 | 91 | 104 |
| `CONSTANT` 行 | 0 | 7 | 25 | 33 | 2 | 5 |
| `// 注释` 行 | 29 | 61 | 116 | 106 | 39 | 12 |
| 标志用 `= TRUE/FALSE` 判断 / 用单独的 `NOT` 判断 | 17 / 9 | 1 / 12 | 49 / 7 | 50 / 9 | 8 / 2 | 7 / 3 |
| `RETURN` 语句 | 0 | 4 | 73 | 105 | 54 | 22 |
| `CALL` 语句 | 0 | 1 | 10 | 19 | 6 | 2 |

说明：

- **输出。** 多个值用逗号列出（`OUTPUT "Total is ", Total`）。9608 也用 `&` 连接，并用
  `NUM_TO_STRING` 转换数字（23 行 `OUTPUT … &`）；9618 更常用逗号（30 比 4）。提示语是 `INPUT`
  之前单独的一行 `OUTPUT`。
- **IF 排版。** IGCSE 和 9608 把 `THEN` 放在下一行、缩进两格；9618 写成 `IF Count > Max THEN`。
  `ELSE IF` 链写成嵌套的 `IF`，各自带 `ENDIF`。
- **循环。** 已知重复次数时用 `FOR`；查找和读文件用 `WHILE`；输入验证和"至少执行一次"的处理用
  `REPEAT … UNTIL`。`FOR` 循环有时会提前结束：把计数器设到终值之后（旧版 IGCSE，`Count ← 10`），
  在循环内 `RETURN`（约十份 AS 答案，多为 9618），以及在四份 2025 年 11 月的 9618 答案中使用
  `BREAK`（9618_w25_ms_21、9618_w25_ms_23），尽管指南中没有 `BREAK`。
- **续行。** 较长的条件用行尾的 `__` 或 `_` 拆开（9608_s20_ms_21、9618_w21_ms_22）。
- **一行多条语句。** 旧版 IGCSE 答案用 `;` 连接赋值（`CountA ← 0; CountB ← 0`），之后的评分方案
  不再这样写。

## 6. 数组、记录和对象

### 6.1 声明数组

`DECLARE StudentNames : ARRAY[1:30] OF STRING` 和
`DECLARE Contacts : ARRAY[1:100, 1:2] OF STRING` 是标准写法（旧版 IGCSE 不声明数组，有时用圆括号
取下标：`HoursHired(BoatNumber)`）。

| `ARRAY[...]` 中的下界 | IG-new | AS-9608 | AS-9618 | AL-9608 | AL-9618 |
|---|---:|---:|---:|---:|---:|
| 1 | 20 | 15 | 8 | 3 | 8 |
| 0 | 0 | 2 | 3 | 10 | 1 |

| `FOR` 循环的起始值 | IG-old | IG-new | AS-9608 | AS-9618 | AL-9608 |
|---|---:|---:|---:|---:|---:|
| 1 | 27 | 82 | 81 | 67 | 9 |
| 0 | 7 | 2 | 9 | 8 | 8 |

因此伪代码默认从 1 开始。从 0 开始的数组出现在下标本身是一个值的时候（表示小时的
`HoursArray[0 : 23]`，9618_s25_ms_22 p13；表示总数 0–35 的 `CheckTotal : ARRAY[0:35]`，
9618_w25_ms_22），出现在旧版 IGCSE 答案中（`FOR Count ← 0 TO 29`），以及 9608 Paper 4 中——那里
的答案必须与程序代码对应（`ARRAY[0:9] OF Node`）。

### 6.2 使用数组

- 数组在循环中逐个元素初始化：
  `FOR Index ← 1 TO 100` / `ResultArray[Index] ← "NO DATA"` / `NEXT Index`。
- 有效元素的个数保存在单独的变量中（`NumElements`、`CurrentSize`、`NumberRecords`），或者用哨兵值
  标记空元素（`""`、`-1`、`99999`、`"****"`、`"Empty"`）。
- 平行数组（`Names[]` 和 `Heights[]`）和二维表（`Results[InLoop, 4]`、`Contacts[Count, 1]`）在
  IGCSE 答案中很常见。记录（`TYPE … ENDTYPE`）和记录数组（`Loan[Index].StudentID`）出现在 AS 和
  A Level 中。
- 排序时如果要移动二维数组的一整行，每一列都用各自的临时变量交换（`Temp1`、`Temp2`、`TempString`）。

### 6.3 剑桥 Python 中的数组

| 形式 | AS-9608 | AL-9608 | AL-9618 | 示例 |
|---|---:|---:|---:|---|
| 先建空列表，再在循环中 `append` | 4 | 4 | 57 | `QueueData = []` / `for x in range(0, 20):` / `QueueData.append("")`（9618_s24_ms_41） |
| 用作声明的列表推导式 | 4 | 3 | 7 | `DataArray = [0 for I in range (100)]`（9618_w22_ms_41） |
| 二维的嵌套推导式 | 1 | 3 | 2 | `ArrayNodes=[[0 for X in range(3)] for Y in range(20)]`（9618_w21_ms_41） |
| `[value] * n` | 5 | 3 | 4 | `ArrayData= [[0]*10 for i in range(10)]`（9618_s22_ms_42） |
| 字面量列表 | 2 | 2 | 9 | `StackData = [0,0,0,0,0,0,0,0,0,0]`（9618_s22_ms_42） |

声明后面跟着一条注释，写明伪代码类型和大小：`Queue = [] #integer 50 elements`、
`HighScores = [] #String, 7 x 3`。
有两份答案建立的二维列表各行是同一个共享列表，这在 Python 中是错误的：
`ResultArray = [['*'] * 2] * 100`（9608_w18_ms_21 p12，一个"另一种"答案）和
`// Board =[["E"]*9]*9`（9608_s16_ms_41 p12）。第三份
`[[Record(-1,"")]*10 for i in range(100)]`（9618_w25_ms_41）在每一行中重复同一个记录对象。

### 6.4 记录和类

伪代码记录：

```
TYPE Student
   DECLARE StudentID : STRING
   DECLARE Email : STRING
   DECLARE Club_1 : INTEGER
ENDTYPE
DECLARE Membership : ARRAY [1:3000] OF Student
```
（9618_w21_ms_22 p5）

伪代码类（A Level）：`CLASS Car` / `PRIVATE Make : STRING` /
`PUBLIC PROCEDURE NEW (CarMake : STRING, …)` / `ENDCLASS`（9618_w22_ms_31）。

Paper 4 答案中的 Python 类：

- 属性是私有的 PascalCase：`self.__CurrentSpeed = 0`（226 行使用私有属性，54 行使用公有属性；
  公有属性主要出现在 2023–2025 年简单的类似记录的类中，如 `self.Key`、`self.Name`、
  `self.QueueArray`）；
- 每个属性都有 `GetX()`，需要时还有 `SetX(NewValue)`（9618 中共 58 个取值方法、18 个设值方法）；
- 构造函数参数用 `P` 标记：`IDP`、`MaxSpeedP`、`DescriptionP`、`pName`、`PColour`、`Numberp`；
- 属性后面跟类型注释：`self.__Name = pName #String`；
- 继承使用 `super().__init__(…)`（5 次）或 `Vehicle.__init__(self, …)`（9618 中 1 次，9608 中
  3 次）；子类通过父类的取值方法访问父类的私有数据（`Vehicle.GetCurrentSpeed(self)`，
  9618_s23_ms_41）。

## 7. 子程序和参数

- 子程序头声明每个参数的类型和返回类型：
  `FUNCTION ChangeSupp(Code1, Code2 : STRING) RETURNS INTEGER`。9618 中用 `CALL` 调用过程
  （`CALL Reset(Port)`）；IGCSE 常常不写 `CALL` 直接调用。
- 局部变量在子程序开头声明。
- 一个函数可以有多条 `RETURN` 语句。9618 答案会在 `FOR` 循环内返回
  （`IF Try = ThisValue THEN RETURN Num`，9618_w22_ms_22），并常常再给出一个带标志、只有一个出口
  的版本。
- 除非写明 `BYREF`，参数按值传递：
  `PROCEDURE UnPack(BYVAL TLine : STRING, BYREF SID, SDesc, SCost : STRING)`
  （9618_w22_ms_23）。
- 当函数有两个结果时，9618 伪代码返回一个记录：
  `FUNCTION Evaluate(NumStr1, NumStr2 : STRING) RETURNS Result`，设置 `RetVal.Done` 和
  `RetVal.Value`（9618_w24_ms_21 p8）；以及 `FUNCTION Pop() RETURNS PopData`（9618_w25_ms_23）。
- Python 答案用两种方式模仿 BYREF：把所有被修改的值作为元组返回，并在调用处重新赋值
  （`ReturnValue, QueueArray, QueueHeadPointer, QueueTailPointer, NumberOfItems = Enqueue(…)`，
  9618_s22_ms_41；`TheQueue, ReturnValue = Enqueue(TheQueue, DataInput)`，9618_w24_ms_42），
  或者把数据设为全局变量（见下一节）。

## 8. 剑桥写出的 Python

9618 Paper 4 答案（381 个不重复代码块，2 920 行），并以 9608 Paper 2 答案（92 个代码块）作比较：

| 特征 | 9608 P2 | 9618 P4 | 示例 |
|---|---:|---:|---|
| `global` 语句 | 0 | 148 | `def Push(DataToPush):` / `global StackData` / `global StackPointer` |
| 声明注释行（`# Index : INTEGER`、`#DECLARE …`） | 137 | 15 | `## Index, Count : Integer`（9608_s21_ms_22） |
| 行尾类型注释（`#integer`） | 2 | 82 | `QueueHeadPointer = 0 #integer` |
| `for X in range(0, N)` / `range(N)` / `range(1, N…)` / `for Item in …` | 7 / 7 / 16 / 2 | 83 / 21 / 5 / 21 | `for X in range(0, NumberRecords):` |
| `while` 循环 / `while True` | 41 / 3 | 56 / 1 | `while Valid == False:` |
| `X = X + 1` / `X += 1` | 34 / 5 | 31 / 23 | 两者都有；`+=` 仅从 2023 年起出现 |
| `== True` 或 `== False` / `not` | 15 / 14 | 33 / 2 | `if ReturnValue == True:` |
| `print` 用逗号分隔多个值 / 用 `+ str(...)` | 14 / 6 | 53 / 4 | `print("The number", DataToFind, "is found", NumberTimes, "times")` |
| `int(input(...))` 或 `float(input(...))` / 全部 `input` | 11 / 29 | 30 / 55 | `Score = int(input("Enter score"))` |
| `open` / `readline` / `for Line in File` / `.read()` | 20 / 28 / 1 / 0 | 29 / 23 / 13 / 5 | 见下文的文件读取 |
| `try` / `except IOError` / 裸 `except:` | 0 / 0 / 0 | 24 / 11 / 13 | `except IOError:` / `print("Could not find file")` |
| `.strip()` / `.split()` | 7 / 1 | 29 / 9 | `Line.strip()`、`Line.split(",")` |
| 返回元组 / 元组交换 / 通过 `Temp` 交换 | 0 / 0 / 4 | 10 / 4 / 6 | `return (True, Queue, Head, Tail, NumItems)` |
| f-string、`.format`、`with open`、`lambda`、`map`、`filter`、`sorted`、`.sort`、`sum`、`min`、`max` | 0 | 0 | （`"%s" % (...)` 出现两次，都在 2018 年 9608 Paper 4 中） |

其他观察：

- 9608 的 Python 中有大写常量（`COMMA = ','`）；9618 的 Python 多数直接写字面值。
- 交互式验证的写法是先给变量一个无效值，使 `while` 循环至少执行一次：`Score = -1` /
  `while Score < 0 or Score > 100000:`（9618_s22_ms_41），或者使用 `Valid` 标志；
  `while True` 加 `break` 很少见。
- 程序通常以一个 `#main` 部分结束，在其中设置全局变量并按顺序调用各子程序。
- 字符串处理使用带注释的下标和切片（`FileData[:5]  #First 5 characters`，9608_s17_ms_21），
  以及 `.upper()`、`.lower()`、`len()`、`str()`、`int()`；从不使用正则表达式。
- 评分方案中的 Python 并不总是合法的。例如：`Found = FALSE` 和 `Return Found`
  （9608_w20_ms_23），`while Index <= 1000 and Error <> TRUE:`（9608_s21_ms_21），
  没有冒号的 `def BubbleSort()` 和 `End Sub`（9608_s20_ms_22），Python 2 的
  `print "No file found"`（9608_s20_ms_42），没有括号的 `FileHandle.close`（9608_s18_ms_21）。
  考官评的是逻辑，所以这些答案被接受；真正的程序不能照抄。

## 9. 常见算法的写法

每种模式给出剑桥的伪代码写法、剑桥在 Python 中的写法，以及推荐的 Python 写法。近似计数来自
`stats/algorithm_patterns.txt`。

### 9.1 输入验证

伪代码（0478_s22_ms_21 p11）：

```
REPEAT
  IF Score < 0 OR Score > 100
    THEN
      OUTPUT "Your entry must be between 0 and 100, inclusive, please try again "
      INPUT Score
  ENDIF
UNTIL Score >= 0 AND Score <= 100
```

或者用 `WHILE` 重新输入的循环（`WHILE Score < 0 OR Score > 100 DO … INPUT Score … ENDWHILE`）。
Paper 4 的 Python 先给变量赋初值或使用标志：

```python
Valid = False
while Valid == False:
    Height = int(input("Enter the height in cm"))
    if Height >= 70 and Height <= 180:
        Valid = True
```
（9618_w24_ms_41）

推荐：使用标志形式，并在 `int(input(...))` 外加上 `try` / `except ValueError`
（如 9608_s17_ms_42 的 `StartDig`，该答案用的是裸 `except`）。

### 9.2 求和、计数、平均值

```
Total ← 0
FOR Count ← 1 TO 50
    Total ← Total + Number[Count]
NEXT Count
Average ← Total / 50
OUTPUT "The average is ", Average
```
（0478_m23_ms_22 p5；`Total ← 0` 给在代码正上方）。总和与计数器在循环前初始化，平均值在循环后
计算并输出。Python：在 `for X in range(0, len(DataArray)):` 中写 `Total = Total + DataArray[X]`，
从不使用 `sum()`。

### 9.3 最大值和最小值

有两种被接受的写法。用第一个元素初始化：
`Max ← List[1]` / `FOR Counter ← 2 TO 1000`（0478_s24_ms_22 p8），
`Highest ← Mark[1]`（9608_s18_ms_21）。或者用可能范围之外的值初始化：
温度用 `Min ← 100`（0478_w23_ms_22），50–99 分的成绩用 `LowestScore ← 100`（9608_s18_ms_22），
`MaxWeek ← -1000`（0478_w23_ms_23）。哨兵值写法更常见（约 16 份答案，而用第一个元素初始化的有
3–5 份）；只有在数据范围已知时它才正确。
通常也会记录最值的位置（`Position ← i`、`LowestIndex ← StudentCounter`）。

### 9.4 线性查找

三种写法，都使用显式下标：

```
Index ← 1
Found ← FALSE
WHILE Index <= 10000 AND Found = FALSE
   IF TagString[Index] = HashTag
      THEN
         Found ← TRUE
      ELSE
         Index ← Index + 1
   ENDIF
ENDWHILE
IF Found = FALSE
   THEN
      Index ← -1
ENDIF
RETURN Index
```
（9608_w20_ms_21 `GetIndex`；约 25 份伪代码和 Python 答案使用带 `Found` 标志的 `WHILE` 循环）

- `REPEAT … UNTIL Found = TRUE OR Index > 10`（9618_s21_ms_22 `IgnoreWord`）；
- `FOR Index ← 1 TO LENGTH(ThisString)`，循环内 `RETURN TRUE`，循环后 `RETURN FALSE`
  （9618_s22_ms_22 `Exists`）。

"未找到"用 `-1`、`FALSE`、`""` 或一条消息表示。Python 答案保持相同的结构
（`while Index < 500 and not Found:`，9608_w19_ms_22）。Python 的 `in` 只在 2016 年出现：一次是
配合 `.index` 做查找（9608_w16_ms_22，其后给出了两种显式循环的替代答案），两次是检查一个字符是否
在有效字符列表中（9608_w16_ms_41、9608_w16_ms_42）。

### 9.5 冒泡排序

AS 写法在 2017–2025 年间是标准写法：

```
PROCEDURE BubbleSort()
  DECLARE Temp : STRING
  DECLARE NoSwaps : BOOLEAN
  DECLARE Boundary, J : INTEGER
  Boundary ← 999
  REPEAT
     NoSwaps ← TRUE
     FOR J ← 1 TO Boundary
        IF Contact[J] > Contact[J+1]
           THEN
              Temp ← Contact[J]
              Contact[J] ← Contact[J+1]
              Contact[J+1] ← Temp
              NoSwaps ← FALSE
        ENDIF
     ENDFOR
     Boundary ← Boundary - 1
  UNTIL NoSwaps = TRUE
ENDPROCEDURE
```
（9608_s20_ms_22；9608_w17_ms_21、9618_w22_ms_22、9618_s25_ms_21 相同）

IGCSE 使用 `Swap` / `Flag`，配合 `REPEAT … UNTIL NOT Swap` 和逐步缩小的 `Last`
（0478_m24_ms_22），或 `WHILE Flag DO`（0478_s24_ms_23）。Paper 4 的 Python 答案常用两层嵌套的
`for` 循环而不用标志（`for X in range(0, ArrayLength-1):` / `for Y in range(0, ArrayLength-X-1):`，
9618_s23_ms_42）。较新的答案用元组交换（`DataArray[J], DataArray[J+1] =
DataArray[J+1], DataArray[J]`，9618_w22_ms_41、9618_w24_ms_41、9618_w25_ms_42）；其余的通过
`Temp` 交换。

推荐的 Python：采用 AS 写法，使用 `NoSwaps`、`Boundary` 并通过 `Temp` 交换。

### 9.6 插入排序

```
FOR Index ← 2 to 1000
   Value ← DataArray[Index]
   Position ← Index – 1
   IF DataArray[Position] > Value THEN
      WHILE Position >= 1 AND DataArray[Position] > Value
         DataArray[Position + 1] ← DataArray[Position]
         Position ← Position – 1
      ENDWHILE
      DataArray[Position + 1] ← Value
   ENDIF
NEXT Index
```
（9618_s25_ms_33；Python 版本见 9618_s25_ms_43 的 `InsertionSort`）。边界判断写在访问数组之前，
这在 Python 中很重要，因为 `DataArray[-1]` 是合法的。

### 9.7 二分查找

迭代写法（`Mid ← (Start + End) DIV 2`、`End ← Mid – 1`、`Start ← Mid + 1`，9618_s25_ms_22）和
递归写法（9618_w25_ms_42 `RecursiveBinarySearch`、9618_s24_ms_42）都有出现。Python 答案用 `//`、
`int(.../2)` 或 `Lower + (Upper - Lower) // 2` 计算中点。

### 9.8 字符串

字符串用 `MID(Text, Index, 1)` 逐个字符处理（约 45 份 AS 答案），并用 `&` 构建结果：

```
FOR Index ← 1 TO LENGTH(OldString)
   ThisChar ← MID(OldString, Index, 1)
   IF ThisChar = Char1 THEN
      ThisChar ← Char2
   ENDIF
   NewString ← NewString & ThisChar
NEXT Index
```
（9618_s23_ms_21 `Replace`）

使用的库例程（调用次数）：

| 例程 | IG-new | AS-9608 | AS-9618 | Python 对应写法 |
|---|---:|---:|---:|---|
| `LENGTH(S)` | 10 | 45 | 54 | `len(S)` |
| `MID(S, P, L)` | — | 46 | 42 | `S[P - 1 : P - 1 + L]` |
| `SUBSTRING(S, P, L)`（IGCSE） | 6 | — | — | `S[P - 1 : P - 1 + L]` |
| `LEFT(S, N)` / `RIGHT(S, N)` | — | 40 / 27 | 35 / 22 | `S[0:N]` / `S[len(S) - N:]` |
| `UCASE` / `LCASE` | 4 / 2 | 3 / 2 | 3 / 5 | `.upper()` / `.lower()` |
| `TO_UPPER` / `TO_LOWER` | — | 2 / 0 | 7 / 4 | `.upper()` / `.lower()` |
| `NUM_TO_STRING` / `NUM_TO_STR` | — | 28 / 0 | 0 / 16 | `str(N)` |
| `STRING_TO_NUM` / `STR_TO_NUM` | — | 11 / 2 | 0 / 31 | `int(S)` 或 `float(S)` |
| `INT(X)` | — | 24 | 27 | `int(X)`（向零截断） |
| `ROUND(X, D)` | 25 | — | — | `round(X, D)`（恰好一半时舍入到偶数） |
| `ASC` / `CHR` | — | 5 / 5 | 0 / 7 | `ord` / `chr` |
| `IS_NUM` | — | 2 | 6 | `try: float(S)` / `except ValueError:` |
| `RAND(X)` / `RND()` | — | 5 / 5 | 14 / 0 | `random.random() * X` |
| `RANDOM()`（0 到 1） | 6 | — | — | `random.random()` |
| `MOD` / `DIV` | 9 / 5 | 2 / 0 | 13 / 6 | `%` / `//`（操作数为负时 Python 向下取整） |
| `EOF(F)` | — | 26 | 20 | `readline()` 返回 `""` |
| `DAY`、`MONTH`、`YEAR`、`SETDATE`、`DAYINDEX`、`TODAY` | — | — | 合计 20 | `datetime.date` |

IGCSE 把 `MOD(X, 2)` 和 `DIV(Total, 60)` 写成函数；9618 把 `Count MOD 2` 和 `(Percent DIV 10)`
写成运算符。随机整数写作 `INT(RAND(6)) + 1`（9618）和 `ROUND(RANDOM() * 5, 0) + 1`（IGCSE）；
Python 答案用 `random.randint(1, 6)`。

Paper 4 的 Python 答案直接对字符串取下标（`Value[0]`、`Data[0:6]`），并从 2024 年起使用
`Line.split(",")`。一份 2025 年的答案用 `random.sample(range(0,101),20)` 填充数组
（9618_w25_ms_42），这是同类库捷径中唯一的一次。

### 9.9 文本文件

伪代码（约 40 份 AS 答案）：

```
OPENFILE "ScoreDetails.txt" FOR READ
WHILE NOT EOF("ScoreDetails.txt")
   READFILE "ScoreDetails.txt", FileData
   …
ENDWHILE
CLOSEFILE "ScoreDetails.txt"
```

模式有 `READ`、`WRITE` 和 `APPEND`（A Level 还有配合 `SEEK`、`GETRECORD`、`PUTRECORD` 的
`RANDOM`）。处理文件的方式是把各行复制到一个新文件（同时使用 `OPENFILE … FOR READ` 和
`OPENFILE … FOR WRITE`）。IGCSE 随 2023 年考纲引入文件处理
（`OPENFILE "Quotations.txt" FOR WRITE`，0478_s23_ms_23）。

Python：9608 Paper 2 答案用 `FileData = File.readline()` / `while FileData != "":` 读取；
9618 Paper 4 答案使用

```python
try:
    DataFile = open("Data.txt", 'r')
    for Line in DataFile:
        DataArray.append(int(Line))
    DataFile.close()
except IOError:
    print("Could not find file")
```
（9618_s23_ms_41）。从不使用 `with open`。

### 9.10 栈、队列、链表、树、哈希表

这些出现在 AL 伪代码中，也几乎出现在每一份 9618 Paper 4 评分方案中：

- **栈**：一个固定大小的数组加上 `TopOfStack`（或 `StackPointer`），初始化为 `-1` 或 `0`；
  `Push` 检查是否已满并返回 `TRUE` / `FALSE`，`Pop` 检查是否为空并返回一个哨兵值（`-1`、`""`、
  `"No data"`、`-999`）。Python 答案使用同样的全局数组和指针（9618_s22_ms_42、9618_s25_ms_42、
  9618_w25_ms_41）。
- **队列**：`HeadPointer`、`TailPointer` 和 `NumberItems`；循环队列在指针到达末尾时把它绕回 0
  （9618_s25_ms_41、9618_s23_ms_42）。
- **链表**：节点数组 `[Data, Next]`，配合 `FirstNode`/`StartPointer` 和空闲链表
  `FirstEmpty`/`FreeListPointer`；`-1` 是空指针（9618_w24_ms_41）。2025 年起出现了使用 `None` 的
  节点对象版本（9618_s25_ms_43）。
- **二叉树**：`[LeftPointer, Data, RightPointer]` 数组，配合 `RootPointer` 和 `FreeNode`
  （9618_w21_ms_41、9618_w25_ms_42），或者带 `GetLeft` / `SetLeft` 的 `Node` 对象
  （9618_s25_ms_41）；遍历是递归的。
- **哈希表**：`Hash ← Key MOD Size`，配合线性探测和绕回（9608_s17_ms_41、9608_s20_ms_41），
  或配合单独的溢出数组（9618_s25_ms_42）。

### 9.11 递归

递归答案用一个 `IF` 判断基本情况（`IF Number = 0 THEN RETURN 0`，9618_w23_ms_42；二分查找中的
`IF Upper < Lower THEN RETURN -1`），Paper 4 常常要求为同一个函数写出递归和迭代两个版本
（9618_w21_ms_41 `Unknown` / `IterativeUnknown`、9618_w23_ms_42）。

## 10. IG、AS 和 AL 的区别

| 方面 | IG（0478） | AS（9608 / 9618 Paper 2） | AL（Paper 3 / 4） |
|---|---|---|---|
| 典型答案 | 针对一个情境的完整程序：输入、验证、数组、求和、输出；2023 年起有 15 分题 | 独立的、带参数的过程和函数，字符串处理，文件 | 数据结构、记录、类、递归；Paper 4 用 Python/VB/Java |
| 声明 | 2023 年前没有；2023 年起用 `DECLARE` | 总是声明 | 伪代码中总是声明；Python 中写成注释 |
| 数组 | 平行一维数组和二维数组，2023 年起从 1 开始 | 从 1 开始的一维/二维数组，记录数组 | Paper 4 中从 0 开始 |
| 选择 | `IF` / `THEN` 在下一行；`CASE OF` | 9608 同 IGCSE；9618 写 `IF … THEN` | 同 AS |
| 循环 | `FOR … NEXT`、`REPEAT … UNTIL`、`WHILE … DO … ENDWHILE` | `FOR … ENDFOR`（9608）/ `NEXT`（9618）、`WHILE`、`REPEAT` | 同 AS |
| 库例程 | `ROUND`、`RANDOM`、`LENGTH`、`SUBSTRING`、`UCASE`、`LCASE`、`MOD()`、`DIV()` | `MID`、`LEFT`、`RIGHT`、`LENGTH`、`NUM_TO_STR`、`STR_TO_NUM`、`INT`、`RAND`、日期 | 同 AS |
| 子程序 | 很少；2023 年起有带类型参数的 `PROCEDURE`/`FUNCTION` | 核心内容；`BYREF`、`RETURNS`、`CALL` | 另加方法、构造函数、继承 |

## 11. 这对你的 Python 项目意味着什么

1. 你创建的每个名称都用 PascalCase：变量、常量、数组、参数、函数、类、属性和方法。Python 关键字和
   库名称保持原样（`def`、`print`、`range`、`self`、`__init__`、`.append`）。
2. 把每个算法写出来：初始化、循环、比较、计数、用 `Temp` 交换、返回。不要把它藏在 `sum`、`max`、
   `sorted`、`in`、`.index`、推导式或 `lambda` 里。
3. 使用从 0 开始的列表，并写带显式起点的 `range(0, N)`。翻译从 1 开始的伪代码循环
   `FOR Index ← 1 TO N` 时，要么改成 `range(0, N)` 并把 `Index` 当作从 0 开始的位置，要么保留从 1
   开始的位置并让第 0 个元素空着不用。在注释中说明你的选择。
4. 在每个子程序开头用注释声明变量（`# DECLARE Total : INTEGER`），并为每个数组写出伪代码类型和
   上下界（`# DECLARE Scores : ARRAY[0:29] OF INTEGER`）。
5. 用标志翻译 `REPEAT … UNTIL`（`Valid = False` / `while Valid == False:`）。
6. 显式比较标志（`while Found == False and Index < NumberOfItems:`）；计数写
   `Count = Count + 1`。
7. 用逗号输出（`print("Total is", Total)`）或用 `+ str(...)`；在 `try` / `except ValueError` 中
   用 `int(input("…"))` 读入数字。
8. 读文件用 `open`、`readline()` 或 `for Line in File` 循环，以及 `close()`，放在
   `try` / `except IOError` 中。
9. 对数据结构，让固定数组和指针保持可见。对小程序，使用带 `global` 语句的模块级数组可以重现
   Paper 4 的风格；对较大的项目，把数组及其指针放进一个带私有属性和 `Get`/`Set` 方法的类中。
10. 当子程序必须带回多个值时（伪代码的 `BYREF`），把它们一起返回并在调用处解包，或者返回一个小的
    记录对象，并在注释中说明。
11. 照搬剑桥的结构，而不是它的疏漏：不要写 `[[x] * n] * m`，不要裸 `except:`，不要写
    `TRUE`/`FALSE`，打开的每个文件都要关闭。

`AGENTS.md` 把这些要点变成带示例的规则；`examples/` 中是按这种方式编写并经过测试的程序。

## 12. 局限性

- 统计是用正则表达式对自动提取的文本逐行匹配计数得到的；少数代码块被拆开、合并或标错。比例是
  可靠的，单个计数可能相差几个。
- 同一考季的不同套卷共用题目，因此这些观察并不相互独立。
- 2023 年以前的 0478 Paper 2 评分方案常常用评分要点描述预期的程序，只给出一个示例答案；每份评分
  方案中的代码比 AS 少。
- Visual Basic、Java 和 Pascal 答案已经提取出来（`corpus/blocks.jsonl`），但本文没有分析。
- 使用的官方文件是 0478 2023–2025 考纲和 9618 2026 年版指南。较早的 9608 指引没有重新核对；上文
  关于 9608 的做法来自其评分方案。
