"""Разбор ответа судьи: починка синтаксиса не отменяет проверку контракта."""

import pytest

from {{ project_slug }}.domain.judge import JudgeParseError, parse_judge_response


def test_parses_plain_json() -> None:
    verdict = parse_judge_response(
        '{"criteria": [{"criterion": "relevance", "reasoning": "по делу", "score": 100}]}'
    )

    assert verdict.scores() == {"relevance": 100.0}
    assert list(verdict.criteria[0].model_dump()) == ["criterion", "reasoning", "score"]


def test_repairs_broken_json() -> None:
    verdict = parse_judge_response(
        '{"criteria": [{"criterion": "relevance", "reasoning": "частично", "score": 50'
    )

    assert verdict.scores() == {"relevance": 50.0}


def test_rejects_score_out_of_range() -> None:
    with pytest.raises(JudgeParseError):
        parse_judge_response('{"criteria": [{"criterion": "relevance", "score": 101}]}')


def test_rejects_empty_verdict() -> None:
    with pytest.raises(JudgeParseError):
        parse_judge_response('{"criteria": []}')
