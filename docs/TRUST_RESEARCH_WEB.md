# 股东与信托：Web 交付与回滚

`/Trust_Research` 接入现有 Streamlit 侧栏。其他页面保持公开；本页在服务端核对预设密码后才建立私有数据读取器。列表、CSV、公告副本和卖方报告均不存放在本公开仓或静态目录。

## 当前冻结数据

私有仓：`chenhongdao2-blip/invest-dashboard-private-data`。当前版本及回滚版本以私有仓的 `releases/current/manifest.json` 和各版本清单为准；税额未在本模块重算。覆盖人数、股池数、模型日期、行情日期和扫描日期均从受保护快照读取，不在公开代码中固定。页面明确把可算金额与资料完整性分开。

首次仅读取版本清单和压缩名单，要求解压后小于 1MB；选中公司或人物时才读取对应明细，打开来源时才读取 PDF／报告，导出时才读取冻结 CSV。每个私有对象均按清单 SHA-256 校验。

公司名单的“总市值·人民币”取快照本币市值乘冻结模型展示汇率，只展示与行情截止日一致的数值；两项“占市值”比例使用同一个人民币分母。日期不匹配或市值缺失时显示待核，不用比例反推市值，也不称为实时行情。

## Streamlit Cloud Secrets

由部署负责人在应用设置的 Secrets 中设置以下三个**顶层键**，不要提交到 Git，也不要在工单或聊天中粘贴实际值：

```toml
TRUST_PASSWORD_SALT = "<由生成脚本输出>"
TRUST_PASSWORD_HASH = "<由生成脚本输出>"
TRUST_DATA_GITHUB_TOKEN = "<仅能读取私有数据仓 Contents 的细粒度令牌>"
```

在可信终端运行 `python3 jobs/trust_web/generate_password_hash.py`，按提示输入拟用密码，复制脚本输出的随机盐和摘要到 Secrets。令牌仅限私有仓 `invest-dashboard-private-data`、`Contents: Read-only`，不授予公开代码仓写权限。保存 Secrets 后重启应用，并分别验证错误密码、正确密码、退出、私有令牌失效和公开页仍可访问。未配置任一项时，本页只给出访问或读取错误，不回退到过时数据。

本地验证可设置 `TRUST_DATA_DIR` 指向独立私有数据包根目录；该变量仅用于本地，不配置到 Cloud。已发布的 Cloud 版本不读取本机路径、localhost 或 Wind 终端。

## 数据发布与回滚

冻结源模型和快照后运行 `jobs/trust_web/build_release.py --source <已验收项目> --evidence <已验收证据目录> --reports <以来源ID命名的私有报告目录> --output <私有仓目录> --release <YYYYMMDD-HHMM>`。输出目录必须在公开代码仓**之外**；再运行 `jobs/trust_web/verify_release.py <private-root>` 验文件指纹、覆盖分母、首包大小和本机路径。只向私有仓提交版本目录与 `releases/current/manifest.json`。更换数据版本时，先保留上一版目录，再更新 current 清单；回滚只恢复上一版 `releases/<id>/manifest.json` 为 current，并重新验证。不要改写已发布版本目录。

公开仓只提交页面、组件、导出脚本和合成测试。提交前执行 `git diff --cached --name-only` 及敏感数据扫描，不使用 `git add -A`。代码回滚使用公开仓上一提交；数据回滚由私有仓 current 清单控制，两者分别保留。

## 继续迭代 UI 的四步提示词

1. **平台与数据边界**：检查平台主题、导航和 Secrets；在独立 worktree 改受保护页面骨架。未鉴权前不得加载清单或明细。冻结税额不重算，先测门禁和导航。
2. **名单与筛选**：用五列公司表和两项独立占市值筛选；首屏只放动态覆盖统计与三条附来源的卖方 insight。股价表现只保留政策以来。在 1280px 宽度核查无横向滚动。
3. **人物与海底捞**：人物统一呈现起点、公式、来源、金额；分红和股票减持分列。海底捞区分大摩报告结论、反推和独立复算；已宣派未支付股息不得写成到账。逐笔明细、未知和共有池去重保持原口径。
4. **视觉与发布**：复核 1440×900、1280×800、390×844；用独立只读设计评议挑出最多三个问题。另测数值、来源、退出与错误令牌；真实 Cloud Secrets 配齐后再做线上验收。
