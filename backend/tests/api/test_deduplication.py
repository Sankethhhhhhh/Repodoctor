from app.api.report_service import deduplicate_recommendations


class TestDeduplicateRecommendations:
    def test_removes_duplicates(self) -> None:
        recs = ["Add tests", "Add tests", "Add CI"]
        result = deduplicate_recommendations(recs)
        assert result == ["Add tests", "Add CI"]

    def test_preserves_order(self) -> None:
        recs = ["First", "Second", "Third", "First", "Second"]
        result = deduplicate_recommendations(recs)
        assert result == ["First", "Second", "Third"]

    def test_keeps_first_occurrence(self) -> None:
        recs = ["Duplicate", "Unique", "Duplicate", "Another", "Unique"]
        result = deduplicate_recommendations(recs)
        assert result[0] == "Duplicate"
        assert result[1] == "Unique"
        assert result[2] == "Another"

    def test_no_duplicates_unchanged(self) -> None:
        recs = ["A", "B", "C"]
        result = deduplicate_recommendations(recs)
        assert result == ["A", "B", "C"]

    def test_empty_list(self) -> None:
        result = deduplicate_recommendations([])
        assert result == []

    def test_single_item(self) -> None:
        result = deduplicate_recommendations(["only"])
        assert result == ["only"]

    def test_all_duplicates(self) -> None:
        recs = ["same", "same", "same"]
        result = deduplicate_recommendations(recs)
        assert result == ["same"]

    def test_no_recommendations_lost(self) -> None:
        unique_recs = [f"Recommendation {i}" for i in range(20)]
        result = deduplicate_recommendations(unique_recs)
        assert len(result) == 20

    def test_ordering_not_sorted(self) -> None:
        recs = ["Zebra", "Apple", "Mango"]
        result = deduplicate_recommendations(recs)
        assert result == ["Zebra", "Apple", "Mango"]
