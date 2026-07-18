import pytest

from app.github.service import parse_repo_url


class TestParseRepoUrl:
    def test_owner_repo_format(self) -> None:
        owner, repo = parse_repo_url("facebook/react")
        assert owner == "facebook"
        assert repo == "react"

    def test_full_url_format(self) -> None:
        owner, repo = parse_repo_url("https://github.com/facebook/react")
        assert owner == "facebook"
        assert repo == "react"

    def test_url_with_trailing_slash(self) -> None:
        owner, repo = parse_repo_url("https://github.com/facebook/react/")
        assert owner == "facebook"
        assert repo == "react"

    def test_url_with_git_suffix(self) -> None:
        owner, repo = parse_repo_url("https://github.com/facebook/react.git")
        assert owner == "facebook"
        assert repo == "react"

    def test_invalid_url_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid repository URL"):
            parse_repo_url("not-a-repo")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid repository URL"):
            parse_repo_url("")

    def test_whitespace_trimmed(self) -> None:
        owner, repo = parse_repo_url("  facebook/react  ")
        assert owner == "facebook"
        assert repo == "react"

    def test_dashes_in_names(self) -> None:
        owner, repo = parse_repo_url("my-org/my-repo-name")
        assert owner == "my-org"
        assert repo == "my-repo-name"

    def test_dots_in_names(self) -> None:
        owner, repo = parse_repo_url("user.name/repo.name")
        assert owner == "user.name"
        assert repo == "repo.name"
