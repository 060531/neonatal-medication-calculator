import unittest
from app import app

class BasicTestCase(unittest.TestCase):
    # ทดสอบเส้นทางหลัก (root route)
    def test_home(self):
        tester = app.test_client(self)
        response = tester.get('/')
        self.assertEqual(response.status_code, 200)
        # แปลง response.data เป็น string ก่อน
        self.assertIn("การบริหารยาในทารกแรกเกิด", response.data.decode('utf-8'))

    # เพิ่มการทดสอบเส้นทางใหม่ small_dose.html
    def test_small_dose(self):
        tester = app.test_client(self)
        response = tester.get('/small_dose')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Small Dose", response.data.decode('utf-8'))

if __name__ == '__main__':
    unittest.main()
