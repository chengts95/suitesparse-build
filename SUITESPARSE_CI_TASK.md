# SuiteSparse Cloud CI 项目任务书

## 1. 项目目标

为 RustPower 建立一个独立、可复用、以 GitHub Actions 为真实构建环境的 SuiteSparse 二进制构建系统。

本项目的构建基础设施必须：

1. **最低要求：KLU 必须能够稳定构建并通过链接/求解 smoke test。**
2. 目标支持 **SuiteSparse 全套组件**。
3. 同时生成 **静态库和动态库**。
4. RustPower / PyPI 下游默认优先消费 **静态 SuiteSparse**。
5. GraphBLAS 属于正式目标，不是可有可无的临时实验。
6. CUDA 为可选增强。没有 GPU/CUDA runner 时不得阻塞 CPU 构建。
7. 不依赖开发者本地拥有 Linux、Windows、macOS 或 ARM 构建机。
8. 主要调试循环由 **云端 AI agent + GitHub Actions** 完成。
9. 构建产物要能作为独立 artifact 被 RustPower、Python wheel、benchmark 或其他项目复用。

当前建议固定 SuiteSparse：

- SuiteSparse: `v7.14.1`
- KLU: `2.3.6`

SuiteSparse 版本必须集中定义，后续升级不得散落在多个 workflow 中。

---

## 2. 项目原则

### 2.1 GitHub Actions 是真实构建环境

本地机器不作为最终兼容性依据。

目标平台上的真实验证必须发生在 GitHub-hosted runner 或后续配置的专用 runner 上。

AI agent 的工作循环应为：

```text
读取任务书和仓库
    ↓
修改 workflow / scripts
    ↓
提交到工作分支
    ↓
push 到 GitHub
    ↓
触发 GitHub Actions
    ↓
读取失败 job / logs / artifacts
    ↓
修复
    ↓
重新 push / rerun
    ↓
直到验收条件成立
```

### 2.2 YAML 尽量薄

复杂构建逻辑应逐步抽取到：

```text
ci/
scripts/
```

但第一版允许先使用单个 workflow 验证构建方法。

### 2.3 CPU CI 与 CUDA CI 分离

默认 CPU 构建必须显式：

```text
SUITESPARSE_USE_CUDA=OFF
```

CUDA 后续单独增加 workflow/job，不得让 CUDA 缺失导致 CPU release 失败。

---

## 3. 构建范围

### P0：KLU 最低可用闭环

必须支持：

- SuiteSparse_config
- AMD
- COLAMD
- BTF
- KLU

并同时构建：

- shared libraries
- static libraries

最低验证：

1. headers 已安装。
2. static KLU 存在。
3. shared KLU 存在。
4. 编译一个最小 C/C++ KLU 程序。
5. 程序完成 analyze / factor / solve。
6. 检查求解结果。
7. 上传安装目录 artifact。

### P1：SuiteSparse 全套 CPU build

目标：

```text
SUITESPARSE_ENABLE_PROJECTS=all
BUILD_SHARED_LIBS=ON
BUILD_STATIC_LIBS=ON
SUITESPARSE_USE_CUDA=OFF
```

覆盖 SuiteSparse 顶层 `all` 所包含的组件，包括但不限于：

- SuiteSparse_config
- AMD
- BTF
- CAMD
- CCOLAMD
- COLAMD
- CHOLMOD
- CXSparse
- LDL
- KLU
- UMFPACK
- ParU
- RBio
- SPQR
- SPEX
- GraphBLAS
- LAGraph
- Mongoose

AI agent 应解决各平台 BLAS/LAPACK、GMP/MPFR、OpenMP、METIS 等依赖差异。

### P2：更多架构

目标顺序不在任务书中做产品决策，由蓝帽另行指定。

CI 架构应允许扩展到：

- Linux x86_64
- Linux ARM64
- Windows x86_64
- Windows ARM64
- macOS x86_64
- macOS ARM64

### P3：CUDA

CUDA 是独立增强项。

可能涉及：

- CHOLMOD CUDA
- SPQR CUDA
- SuiteSparse GPU runtime

CUDA job 的失败不能使 CPU artifact 无法发布，除非未来蓝帽明确改变此规则。

---

## 4. Artifact 规范

每个平台至少输出一个规范化 artifact。

建议目录：

```text
suitesparse-<version>-<platform>-<arch>/
├── include/
├── lib/
├── bin/
├── share/
├── licenses/
└── metadata.json
```

`metadata.json` 至少包含：

