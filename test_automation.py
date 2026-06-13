import unittest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

class HospitalAutomationTest(unittest.TestCase):

    def setUp(self):
        # Khởi tạo trình duyệt Chrome tự động
        self.driver = webdriver.Chrome()
        # Địa chỉ chạy thử ứng dụng Flask mặc định của bạn
        self.base_url = "http://127.0.0.1:5000" 
        self.driver.maximize_window()
        time.sleep(2)

    def test_add_patient_and_assign_room(self):
        """Kịch bản: Tự động thêm bệnh nhân mới và kiểm tra tính năng lưu dữ liệu"""
        driver = self.driver
        driver.get(self.base_url)
        time.sleep(2)

        # 1. Giả lập click vào nút hoặc chuyển hướng sang trang Thêm bệnh nhân
        # (Selenium sẽ tự tìm các thẻ liên kết có chứa chữ 'Bệnh nhân' hoặc 'Thêm' để bấm)
        try:
            patient_nav = driver.find_element(By.PARTIAL_LINK_TEXT, "Bệnh nhân")
            patient_nav.click()
            time.sleep(1)
        except:
            print("Đang ở trang chủ hoặc không tìm thấy thanh điều hướng, tiếp tục test form...")

        # 2. Tự động điền dữ liệu giả lập vào Form Thêm Bệnh Nhân
        # Tìm ô nhập Họ tên (thường có name hoặc id là 'name' hoặc 'patient_name')
        name_input = driver.find_element(By.NAME, "name") 
        name_input.send_keys("Nguyễn Văn Máy Tính")

        # Tìm ô nhập Tuổi
        age_input = driver.find_element(By.NAME, "age")
        age_input.send_keys("25")

        # Tìm ô nhập Triệu chứng / Bệnh lý
        disease_input = driver.find_element(By.NAME, "symptom") # hoặc 'disease' tùy thuộc vào form HTML của bạn
        disease_input.send_keys("Đau đầu nhẹ do thức đêm viết kịch bản test tự động")
        time.sleep(2)

        # 3. Tự động bấm nút Gửi/Lưu form (Submit)
        submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()
        time.sleep(3) # Đợi hệ thống xử lý thuật toán dsa và lưu vào danh sách

        # 4. Kiểm tra kết quả mong đợi (Assertion)
        # Hệ thống sẽ tải lại trang, máy tính tự đọc xem chữ 'Nguyễn Văn Máy Tính' đã xuất hiện trong danh sách chưa
        page_source = driver.page_source
        self.assertIn("Nguyễn Văn Máy Tính", page_source, "Lỗi: Bệnh nhân mới không được lưu vào hệ thống!")
        print("Chúc mừng nhóm! Kịch bản kiểm thử tự động chạy THÀNH CÔNG và ĐẠT CHUẨN! 🎉")

    def tearDown(self):
        # Sau khi test xong thì tự động đóng trình duyệt gọn gàng
        self.driver.quit()

if __name__ == "__main__":
    unittest.main()