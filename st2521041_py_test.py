import pytest
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ─────────────────────────────────────────────
# FIXTURE FOR BROWSER SETUP
# ─────────────────────────────────────────────

@pytest.fixture(scope="module")
def driver():
    """Set up Chrome WebDriver and navigate to the local site before tests."""
    options = Options()
    # options.add_argument("--headless") # Uncomment if you want to run tests in headless mode (no UI)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,800")

    drv = webdriver.Chrome(options=options)

    # Get absolute path to index.html in the same directory as this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = f"file:///{current_dir}/index.html"
    drv.get(file_path)

    drv.implicitly_wait(2)
    yield drv
    drv.quit()  # Close browser after all tests


def login(driver, username="admin", password="@Dm1n"):
    """Helper function to perform login."""
    driver.find_element(By.ID, "username").clear()
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.XPATH, "//div[@class='login-panel']//button").click()
    time.sleep(0.5)


# ─────────────────────────────────────────────
# 1. LOGIN TESTS
# ─────────────────────────────────────────────

class TestLogin:

    def test_login_page_visible(self, driver):
        """Check that the login page is visible on initial load."""
        login_page = driver.find_element(By.ID, "loginPage")
        assert login_page.is_displayed(), "Login page should be visible on startup"

    def test_invalid_credentials_show_error(self, driver):
        """Check that invalid credentials show an error."""
        driver.find_element(By.ID, "username").send_keys("invalid_login")
        driver.find_element(By.ID, "password").send_keys("invalid_password")
        driver.find_element(By.XPATH, "//div[@class='login-panel']//button").click()

        error_msg = driver.find_element(By.ID, "loginError")
        assert error_msg.text == "Incorrect username or password.", \
            "Error message should appear for invalid login/password"

    def test_valid_login_shows_app(self, driver):
        """Check that valid credentials hide login and show main app."""
        driver.get(driver.current_url)  # Reset state
        login(driver)

        login_page = driver.find_element(By.ID, "loginPage")
        app = driver.find_element(By.ID, "app")

        assert not login_page.is_displayed(), "Login page should disappear after login"
        assert app.is_displayed(), "Main app should be visible after login"

    def test_user_initials_displayed(self, driver):
        """Check that user initials (AD) appear in the top-right corner."""
        initials = driver.find_element(By.ID, "userBadge")
        assert initials.text == "AD", f"Expected initials 'AD', got '{initials.text}'"


# ─────────────────────────────────────────────
# 2. NAVIGATION TESTS
# ─────────────────────────────────────────────

class TestNavigation:

    @pytest.fixture(autouse=True)
    def ensure_logged_in(self, driver):
        """Ensure user is logged in before each test."""
        app = driver.find_element(By.ID, "app")
        if not app.is_displayed():
            login(driver)

    def test_cameras_tab_active_on_login(self, driver):
        """Cameras tab should be active by default after login."""
        cameras = driver.find_element(By.ID, "cameras")
        assert cameras.is_displayed(), "Cameras section should be visible first"

    def test_navigate_to_lenses(self, driver):
        """Check navigation to Lenses tab."""
        driver.find_element(By.XPATH, "//nav//button[@data-page='lenses']").click()
        lenses = driver.find_element(By.ID, "lenses")
        assert lenses.is_displayed(), "Lenses section should be visible after click"

    def test_navigate_to_contact(self, driver):
        """Check navigation to Contact tab."""
        driver.find_element(By.XPATH, "//nav//button[@data-page='contact']").click()
        contact = driver.find_element(By.ID, "contact")
        assert contact.is_displayed(), "Contact section should be visible after click"

    def test_navigate_back_to_cameras(self, driver):
        """Check navigation back to Cameras."""
        driver.find_element(By.XPATH, "//nav//button[@data-page='cameras']").click()
        cameras = driver.find_element(By.ID, "cameras")
        assert cameras.is_displayed(), "Cameras section should be visible again"

    def test_only_one_page_visible_at_a_time(self, driver):
        """Ensure only one page is visible at a time."""
        driver.find_element(By.XPATH, "//nav//button[@data-page='lenses']").click()
        cameras = driver.find_element(By.ID, "cameras")
        contact = driver.find_element(By.ID, "contact")
        assert not cameras.is_displayed(), "Cameras should be hidden when Lenses is active"
        assert not contact.is_displayed(), "Contact should be hidden when Lenses is active"


# ─────────────────────────────────────────────
# 3. CONTACT FORM VALIDATION TESTS
# ─────────────────────────────────────────────

