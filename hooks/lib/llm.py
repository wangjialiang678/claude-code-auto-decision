"""
llm.py - LLM 增强模块（可选）

支持两种调用方式：
1. claude: 直接调用 claude CLI（推荐，不需要额外 API Key）
2. openai: 调用 OpenAI API（需要 API Key）
"""

import json
import os
import subprocess
import re
from typing import Optional
from .storage import load_config


def is_llm_enabled() -> bool:
    """检查 LLM 是否启用"""
    config = load_config()
    return config.get("llm", {}).get("enabled", False)


def call_claude_cli(prompt: str, model: str = "haiku", timeout: int = 30) -> Optional[str]:
    """
    调用 claude CLI（推荐方式）

    直接使用 Claude Code 的订阅额度，不需要额外 API Key
    """
    try:
        result = subprocess.run(
            ['claude', '-p', prompt, '--max-turns', '1', '--model', model],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, 'CLAUDE_SKIP_HOOKS': '1'}  # 避免递归触发 hooks
        )
        return result.stdout.strip() if result.stdout else None
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        # claude CLI 不存在
        return None
    except Exception:
        return None


def call_openai_api(prompt: str, model: str = "gpt-4o-mini", timeout: int = 10) -> Optional[str]:
    """调用 OpenAI API（备选方式）"""
    config = load_config()
    api_key_env = config.get("llm", {}).get("api_key_env", "OPENAI_API_KEY")
    api_key = os.environ.get(api_key_env)

    if not api_key:
        return None

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            timeout=timeout,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


def call_llm(prompt: str) -> Optional[str]:
    """
    统一的 LLM 调用接口

    根据配置选择调用方式：
    - provider: "claude" → 调用 claude CLI（默认，推荐）
    - provider: "openai" → 调用 OpenAI API
    """
    config = load_config()
    llm_config = config.get("llm", {})

    if not llm_config.get("enabled"):
        return None

    provider = llm_config.get("provider", "claude")  # 默认用 claude CLI
    model = llm_config.get("model", "haiku")
    timeout = llm_config.get("timeout", 30)

    if provider == "claude":
        return call_claude_cli(prompt, model, timeout)
    elif provider == "openai":
        return call_openai_api(prompt, model, timeout)
    else:
        return None


def extract_json(text: str) -> Optional[dict]:
    """从文本中提取 JSON"""
    if not text:
        return None

    # 处理 markdown 代码块
    if "```" in text:
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if match:
            text = match.group(1)

    # 提取 JSON 对象
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None


def llm_decide(tool_name: str, tool_input: dict, context: dict = None) -> tuple[str, Optional[str]]:
    """
    使用 LLM 进行智能决策

    当规则没有命中时调用，返回 (action, reason)
    """
    if not is_llm_enabled():
        return "ask", None

    prompt = f"""你是一个 Claude Code 操作审批助手。

用户正在使用 Claude Code，Claude 想要执行以下操作：

工具: {tool_name}
输入: {json.dumps(tool_input, ensure_ascii=False)[:500]}

请判断这个操作是否应该自动批准。考虑：
1. 操作是否安全（不会造成数据丢失或系统损坏）
2. 操作是否是常见的开发操作
3. 操作是否可能需要用户确认

请用 JSON 格式回复：
{{"decision": "allow 或 deny 或 ask", "reason": "简短说明"}}

只返回 JSON，不要其他内容。"""

    result_text = call_llm(prompt)
    result = extract_json(result_text)

    if result:
        return result.get("decision", "ask"), result.get("reason")
    return "ask", None


def llm_generate_rule_suggestion(pattern_data: dict) -> Optional[dict]:
    """
    使用 LLM 生成更智能的规则建议

    可以泛化模式，生成更通用的规则
    """
    if not is_llm_enabled():
        return None

    prompt = f"""分析以下用户行为模式，生成一条自动决策规则：

行为数据:
{json.dumps(pattern_data, ensure_ascii=False, indent=2)}

请生成一条规则，格式：
{{
  "tool": "工具名",
  "action": "allow 或 deny",
  "pattern": "正则表达式（如果适用）",
  "path": "glob 模式（如果适用）",
  "reason": "规则说明"
}}

考虑：
1. 是否可以泛化模式（比如 npm test 和 npm run test 合并）
2. 规则应该尽量精确，避免误判
3. 说明要简洁明了

只返回 JSON，不要其他内容。"""

    result_text = call_llm(prompt)
    return extract_json(result_text)


def llm_generate_session_summary(feedback: list[dict], stats: dict) -> str:
    """
    使用 LLM 生成会话总结
    """
    if not is_llm_enabled():
        return generate_simple_summary(stats)

    # 只发送最近 20 条记录，避免 token 过多
    recent_feedback = feedback[-20:] if len(feedback) > 20 else feedback

    prompt = f"""总结以下 Claude Code 工作会话：

操作记录:
{json.dumps(recent_feedback, ensure_ascii=False, indent=2)}

统计:
{json.dumps(stats, ensure_ascii=False, indent=2)}

请生成一份简洁的会话总结，包括：
1. 主要完成了什么工作
2. 有哪些值得注意的决策
3. 学到了什么（如果有新规则）

用 Markdown 格式，不超过 200 字。"""

    result = call_llm(prompt)
    return result if result else generate_simple_summary(stats)


def generate_simple_summary(stats: dict) -> str:
    """生成简单的统计总结（无 LLM 时使用）"""
    return f"""## 统计

- 总操作数: {stats.get('total', 0)}
- 自动允许: {stats.get('auto_allowed', 0)}
- 自动拒绝: {stats.get('auto_denied', 0)}
- 用户批准: {stats.get('user_approved', 0)}
- 用户拒绝: {stats.get('user_rejected', 0)}

## 备注

本次会话未启用 LLM 总结功能。
"""
