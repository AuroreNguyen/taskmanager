import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models import User, Task

@pytest.fixture
def client():
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False 

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def login(client, username, password):
    return client.post('/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)

def test_register_and_login(client):
    response = client.post('/register', data=dict(
        username='newuser',
        password='password123',
        confirm='password123'
    ), follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Registration successful" in response.data or b"Please log in" in response.data

    response = login(client, 'newuser', 'password123')
    
    assert response.status_code == 200
    assert b"Logged in successfully" in response.data

def test_create_task(client):
    client.post('/register', data={'username': 'taskuser', 'password': 'pw', 'confirm': 'pw'})
    login(client, 'taskuser', 'pw')

    response = client.post('/tasks/new', data={
        'title': 'Integration Test Task',
        'description': 'Testing creation',
        'due_date': '2025-12-31'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Task created" in response.data
    assert b"Integration Test Task" in response.data

def test_edit_and_toggle_task(client):
    client.post('/register', data={'username': 'edituser', 'password': 'pw', 'confirm': 'pw'})
    login(client, 'edituser', 'pw')

    client.post('/tasks/new', data={'title': 'Original Task', 'due_date': '2025-01-01'})
    
    with client.application.app_context():
        task = Task.query.filter_by(title='Original Task').first()
        task_id = task.id

    response = client.post(f'/tasks/{task_id}/toggle', follow_redirects=True)
    assert response.status_code == 200
    assert b"Task status updated" in response.data

    with client.application.app_context():
        t = Task.query.get(task_id)
        assert t.is_completed is True