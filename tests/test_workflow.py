"""ใช้ unittest ของ Python: ทดสอบ workflow, สิทธิ์, CSRF และไฟล์ภาพจริง."""
from datetime import date, timedelta, datetime
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import re
import unittest

from PIL import Image

from app import create_app
from models import db, User, RepairRequest, RepairImage
from services import generate_request_no


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.app = create_app({
            'TESTING': True,
            'SECRET_KEY': 'test-key',
            'SQLALCHEMY_DATABASE_URI': 'sqlite://',
            'UPLOAD_FOLDER': self.folder.name,
        })
        with self.app.app_context():
            db.create_all()
            for role in ('admin', 'teacher', 'technician'):
                user = User(username=role, fullname=role, role=role)
                user.set_password('Practice123!')
                db.session.add(user)
            other = User(username='other', fullname='Other teacher', role='teacher')
            other.set_password('Practice123!')
            db.session.add(other)
            db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.folder.cleanup()

    def token(self, page):
        response = self.client.get(page)
        self.assertEqual(response.status_code, 200)
        match = re.search(r'name="csrf_token" value="([^"]+)"', response.get_data(as_text=True))
        self.assertIsNotNone(match)
        return match.group(1)

    def login(self, username):
        if self.logged_in():
            self.client.post('/logout', data={'csrf_token': self.token('/dashboard')})
        result = self.client.post('/login', data={
            'csrf_token': self.token('/login'), 'username': username, 'password': 'Practice123!',
        })
        self.assertEqual(result.status_code, 302)

    def logged_in(self):
        with self.client.session_transaction() as sess:
            return '_user_id' in sess

    def post(self, path, data, page='/dashboard'):
        return self.client.post(path, data={**data, 'csrf_token': self.token(page)}, follow_redirects=True)

    def create_repair(self, **overrides):
        data = dict(building='อาคาร 3', room='301', problem_type='aircon',
                    description='แอร์ไม่เย็น', urgency='high')
        data.update(overrides)
        return self.post('/repair/create', data, '/repair/create')

    def test_complete_workflow_and_scoped_access(self):
        self.login('teacher')
        response = self.create_repair()
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            repair = db.session.scalar(db.select(RepairRequest))
            repair_id = repair.id
            self.assertEqual(repair.status, 'pending')
            technician = db.session.scalar(db.select(User).where(User.role == 'technician'))
            technician_id = technician.id
        self.assertEqual(self.client.get('/admin/users').status_code, 403)
        self.login('other')
        self.assertEqual(self.client.get(f'/repair/{repair_id}').status_code, 404)
        self.assertNotIn('แอร์ไม่เย็น', self.client.get('/export/csv').get_data(as_text=True))
        self.login('admin')
        self.post(f'/repair/{repair_id}/assign', {
            'technician_id': technician_id, 'due_date': (date.today() + timedelta(days=2)).isoformat(),
        })
        self.login('technician')
        # ป้องกันข้ามขั้นตอน accepted → completed
        self.post(f'/repair/{repair_id}/status', {'action': 'complete', 'cost': '100', 'result': 'ซ่อมแล้ว'})
        with self.app.app_context():
            self.assertEqual(db.session.get(RepairRequest, repair_id).status, 'accepted')
        self.post(f'/repair/{repair_id}/status', {'action': 'start'})
        self.post(f'/repair/{repair_id}/status', {'action': 'complete', 'cost': '-1', 'result': 'ผิด'})
        with self.app.app_context():
            self.assertEqual(db.session.get(RepairRequest, repair_id).status, 'in_progress')
        self.post(f'/repair/{repair_id}/status', {'action': 'complete', 'cost': '1500.25', 'result': 'ล้างแอร์'})
        with self.app.app_context():
            repair = db.session.get(RepairRequest, repair_id)
            self.assertEqual(repair.status, 'completed')
            self.assertEqual(str(repair.cost), '1500.25')
            self.assertEqual(repair.result, 'ล้างแอร์')
            self.assertEqual(repair.completion_date, date.today())
        self.assertEqual(self.client.get(f'/repair/{repair_id}/print').status_code, 200)

    def test_images_and_csrf(self):
        self.login('teacher')
        self.assertEqual(self.client.post('/repair/create', data={}).status_code, 400)
        self.create_repair()
        with self.app.app_context():
            repair_id = db.session.scalar(db.select(RepairRequest.id))
        page = f'/repair/{repair_id}'
        self.post(f'{page}/images', {'image_type': 'before', 'image': (BytesIO(b'fake'), 'fake.jpg')}, page)
        with self.app.app_context():
            self.assertEqual(db.session.scalar(db.select(db.func.count()).select_from(RepairImage)), 0)
        image = BytesIO()
        Image.new('RGB', (10, 10), 'red').save(image, 'PNG')
        image.seek(0)
        self.post(f'{page}/images', {'image_type': 'before', 'image': (image, '../../photo.png')}, page)
        with self.app.app_context():
            stored = db.session.scalar(db.select(RepairImage))
            image_id = stored.id
            self.assertNotIn('/', stored.image_path)
            self.assertTrue((Path(self.folder.name) / stored.image_path).is_file())
        self.assertEqual(self.client.get(f'/images/{image_id}').status_code, 200)
        self.login('other')
        self.assertEqual(self.client.get(f'/images/{image_id}').status_code, 404)

    def test_number_validation_and_csv(self):
        self.assertEqual(generate_request_no(1, datetime(2026, 9, 1)), 'RP-202609-001')
        with self.assertRaises(ValueError):
            generate_request_no(1000)
        self.login('teacher')
        self.assertEqual(self.create_repair(problem_type='invalid').status_code, 400)
        self.create_repair(description='=1+1')
        self.create_repair()
        with self.app.app_context():
            numbers = db.session.scalars(db.select(RepairRequest.request_no).order_by(RepairRequest.id)).all()
            self.assertEqual(len(set(numbers)), 2)
            self.assertTrue(numbers[0].endswith('-001'))
            self.assertTrue(numbers[1].endswith('-002'))
        response = self.client.get('/export/csv')
        self.assertTrue(response.data.startswith(b'\xef\xbb\xbf'))
        self.assertIn("'=1+1", response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
