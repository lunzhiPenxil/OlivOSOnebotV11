
# OlivOSOnebotV11 测试

测试通过 `OLIVOS_SOURCE` 指向真实 OlivOS 源码，并使用宿主框架提供的
`OlivOS.API.Event`、`OlivOS.messageAPI.Message_templet` 等对象，不再注入 OlivOS stub。
这样能覆盖插件与真实宿主之间的兼容边界。

`tests/conftest.py` 会依次查找 `OLIVOS_SOURCE`、`.ci/OlivOS`、同级 `OlivOS-dev` 和同级
`OlivOS`。导入 OlivOS 前会切换到临时工作目录，避免在插件仓库中生成 `lib/`、`plugin/`
等运行期目录。每个用例还会重置插件模块级状态、WebSocket 客户端列表和反向 HTTP 队列。

## 本地运行

```powershell
$env:OLIVOS_SOURCE = 'D:\MyProject\run\OlivOS-dev'
python -m pytest tests -q
```

## 覆盖率

```powershell
New-Item -ItemType Directory -Force test-results | Out-Null
python -m pytest tests `
  --cov=OlivOSOnebotV11 `
  --cov-branch `
  --cov-context=test `
  --cov-report=term-missing `
  --cov-report=xml:test-results/coverage.xml `
  --cov-report=json:test-results/coverage.json `
  --cov-report=html:test-results/html `
  --junitxml=test-results/junit.xml
python tests/coverage_summary.py test-results/coverage.json
```

覆盖率默认不设置门槛。当前基线（60 个测试，Windows + Python 3.11）为：

- 行覆盖率：63.25%（1129 / 1785）
- 分支覆盖率：54.89%（337 / 614）
- 行与分支综合覆盖率：61.11%

基线只是当前快照，不作为构建门槛。新增业务行为时应补充对应测试，不要用旧版本代码快照
代替当前实现的行为验证。

## CI

`.github/workflows/ci.yml` 固定为 `flake8 -> tests + coverage -> build`。测试任务会把
`OlivOS-Team/OlivOS` checkout 到 `.ci/OlivOS`，上传覆盖率、JUnit 与 HTML 报告；任一前置
任务失败时，后续任务不会执行。
