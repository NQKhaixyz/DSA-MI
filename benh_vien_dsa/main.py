"""
Module main.py: Điểm vào chính của Hệ thống Quản lý Bệnh viện DSA.
Khởi tạo dữ liệu mẫu và chạy CLI tương tác.
"""

# Import hàm sinh dữ liệu mẫu và lớp CLI
try:
    from benh_vien_dsa.mock_generator import init_mock_data_small
    from benh_vien_dsa.cli import HospitalCLI
except ImportError:
    from mock_generator import init_mock_data_small
    from cli import HospitalCLI


if __name__ == "__main__":
    print("Đang khởi tạo dữ liệu mẫu...")
    init_mock_data_small()
    print("Khởi tạo xong. Chào mừng đến Hệ thống Quản lý Bệnh viện DSA!")
    cli = HospitalCLI()
    cli.run()
