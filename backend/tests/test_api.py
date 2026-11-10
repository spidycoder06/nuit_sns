import io
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.detection import analyze, load_audio, make_demo, AudioValidationError

client = TestClient(app)


def test_health():
    assert client.get('/api/health').json()['status'] == 'ok'


def test_samples_and_analysis():
    for kind in ['normal', 'harmless_high', 'simulated_nonlinear']:
        response = client.get('/api/demo/' + kind)
        assert response.status_code == 200
        resp = client.post('/api/analyze', files={'file': (kind + '.wav', response.content, 'audio/wav')})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert 0 <= data['score'] <= 1.01
        assert data['sample_rate'] == 48000
        assert len(data['spectrum']) > 100
        assert data['verdict'] in ('suspicious', 'not_flagged')


def test_reject_low_sample_rate():
    import soundfile as sf
    out = io.BytesIO()
    sf.write(out, np.sin(np.arange(4000) / 20), 16000, format='WAV')
    response = client.post('/api/analyze', files={'file': ('low.wav', out.getvalue(), 'audio/wav')})
    assert response.status_code == 422
    assert '44,100' in response.json()['detail']


def test_invalid_upload_and_unknown_sample():
    assert client.post('/api/analyze', files={'file': ('x.wav', b'invalid', 'audio/wav')}).status_code == 422
    assert client.get('/api/demo/unknown').status_code == 404


def test_threshold_validation():
    wav = make_demo('normal')
    assert client.post('/api/analyze?threshold=1.5', files={'file': ('x.wav', wav, 'audio/wav')}).status_code == 422
