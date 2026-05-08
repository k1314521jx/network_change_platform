"""
AI审核响应解析服务

解析LLM返回的AI审核结果JSON，校验结构完整性。
"""

import json
import logging

logger = logging.getLogger("ai_review_service")

REQUIRED_DIMENSIONS = [
    "结构完整性", "实体一致性", "参数引用正确性",
    "命令-角色一致性", "执行安全性", "模板绑定质量",
    "整体连贯性与逻辑流",
]


def parse_ai_review_response(raw_response: str) -> dict:
    """解析AI审核LLM响应，校验结构完整性"""
    try:
        result = json.loads(raw_response)
    except json.JSONDecodeError:
        logger.error(f"[AI-Review] JSON解析失败，前500字符:\n{raw_response[:500]}")
        raise ValueError(f"AI审核返回非法JSON")

    if "score" not in result or not isinstance(result["score"], (int, float)):
        raise ValueError("AI审核结果缺少有效的score字段")
    if "dimensions" not in result or not isinstance(result["dimensions"], list):
        raise ValueError("AI审核结果缺少dimensions数组")
    if "suggestions" not in result or not isinstance(result["suggestions"], list):
        raise ValueError("AI审核结果缺少suggestions数组")
    if "summary" not in result or not isinstance(result["summary"], str):
        raise ValueError("AI审核结果缺少summary字段")

    if len(result["dimensions"]) != 7:
        raise ValueError(f"AI审核维度数量异常: 期望7个, 实际{len(result['dimensions'])}个")

    for dim in result["dimensions"]:
        if not all(k in dim for k in ("name", "score", "comment")):
            raise ValueError(f"维度缺少必要字段: {dim}")

    # score取整
    result["score"] = int(result["score"])

    logger.info(
        f"[AI-Review] 解析通过 | 总分: {result['score']} | "
        f"维度: {len(result['dimensions'])} | 建议: {len(result['suggestions'])}"
    )
    return result
