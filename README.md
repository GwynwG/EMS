# 特种材料制备设备状态监测与智能预警原型系统

## 系统概述

本系统是一套面向生产现场设备状态监测、异常预警和寿命评估的完整软件原型。核心架构采用**四模块领域模型**：执行控制模块、能量输入模块、环境约束模块、状态维持模块。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 按顺序运行脚本

```bash
# 01. 导入 Excel 数据（无数据时自动生成 demo）
python scripts/01_import_excel_data.py

# 02. 数据清洗与样本构造
python scripts/02_clean_and_build_samples.py

# 03. 构建四模块特征
python scripts/03_build_module_features.py

# 04. 训练基线模型（PCA + Isolation Forest）
python scripts/04_train_baseline_models.py

# 05. 运行 Mock DCS 在线监测
python scripts/05_run_mock_online_monitoring.py

# 06. 启动 Streamlit 仪表盘
streamlit run app/streamlit_app.py
```

## 项目结构

```
equipment_monitoring_system/
├── configs/                    # 配置文件
│   ├── app_config.yaml         # 应用配置
│   ├── variable_dictionary.yaml # 变量字典
│   ├── model_config.yaml       # 模型配置
│   ├── feature_config.yaml     # 特征配置
│   └── alarm_rules.yaml        # 预警规则
├── data/                       # 数据目录
│   ├── raw_excel/              # 原始 Excel 数据
│   ├── processed/              # 处理后数据
│   ├── samples/                # 样本数据
│   └── demo/                   # Demo 数据
├── src/                        # 源码
│   ├── domain_framework/       # 四模块领域框架
│   ├── data_ingestion/         # 数据接入层
│   ├── data_foundation/        # 数据底座
│   ├── feature_engineering/    # 特征工程
│   ├── models/                 # 模型算法
│   ├── online_monitoring/      # 在线监测
│   ├── visualization/          # 可视化
│   └── utils/                  # 工具模块
├── scripts/                    # 流水线脚本
├── app/                        # Streamlit 应用
├── outputs/                    # 输出目录
└── tests/                      # 测试
```

## 四模块领域模型

| 模块 | 说明 | 核心变量 |
|------|------|----------|
| 执行控制 | 描述设备如何被调节 | 设定值、控制指令、阀位、联锁状态 |
| 能量输入 | 描述设备获得多少驱动能量 | 电压、电流、功率、能量效率 |
| 环境约束 | 描述设备在什么边界条件下运行 | 冷却水、真空度、环境温湿度 |
| 状态维持 | 核心状态层 | 温度、压力、振动、稳定性指标 |

### 耦合关系

- 执行控制 → 能量输入
- 执行控制 → 环境约束
- 能量输入 → 状态维持
- 环境约束 → 状态维持
- 状态维持 → 执行控制（反馈）

## 扩展真实 DCS 接口

1. 继承 `src/data_ingestion/dcs_connector_base.py` 中的 `DCSConnectorBase`
2. 实现 `connect()`, `disconnect()`, `read_latest()`, `read_range()` 方法
3. 在配置文件中将 `dcs.connector_type` 改为自定义类型
4. 在 `OnlineInferenceService` 中注入新的连接器

```python
class RealDCSConnector(DCSConnectorBase):
    def connect(self) -> bool:
        # 实现 OPC-UA / Modbus / API 连接
        ...
    def read_latest(self, tags, n_rows):
        # 实现实时数据读取
        ...
```

## 扩展更复杂模型

### XGBoost

1. 安装: `pip install xgboost`
2. 在 `configs/model_config.yaml` 中设置 `xgboost.enabled: true`
3. 在训练脚本中添加 XGBoost 训练流程

### Autoencoder

1. 安装: `pip install tensorflow`
2. 在 `configs/model_config.yaml` 中设置 `autoencoder.enabled: true`
3. 使用 `AutoencoderModel` 类进行训练

### PLS

1. 在 `configs/model_config.yaml` 中设置 `pls.enabled: true`
2. 使用 `PLSMonitor` 类

## 寿命评估（扩展方向）

寿命评估可通过以下方式实现：
1. 基于退化指标（`degradation_index`）的趋势外推
2. 基于健康指数的衰减曲线拟合
3. 基于历史故障数据的生存分析
4. 预留接口在 `src/models/` 目录下

## 技术栈

- Python 3.10+
- pandas / numpy / scikit-learn
- matplotlib（离线图表）
- Streamlit + streamlit-echarts（Web 界面）
- PyYAML（配置管理）
- joblib（模型持久化）