class TestContactForm:

    @pytest.fixture(autouse=True)
    def open_contact_page_and_clear(self, driver):
        """Navigate to contact page and clear form before each test."""
        app = driver.find_element(By.ID, "app")
        if not app.is_displayed():
            login(driver)

        driver.find_element(By.XPATH, "//nav//button[@data-page='contact']").click()

        # Clear all input fields
        for field_id in ("name", "email", "phone", "message"):
            field = driver.find_element(By.ID, field_id)
            field.clear()

        # Clear error messages via JavaScript
        driver.execute_script(
            "document.getElementById('nameError').innerText='';"
            "document.getElementById('emailError').innerText='';"
            "document.getElementById('phoneError').innerText='';"
            "document.getElementById('formSuccess').innerText='';"
        )

    # Name field tests

    def test_name_required_on_submit(self, driver):
        """Submitting without a name should show an error."""
        driver.find_element(By.XPATH, "//form//button[@type='submit']").click()
        error = driver.find_element(By.ID, "nameError")
        assert error.text == "Name is required.", \
            f"Expected name required error, got: '{error.text}'"

    # Email field tests

    def test_email_required_error_on_empty(self, driver):
        """Clearing email field should trigger required error."""
        email_field = driver.find_element(By.ID, "email")
        email_field.send_keys("a")
        email_field.send_keys(Keys.BACKSPACE)

        error = driver.find_element(By.ID, "emailError")
        assert error.text == "Email address is required.", \
            "Expected empty email error"

    def test_invalid_email_format_shows_error(self, driver):
        """Invalid email format should show error."""
        driver.find_element(By.ID, "email").send_keys("not_an_email")

        error = driver.find_element(By.ID, "emailError")
        assert "valid email" in error.text, \
            f"Expected email format error, got: '{error.text}'"

    def test_valid_email_clears_error(self, driver):
        """Valid email should clear error."""
        driver.find_element(By.ID, "email").send_keys("testuser@example.com")
        error = driver.find_element(By.ID, "emailError")
        assert error.text == "", \
            f"Email error should disappear, but got: '{error.text}'"

    # Phone field tests

    def test_phone_required_error_on_empty(self, driver):
        """Clearing phone field should trigger required error."""
        phone_field = driver.find_element(By.ID, "phone")
        phone_field.send_keys("1")
        phone_field.send_keys(Keys.BACKSPACE)

        error = driver.find_element(By.ID, "phoneError")
        assert error.text == "Phone number is required.", \
            "Expected empty phone error"

    def test_invalid_phone_shows_error(self, driver):
        """Too short phone number should show error."""
        driver.find_element(By.ID, "phone").send_keys("123")

        error = driver.find_element(By.ID, "phoneError")
        assert "7–15 digits" in error.text, \
            f"Expected phone length error, got: '{error.text}'"

    def test_valid_phone_clears_error(self, driver):
        """Valid phone number should clear error."""
        driver.find_element(By.ID, "phone").send_keys("+359 888 123456")
        error = driver.find_element(By.ID, "phoneError")
        assert error.text == "", \
            f"Phone error should disappear, but got: '{error.text}'"


# ─────────────────────────────────────────────
# 4. SEND MESSAGE TEST
# ─────────────────────────────────────────────

class TestSendMessage:

    @pytest.fixture(autouse=True)
    def open_contact_page(self, driver):
        """Ensure we are on contact page before sending."""
        app = driver.find_element(By.ID, "app")
        if not app.is_displayed():
            login(driver)
        driver.find_element(By.XPATH, "//nav//button[@data-page='contact']").click()

    def test_send_message_succeeds_with_valid_data(self, driver):
        """Valid form submission should show success message."""
        driver.find_element(By.ID, "name").clear()
        driver.find_element(By.ID, "name").send_keys("Ivan Ivanov")

        driver.find_element(By.ID, "email").clear()
        driver.find_element(By.ID, "email").send_keys("ivan@example.com")

        driver.find_element(By.ID, "phone").clear()
        driver.find_element(By.ID, "phone").send_keys("+359 888 000 111")

        driver.find_element(By.ID, "message").clear()
        driver.find_element(By.ID, "message").send_keys(
            "Hello, I would like to ask about camera rentals."
        )

        driver.find_element(By.XPATH, "//form//button[@type='submit']").click()

        success = driver.find_element(By.ID, "formSuccess")
        assert success.text == "Message sent successfully!", \
            f"Expected success message, got: '{success.text}'"


# ─────────────────────────────────────────────
# 5. LOGOUT TEST
# ─────────────────────────────────────────────

class TestLogout:

    def test_logout_reloads_to_login_page(self, driver):
        """Clicking Sign Out should return user to login page."""
        app = driver.find_element(By.ID, "app")
        if not app.is_displayed():
            login(driver)

        driver.find_element(By.XPATH, "//button[contains(@class, 'logout')]").click()
        time.sleep(0.5)

        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "loginPage"))
        )
        login_page = driver.find_element(By.ID, "loginPage")
        assert login_page.is_displayed(), \
            "Login page should be visible after logout"