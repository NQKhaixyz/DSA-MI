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
                reception: 'Lễ tân',
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
            loadPatients();
            break;
        case 'doctors':
            loadDoctors();
            break;
        case 'reception':
            initReception();
            break;
        case 'clinic':
            loadClinic();
            refreshInterval = setInterval(() => {
                if (window.currentRoomId) loadRoomQueue(window.currentRoomId);
            }, 5000);
            break;
        case 'payment':
            loadPaymentTab();
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
        // API trả về snake_case: patients_count, doctors_count, active_visits, emergency_count
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
// Patients: Load danh sách bệnh nhân
// ============================================
async function loadPatients() {
    try {
        const patients = await apiFetch('/api/patients');
        renderPatientTable(patients);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ============================================
// Render bảng danh sách bệnh nhân
// ============================================
function renderPatientTable(patients) {
    const tbody = document.getElementById('patients-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    (patients || []).forEach(p => {
        const tmpl = document.getElementById('tmpl-patient-row');
        if (!tmpl) return;
        const row = tmpl.content.cloneNode(true);
        // API trả snake_case: patientID, fullName, hasInsurance
        row.querySelector('.p-id').textContent = p.patientID || '--';
        row.querySelector('.p-name').textContent = p.fullName || '--';
        row.querySelector('.p-gender').textContent = p.gender || '--';
        row.querySelector('.p-dob').textContent = formatDate(p.dob);
        row.querySelector('.p-phone').textContent = p.phone || '--';
        row.querySelector('.p-blood').textContent = p.bloodType || '--';
        row.querySelector('.p-bhyt').textContent = p.hasInsurance ? 'Có' : 'Không';
        tbody.appendChild(row);
    });
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
        // API trả departmentID, departmentName, doctorIDs[], roomIDs[]
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
            // API trả fullName, departmentID, degree
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

        detailCard.style.display = 'block';
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ============================================
// Reception: Khởi tạo form (không load data)
// ============================================
function initReception() {
    populatePatientsSelect();
    populateDoctorsSelect();
    populateDepartmentsSelect();
}

// ============================================
// Clinic (Phòng khám): Load phòng và queue
// ============================================
async function loadClinic() {
    await populateRoomsSelect();
    const roomSelect = document.getElementById('room-select');
    if (roomSelect && !roomSelect.dataset.listenerAttached) {
        roomSelect.dataset.listenerAttached = 'true';
        roomSelect.addEventListener('change', (e) => {
            const roomId = e.target.value;
            window.currentRoomId = roomId || null;
            if (roomId) {
                document.getElementById('room-queue-card').style.display = 'block';
                loadRoomQueue(roomId);
            } else {
                document.getElementById('room-queue-card').style.display = 'none';
            }
        });
    }
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

    // API trả priority3, priority2, priority1
    (data.priority3 || []).forEach(v => qEmergency.appendChild(makeQueueItem(v, 'red-border')));
    (data.priority2 || []).forEach(v => qBooking.appendChild(makeQueueItem(v, 'yellow-border')));
    (data.priority1 || []).forEach(v => qWalkin.appendChild(makeQueueItem(v, 'green-border')));

    // currentVisit là string visitID
    const currentId = data.currentVisit;
    const visitBox = document.getElementById('current-visit-box');
    const callBox = document.getElementById('call-next-box');
    if (currentId) {
        window.currentVisitId = currentId;
        document.getElementById('cv-name').textContent = 'Đang khám';
        document.getElementById('cv-code').textContent = currentId;
        document.getElementById('cv-stt').textContent = '--';
        document.getElementById('cv-big-stt').textContent = '--';
        visitBox.style.display = 'block';
        callBox.style.display = 'none';
    } else {
        window.currentVisitId = null;
        visitBox.style.display = 'none';
        callBox.style.display = 'block';
    }
}

function makeQueueItem(visit, borderClass) {
    const tmpl = document.getElementById('tmpl-queue-item');
    const el = tmpl.content.cloneNode(true).querySelector('.queue-item');
    el.classList.add(borderClass);
    // Visit.to_dict() trả visitID, patientID, không có patientName
    el.querySelector('.q-name').textContent = visit.visitID || '--';
    el.querySelector('.q-meta').textContent = 'Mã BN: ' + (visit.patientID || '--');
    el.querySelector('.q-wait').textContent = visit.queuePriority === 3 ? 'Cấp cứu' : (visit.queuePriority === 2 ? 'Ưu tiên' : 'Thường');
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
        sel.innerHTML = '<option value="">-- Chọn lượt khám cần thanh toán --</option>';
        (visits || []).forEach(v => {
            const opt = document.createElement('option');
            opt.value = v.visitID;
            opt.textContent = (v.patientName || '--') + ' (' + v.visitID + ') - ' + v.status;
            sel.appendChild(opt);
        });
    } catch (err) {
        console.error('loadPaymentTab', err);
    }
}

async function searchPayment() {
    const visitId = document.getElementById('payment-visit-select').value;
    if (!visitId) return showToast('Vui lòng chọn lượt khám', 'warning');
    try {
        const data = await apiFetch('/api/payment-detail/' + visitId);
        renderPaymentDetail(data);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

function renderPaymentDetail(data) {
    if (!data || !data.visit) return;
    const visit = data.visit;
    window.currentVisitId = visit.visitID;

    document.getElementById('payment-detail').style.display = 'block';
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

    // Thuốc
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
async function populatePatientsSelect() {
    try {
        const patients = await apiFetch('/api/patients');
        const sel = document.getElementById('book-patient');
        if (!sel) return;
        sel.innerHTML = '<option value="">-- Chọn BN --</option>';
        (patients || []).forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.patientID || p.id;
            opt.textContent = (p.fullName || p.name || '--') + ' (' + (p.patientID || p.id) + ')';
            sel.appendChild(opt);
        });
    } catch (err) {
        console.error('populatePatientsSelect', err);
    }
}

async function populateDoctorsSelect() {
    try {
        const doctors = await apiFetch('/api/doctors');
        const sel = document.getElementById('book-doctor');
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
        const selects = [document.getElementById('book-dept'), document.getElementById('ci-dept')];
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

async function populateServicesSelect() {
    try {
        const services = await apiFetch('/api/services');
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

async function populateRoomsSelect() {
    try {
        const rooms = await apiFetch('/api/rooms');
        const sel = document.getElementById('room-select');
        if (!sel) return;
        sel.innerHTML = '<option value="">-- Chọn phòng --</option>';
        (rooms || []).forEach(r => {
            const opt = document.createElement('option');
            // API trả roomID, departmentID, doctorID
            opt.value = r.roomID || r.id;
            opt.textContent = (r.roomID || '--') + ' - ' + (r.departmentID || '');
            sel.appendChild(opt);
        });
    } catch (err) {
        console.error('populateRoomsSelect', err);
    }
}

// ============================================
// Event Handlers: Gắn sự kiện cho các form và nút
// ============================================
function initEventHandlers() {
    // 1. Form thêm bệnh nhân
    const patientForm = document.getElementById('patient-form');
    if (patientForm) {
        patientForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = {
                fullName: document.getElementById('p-name').value,
                gender: document.getElementById('p-gender').value,
                dob: document.getElementById('p-dob').value,
                citizenID: document.getElementById('p-idcard').value,
                phone: document.getElementById('p-phone').value,
                email: document.getElementById('p-email').value,
                address: document.getElementById('p-address').value,
                bloodType: document.getElementById('p-blood').value,
                hasInsurance: document.getElementById('p-bhyt').checked
            };
            try {
                await apiFetch('/api/patients', { method: 'POST', body: JSON.stringify(payload) });
                showToast('Thêm BN thành công');
                patientForm.reset();
                loadPatients();
                populatePatientsSelect();
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    // 2. Form đặt lịch
    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = {
                patient_id: document.getElementById('book-patient').value,
                department_sequence: [document.getElementById('book-dept').value],
                selected_doctor_id: document.getElementById('book-doctor').value,
                date: document.getElementById('book-date').value,
                time_slot: document.getElementById('book-time').value
            };
            try {
                await apiFetch('/api/appointments', { method: 'POST', body: JSON.stringify(payload) });
                showToast('Đặt lịch thành công');
                bookingForm.reset();
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    // 3. Form check-in
    const checkinForm = document.getElementById('checkin-form');
    if (checkinForm) {
        checkinForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = {
                patient_id: document.getElementById('checkin-id').value || '',
                full_name: document.getElementById('ci-name').value,
                gender: document.getElementById('ci-gender').value,
                dob: document.getElementById('ci-dob').value,
                citizen_id: '000000000000',
                phone: document.getElementById('ci-phone').value,
                address: 'Không rõ',
                blood_type: 'O',
                severity: document.getElementById('ci-priority').value || 'BinhThuong',
                department_sequence: [document.getElementById('ci-dept').value],
                is_appointment: false
            };
            try {
                const data = await apiFetch('/api/checkin', { method: 'POST', body: JSON.stringify(payload) });
                showToast('Check-in thành công. Mã visit: ' + (data.visit?.visitID || data.visit?.id || ''));
                checkinForm.reset();
                loadDashboard();
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    // 4. Kích hoạt cấp cứu
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

    // 5. Gọi bệnh nhân tiếp theo
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
                    window.currentVisitId = data.visit.visitId || data.visit.id;
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

    // 6. Chỉ định dịch vụ
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

    // 7. Kê đơn thuốc
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
                const name = r.querySelector('.med-name').value.trim();
                const qty = parseInt(r.querySelector('.med-qty').value) || 1;
                if (name) medicineList[name] = qty;
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

    // 8. Hoàn tất khám
    const btnComplete = document.getElementById('btn-complete-visit');
    if (btnComplete) {
        btnComplete.addEventListener('click', async () => {
            const visitId = window.currentVisitId;
            if (!visitId) return showToast('Chưa có bệnh nhân đang khám', 'warning');
            try {
                await apiFetch('/api/complete', { method: 'POST', body: JSON.stringify({ visit_id: visitId }) });
                document.getElementById('current-visit-box').style.display = 'none';
                document.getElementById('call-next-box').style.display = 'block';
                showToast('Hoàn tất khám thành công');
                window.currentVisitId = null;
                loadRoomQueue(window.currentRoomId);
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    // 9. Chuyển khoa
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
                document.getElementById('current-visit-box').style.display = 'none';
                document.getElementById('call-next-box').style.display = 'block';
                window.currentVisitId = null;
                loadRoomQueue(window.currentRoomId);
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    // 10. Thanh toán
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

    // data.bill từ API
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
    
    // Lấy dịch vụ và thuốc từ bảng đã hiển thị
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
    populatePatientsSelect();
    populateDoctorsSelect();
    populateDepartmentsSelect();
    populateServicesSelect();
    populateMedicinesSelect();
    populateRoomsSelect();
});
