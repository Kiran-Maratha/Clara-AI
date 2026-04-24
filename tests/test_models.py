import unittest
from app import create_app
from models import db, User, Chat

class FlaskModelTestCase(unittest.TestCase):
    def setUp(self):
        # Create a test client and configure the app for testing
        self.app = create_app()
        self.app.config['TESTING'] = True
        # Use an in-memory database for testing so we don't interfere with the real db
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' 
        self.client = self.app.test_client()

        # Create an application context
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create all tables in the in-memory database
        db.create_all()

    def tearDown(self):
        # Remove the session and drop all tables
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_creation(self):
        """Test that a user can be successfully created and queried."""
        user = User(full_name='Test User', email='test@example.com', password='password123')
        db.session.add(user)
        db.session.commit()

        queried_user = User.query.filter_by(email='test@example.com').first()
        
        self.assertIsNotNone(queried_user)
        self.assertEqual(queried_user.full_name, 'Test User')
        self.assertEqual(queried_user.email, 'test@example.com')
        self.assertTrue(hasattr(queried_user, 'password'))

    def test_chat_creation(self):
        """Test that a chat can be created and associated with a user."""
        user = User(full_name='Test User 2', email='test2@example.com', password='password123')
        db.session.add(user)
        db.session.commit()

        chat = Chat(user_id=user.id, title='Test Initial Chat')
        db.session.add(chat)
        db.session.commit()

        queried_chat = Chat.query.filter_by(title='Test Initial Chat').first()
        
        self.assertIsNotNone(queried_chat)
        self.assertEqual(queried_chat.user_id, user.id)
        self.assertFalse(queried_chat.is_starred) # Default value should be False

if __name__ == '__main__':
    unittest.main()
