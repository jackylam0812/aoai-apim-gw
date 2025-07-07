# Azure OpenAI 多节点负载均衡方案

本项目展示了如何使用 Azure API Management (APIM) 作为代理服务器，实现多个 Azure OpenAI 服务节点的负载均衡和高可用性。

## 🎯 项目概述

该解决方案通过 Azure API Management 提供以下功能：
- **多节点负载均衡**：跨多个 Azure OpenAI 服务实例分发请求
- **优先级路由**：基于优先级和权重的智能路由策略
- **自动故障转移**：当某个节点不可用时自动切换到备用节点
- **托管身份认证**：使用托管身份安全访问 Azure OpenAI 服务
- **速率限制处理**：自动重试机制处理 429 错误
- **统一API网关**：为多个后端提供单一访问入口

## 🏗️ 架构图

```
Client Request
      ↓
Azure API Management (Gateway)
      ↓
Backend Pool (Load Balancer)
      ↓
┌─────────────┬─────────────┬─────────────┐
│  OpenAI-1   │  OpenAI-2   │  OpenAI-3   │
│ (Priority 1)│ (Priority 2)│ (Priority 2)│
│Canada East  │   UK South  │Spain Central│
└─────────────┴─────────────┴─────────────┘
```

## 📋 前置条件

- Azure 订阅
- Azure CLI 已安装并已登录
- Python 3.7+
- 对应权限创建以下资源：
  - Azure API Management
  - Azure OpenAI 服务
  - 资源组

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd AOAI-APIM-LB
```

### 2. 配置部署参数

编辑 `deploy.py` 文件中的关键配置：

```python
# 部署基本配置
deployment_name = "aoai-gateway-02"  # 更改为您的命名风格
resource_group_name = f"lab-{deployment_name}"
resource_group_location = "eastasia"  # 选择合适的区域

# API Management SKU
apim_sku = 'Basicv2'  # 可选: Developer, Basic, Basicv2, Standard, Premium

# OpenAI 资源配置 - 支持优先级和权重路由
openai_resources = [
    {"name": "openai1", "location": "canadaeast", "priority": 1},  # 最高优先级
    {"name": "openai2", "location": "uksouth", "priority": 2, "weight": 50},    # 次级优先级，权重50%
    {"name": "openai3", "location": "spaincentral", "priority": 2, "weight": 50} # 次级优先级，权重50%
]

# OpenAI 模型配置
openai_deployment_name = "gpt-4.1-api"
openai_model_name = "gpt-4.1"
openai_model_version = "2025-04-14"
openai_model_capacity = 500  # TPM (Tokens Per Minute， 500即分配500K TPM)
openai_model_sku = 'GlobalStandard'  # 或 'Standard'
openai_api_version = "2024-10-21"
```

### 3. 执行部署

```bash
# 登录 Azure (如果尚未登录)
az login

# 运行部署脚本
python deploy.py
```

部署完成后，脚本会输出：
- API Management 服务网关 URL
- 订阅密钥（用于API调用）
- 服务ID


## 📁 项目结构

```
AOAI-APIM-LB/
├── main.bicep          # 主要 Bicep 模板
├── policy.xml          # APIM 策略配置
├── params.json         # 部署参数（自动生成）
├── deploy.py           # 部署脚本
├── utils.py            # 工具函数
└── README.md           # 项目说明文档
```

## ⚙️ 配置详解

### OpenAI 资源配置

支持两种负载均衡策略：

1. **优先级路由**：
   ```python
   # Priority 1 优先使用，只有当 Priority 1 不可用时才使用 Priority 2
   {"name": "openai1", "location": "canadaeast", "priority": 1}
   {"name": "openai2", "location": "uksouth", "priority": 2}
   ```

2. **权重分配**：
   ```python
   # 同一优先级内按权重分配流量
   {"name": "openai2", "location": "uksouth", "priority": 2, "weight": 50}
   {"name": "openai3", "location": "spaincentral", "priority": 2, "weight": 50}
   ```

### 策略配置 (policy.xml)

核心策略功能：
- **托管身份认证**：自动获取访问令牌
- **后端路由**：动态选择后端服务
- **重试机制**：处理 429 (速率限制) 和 503 错误
- **错误处理**：统一错误响应格式

## 🔧 高级配置

### 自定义重试策略

修改 `policy.xml` 中的重试配置：

```xml
<retry count="2" interval="0" first-fast-retry="true" 
       condition="@(context.Response.StatusCode == 429 || 
                    (context.Response.StatusCode == 503 && 
                     !context.Response.StatusReason.Contains('Backend pool')))">
    <forward-request buffer-request-body="true" />
</retry>
```

### 添加更多 OpenAI 节点

在 `deploy.py` 中添加新的资源配置：

```python
openai_resources = [
    {"name": "openai1", "location": "eastus", "priority": 1},
    {"name": "openai2", "location": "westus", "priority": 2, "weight": 30},
    {"name": "openai3", "location": "northeurope", "priority": 2, "weight": 70},
    {"name": "openai4", "location": "japaneast", "priority": 3}  # 新增节点
]
```

## 📊 监控和诊断


### Azure 门户监控

在 Azure 门户中可以监控：
- **API Management 分析**：请求量、错误率、响应时间
- **OpenAI 服务指标**：Token 使用量、请求量、配额使用情况
- **后端健康状况**：服务可用性和性能指标

## 🛠️ 故障排除

### 常见问题

1. **部署失败**
   ```bash
   # 检查 Azure CLI 登录状态
   az account show
   
   # 检查区域可用性
   az account list-locations --output table
   ```

2. **API 调用 401 错误**
   - 确认托管身份权限
   - 检查 API 密钥是否正确

3. **负载均衡不工作**
   - 验证后端池配置
   - 检查策略 XML 语法
   - 查看 APIM 诊断日志

### 清理资源

```bash
# 使用工具函数清理所有资源
python -c "import utils; utils.cleanup_resources('aoai-gateway-02')"
```


## 💰 成本优化

1. **选择合适的 SKU**：
   - Developer：开发测试环境
   - Basic/Basicv2：生产环境
   - Standard/Premium：高可用性需求

2. **OpenAI 配额管理**：
   - 合理设置 TPM 限制
   - 使用 GlobalStandard SKU 获得更好的价格


## 📖 相关文档

- [Azure API Management 文档](https://docs.microsoft.com/azure/api-management/)
- [Azure OpenAI 服务文档](https://docs.microsoft.com/azure/cognitive-services/openai/)
- [Bicep 模板参考](https://docs.microsoft.com/azure/azure-resource-manager/bicep/)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。
