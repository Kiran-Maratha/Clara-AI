import unittest
from app import create_app
from routes import is_malicious
from models import db

class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' 
        self.client = self.app.test_client()

        # Create an application context
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_is_malicious_function(self):
        """Test the SQli/XSS detection utility."""
        # Clean inputs should be False
        self.assertFalse(is_malicious("Hello, world!"))
        self.assertFalse(is_malicious("user123"))
        self.assertFalse(is_malicious("What's up?"))
        
        # Test XSS strings
        self.assertTrue(is_malicious("<script>alert(1)</script>"))
        self.assertTrue(is_malicious("javascript:alert('pwned')"))
        self.assertTrue(is_malicious("<img src='x' onerror='alert(1)'>"))
        
        # Test SQLi strings
        self.assertTrue(is_malicious("DROP TABLE users;"))
        self.assertTrue(is_malicious("admin' or 1=1 --"))
        self.assertTrue(is_malicious("UNION SELECT * FROM passwords"))
        
        # Test non-string input
        self.assertFalse(is_malicious(None))
        self.assertFalse(is_malicious(123))

    def test_index_page(self):
        """Test that the index page loads successfully."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<title>', response.data)

    def test_login_page(self):
        """Test that the login page loads successfully."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<form', response.data.lower())
        
    def test_register_page(self):
        """Test that the register page loads successfully."""
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<form', response.data.lower())

if __name__ == '__main__':
    unittest.main()
