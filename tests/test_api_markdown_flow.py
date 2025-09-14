import json
import urllib.request


BASE = 'http://localhost:8080/api'


def _post(path: str, body: dict):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def test_markdown_preview_and_create_project():
    md = """---\ntitle: サンプル\n---\n# 見出し\n本文\n"""
    preview = _post('/markdown/preview', {'content': md, 'filename': 'sample.md'})
    assert 'quality' in preview and preview['quality'] >= 0

    created = _post('/projects/', {
        'input_source': 'markdown',
        'markdown_content': md,
        'markdown_filename': 'sample.md',
        'scenario_type': 'product_introduction'
    })
    assert 'project_id' in created
