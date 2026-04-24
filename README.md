# jcc-s17-lineup

`jcc-s17-lineup` 是一个面向金铲铲 S17 的本地 Skill 包，内置两份 Excel 原始资料、合并后的结构化数据，以及一组可直接被 AI 或命令行调用的 Python 脚本。

## 包含内容

- `SKILL.md`: Skill 触发说明和调用流程
- `assets/source-workbooks/`: 原始 Excel 资料
- `assets/s17_data.json`: 合并后的结构化数据
- `scripts/query_units.py`: 查棋子
- `scripts/query_traits.py`: 查羁绊
- `scripts/query_knowledge.py`: 查装备、海克斯、经济运营、赛季概览
- `scripts/build_lineup.py`: 根据自然语言条件组阵容
- `scripts/evaluate_lineup.py`: 评估指定阵容
- `scripts/extract_data.py`: 从 Skill 内置 Excel 重新抽取数据

## 数据来源

- `assets/source-workbooks/金铲铲S17棋子羁绊大全.xlsx`
- `assets/source-workbooks/金铲铲S17赛季完全辅助手册.xlsx`

当前合并数据覆盖：

- 棋子
- 羁绊
- 羁绊档位
- 基础散件
- 成装
- 转职纹章
- 海克斯
- 升级经验
- D 牌概率
- 利息与收入规则
- 运营阶段建议
- 关键技巧

## 常用命令

在 Skill 根目录运行：

```bash
python3 scripts/query_units.py 游侠
python3 scripts/query_traits.py 暗星
python3 scripts/query_knowledge.py 白银 --category augments
python3 scripts/query_knowledge.py 8级 --category shop_odds
python3 scripts/build_lineup.py "在8人口下，开启羁绊数量最多的8个棋子"
python3 scripts/evaluate_lineup.py 贝蕾亚 雷克塞 卑尔维斯 卡莎 菲兹 泰隆 锐雯 烬
```

## 刷新数据

当 `assets/source-workbooks/` 里的 Excel 更新后，执行：

```bash
python3 scripts/extract_data.py
```

脚本会重新生成 `assets/s17_data.json`。

## 说明

- 阵容生成是确定性推荐工具，不是实时环境强度榜。
- 羁绊档位优先从羁绊效果文本中的 `(2)`、`（3）`、`2未来` 这类标记提取。
- 如果羁绊描述没有显式档位，工具会按 `1` 视为可计入激活，用于保留专属羁绊和描述型羁绊的信息。
