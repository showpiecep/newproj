"""Разбор ответа судьи: починка синтаксиса не отменяет проверку контракта."""

import pytest

from {{ project_slug }}.domain.judge import JudgeParseError, parse_judge_response


def test_parses_plain_json() -> None:
    verdict = parse_judge_response(
        '{"criteria": [{"criterion": "relevance", "score": 1.0, "reasoning": "по делу"}]}'
    )

    assert verdict.scores() == {"relevance": 1.0}


def test_repairs_broken_json() -> None:
    verdict = parse_judge_response(
        '{"criteria": [{"criterion": "relevance", "score": 0.5, "reasoning": "частично"'
    )

    assert verdict.scores() == {"relevance": 0.5}


def test_rejects_score_out_of_range() -> None:
    with pytest.raises(JudgeParseError):
        parse_judge_response('{"criteria": [{"criterion": "relevance", "score": 7}]}')


def test_rejects_empty_verdict() -> None:
    with pytest.raises(JudgeParseError):
        parse_judge_response('{"criteria": []}')