```json
{
  "suitesparse_version": "7.14.1",
  "platform": "linux",
  "arch": "x86_64",
  "compiler": "gcc",
  "build_type": "Release",
  "static": true,
  "shared": true,
  "cuda": false,
  "projects": "klu"
}
```

正式 full build 时 `projects` 改为 `all`。

不得依赖 artifact 文件名猜测内部构建配置。

---

## 5. PyPI / RustPower 消费规则

本 CI 项目只负责生成 SuiteSparse artifact，不直接决定 RustPower 是否长期保留 Python。

现阶段下游约束：

- RustPower Python wheel 默认优先使用 static SuiteSparse。
- 独立 CI 仍保留 shared libraries，供测试、开发和其他消费者使用。
- 不要求现在创建一个独立 `suitesparse` PyPI package。
- 后续若需要将 SuiteSparse 本身发布到 PyPI，应单独立项。

静态链接进入 wheel 前，必须单独检查各 SuiteSparse 组件及其依赖的许可证和再分发要求。

---

## 6. GitHub Actions 触发方式

第一版至少支持：

### Pull / Push 快速验证

默认只跑 KLU：

```text
profile = klu
CUDA = OFF
static = ON
shared = ON
```

### workflow_dispatch

允许 AI agent 手动指定：

- `profile=klu`
- `profile=full`
- SuiteSparse ref/tag
- 后续可增加 platform / arch / cuda 参数

这样 AI 调试某个平台时不必每次重跑全部矩阵。

### Release / tag

后续版本可在 SuiteSparse 版本 tag 或 RustPower release 时触发完整矩阵。

---

## 7. AI Agent 执行要求

交给 Codex Cloud 或其他云端 coding agent 时，使用以下完成标准。

Agent 必须：

1. 先阅读本任务书。
2. 检查仓库现有 `.github/workflows/`，避免破坏 RustPower 已有 workflow。
3. 将新 CI 保持为独立 workflow。
4. 首先让 KLU 在目标 matrix 上稳定通过。
5. 每个 job 失败时读取日志，定位到实际 CMake / compiler / linker / dependency 原因。
6. 不允许通过删除测试或静默忽略错误伪造绿色 CI。
7. KLU 全绿后，再推进 `profile=full`。
8. full build 中允许逐个平台修复依赖，但不得破坏已经工作的 KLU profile。
9. 每次重要修复后重新触发相应 GitHub Actions 验证。
10. 最终总结：
   - 哪些平台通过 KLU
   - 哪些平台通过 full SuiteSparse
   - static/shared 是否均存在
   - GraphBLAS 状态
   - CUDA 状态
   - 尚存问题
   - artifact 名称

如果 agent 无法读取 GitHub Actions 日志，应停止猜测，并明确报告缺少的 GitHub 权限、网络访问或工具能力。

---

## 8. 最低验收标准

项目的最低完成条件：

```text
KLU
+ SuiteSparse_config
+ AMD
+ COLAMD
+ BTF
```

在蓝帽指定的最低平台集合中：

- configure PASS
- build PASS
- install PASS
- static library present
- shared library present
- KLU smoke test PASS
- artifact upload PASS

在此之前，不把 CI 称为完成。

---

## 9. 全套验收标准

全套目标完成时：

- `SUITESPARSE_ENABLE_PROJECTS=all`
- static + shared 均构建
- GraphBLAS 构建成功
- CPU build 不依赖 CUDA
- 对应平台安装 artifact 可被后续 job 下载并使用
- KLU smoke test 仍然通过
- 至少增加一个 full-suite smoke/configuration check
- 依赖、编译器、SuiteSparse 版本可追踪

---

## 10. 非目标

当前阶段不要求：

- 强制 CUDA 成功
- 建立独立 SuiteSparse PyPI 包
- 为所有架构立即提供 production support
- 在开发者本地复现所有 runner
- 修改 RustPower 核心算法
- 为了 CI 兼容而降低 KLU/SuiteSparse 版本

---

## 11. 给云端 Agent 的首轮执行指令

> 在 RustPower 仓库中实现独立 SuiteSparse GitHub Actions CI。先以本任务书的 P0 为硬性目标。使用 SuiteSparse v7.14.1。CI 必须同时构建 static 和 shared libraries，显式禁用 CUDA，并对 KLU 做真实 compile/link/solve smoke test。不要依赖开发者本地环境。通过 GitHub Actions runner 验证 Linux、Windows、macOS。KLU 稳定后再尝试 full SuiteSparse，包括 GraphBLAS。每次失败读取真实 CI 日志后修复，不要猜测性跳过测试。保留现有 RustPower workflows。
