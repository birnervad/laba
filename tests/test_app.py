# tests/test_app.py
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_page(client):
    """Тестируем главную страницу."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Загрузка изображения для обработки" in response.data

def test_captcha_endpoint(client):
    """Тестируем endpoint для генерации капчи."""
    response = client.get('/captcha')
    assert response.status_code == 200
    assert response.content_type == 'image/png'

def test_upload_endpoint(client):
    """Тестируем загрузку изображения."""
    # Создаем тестовый файл
    from io import BytesIO
    data = {
        'image': (BytesIO(b"fake image data"), 'test.jpg'),
        'cell_size': '10',
        'color': '#ffffff',
        'captcha': 'TESTCAPTCHA'  # Пример капчи
    }
    response = client.post('/', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert b"Неверный код проверки" in response.data  # Проверяем, что капча не прошла