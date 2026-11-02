# 本地运行证据

真实运行的轨迹、截图、报告和验收结果保存在本地，可能包含用户输入，因此默认不提交到 GitHub。

可运行 `python tests/live_power_acceptance.py` 重新生成自己的验收证据。此命令使用已配置的真实模型，会产生调用费用。普通自动测试使用 `python -m pytest -q tests`。
