const API_BASE = '';  // FE và BE chạy cùng domain

// ============================================
// Global State
// ============================================
window.currentVisitId = null;
window.currentRoomId = null;
let refreshInterval = null;

// ============================================
// Helper: Gọi API với fetch, tự động parse JSON
// ============================================
async function apiFetch(url, options = {}) {
    showLoading();
    try {
        const res = await fetch(API_BASE + url, {
            headers: { 'Content-Type': 'application/json' },
            ...options
        });
        const data = await res.json();
        if (!res.ok) {
            const err = new Error(data.message || 'Lỗi HTTP ' + res.status);
            err.status = res.status;
            throw err;
        }
        // Nếu API trả về {success: true, data: ...}, unwrap .data để tiện dùng
        if (data && data.success && data.data !== undefined) {
            return data.data;
        }
        return data;
    } finally {
        hideLoading();
    }
}

// ============================================
// Helper: Hiển thị toast notification
// ============================================
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const tmpl = document.getElementById('tmpl-toast');
    if (!container || !tmpl) return;

    const clone = tmpl.content.cloneNode(true);
    const toast = clone.querySelector('.toast');
    toast.classList.add(type);

    const icon = toast.querySelector('.toast-icon i');
    if (type === 'success') icon.className = 'fa-solid fa-circle-check';
    else if (type === 'error') icon.className = 'fa-solid fa-circle-xmark';
    else if (type === 'warning') icon.className = 'fa-solid fa-triangle-exclamation';

    toast.querySelector('.toast-title').textContent = type === 'error' ? 'Lỗi' : (type === 'warning' ? 'Cảnh báo' : 'Thành công');
    toast.querySelector('.toast-msg').textContent = message;

    container.appendChild(toast);
    setTimeout(() => {
        toast.style.transition = 'opacity .3s';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================
// Helper: Toggle loading spinner
// ============================================
function showLoading() {
    const el = document.getElementById('loading');
    if (el) el.classList.remove('hidden');
}
function hideLoading() {
    const el = document.getElementById('loading');
    if (el) el.classList.add('hidden');
}

// ============================================
// Helper: Định dạng tiền VND
// ============================================
function formatMoney(n) {
    return new Intl.NumberFormat('vi-VN').format(n || 0) + ' đ';
}

// ============================================
// Helper: Định dạng ngày tháng
// ============================================
function formatDate(d) {
    if (!d) return '--';
    const date = new Date(d);
    if (isNaN(date)) return d;
    return date.toLocaleDateString('vi-VN');
}

// ============================================
// Tab Navigation: Khởi tạo sự kiện chuyển tab
// ============================================
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            const tab = link.getAttribute('data-tab');
            if (!tab) return;

            // Bỏ active khỏi tất cả nav và section
            navLinks.forEach(l => l.classList.remove('active'));
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));

            // Active nav được click
            link.classList.add('active');

            // Hiện section tương ứng
            const section = document.getElementById('section-' + tab);
            if (section) section.classList.add('active');

            // Cập nhật tiêu đề trang
            const titles = {
                dashboard: 'Dashboard',
                patients: 'Quản lý Bệnh nhân',
                doctors: 'Bác sĩ / Khoa / Phòng',
                clinic: 'Phòng Khám',
                payment: 'Thu ngân & Kho Dược',
                settings: 'Cài đặt'
            };
            document.getElementById('page-title').textContent = titles[tab] || tab;

            // Dừng auto-refresh cũ và load tab mới
            if (refreshInterval) {
                clearInterval(refreshInterval);
                refreshInterval = null;
            }
            loadTabData(tab);
        });
    });
}

// ============================================
// Tab Data Loaders: Điều phối load dữ liệu theo tab
// ============================================
function loadTabData(tab) {
    switch (tab) {
        case 'dashboard':
            loadDashboard();
            refreshInterval = setInterval(loadDashboard, 5000);
            break;
        case 'patients':
            loadPatientManagement();
            break;
        case 'doctors':
            loadDoctors();
            break;
        case 'clinic':
            loadClinicOverview();
            refreshInterval = setInterval(() => {
                if (window.currentRoomId) loadRoomQueue(window.currentRoomId);
            }, 5000);
            break;
        case 'payment':
            loadPaymentTab();
            refreshInterval = setInterval(loadPaymentTab, 5000);
            break;
        case 'settings':
            initSettings();
            break;
    }
}

