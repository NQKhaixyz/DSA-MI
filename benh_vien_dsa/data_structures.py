"""
Module định nghĩa các cấu trúc dữ liệu đặc biệt cho hệ thống.
Bao gồm MultiLevelQueue: hàng đợi nhiều mức ưu tiên dùng collections.deque.
"""

from collections import deque
from typing import Any, Optional


def is_valid_time(visit_obj: Any) -> bool:
    """
    Kiểm tra xem bệnh nhân có đến đúng giờ hẹn hay không.
    Nếu bệnh nhân đến sau khung giờ đã đặt thì trả về False
    để dequeue() chuyển từ ưu tiên (2) → thường (1).
    """
    try:
        from . import global_state, config
    except ImportError:
        import global_state
        import config

    # Không phải đặt hẹn → luôn hợp lệ
    apt_id = getattr(visit_obj, "appointmentID", None)
    if not apt_id:
        return True

    # Kiểm tra bệnh nhân có đến trễ không
    time_slot = getattr(visit_obj, "currentTimeSlot", "")
    if time_slot:
        try:
            from datetime import datetime

            now = datetime.now()
            slot_str = time_slot.strip()
            # Xử lý định dạng "HH:MM" hoặc "HH:MM-HH:MM"
            if "-" in slot_str:
                end_str = slot_str.split("-")[1].strip()
            else:
                end_str = slot_str
            parts = end_str[:5].split(":")
            end_hour, end_min = int(parts[0]), int(parts[1])
            slot_end = now.replace(
                hour=end_hour, minute=end_min, second=0, microsecond=0
            )
            # Nếu giờ hiện tại > giờ kết thúc slot → đến trễ
            if now > slot_end:
                return False
        except (ValueError, AttributeError, IndexError):
            pass

    return True


class MultiLevelQueue:
    """
    Hàng đợi đa mức ưu tiên sử dụng 3 deque riêng biệt.
    Mức ưu tiên: 3 (Cấp cứu) > 2 (Hẹn trước) > 1 (Tới trực tiếp).
    """

    def __init__(self):
        # Khởi tạo 3 hàng đợi riêng biệt cho từng mức ưu tiên
        self.queues = {
            3: deque(),  # Hàng đợi cấp cứu (cao nhất)
            2: deque(),  # Hàng đợi đặt hẹn
            1: deque(),  # Hàng đợi tới trực tiếp
        }

    def enqueue(self, item: Any, priority: int) -> None:
        """
        Thêm phần tử vào CUỐI deque của mức ưu tiên tương ứng.
        """
        if priority in self.queues:
            self.queues[priority].append(item)

    def dequeue(self) -> Optional[Any]:
        """
        Lấy phần tử theo thứ tự ưu tiên: 3 -> 2 -> 1.
        Với mức 2 (hẹn trước), nếu bệnh nhân KHÔNG đúng giờ thì
        tự động chuyển xuống mức 1 (thường) và xét BN tiếp theo.
        """
        # Kiểm tra hàng đợi cấp cứu (3) trước tiên
        if len(self.queues[3]) > 0:
            return self.queues[3].popleft()

        # Kiểm tra hàng đợi đặt hẹn (2) — loop để xử lý nhiều BN đến trễ
        while len(self.queues[2]) > 0:
            candidate = self.queues[2][0]
            if is_valid_time(candidate):
                return self.queues[2].popleft()
            # Đến trễ: chuyển từ ưu tiên (2) → thường (1)
            self.queues[2].popleft()
            try:
                from . import config
            except ImportError:
                import config
            candidate.queuePriority = config.PRIORITY_WALKIN
            self.queues[1].append(candidate)

        # Kiểm tra hàng đợi tới trực tiếp (1)
        if len(self.queues[1]) > 0:
            return self.queues[1].popleft()

        # Không còn ai trong hàng đợi
        return None

    def appendleft_emergency(self, item: Any) -> None:
        """
        Thêm phần tử vào ĐẦU hàng đợi cấp cứu (3).
        Dùng khi có ca cấp cứu cần được ưu tiên tuyệt đối.
        """
        self.queues[3].appendleft(item)

    def remove(self, item: Any, priority: int) -> None:
        """
        Xóa một phần tử cụ thể khỏi deque của mức ưu tiên cho trước.
        """
        if priority in self.queues:
            self.queues[priority].remove(item)

    def get_total_size(self) -> int:
        """
        Trả về tổng số phần tử trong cả 3 hàng đợi.
        """
        return sum(len(q) for q in self.queues.values())

    def get_size(self, priority: int) -> int:
        """
        Trả về số phần tử trong hàng đợi của một mức ưu tiên cụ thể.
        """
        return len(self.queues.get(priority, []))

    def is_empty(self) -> bool:
        """
        Kiểm tra xem toàn bộ hàng đợi có rỗng hay không.
        """
        return self.get_total_size() == 0

    def peek(self, priority: int) -> Optional[Any]:
        """
        Xem phần tử ĐẦU TIÊN của hàng đợi mức ưu tiên cho trước mà không xóa.
        """
        q = self.queues.get(priority)
        if q and len(q) > 0:
            return q[0]
        return None

    def display(self) -> str:
        """
        Trả về chuỗi mô tả trạng thái hiện tại của cả 3 hàng đợi.
        """
        lines = []
        for p in [3, 2, 1]:
            size = len(self.queues[p])
            lines.append(f"  Priority {p}: {size} patient(s)")
        return "\n".join(lines)
