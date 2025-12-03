import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import threading
import time
import sys
import os
import uuid

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db
from models import User

PORT = 5001
BASE_URL = f"http://localhost:{PORT}"
DB_FILE = f'e2e_test_{uuid.uuid4().hex}.db'

@pytest.fixture(scope="module")
def test_server():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_FILE}'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
        
        if not User.query.filter_by(username="selenium_user").first():
            u = User(username="selenium_user")
            u.set_password("pass123")
            db.session.add(u)
            db.session.commit()

    def run_server():
        app.run(port=PORT, use_reloader=False)

    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    time.sleep(2)
    
    yield app

    if os.path.exists(DB_FILE):
        try:
            os.remove(DB_FILE)
        except Exception:
            pass

@pytest.fixture(scope="module")
def driver():
    options = webdriver.ChromeOptions()
    
    driver_path = ChromeDriverManager().install()
    if not driver_path.endswith(".exe"):
        folder = os.path.dirname(driver_path)
        potential_path = os.path.join(folder, "chromedriver.exe")
        if os.path.exists(potential_path):
            driver_path = potential_path
            
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)
    
    yield driver
    
    driver.quit()

def ensure_login(driver):
    if "login" in driver.current_url or len(driver.find_elements(By.NAME, "username")) > 0:
        user_input = driver.find_element(By.NAME, "username")
        user_input.clear()
        user_input.send_keys("selenium_user")
        
        pass_input = driver.find_element(By.NAME, "password")
        pass_input.clear()
        pass_input.send_keys("pass123")
        
        driver.find_element(By.TAG_NAME, "button").click()

def test_e2e_register_login(test_server, driver):
    unique_user = f"new_user_{uuid.uuid4().hex[:6]}"
    
    driver.get(f"{BASE_URL}/register")
    
    driver.find_element(By.NAME, "username").send_keys(unique_user)
    driver.find_element(By.NAME, "password").send_keys("pass123")
    driver.find_element(By.NAME, "confirm").send_keys("pass123")
    
    driver.find_element(By.TAG_NAME, "button").click()
    
    WebDriverWait(driver, 5).until(EC.url_contains("login"))
    assert "login" in driver.current_url
    
    driver.find_element(By.NAME, "username").send_keys(unique_user)
    driver.find_element(By.NAME, "password").send_keys("pass123")
    driver.find_element(By.TAG_NAME, "button").click()
    
    WebDriverWait(driver, 5).until(lambda d: "Log In" not in d.page_source)
    assert "Task Manager" in driver.page_source

def test_e2e_create_task(test_server, driver):
    driver.get(f"{BASE_URL}/tasks/new")
    
    ensure_login(driver)
    
    if "tasks/new" not in driver.current_url:
        driver.get(f"{BASE_URL}/tasks/new")
    
    driver.find_element(By.NAME, "title").send_keys("Selenium Task")
    driver.find_element(By.NAME, "description").send_keys("Automated testing")
    
    date_input = driver.find_element(By.NAME, "due_date")
    driver.execute_script("arguments[0].value = '2025-01-01';", date_input)
    
    driver.find_element(By.TAG_NAME, "button").click()
    
    assert "Selenium Task" in driver.page_source

def test_e2e_toggle_task(test_server, driver):
    driver.get(f"{BASE_URL}/")
    
    ensure_login(driver)
    
    toggle_forms = driver.find_elements(By.XPATH, "//form[contains(@action, '/toggle')]")
    
    if toggle_forms:
        toggle_button = toggle_forms[0].find_element(By.TAG_NAME, "button")
        toggle_button.click()
        assert "Task status updated" in driver.page_source
    else:
        pytest.fail("Aucun bouton de toggle trouvé")