// ============================================
// Dashboard: Load thống kê và bảng chờ khám
// ============================================
async function loadDashboard() {
    try {
        const data = await apiFetch('/api/dashboard');
        document.getElementById('dash-total-patients').textContent = data.patients_count ?? 0;
        document.getElementById('dash-total-doctors').textContent = data.doctors_count ?? 0;
        document.getElementById('dash-active-visits').textContent = data.active_visits ?? 0;
        document.getElementById('dash-emergency').textContent = data.emergency_count ?? 0;

        const rooms = await apiFetch('/api/rooms');
        renderWaitingTable(rooms);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ============================================
// Render bảng bệnh nhân đang chờ từ danh sách phòng
// ============================================
function renderWaitingTable(rooms) {
    const tbody = document.getElementById('waiting-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    let stt = 1;
    (rooms || []).forEach(room => {
        if (!room.queue || !room.queue.length) return;
        room.queue.forEach(visit => {
            const tmpl = document.getElementById('tmpl-waiting-row');
            if (!tmpl) return;
            const row = tmpl.content.cloneNode(true);
            row.querySelector('.w-stt').textContent = stt++;
            row.querySelector('.w-name').textContent = visit.patientName || '--';
            row.querySelector('.w-dept').textContent = visit.departmentName || room.departmentName || '--';
            row.querySelector('.w-room').textContent = room.name || '--';

            const badge = row.querySelector('.w-priority .badge');
            const p = visit.priority || 1;
            badge.textContent = p === 3 ? 'Cấp cứu' : (p === 2 ? 'Ưu tiên' : 'Thường');
            badge.className = 'badge ' + (p === 3 ? 'badge-red' : (p === 2 ? 'badge-yellow' : 'badge-green'));

            row.querySelector('.w-wait').textContent = visit.waitTime || '--';
            tbody.appendChild(row);
        });
    });
}

// ============================================
// PATIENT MANAGEMENT: Load danh sách tiếp đón trong ngày
// ============================================
async function loadPatientManagement() {
    try {
        const visits = await apiFetch('/api/today-visits');
        renderReceptionTable(visits);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ============================================
// Render bảng danh sách tiếp đón (bên phải form)
// ============================================
function renderReceptionTable(visits) {
    const tbody = document.getElementById('reception-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    (visits || []).forEach(v => {
        const tmpl = document.getElementById('tmpl-reception-row');
        if (!tmpl) return;
        const row = tmpl.content.cloneNode(true);
        row.querySelector('.rv-visit-id').textContent = v.visitID || '--';
        row.querySelector('.rv-name').textContent = v.patientName || '--';
        row.querySelector('.rv-type').textContent = v.receptionType || '--';
        row.querySelector('.rv-dept').textContent = v.departmentName || '--';

        const statusBadge = row.querySelector('.rv-status .badge');
        const status = v.status || 'ChoCheckIn';
        statusBadge.textContent = status;
        if (status === 'ChoCheckIn') statusBadge.classList.add('badge-red');
        else if (status === 'DangKham') statusBadge.classList.add('badge-yellow');
        else if (status === 'DaHoanThanh') statusBadge.classList.add('badge-green');
        else statusBadge.classList.add('badge-blue');

        const btn = row.querySelector('.btn-checkin');
        if (status === 'ChoCheckIn') {
            btn.classList.add('btn-danger');
            btn.textContent = 'Check-in';
            btn.addEventListener('click', () => handleCheckinClick(v.visitID, btn));
        } else if (status === 'DaHoanThanh') {
            btn.classList.add('btn-success');
            btn.textContent = 'Đã hoàn thành';
            btn.disabled = true;
        } else {
            btn.classList.add('btn-success');
            btn.textContent = 'Đã check-in';
            btn.disabled = true;
        }

        tbody.appendChild(row);
    });
}

// ============================================
// Handler: Click nút Check-in (ĐỎ -> XANH LÁ)
// ============================================
async function handleCheckinClick(visitId, btnElement) {
    try {
        const data = await apiFetch('/api/confirm-checkin/' + visitId, { method: 'POST' });
        if (data.success) {
            showToast('Check-in thành công — Đã xếp vào hàng đợi phòng khám');
            // Chuyển nút sang XANH LÁ và disabled
            btnElement.classList.remove('btn-danger');
            btnElement.classList.add('btn-success');
            btnElement.textContent = 'Đã check-in';
            btnElement.disabled = true;
            // Cập nhật badge trạng thái
            loadPatientManagement();
            loadDashboard();
        } else {
            showToast(data.message || 'Check-in thất bại', 'error');
        }
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ============================================
// Doctors: Load danh sách khoa và chi tiết
// ============================================
async function loadDoctors() {
    try {
        const depts = await apiFetch('/api/departments');
        renderDepartmentsList(depts);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ============================================
// Render danh sách khoa dạng card
// ============================================
function renderDepartmentsList(depts) {
    const container = document.getElementById('dept-list');
    const select = document.getElementById('dept-select');
    if (!container) return;
    container.innerHTML = '';
    if (select) select.innerHTML = '<option value="">-- Chọn khoa --</option>';

    (depts || []).forEach(d => {
        const deptId = d.departmentID || d.id;
        const deptName = d.departmentName || d.name;
        const docCount = (d.doctorIDs || []).length;
        const roomCount = (d.roomIDs || []).length;
        
        if (select) {
            const opt = document.createElement('option');
            opt.value = deptId;
            opt.textContent = deptName;
            select.appendChild(opt);
        }

        const tmpl = document.getElementById('tmpl-dept-card');
        if (!tmpl) return;
        const card = tmpl.content.cloneNode(true);
        card.querySelector('.d-name').textContent = deptName || '--';
        card.querySelector('.d-count').textContent = docCount;
        card.querySelector('.d-rooms').textContent = roomCount;

        const cardEl = card.querySelector('.card');
        cardEl.addEventListener('click', () => loadDeptDetail(deptId, deptName));
        container.appendChild(card);
    });

    if (select) {
        select.addEventListener('change', (e) => {
            if (e.target.value) {
                const name = e.target.options[e.target.selectedIndex].text;
                loadDeptDetail(e.target.value, name);
            }
        });
    }
}

// ============================================
// Load chi tiết khoa: bác sĩ và phòng
// ============================================
async function loadDeptDetail(deptId, deptName) {
    try {
        const [doctors, rooms] = await Promise.all([
            apiFetch('/api/departments/' + deptId + '/doctors'),
            apiFetch('/api/departments/' + deptId + '/rooms')
        ]);

        const detailCard = document.getElementById('dept-detail-card');
        document.getElementById('dept-detail-title').textContent = 'Chi tiết khoa: ' + (deptName || '--');

        const docsGrid = document.getElementById('dept-doctors-grid');
        docsGrid.innerHTML = '';
        (doctors || []).forEach(doc => {
            const tmpl = document.getElementById('tmpl-doctor-card');
            if (!tmpl) return;
            const card = tmpl.content.cloneNode(true);
            card.querySelector('.doc-name').textContent = doc.fullName || '--';
            card.querySelector('.doc-spec').textContent = doc.degree || doc.departmentID || '--';
            docsGrid.appendChild(card);
        });

        const roomsGrid = document.getElementById('dept-rooms-grid');
        roomsGrid.innerHTML = '';
        (rooms || []).forEach(r => {
            const tmpl = document.getElementById('tmpl-room-card');
            if (!tmpl) return;
            const card = tmpl.content.cloneNode(true);
            card.querySelector('.r-name').textContent = r.name || '--';
            card.querySelector('.r-count').textContent = (r.queueLength || 0) + ' BN chờ';
            card.querySelector('.r-doctor').textContent = 'BS: ' + (r.doctorName || '--');
            roomsGrid.appendChild(card);
        });

        detailCard.classList.remove('hidden');
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ============================================
// Clinic Overview: Danh sách phòng khám dạng card
// ============================================
async function loadClinicOverview() {
    try {
        const rooms = await apiFetch('/api/rooms');
        renderClinicOverview(rooms);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function renderClinicOverview(rooms) {
    const container = document.getElementById('rooms-overview');
    if (!container) return;
    container.innerHTML = '';

    (rooms || []).forEach(r => {
        const tmpl = document.getElementById('tmpl-room-overview');
        if (!tmpl) return;
        const card = tmpl.content.cloneNode(true);
        const roomName = r.roomID || r.name || '--';
        card.querySelector('.ro-name').textContent = roomName;
        card.querySelector('.ro-count').textContent = (r.queueLength || 0) + ' BN chờ';
        card.querySelector('.ro-dept').textContent = 'Khoa: ' + (r.departmentID || '--');

        const doctorId = r.doctorID || r.doctorId || '--';
        card.querySelector('.ro-doctor').textContent = 'BS: ' + doctorId;

        const cardEl = card.querySelector('.room-overview-card');
        cardEl.addEventListener('click', () => openRoomDetail(r.roomID, roomName, r.departmentID));
        container.appendChild(card);
    });
}

function openRoomDetail(roomId, roomName, deptId) {
    window.currentRoomId = roomId;
    document.getElementById('rooms-overview').parentElement.classList.add('hidden');
    document.getElementById('room-detail').classList.remove('hidden');
    document.getElementById('room-detail-name').textContent = roomName;

    // Load queue
    loadRoomQueue(roomId);

    // Load dịch vụ theo đúng Khoa của phòng (Fix bug hiển thị full dịch vụ)
    populateServicesSelect(deptId);
}

function closeRoomDetail() {
    window.currentRoomId = null;
    window.currentVisitId = null;
    document.getElementById('room-detail').classList.add('hidden');
    document.getElementById('rooms-overview').parentElement.classList.remove('hidden');
}

// ============================================
// Load queue của phòng: 3 cột và BN đang khám
// ============================================
async function loadRoomQueue(roomId) {
    if (!roomId || roomId === 'undefined') {
        console.warn('loadRoomQueue: roomId is undefined or empty');
        return;
    }
    try {
        const data = await apiFetch('/api/rooms/' + roomId + '/queue');
        renderRoomQueue(data);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function renderRoomQueue(data) {
    const qEmergency = document.getElementById('queue-emergency');
    const qBooking = document.getElementById('queue-booking');
    const qWalkin = document.getElementById('queue-walkin');
    if (!qEmergency || !qBooking || !qWalkin) return;

    qEmergency.innerHTML = '';
    qBooking.innerHTML = '';
    qWalkin.innerHTML = '';

    (data.priority3 || []).forEach(v => qEmergency.appendChild(makeQueueItem(v, 'red-border')));
    (data.priority2 || []).forEach(v => qBooking.appendChild(makeQueueItem(v, 'yellow-border')));
    (data.priority1 || []).forEach(v => qWalkin.appendChild(makeQueueItem(v, 'green-border')));

    const currentId = data.currentVisit;
    const visitBox = document.getElementById('current-visit-box');
    const callBox = document.getElementById('call-next-box');
    if (currentId) {
        window.currentVisitId = currentId;
        document.getElementById('cv-name').textContent = 'Đang khám';
        document.getElementById('cv-code').textContent = currentId;
        document.getElementById('cv-stt').textContent = '--';
        document.getElementById('cv-big-stt').textContent = '--';
        visitBox.classList.remove('hidden');
        callBox.classList.add('hidden');
    } else {
        window.currentVisitId = null;
        visitBox.classList.add('hidden');
        callBox.classList.remove('hidden');
    }
}

function makeQueueItem(visit, borderClass) {
    const tmpl = document.getElementById('tmpl-queue-item');
    const el = tmpl.content.cloneNode(true).querySelector('.queue-item');
    el.classList.add(borderClass);
    el.querySelector('.qi-name').textContent = visit.patientName || 'Không rõ';
    el.querySelector('.qi-id').textContent = 'BN: ' + (visit.patientID || '--') + ' | Visit: ' + (visit.visitID || '--');
    const badge = el.querySelector('.qi-priority');
    badge.textContent = visit.priorityLabel || (visit.queuePriority === 3 ? 'Cấp cứu' : (visit.queuePriority === 2 ? 'Ưu tiên' : 'Thường'));
    if (visit.queuePriority === 3) badge.classList.add('badge-red');
    else if (visit.queuePriority === 2) badge.classList.add('badge-yellow');
    else badge.classList.add('badge-green');
    const sttBadge = el.querySelector('.qi-stt');
    sttBadge.textContent = '#' + (visit.visitID || '').slice(-4);
    return el;
}

// ============================================
// Payment (Thu ngân): Tải danh sách visit và hiển thị chi tiết
// ============================================
async function loadPaymentTab() {
    try {
        const visits = await apiFetch('/api/active-visits');
        const sel = document.getElementById('payment-visit-select');
        if (!sel) return;
        // Giữ lại giá trị đang chọn để không bị reset khi auto-refresh
        const currentValue = sel.value;
        sel.innerHTML = '<option value="">-- Chọn lượt khám cần thanh toán --</option>';
        (visits || []).forEach(v => {
            const opt = document.createElement('option');
            opt.value = v.visitID;
            opt.textContent = (v.patientName || '--') + ' (' + v.visitID + ') - ' + v.status;
            sel.appendChild(opt);
        });
        // Khôi phục giá trị đã chọn nếu còn tồn tại trong danh sách mới
        if (currentValue) {
            const stillExists = Array.from(sel.options).some(o => o.value === currentValue);
            if (stillExists) sel.value = currentValue;
        }
    } catch (err) {
        console.error('loadPaymentTab', err);
    }
}

async function searchPayment() {
    const sel = document.getElementById('payment-visit-select');
    const visitId = sel ? sel.value : '';
    
    if (!visitId) {
        showToast('Vui lòng chọn lượt khám từ dropdown trước khi bấm Tải', 'warning');
        return;
    }
    try {
        const data = await apiFetch('/api/payment-detail/' + visitId);
        console.log('DEBUG: Full payment data:', JSON.stringify(data, null, 2));
        renderPaymentDetail(data);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function renderPaymentDetail(data) {
    if (!data || !data.visit) return;
    const visit = data.visit;
    window.currentVisitId = visit.visitID;

    document.getElementById('payment-detail').classList.remove('hidden');
    document.getElementById('pay-patient-name').textContent = visit.patientName || '--';
    document.getElementById('pay-visit-id').textContent = visit.visitID || '--';
    document.getElementById('pay-doctor').textContent = visit.doctorName || '--';
    document.getElementById('pay-dept').textContent = visit.departmentName || '--';

    // BHYT: nếu có BHYT thì mặc định 80%
    const bhytInput = document.getElementById('pay-bhyt');
    if (visit.hasInsurance) {
        bhytInput.value = 80;
    } else {
        bhytInput.value = 0;
    }

    // Dịch vụ
    const svcBody = document.getElementById('pay-services-body');
    svcBody.innerHTML = '';
    let sumServices = 0;
    (visit.services || []).forEach(s => {
        const tr = document.createElement('tr');
        tr.innerHTML = '<td>' + (s.serviceName || '--') + '</td><td style="text-align:right;">' + formatMoney(s.price) + '</td>';
        svcBody.appendChild(tr);
        sumServices += s.price || 0;
    });

    // Thuốc — ĐƠN GIÁ lấy từ Kho dược (Medicine Inventory)
    const medBody = document.getElementById('pay-meds-body');
    medBody.innerHTML = '';
    let sumMeds = 0;
    (visit.medicines || []).forEach(m => {
        const total = (m.unitPrice || 0) * (m.quantity || 1);
        const tr = document.createElement('tr');
        tr.innerHTML = '<td>' + (m.medicineName || '--') + '</td><td style="text-align:center;">' + (m.quantity || 1) + '</td><td style="text-align:right;">' + formatMoney(m.unitPrice) + '</td><td style="text-align:right;">' + formatMoney(total) + '</td>';
        medBody.appendChild(tr);
        sumMeds += total;
    });

    document.getElementById('pay-sum-services').textContent = formatMoney(sumServices);
    document.getElementById('pay-sum-meds').textContent = formatMoney(sumMeds);
    recalcTotal();

    document.getElementById('invoice-box').classList.add('hidden');
}

function recalcTotal() {
    const svc = parseCurrency(document.getElementById('pay-sum-services').textContent);
    const med = parseCurrency(document.getElementById('pay-sum-meds').textContent);
    const bhyt = parseFloat(document.getElementById('pay-bhyt').value) || 0;
    const total = Math.max(0, (svc + med) * (1 - bhyt / 100));
    document.getElementById('pay-total').textContent = formatMoney(total);
}

function parseCurrency(str) {
    return parseInt((str || '0').replace(/[^0-9]/g, '')) || 0;
}

// ============================================
// Settings: Khởi tạo nút Save / Load / Mock
// ============================================
function initSettings() {
    const status = document.getElementById('settings-status');

    document.getElementById('btn-save-json').addEventListener('click', async () => {
        if (!confirm('Bạn có chắc muốn lưu dữ liệu ra file JSON?')) return;
        try {
            const data = await apiFetch('/api/save', { method: 'POST' });
            status.textContent = 'Trạng thái: Đã lưu dữ liệu thành công. ' + (data.filename || '');
            showToast('Lưu dữ liệu thành công');
        } catch (err) {
            showToast(err.message, 'error');
        }
    });

    document.getElementById('btn-load-json').addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        if (!confirm('Bạn có chắc muốn tải dữ liệu từ file JSON? Dữ liệu hiện tại có thể bị ghi đè.')) return;
        try {
            const text = await file.text();
            const payload = JSON.parse(text);
            await apiFetch('/api/load', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            status.textContent = 'Trạng thái: Đã tải dữ liệu thành công từ ' + file.name;
            showToast('Tải dữ liệu thành công');
        } catch (err) {
            showToast(err.message, 'error');
        }
    });

    document.getElementById('btn-mock-data').addEventListener('click', async () => {
        if (!confirm('Bạn có chắc muốn sinh dữ liệu mẫu (Mock)? Dữ liệu hiện tại có thể bị ghi đè.')) return;
        try {
            await apiFetch('/api/mock', { method: 'POST' });
            status.textContent = 'Trạng thái: Đã sinh dữ liệu mẫu thành công.';
            showToast('Sinh dữ liệu mẫu thành công');
        } catch (err) {
            showToast(err.message, 'error');
        }
    });
}

// ============================================
// Populate Select Boxes
// ============================================
async function populateDoctorsSelect() {
    try {
        const doctors = await apiFetch('/api/doctors');
        const sel = document.getElementById('reception-doctor');
        if (!sel) return;
        sel.innerHTML = '<option value="">-- Chọn bác sĩ --</option>';
        (doctors || []).forEach(d => {
            const opt = document.createElement('option');
            opt.value = d.doctorID || d.id;
            opt.textContent = (d.fullName || d.name || '--') + ' - ' + (d.degree || d.specialty || d.departmentID || '');
            sel.appendChild(opt);
        });
    } catch (err) {
        console.error('populateDoctorsSelect', err);
    }
}

async function populateDepartmentsSelect() {
    try {
        const depts = await apiFetch('/api/departments');
        const selects = [document.getElementById('reception-dept')];
        selects.forEach(sel => {
            if (!sel) return;
            sel.innerHTML = '<option value="">-- Chọn khoa --</option>';
            (depts || []).forEach(d => {
                const opt = document.createElement('option');
                opt.value = d.departmentID || d.id;
                opt.textContent = d.departmentName || d.name;
                sel.appendChild(opt);
            });
        });
    } catch (err) {
        console.error('populateDepartmentsSelect', err);
    }
}

// ============================================
// Populate Services: CHỈ theo Khoa của phòng (Fix bug hiển thị full)
// ============================================
async function populateServicesSelect(departmentID) {
    try {
        let services = [];
        if (departmentID && window.currentRoomId) {
            // Ưu tiên gọi API filter theo phòng
            services = await apiFetch('/api/rooms/' + window.currentRoomId + '/services');
        } else {
            services = await apiFetch('/api/services');
        }
        const container = document.getElementById('services-list');
        if (!container) return;
        container.innerHTML = '';
        (services || []).forEach(s => {
            const div = document.createElement('div');
            div.className = 'checkbox-group';
            div.style.marginBottom = '8px';
            const sid = s.serviceID || s.id;
            const sname = s.serviceName || s.name;
            div.innerHTML = '<input type="checkbox" id="svc-' + sid + '" value="' + sid + '"><label for="svc-' + sid + '">' + sname + ' - ' + formatMoney(s.price) + '</label>';
            container.appendChild(div);
        });
    } catch (err) {
        console.error('populateServicesSelect', err);
    }
}

async function populateMedicinesSelect() {
    try {
        const medicines = await apiFetch('/api/medicines');
        window.medicinesData = medicines || [];
        let dl = document.getElementById('dl-medicines');
        if (!dl) {
            dl = document.createElement('datalist');
            dl.id = 'dl-medicines';
            document.body.appendChild(dl);
        }
        dl.innerHTML = '';
        (medicines || []).forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.medicineName || m.name;
            opt.setAttribute('data-id', m.medicineID || m.id);
            opt.setAttribute('data-price', m.unitPrice || m.price);
            dl.appendChild(opt);
        });
    } catch (err) {
        console.error('populateMedicinesSelect', err);
    }
}

// ============================================
// Event Handlers: Gắn sự kiện cho các form và nút
// ============================================
function initEventHandlers() {
    // 1. Form tiếp đón (gộp bệnh nhân + lễ tân)
    const receptionForm = document.getElementById('reception-form');
    if (receptionForm) {
        receptionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const type = document.getElementById('reception-type').value;
            const isApt = type === 'appointment';
            const payload = {
                full_name: document.getElementById('p-name').value,
                gender: document.getElementById('p-gender').value,
                dob: document.getElementById('p-dob').value,
                citizen_id: document.getElementById('p-idcard').value || '000000000000',
                phone: document.getElementById('p-phone').value,
                blood_type: document.getElementById('p-blood').value || 'O',
                hasInsurance: document.getElementById('p-bhyt').checked,
                department_sequence: [document.getElementById('reception-dept').value],
                is_appointment: isApt,
                appointment_date: isApt ? document.getElementById('reception-date').value : null,
                time_slot: isApt ? document.getElementById('reception-time').value : null,
                selected_doctor_id: isApt ? document.getElementById('reception-doctor').value : null,
            };
            try {
                const data = await apiFetch('/api/checkin', { method: 'POST', body: JSON.stringify(payload) });
                showToast('Thêm bệnh nhân thành công. Mã visit: ' + (data.visit?.visitID || ''));
                receptionForm.reset();
                loadPatientManagement();
                loadDashboard();
            } catch (err) {
                showToast(err.message, 'error');
            }
        });

        // Toggle fields theo hình thức tiếp đón
        const typeSelect = document.getElementById('reception-type');
        const aptGroup = document.getElementById('group-appointment');
        if (typeSelect && aptGroup) {
            typeSelect.addEventListener('change', () => {
                if (typeSelect.value === 'appointment') {
                    aptGroup.classList.remove('hidden');
                } else {
                    aptGroup.classList.add('hidden');
                }
            });
        }
    }

    // 2. Kích hoạt cấp cứu
    const btnEmergency = document.getElementById('btn-emergency-activate');
    if (btnEmergency) {
        btnEmergency.addEventListener('click', async () => {
            const visitId = document.getElementById('emergency-visit-id').value.trim();
            if (!visitId) return showToast('Vui lòng nhập mã Visit', 'warning');
            try {
                await apiFetch('/api/emergency', { method: 'POST', body: JSON.stringify({ visit_id: visitId }) });
                showToast('Kích hoạt cấp cứu thành công');
                const activeSection = document.querySelector('.section.active');
                if (activeSection && activeSection.id === 'section-clinic') loadRoomQueue(window.currentRoomId);
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    // 3. Gọi bệnh nhân tiếp theo
    const btnCallNext = document.getElementById('btn-call-next');
    if (btnCallNext) {
        btnCallNext.addEventListener('click', async () => {
            if (!window.currentRoomId) return showToast('Vui lòng chọn phòng', 'warning');
            try {
                const data = await apiFetch('/api/call-next', {
                    method: 'POST',
                    body: JSON.stringify({ room_id: window.currentRoomId })
                });
                if (data.visit) {
                    window.currentVisitId = data.visit.visitID || data.visit.visitId || data.visit.id;
                    showToast('Gọi BN: ' + (data.visit.patientName || data.visit.id));
                    loadRoomQueue(window.currentRoomId);
                } else {
                    showToast('Không có BN chờ', 'warning');
                }
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    // 4. Chỉ định dịch vụ
    const btnAddServices = document.getElementById('btn-add-services');
    if (btnAddServices) {
        btnAddServices.addEventListener('click', async () => {
            const visitId = window.currentVisitId;
            if (!visitId) return showToast('Chưa có bệnh nhân đang khám', 'warning');
            const checkboxes = document.querySelectorAll('#services-list input[type=checkbox]:checked');
            const serviceIds = Array.from(checkboxes).map(cb => cb.value);
            if (!serviceIds.length) return showToast('Vui lòng chọn ít nhất một dịch vụ', 'warning');
            try {
                await apiFetch('/api/add-service', {
                    method: 'POST',
                    body: JSON.stringify({ visit_id: visitId, service_ids: serviceIds })
                });
                showToast('Chỉ định dịch vụ thành công');
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    // 5. Kê đơn thuốc — GỬI MEDICINE ID thay vì tên (Fix bug tính tiền = 0)
    const btnAddMedRow = document.getElementById('btn-add-med-row');
    if (btnAddMedRow) {
        btnAddMedRow.addEventListener('click', () => {
            const tmpl = document.getElementById('tmpl-medicine-row');
            const row = tmpl.content.cloneNode(true);
            const input = row.querySelector('.med-name');
            if (input) input.setAttribute('list', 'dl-medicines');
            row.querySelector('.btn-remove-row').addEventListener('click', (e) => {
                e.target.closest('.form-group').remove();
            });
            document.getElementById('meds-list').appendChild(row);
        });
    }

    const btnSavePrescription = document.getElementById('btn-save-prescription');
    if (btnSavePrescription) {
        btnSavePrescription.addEventListener('click', async () => {
            const visitId = window.currentVisitId;
            if (!visitId) return showToast('Chưa có bệnh nhân đang khám', 'warning');
            const rows = document.querySelectorAll('#meds-list .form-group');
            const medicineList = {};
            rows.forEach(r => {
                const input = r.querySelector('.med-name');
                const qty = parseInt(r.querySelector('.med-qty').value) || 1;
                let medId = input.value.trim();
                // Lấy medicineID từ datalist option (Fix bug tên -> ID)
                const dl = document.getElementById('dl-medicines');
                const opt = Array.from(dl.options).find(o => o.value === input.value);
                if (opt) medId = opt.getAttribute('data-id') || medId;
                if (medId) medicineList[medId] = qty;
            });
            if (!Object.keys(medicineList).length) return showToast('Vui lòng nhập thuốc', 'warning');
            try {
                await apiFetch('/api/add-prescription', {
                    method: 'POST',
                    body: JSON.stringify({ visit_id: visitId, doctor_id: null, medicine_list: medicineList })
                });
                showToast('Kê đơn thuốc thành công');
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    // 6. Hoàn tất khám
    const btnComplete = document.getElementById('btn-complete-visit');
    if (btnComplete) {
        btnComplete.addEventListener('click', async () => {
            const visitId = window.currentVisitId;
            if (!visitId) return showToast('Chưa có bệnh nhân đang khám', 'warning');
            try {
                await apiFetch('/api/complete', { method: 'POST', body: JSON.stringify({ visit_id: visitId }) });
                document.getElementById('current-visit-box').classList.add('hidden');
                document.getElementById('call-next-box').classList.remove('hidden');
                showToast('Hoàn tất khám thành công');
                window.currentVisitId = null;
                loadRoomQueue(window.currentRoomId);
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    // 7. Chuyển khoa
    const btnTransfer = document.getElementById('btn-transfer-dept');
    if (btnTransfer) {
        btnTransfer.addEventListener('click', async () => {
            const visitId = window.currentVisitId;
            if (!visitId) return showToast('Chưa có bệnh nhân đang khám', 'warning');
            const newDept = document.getElementById('transfer-dept').value.trim();
            if (!newDept) return showToast('Vui lòng nhập tên khoa chuyển đến', 'warning');
            try {
                await apiFetch('/api/transfer', {
                    method: 'POST',
                    body: JSON.stringify({ visit_id: visitId, new_dept_id: newDept })
                });
                showToast('Chuyển khoa thành công');
                document.getElementById('current-visit-box').classList.add('hidden');
                document.getElementById('call-next-box').classList.remove('hidden');
                window.currentVisitId = null;
                loadRoomQueue(window.currentRoomId);
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    // 8. Thanh toán
    const btnPay = document.getElementById('btn-pay');
    if (btnPay) {
        btnPay.addEventListener('click', async () => {
            const visitId = window.currentVisitId;
            if (!visitId) return showToast('Chưa có thông tin thanh toán', 'warning');
            try {
                const data = await apiFetch('/api/pay', {
                    method: 'POST',
                    body: JSON.stringify({ visit_id: visitId })
                });
                showToast('Thanh toán thành công');
                renderInvoice(data);
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    // Tìm kiếm thanh toán
    const btnPaymentSearch = document.getElementById('btn-payment-search');
    if (btnPaymentSearch) btnPaymentSearch.addEventListener('click', searchPayment);

    // BHYT change recalc
    const bhytInput = document.getElementById('pay-bhyt');
    if (bhytInput) bhytInput.addEventListener('input', recalcTotal);
}

// ============================================
// Render hóa đơn sau thanh toán
// ============================================
function renderInvoice(data) {
    const box = document.getElementById('invoice-box');
    box.classList.remove('hidden');

    const bill = data.bill || data;
    document.getElementById('inv-id').textContent = bill.billID || '--';
    document.getElementById('inv-date').textContent = new Date().toLocaleString('vi-VN');
    document.getElementById('inv-name').textContent = document.getElementById('pay-patient-name').textContent;
    document.getElementById('inv-code').textContent = document.getElementById('pay-visit-id').textContent;
    document.getElementById('inv-dept').textContent = document.getElementById('pay-dept').textContent;
    document.getElementById('inv-doctor').textContent = document.getElementById('pay-doctor').textContent;
    document.getElementById('inv-bhyt').textContent = document.getElementById('pay-bhyt').value + '%';
    document.getElementById('inv-total').textContent = formatMoney(bill.finalTotal);

    const tbody = document.getElementById('inv-body');
    tbody.innerHTML = '';
    let stt = 1;
    
    const svcRows = document.querySelectorAll('#pay-services-body tr');
    svcRows.forEach(row => {
        const tds = row.querySelectorAll('td');
        const tr = document.createElement('tr');
        tr.innerHTML = '<td>' + (stt++) + '</td><td>' + tds[0].textContent + '</td><td>1</td><td>' + tds[1].textContent + '</td><td>' + tds[1].textContent + '</td>';
        tbody.appendChild(tr);
    });
    
    const medRows = document.querySelectorAll('#pay-meds-body tr');
    medRows.forEach(row => {
        const tds = row.querySelectorAll('td');
        const tr = document.createElement('tr');
        tr.innerHTML = '<td>' + (stt++) + '</td><td>' + tds[0].textContent + '</td><td>' + tds[1].textContent + '</td><td>' + tds[2].textContent + '</td><td>' + tds[3].textContent + '</td>';
        tbody.appendChild(tr);
    });

    box.scrollIntoView({ behavior: 'smooth' });
}

// ============================================
// Initialization: Chạy khi DOM sẵn sàng
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initEventHandlers();
    loadTabData('dashboard');
    populateDoctorsSelect();
    populateDepartmentsSelect();
    populateMedicinesSelect();
});
