# 低阶统计约束下的高阶组合结构：论文配套可复现代码

[English README](../README.md) · [算法与论文映射](experiment-mapping.md) · [实现边界](implementation-notes.md) · [论文数值核对](../README.md#verification)

这是上传的《**低阶统计约束下的高阶组合结构：变换、定向构造与可实现性**》
第 1–6 节 TeX 修订稿的配套实验仓库。

**设计重点：论文中的数值构造可以一键复现；核心函数也可以独立用于其他组合系统。**
因此不把论文里的答案直接写死为程序输出，而是将数据定义、合法交换、
精确增量、零和配对、残差扣减、可实现性求解与验收分开实现。

## 1. 克隆后先运行以下命令

要求 Python 3.10 或更新版本，运行算法及测试无需安装第三方计算库。

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m examples.run_all --output results-local
```

批量复现完毕后，还可以独立检查输出文件：

```bash
python tests/check_outputs.py results-local
python tests/verify_paper_numbers.py
```

单独运行任一案例（以第 5 节构造为例）：

```bash
python -m examples.ex03_directed_freeze
```

每个案例运行时打印完整 JSON；批量脚本把每个 JSON、
第 6 个实验的损失轨迹 CSV 写入指定输出目录。

## 2. 六组实验如何对应论文

| 文件 | 原稿对应部分 | 复现内容 |
|---|---|---|
| `examples/ex01_cross_stratum.py` | 第 3 节 | `{1}`、`{2,3}` 的跨基数交换，目标二阶损失从 4 下降到 0，精确增量 -4。 |
| `examples/ex02_zero_sum.py` | 第 4 节 | 六元素系统 `XA→XB`，签名抵消，所有低阶统计一致，`T3=4`、`L1=8`、`d3=1`；另外自动枚举匹配交换。 |
| `examples/ex03_directed_freeze.py` | 第 5 节 | 诱导 `124`、临时冻结、资源扣减、自由部分补偿产生 `456`、整体验收；`E:0→4→0`；再运行通用定向构造器。 |
| `examples/ex04_resource_conflict.py` | 第 6 节 | `a,b,c,d` 资源冲突：`abc` 是团候选，但在原始正关联覆盖下最大可实现次数为 0。附加对照实验：取消覆盖后可以出现一次。 |
| `examples/ex05_reachability.py` | 第 6 节 | 比较「一般 2-switch 终点」「逐步精确保持二阶计数的 2-switch」「把两次交换合成一次零和操作」的可达性。 |
| `examples/ex06_seeded_fitting.py` | 第 3 节算法的额外计算实验 | 最大流初始化、残差引导与随机混合提案、退火接受、固定种子和最优已见状态；从 `E=16` 拟合到 `E=0`。 |

**特别说明：**前五组的主要案例直接摘自论文。第六组的具体混合基数数据是
为检验代码可复用性而新增的基准实例，不冒充论文已有的数值算例。

## 3. 为什么这样拆分代码？

```text
paper/
  main-zh.tex / main-zh.pdf 中文原稿 / PDF 占位（待编译）
  main-en.tex / main-en.pdf 英文译文及编译 PDF
  references.bib            待填文献，未编造文献
src/hocomb/
  core.py                   系统、统计、损失和残差扣减
  switches.py               局部交换、精确损失增量、零和配对
  baseline.py               最大流初始化和残差引导拟合
  directed.py               诱导、临时冻结、补偿、验收
  feasibility.py            有限类型的精确整数可行性搜索
  reachability.py           状态图上的可达性搜索
examples/                    论文案例和额外计算实验
tests/                       自动测试、输出检查、论文数值核对
results/                     已生成的 JSON 与 CSV
docs/                        论文映射、实现边界、中文说明、发布清单
.github/workflows/           推送 GitHub 后的自动验证
```

**`core.py` 的关键建模细节：**组合系统是有记录编号的多重集；
重复出现的完整组合单元不能直接去重。`t_S` 统计包含 `S` 的完整记录数，
不是仅统计「恰好等于 S」的记录；这对不同基数的系统尤其重要。

**`switches.py` 的关键实现：**先用局部签名精确计算一次交换对
`(t_ij,s_i)` 的增量，再用
`2rΔ+Δ²` 计算原始加权平方损失的改变量，不依赖整表重算作候选评分。
测试还会将其与全量重算逐条对比。

**`directed.py` 的关键实现：**「临时冻结」不是「已经提交」。
只有整个候选恢复要求的二阶计数、满足硬约束并履行旧目标承诺后，
才可以永久提交新冻结记录。等号目标还必须继续全局检查。

**`feasibility.py` 的关键实现：**与原稿第 6 节的整数模型一致，
使用合法完整记录类型 `B` 的非负整数重数 `z_B`。
这里是精确的记忆化枚举器，适合论文的小系统；
并不声称它是可扩展到大规模的通用混合整数规划求解器。

## 4. 如何检查论文中的数字？

```bash
python -m examples.ex02_zero_sum
# 检查 same_pair_counts=true、L1_h3=8、T3=4、d3=1

python -m examples.ex03_directed_freeze
# 检查 E_initial=0、E_provisional=4、E_committed=0
# 检查剩余配额 (1,1,2,1,2,2) 和再次冻结后的 (1,1,2,0,1,1)

python -m examples.ex04_resource_conflict
# 检查 abc 属于 triangle_candidates，但 U_abc=0
```

通用定向构造器可能找到与论文展示顺序不同、但满足同一低阶条件的合法状态。
因此我们保留两条复现路径：**固定论文构造的逐步证书**，以及
**独立搜索得到的计算证书**。

## 5. 发布到 GitHub 前要做的事

你需要自行确认论文作者、软件与论文的版权声明及引用信息。
`CITATION.cff` 与 `LICENSE` 目前是**空占位文件**，请填入真实作者、版权人
与许可证后再公开发布。论文原稿没有正式的引文命令及参考文献条目，
所以没有凭空生成 BibTeX 内容。
英文版 PDF 已随源码提供；中文版 `main-zh.pdf` 目前是空占位文件，
可用 XeLaTeX 编译 `main-zh.tex` 生成（需要 Noto Serif CJK SC 字体）。
发布步骤见 `docs/upload-to-github.md`。

后续如果要投论文或做完整算法实验，可以继续加入更大规模的
MILP 求解、消融研究、运行时间统计以及不同随机种子的多次实验。
当前仓库的目标是 **可检查、可运行、和原稿一致的第一版研究代码**。
