"""API route tests for CodePulse."""


def test_health_check(client):
    """GET /api/health returns 200 with status healthy."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "CodePulse"
    assert "version" in data


def test_analyze_simple_code(client):
    """POST /api/analyze with valid code returns analysis results."""
    payload = {
        "code": "def hello():\n    return 'world'\n",
        "filename": "hello.py",
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["filename"] == "hello.py"
    assert data["total_lines"] == 2
    assert data["functions_count"] == 1
    assert data["grade"] in ("A", "B", "C", "D", "F")
    assert "maintainability_index" in data
    assert "halstead_volume" in data


def test_analyze_empty_code(client):
    """POST /api/analyze with empty code returns 400."""
    resp = client.post("/api/analyze", json={"code": ""})
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data


def test_analyze_no_body(client):
    """POST /api/analyze with no JSON body returns 400."""
    resp = client.post("/api/analyze", content_type="application/json")
    assert resp.status_code == 400


def test_get_analyses_list(client):
    """GET /api/analyses returns a list."""
    resp = client.get("/api/analyses")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)


def test_get_stats(client):
    """GET /api/stats returns aggregate statistics."""
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "total_analyses" in data
    assert "avg_complexity" in data
    assert "grade_distribution" in data


def test_get_sample(client):
    """GET /api/sample returns sample code."""
    resp = client.get("/api/sample")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "code" in data
    assert len(data["code"]) > 50


def test_analyze_and_retrieve(client):
    """Analyze code then retrieve it by ID."""
    payload = {"code": "x = 1\ny = 2\n", "filename": "vars.py"}
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    analysis_id = data.get("id")
    assert analysis_id is not None

    resp2 = client.get(f"/api/analyses/{analysis_id}")
    assert resp2.status_code == 200
    detail = resp2.get_json()
    assert detail["filename"] == "vars.py"
    assert "details" in detail


def test_analysis_not_found(client):
    """GET /api/analyses/<nonexistent> returns 404."""
    resp = client.get("/api/analyses/99999")
    assert resp.status_code == 404


def test_analyze_complex_code(client):
    """Analyze code with known complexity and verify metrics."""
    code = '''
def process(data, flag):
    results = []
    for item in data:
        if flag:
            if item > 0:
                for sub in item:
                    if sub != 0:
                        results.append(sub)
            elif item == 0:
                pass
        else:
            try:
                results.append(str(item))
            except Exception:
                pass
    return results
'''
    resp = client.post("/api/analyze", json={"code": code, "filename": "complex.py"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["complexity_score"] > 1
    assert data["functions_count"] == 1
    assert data["maintainability_index"] > 0
