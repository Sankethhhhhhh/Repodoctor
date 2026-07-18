from typing import Any

from app.scoring.pipeline import ScoringResult


class Recommendation:
    def __init__(
        self,
        priority: str,
        title: str,
        estimated_score_gain: int,
    ) -> None:
        self.priority = priority
        self.title = title
        self.estimated_score_gain = estimated_score_gain

    def to_dict(self) -> dict[str, Any]:
        return {
            "priority": self.priority,
            "title": self.title,
            "estimated_score_gain": self.estimated_score_gain,
        }


def generate_recommendations(
    result: ScoringResult,
) -> list[Recommendation]:
    recommendations: list[Recommendation] = []

    for rule in result.rules:
        if not rule.passed and rule.recommendation:
            gain = rule.weight
            cat_weight = 0
            for cat in result.categories:
                if cat.name == rule.category.value:
                    cat_weight = cat.max_score
                    break

            estimated_gain = round(gain / cat_weight * 15) if cat_weight > 0 else gain

            priority = "HIGH" if estimated_gain >= 3 else "MEDIUM"

            recommendations.append(
                Recommendation(
                    priority=priority,
                    title=rule.recommendation,
                    estimated_score_gain=estimated_gain,
                )
            )

    recommendations.sort(
        key=lambda r: (
            0 if r.priority == "HIGH" else 1,
            -r.estimated_score_gain,
        )
    )

    return recommendations[:10]
