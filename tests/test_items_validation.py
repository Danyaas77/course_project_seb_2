def test_create_item_accepts_boundary_length(client, auth_headers):
    boundary_name = "A" * 100
    r = client.post("/items", json={"name": boundary_name}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == boundary_name
    assert body["id"] == 1


def test_create_item_rejects_invalid_characters(client, auth_headers):
    r = client.post(
        "/items",
        json={"name": "Bad<script>payload"},
        headers=auth_headers,
    )
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == "validation_error"
    assert any(detail["field"].endswith("name") for detail in body["errors"])
