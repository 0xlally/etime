from app.main import mask_database_url


def test_mask_database_url_hides_password():
    masked = mask_database_url(
        "postgresql+psycopg2://etime:secret-password@db:5432/etime"
    )

    assert masked == "postgresql+psycopg2://etime:***@db:5432/etime"
    assert "secret-password" not in masked


def test_mask_database_url_keeps_passwordless_urls():
    assert mask_database_url("sqlite:///./test.db") == "sqlite:///./test.db"
