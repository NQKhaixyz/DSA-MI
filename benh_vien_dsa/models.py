"""
Module định nghĩa các lớp đối tượng (models) cốt lõi của hệ thống quản lý bệnh viện.
Mỗi lớp đại diện cho một thực thể trong quy trình khám chữa bệnh.
"""

from typing import Any, Optional, Tuple

try:
    from . import config
    from .data_structures import MultiLevelQueue
except ImportError:
    import config
    from data_structures import MultiLevelQueue


class Patient:
    """
    Lớp đại diện cho bệnh nhân trong hệ thống.
    """

    def __init__(
        self,
        patientID: str,
        fullName: str,
        gender: str,
        dob: str,
        citizenID: str,
        phone: str,
        email: str,
        address: str,
        bloodType: str,
        hasInsurance: bool = False,
    ):
        self.patientID = patientID  # Mã định danh bệnh nhân
        self.fullName = fullName  # Họ và tên đầy đủ
        self.gender = gender  # Giới tính
        self.dob = dob  # Ngày sinh (dd/mm/yyyy)
        self.citizenID = citizenID  # Số CCCD/CMND
        self.phone = phone  # Số điện thoại
        self.email = email  # Email liên hệ
        self.address = address  # Địa chỉ thường trú
        self.bloodType = bloodType  # Nhóm máu
        self.hasInsurance = hasInsurance  # Có BHYT hay không

    def updateInfo(self, **kwargs) -> None:
        """
        Cập nhật thông tin bệnh nhân theo các tham số truyền vào.
        Ví dụ: patient.updateInfo(phone="0909123456", address="HN")
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def displayInfo(self) -> str:
        """
        Trả về chuỗi tóm tắt thông tin bệnh nhân để hiển thị.
        """
        return (
            f"Patient[ID={self.patientID}, Name={self.fullName}, "
            f"Gender={self.gender}, DOB={self.dob}, "
            f"Insurance={self.hasInsurance}]"
        )

    def to_dict(self) -> dict:
        return {
            "patientID": self.patientID,
            "fullName": self.fullName,
            "gender": self.gender,
            "dob": self.dob,
            "citizenID": self.citizenID,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "bloodType": self.bloodType,
            "hasInsurance": self.hasInsurance,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Patient":
        return cls(
            patientID=data["patientID"],
            fullName=data["fullName"],
            gender=data["gender"],
            dob=data["dob"],
            citizenID=data["citizenID"],
            phone=data["phone"],
            email=data["email"],
            address=data["address"],
            bloodType=data["bloodType"],
            hasInsurance=data.get("hasInsurance", False),
        )


class Visit:
    """
    Lớp đại diện cho một lượt khám (một phiên khám bệnh) của bệnh nhân.
    """

    def __init__(
        self,
        visitID: str,
        patientID: str,
        visitDate: str,
        arrivalTime: str,
        checkinTime: Optional[str] = None,
    ):
        self.visitID = visitID  # Mã lượt khám
        self.patientID = patientID  # Mã bệnh nhân
        self.visitDate = visitDate  # Ngày khám
        self.arrivalTime = arrivalTime  # Thời gian đến bệnh viện
        self.checkinTime = checkinTime  # Thời gian check-in (nếu có)
        self.currentTimeSlot = ""  # Khung giờ hiện tại (ví dụ: "08:00", "10:00")
        self.severity = "BinhThuong"  # Mức độ nghiêm trọng (mặc định: Bình thường)
        self.queuePriority = (
            config.PRIORITY_WALKIN
        )  # Ưu tiên hàng đợi (mặc định: đến trực tiếp)
        self.status = config.STATUS_ACTIVE  # Trạng thái lượt khám
        self.departmentSequence: list[
            str
        ] = []  # Danh sách ID các khoa cần khám theo thứ tự
        self.currentDepartmentIndex = -1  # Chỉ số khoa hiện tại (-1: chưa bắt đầu)
        self.assignedDoctorIDs: list[str] = []  # Danh sách ID bác sĩ đã phụ trách
        self.assignedRoomID: Optional[str] = None  # ID phòng khám hiện tại
        self.usedServiceIDs: list[str] = []  # Các dịch vụ đã sử dụng
        self.prescriptionID: Optional[str] = None  # ID đơn thuốc
        self.billID: Optional[str] = None  # ID hóa đơn
        self.appointmentID: Optional[str] = None  # ID lịch hẹn (nếu có)
        self.appointmentDate: Optional[str] = None  # Ngày hẹn (để kiểm tra đến muộn)
        self.visited_departments: set[str] = (
            set()
        )  # Tập hợp các khoa đã khám (tránh lặp/cycle)

    def addDepartment(self, dept_id: str) -> Tuple[bool, str]:
        """
        Thêm một khoa vào chuỗi khám.
        Kiểm tra: không được lặp lại khoa đã khám (cycle) và không vượt quá 3 khoa/ngày.
        Trả về (True, msg) nếu thành công, (False, msg) nếu thất bại.
        """
        if dept_id in self.visited_departments:
            return False, f"Khoa '{dept_id}' đã được khám, không thể thêm lại (cycle)."
        if len(self.departmentSequence) >= config.MAX_DEPARTMENTS_PER_DAY:
            return False, f"Đã đạt giới hạn {config.MAX_DEPARTMENTS_PER_DAY} khoa/ngày."
        self.departmentSequence.append(dept_id)
        return True, f"Thêm khoa '{dept_id}' thành công."

    def moveToNextDepartment(self) -> Optional[str]:
        """
        Chuyển sang khoa tiếp theo trong chuỗi khám.
        Trả về ID khoa tiếp theo, hoặc None nếu đã hết.
        """
        self.currentDepartmentIndex += 1
        if 0 <= self.currentDepartmentIndex < len(self.departmentSequence):
            current_dept = self.departmentSequence[self.currentDepartmentIndex]
            self.visited_departments.add(current_dept)
            return current_dept
        return None

    def addService(self, service_id: str) -> None:
        """
        Ghi nhận một dịch vụ y tế đã được sử dụng trong lượt khám.
        """
        self.usedServiceIDs.append(service_id)

    def assignDoctor(self, doc_id: str) -> None:
        """
        Ghi nhận bác sĩ được phân công cho lượt khám.
        """
        self.assignedDoctorIDs.append(doc_id)

    def updatePriority(self, priority: int) -> None:
        """
        Cập nhật mức độ ưu tiên trong hàng đợi.
        """
        self.queuePriority = priority

    def updateStatus(self, status: str) -> None:
        """
        Cập nhật trạng thái lượt khám.
        """
        self.status = status

    def getCurrentDepartment(self) -> Optional[str]:
        """
        Lấy ID khoa đang khám hiện tại.
        """
        if 0 <= self.currentDepartmentIndex < len(self.departmentSequence):
            return self.departmentSequence[self.currentDepartmentIndex]
        return None

    def isCompleted(self) -> bool:
        """
        Kiểm tra xem lượt khám đã hoàn tất chuỗi khoa hay chưa.
        Trả về True nếu đã đi qua hết tất cả các khoa trong danh sách.
        """
        if not self.departmentSequence:
            return False
        return self.currentDepartmentIndex >= len(self.departmentSequence) - 1

    def to_dict(self) -> dict:
        return {
            "visitID": self.visitID,
            "patientID": self.patientID,
            "visitDate": self.visitDate,
            "arrivalTime": self.arrivalTime,
            "checkinTime": self.checkinTime,
            "severity": self.severity,
            "queuePriority": self.queuePriority,
            "status": self.status,
            "departmentSequence": self.departmentSequence,
            "currentDepartmentIndex": self.currentDepartmentIndex,
            "assignedDoctorIDs": self.assignedDoctorIDs,
            "assignedRoomID": self.assignedRoomID,
            "usedServiceIDs": self.usedServiceIDs,
            "prescriptionID": self.prescriptionID,
            "billID": self.billID,
            "appointmentID": self.appointmentID,
            "appointmentDate": self.appointmentDate,
            "visited_departments": list(self.visited_departments),
            "currentTimeSlot": self.currentTimeSlot,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Visit":
        obj = cls(
            visitID=data["visitID"],
            patientID=data["patientID"],
            visitDate=data["visitDate"],
            arrivalTime=data["arrivalTime"],
            checkinTime=data.get("checkinTime"),
        )
        obj.severity = data.get("severity", "BinhThuong")
        obj.queuePriority = data.get("queuePriority", config.PRIORITY_WALKIN)
        obj.status = data.get("status", config.STATUS_ACTIVE)
        obj.departmentSequence = data.get("departmentSequence", [])
        obj.currentDepartmentIndex = data.get("currentDepartmentIndex", -1)
        obj.assignedDoctorIDs = data.get("assignedDoctorIDs", [])
        obj.assignedRoomID = data.get("assignedRoomID")
        obj.usedServiceIDs = data.get("usedServiceIDs", [])
        obj.prescriptionID = data.get("prescriptionID")
        obj.billID = data.get("billID")
        obj.appointmentID = data.get("appointmentID")
        obj.appointmentDate = data.get("appointmentDate")
        obj.visited_departments = set(data.get("visited_departments", []))
        obj.currentTimeSlot = data.get("currentTimeSlot", "")
        return obj


class Doctor:
    """
    Lớp đại diện cho bác sĩ trong bệnh viện.
    """

    def __init__(
        self,
        doctorID: str,
        fullName: str,
        gender: str,
        dob: str,
        phone: str,
        email: str,
        address: str,
        departmentID: str,
        degree: str,
        licenseNumber: str,
        yearsExperience: int,
        roomID: Optional[str] = None,
    ):
        self.doctorID = doctorID  # Mã định danh bác sĩ
        self.fullName = fullName  # Họ tên đầy đủ
        self.gender = gender  # Giới tính
        self.dob = dob  # Ngày sinh
        self.phone = phone  # Số điện thoại
        self.email = email  # Email
        self.address = address  # Địa chỉ
        self.departmentID = departmentID  # ID khoa trực thuộc
        self.degree = degree  # Bằng cấp chuyên môn
        self.licenseNumber = licenseNumber  # Số chứng chỉ hành nghề
        self.yearsExperience = yearsExperience  # Số năm kinh nghiệm
        self.roomID = roomID  # ID phòng làm việc (nếu có)
        self.currentVisitID: Optional[str] = None  # ID lượt khám đang phụ trách

    def assignPatient(self, visit_id: str) -> None:
        """
        Phân công một lượt khám cho bác sĩ.
        """
        self.currentVisitID = visit_id

    def completeExamination(self) -> None:
        """
        Đánh dấu đã hoàn thành khám lượt hiện tại.
        """
        self.currentVisitID = None

    def addServiceToVisit(self, visit_obj: "Visit", service_id: str) -> None:
        """
        Thêm một dịch vụ vào lượt khám thông qua đối tượng Visit.
        """
        visit_obj.addService(service_id)

    def transferDepartment(self, visit_obj: "Visit", new_dept_id: str) -> None:
        """
        Chuyển bệnh nhân sang khoa mới bằng cách gọi visit.addDepartment.
        """
        visit_obj.addDepartment(new_dept_id)

    def to_dict(self) -> dict:
        return {
            "doctorID": self.doctorID,
            "fullName": self.fullName,
            "gender": self.gender,
            "dob": self.dob,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "departmentID": self.departmentID,
            "degree": self.degree,
            "licenseNumber": self.licenseNumber,
            "yearsExperience": self.yearsExperience,
            "roomID": self.roomID,
            "currentVisitID": self.currentVisitID,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Doctor":
        obj = cls(
            doctorID=data["doctorID"],
            fullName=data["fullName"],
            gender=data["gender"],
            dob=data["dob"],
            phone=data["phone"],
            email=data["email"],
            address=data["address"],
            departmentID=data["departmentID"],
            degree=data["degree"],
            licenseNumber=data["licenseNumber"],
            yearsExperience=data["yearsExperience"],
            roomID=data.get("roomID"),
        )
        obj.currentVisitID = data.get("currentVisitID")
        return obj


class Department:
    """
    Lớp đại diện cho một khoa trong bệnh viện.
    """

    def __init__(self, departmentID: str, departmentName: str):
        self.departmentID = departmentID  # Mã định danh khoa
        self.departmentName = departmentName  # Tên khoa
        self.doctorIDs: list[str] = []  # Danh sách ID bác sĩ thuộc khoa
        self.roomIDs: list[str] = []  # Danh sách ID phòng thuộc khoa
        self.serviceIDs: list[str] = []  # Danh sách ID dịch vụ của khoa

    def addDoctor(self, doc_id: str) -> None:
        """
        Thêm bác sĩ vào khoa.
        """
        self.doctorIDs.append(doc_id)

    def addRoom(self, room_id: str) -> None:
        """
        Thêm phòng vào khoa.
        """
        self.roomIDs.append(room_id)

    def addService(self, svc_id: str) -> None:
        """
        Thêm dịch vụ vào khoa.
        """
        self.serviceIDs.append(svc_id)

    def to_dict(self) -> dict:
        return {
            "departmentID": self.departmentID,
            "departmentName": self.departmentName,
            "doctorIDs": self.doctorIDs,
            "roomIDs": self.roomIDs,
            "serviceIDs": self.serviceIDs,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Department":
        obj = cls(
            departmentID=data["departmentID"],
            departmentName=data["departmentName"],
        )
        obj.doctorIDs = data.get("doctorIDs", [])
        obj.roomIDs = data.get("roomIDs", [])
        obj.serviceIDs = data.get("serviceIDs", [])
        return obj


class Room:
    """
    Lớp đại diện cho một phòng khám / phòng thực hiện dịch vụ.
    """

    def __init__(self, roomID: str, departmentID: str, doctorID: str):
        self.roomID = roomID  # Mã phòng
        self.departmentID = departmentID  # ID khoa quản lý
        self.doctorID = doctorID  # ID bác sĩ phụ trách phòng
        self.queues = MultiLevelQueue()  # Hàng đợi đa mức ưu tiên của phòng
        self.currentVisitID: Optional[str] = (
            None  # ID lượt khám đang diễn ra trong phòng
        )

    def addToQueue(self, visit_obj: "Visit", priority: int) -> None:
        """
        Thêm một lượt khám vào hàng đợi của phòng với mức ưu tiên cho trước.
        """
        self.queues.enqueue(visit_obj, priority)

    def callNextPatient(self) -> Optional["Visit"]:
        """
        Gọi bệnh nhân tiếp theo theo strict priority (3 -> 2 -> 1).
        Khi lấy được visit, đặt currentVisitID của phòng.
        """
        visit = self.queues.dequeue()
        if visit is not None:
            self.currentVisitID = visit.visitID
        return visit

    def getQueueSize(self) -> int:
        """
        Trả về tổng số bệnh nhân đang chờ trong phòng.
        """
        return self.queues.get_total_size()

    def isBusy(self) -> bool:
        """
        Kiểm tra xem phòng đang có bệnh nhân khám hay không.
        """
        return self.currentVisitID is not None

    def emergencyPreempt(self, visit_obj: "Visit") -> None:
        """
        Xử lý cấp cứu ưu tiên: xóa visit khỏi hàng đợi hiện tại (nếu đang nằm trong hàng đợi),
        sau đó đưa vào đầu hàng đợi cấp cứu (3) và cập nhật queuePriority của visit.
        """
        # Xóa khỏi hàng đợi cũ dựa trên priority hiện tại
        self.queues.remove(visit_obj, visit_obj.queuePriority)
        # Đưa vào đầu hàng đợi cấp cứu
        self.queues.appendleft_emergency(visit_obj)
        # Cập nhật ưu tiên của visit thành cấp cứu
        visit_obj.updatePriority(config.PRIORITY_EMERGENCY)

    def to_dict(self) -> dict:
        queues_data = {}
        for priority, q in self.queues.queues.items():
            queues_data[str(priority)] = [visit.visitID for visit in q]

        # Lấy tên bác sĩ từ global_doctors nếu có
        doctor_name = "Không rõ"
        try:
            from . import global_state

            doc = global_state.global_doctors.get(self.doctorID)
            if doc:
                doctor_name = doc.fullName
        except:
            pass

        return {
            "roomID": self.roomID,
            "name": self.roomID,  # Alias cho frontend
            "departmentID": self.departmentID,
            "doctorID": self.doctorID,
            "doctorName": doctor_name,  # Thêm tên bác sĩ cho frontend
            "queues": queues_data,
            "queueLength": self.getQueueSize(),
            "currentVisitID": self.currentVisitID,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Room":
        obj = cls(
            roomID=data["roomID"],
            departmentID=data["departmentID"],
            doctorID=data["doctorID"],
        )
        obj.currentVisitID = data.get("currentVisitID")
        obj.queues = MultiLevelQueue()
        return obj


class Service:
    """
    Lớp đại diện cho một dịch vụ y tế / xét nghiệm / thủ thuật.
    """

    def __init__(
        self, serviceID: str, serviceName: str, departmentID: str, price: float
    ):
        self.serviceID = serviceID  # Mã dịch vụ
        self.serviceName = serviceName  # Tên dịch vụ
        self.departmentID = departmentID  # ID khoa cung cấp dịch vụ
        self.price = price  # Giá dịch vụ

    def displayService(self) -> str:
        """
        Trả về chuỗi mô tả dịch vụ để hiển thị.
        """
        return (
            f"Service[ID={self.serviceID}, Name={self.serviceName}, "
            f"Dept={self.departmentID}, Price={self.price}]"
        )

    def to_dict(self) -> dict:
        return {
            "serviceID": self.serviceID,
            "serviceName": self.serviceName,
            "departmentID": self.departmentID,
            "price": self.price,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Service":
        return cls(
            serviceID=data["serviceID"],
            serviceName=data["serviceName"],
            departmentID=data["departmentID"],
            price=data["price"],
        )


class Medicine:
    """
    Lớp đại diện cho một loại thuốc trong kho.
    """

    def __init__(
        self, medicineID: str, medicineName: str, unitPrice: float, stockQuantity: int
    ):
        self.medicineID = medicineID  # Mã thuốc
        self.medicineName = medicineName  # Tên thuốc
        self.unitPrice = unitPrice  # Đơn giá
        self.stockQuantity = stockQuantity  # Số lượng tồn kho

    def addStock(self, qty: int) -> None:
        """
        Nhập thêm thuốc vào kho.
        """
        self.stockQuantity += qty

    def deductStock(self, qty: int) -> bool:
        """
        Xuất thuốc khỏi kho. Trả về False nếu không đủ tồn kho.
        """
        if qty > self.stockQuantity:
            return False
        self.stockQuantity -= qty
        return True

    def checkAvailability(self, qty: int) -> bool:
        """
        Kiểm tra xem kho có đủ số lượng thuốc yêu cầu hay không.
        """
        return self.stockQuantity >= qty

    def to_dict(self) -> dict:
        return {
            "medicineID": self.medicineID,
            "medicineName": self.medicineName,
            "unitPrice": self.unitPrice,
            "stockQuantity": self.stockQuantity,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Medicine":
        return cls(
            medicineID=data["medicineID"],
            medicineName=data["medicineName"],
            unitPrice=data["unitPrice"],
            stockQuantity=data["stockQuantity"],
        )


class Prescription:
    """
    Lớp đại diện cho đơn thuốc do bác sĩ kê.
    """

    def __init__(self, prescriptionID: str, visitID: str, doctorID: str):
        self.prescriptionID = prescriptionID  # Mã đơn thuốc
        self.visitID = visitID  # ID lượt khám
        self.doctorID = doctorID  # ID bác sĩ kê đơn
        self.medicineList: dict[str, int] = {}  # Dict: medicineID -> số lượng
        self.note = ""  # Ghi chú của bác sĩ

    def addMedicine(self, med_id: str, qty: int) -> None:
        """
        Thêm thuốc vào đơn. Nếu thuốc đã có thì cộng dồn số lượng.
        """
        if med_id in self.medicineList:
            self.medicineList[med_id] += qty
        else:
            self.medicineList[med_id] = qty

    def removeMedicine(self, med_id: str) -> None:
        """
        Xóa một loại thuốc khỏi đơn.
        """
        if med_id in self.medicineList:
            del self.medicineList[med_id]

    def calculateMedicineCost(self, inventory_dict: dict[str, "Medicine"]) -> float:
        """
        Tính tổng chi phí thuốc dựa trên đơn giá trong inventory_dict.
        """
        total = 0.0
        for med_id, qty in self.medicineList.items():
            medicine = inventory_dict.get(med_id)
            if medicine:
                total += medicine.unitPrice * qty
        return total

    def to_dict(self) -> dict:
        return {
            "prescriptionID": self.prescriptionID,
            "visitID": self.visitID,
            "doctorID": self.doctorID,
            "medicineList": self.medicineList,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Prescription":
        obj = cls(
            prescriptionID=data["prescriptionID"],
            visitID=data["visitID"],
            doctorID=data["doctorID"],
        )
        obj.medicineList = data.get("medicineList", {})
        obj.note = data.get("note", "")
        return obj


class Bill:
    """
    Lớp đại diện cho hóa đơn thanh toán của một lượt khám.
    """

    def __init__(self, billID: str, visitID: str):
        self.billID = billID  # Mã hóa đơn
        self.visitID = visitID  # ID lượt khám
        self.serviceCost = 0.0  # Tổng chi phí dịch vụ
        self.medicineCost = 0.0  # Tổng chi phí thuốc
        self.insuranceDiscount = 0.0  # Mức giảm trừ BHYT
        self.finalTotal = 0.0  # Tổng tiền cuối cùng
        self.paymentStatus = "ChuaThanhToan"  # Trạng thái thanh toán

    def calculateTotal(self) -> None:
        """
        Tính tổng tiền cuối cùng sau khi áp dụng giảm trừ BHYT.
        """
        self.finalTotal = (
            self.serviceCost + self.medicineCost
        ) - self.insuranceDiscount
        if self.finalTotal < 0:
            self.finalTotal = 0.0

    def applyInsurance(
        self, has_insurance: bool, discount_percent: float = 80.0
    ) -> None:
        """
        Áp dụng giảm trừ BHYT: nếu có BHYT thì giảm `discount_percent`% tổng viện phí.
        Mặc định giảm 80% (bệnh nhân chỉ phải trả 20%).
        """
        total = self.serviceCost + self.medicineCost
        if has_insurance:
            self.insuranceDiscount = total * (discount_percent / 100.0)
        else:
            self.insuranceDiscount = 0.0
        self.calculateTotal()

    def generateInvoice(self) -> str:
        """
        Tạo chuỗi hóa đơn chi tiết để in / hiển thị.
        """
        lines = [
            f"--- HÓA ĐƠN {self.billID} ---",
            f"Lượt khám: {self.visitID}",
            f"Chi phí dịch vụ : {self.serviceCost:,.0f} VND",
            f"Chi phí thuốc   : {self.medicineCost:,.0f} VND",
            f"Giảm trừ BHYT   : {self.insuranceDiscount:,.0f} VND",
            f"TỔNG THANH TOÁN : {self.finalTotal:,.0f} VND",
            f"Trạng thái      : {self.paymentStatus}",
        ]
        return "\n".join(lines)

    def markPaid(self) -> None:
        """
        Đánh dấu hóa đơn đã được thanh toán đầy đủ.
        """
        self.paymentStatus = "DaThanhToan"

    def to_dict(self) -> dict:
        return {
            "billID": self.billID,
            "visitID": self.visitID,
            "serviceCost": self.serviceCost,
            "medicineCost": self.medicineCost,
            "insuranceDiscount": self.insuranceDiscount,
            "finalTotal": self.finalTotal,
            "paymentStatus": self.paymentStatus,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Bill":
        obj = cls(
            billID=data["billID"],
            visitID=data["visitID"],
        )
        obj.serviceCost = data.get("serviceCost", 0.0)
        obj.medicineCost = data.get("medicineCost", 0.0)
        obj.insuranceDiscount = data.get("insuranceDiscount", 0.0)
        obj.finalTotal = data.get("finalTotal", 0.0)
        obj.paymentStatus = data.get("paymentStatus", "ChuaThanhToan")
        return obj


class Appointment:
    """
    Lớp đại diện cho lịch hẹn khám bệnh của bệnh nhân.
    """

    def __init__(
        self,
        appointmentID: str,
        patientID: str,
        departmentSequence: list[str],
        selectedDoctorID: str,
        appointmentDate: str,
        timeSlot: str,
    ):
        self.appointmentID = appointmentID  # Mã lịch hẹn
        self.patientID = patientID  # Mã bệnh nhân
        self.departmentSequence = departmentSequence  # Danh sách khoa cần khám
        self.selectedDoctorID = selectedDoctorID  # ID bác sĩ đã chọn
        self.appointmentDate = appointmentDate  # Ngày hẹn
        self.timeSlot = timeSlot  # Khung giờ hẹn
        self.status = "DaDat"  # Trạng thái lịch hẹn

    def confirmAppointment(self) -> None:
        """
        Xác nhận lịch hẹn (ví dụ sau khi bệnh nhân check-in).
        """
        self.status = "DaXacNhan"

    def cancelAppointment(self) -> None:
        """
        Hủy lịch hẹn.
        """
        self.status = "DaHuy"

    def updateSlot(self, new_slot: str) -> None:
        """
        Cập nhật khung giờ hẹn mới.
        """
        self.timeSlot = new_slot

    def to_dict(self) -> dict:
        return {
            "appointmentID": self.appointmentID,
            "patientID": self.patientID,
            "departmentSequence": self.departmentSequence,
            "selectedDoctorID": self.selectedDoctorID,
            "appointmentDate": self.appointmentDate,
            "timeSlot": self.timeSlot,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Appointment":
        obj = cls(
            appointmentID=data["appointmentID"],
            patientID=data["patientID"],
            departmentSequence=data.get("departmentSequence", []),
            selectedDoctorID=data["selectedDoctorID"],
            appointmentDate=data["appointmentDate"],
            timeSlot=data["timeSlot"],
        )
        obj.status = data.get("status", "DaDat")
        return obj
