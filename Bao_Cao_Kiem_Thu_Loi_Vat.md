# BÁO CÁO KIỂM THỬ CHUYÊN SÂU & KHẮC PHỤC TRIỆT ĐỂ LỖI VẶT (DOGFOODING AUDIT)

> **Mục tiêu:** Đóng vai người dùng trải nghiệm thực tế mọi ngóc ngách của ứng dụng Focus Flow • Pomodoro 50/10 Pro, tìm kiếm toàn bộ các lỗi vặt, lệch nhịp giao diện, bất đồng bộ dữ liệu và bổ sung cơ chế tự động kỷ luật (tắt màn hình / khóa máy / rèm đen) cho chế độ Nghỉ Mắt 50/10.

---

## 1. Nâng Cấp Trọng Tâm: Kỷ Luật Tự Động Cho Chế Độ Nghỉ Mắt 50/10

### Vấn đề trước đây:
- Khi hết 50 phút dùng máy tính, popup *"ĐÃ HẾT 50 PHÚT DÙNG MÁY TÍNH"* xuất hiện nhưng **không có bộ đếm ngược tự động ép buộc**. Nếu người dùng rời khỏi bàn hoặc phớt lờ, máy tính vẫn sáng vô thời hạn và không bao giờ tự tắt màn hình.
- Có sự lệch nhãn giữa giao diện (`turnoff`) và backend Python (`screen_off`), dẫn đến việc khi chọn *"Tắt Màn Hình Hoàn Toàn"* trong Cài đặt, lệnh tắt màn hình không được thực thi.

### Giải pháp đã hoàn thành:
1. **Đồng bộ hóa 100% cơ chế kỷ luật giữa Học Tập và Nghỉ Mắt**:
   - Khi hết 50 phút dùng máy, popup tự động kích hoạt **Thanh đếm ngược kỷ luật 15 giây**:
     - Nếu chọn Tắt màn hình: *"⚡ Tự động tắt màn hình bảo vệ mắt sau: 15s"*
     - Nếu chọn Khóa máy: *"🔒 Tự động khóa máy tính nghỉ ngơi sau: 15s"*
     - Nếu chọn Rèm đen: *"🛡️ Tự động kích hoạt rèm đen sau: 15s"*
   - Nếu sau 15 giây người dùng không bấm *"Dùng thêm 5 phút"*, hệ thống **tự động kích hoạt giờ nghỉ mắt 10 phút và gửi tín hiệu tắt màn hình ngay lập tức**.
2. **Khắc phục lỗi lệch từ khóa `turnoff` $\leftrightarrow$ `screen_off`**:
   - Chuẩn hóa trên toàn bộ Python `main.py`, `system_actions.py` và JavaScript.
   - Hàm `turn_off_monitor()` và `wake_up_monitor()` được đưa vào daemon thread riêng biệt với timeout an toàn, loại trừ 100% nguy cơ treo giao diện.
3. **Nâng cấp thẩm mỹ Popup Nghỉ Mắt**:
   - Gỡ bỏ nền xanh lam cứng nhắc `rgb(10, 25, 47)` cũ.
   - Tự động ăn theo tông màu nền không gian bạn chọn (Espresso, Matcha, Gỗ Trầm, OLED, v.v.) với hiệu ứng viền phát sáng và kính mờ cao cấp.

---

## 2. Bảng Tổng Hợp Các Lỗi Vặt Được Phát Hiện & Xử Lý

| STT | Vị trí / Tính năng | Hiện tượng lỗi vặt trước đây | Nguyên nhân kỹ thuật | Giải pháp đã khắc phục |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Bàn xoay đĩa than Lofi** | Bấm bắt đầu học nhưng đĩa không quay, cần gạt không hạ, giờ ở tâm đĩa đứng yên ở `50:00`. | Các class `.spinning`, `.playing` và id `vinylClockDigits`, `vinylProgressArc` chưa được gắn vào vòng lặp `updateTimer`. | Tự động hạ cần gạt (`.playing`), xoay đĩa than (`.spinning`), chạy viền vòng cung tiến độ và đếm ngược từng giây tại tâm đĩa. Bổ sung tính năng nhấp trực tiếp vào đĩa than để Play/Pause. |
| **2** | **Âm thanh nền Lofi** | Nhấp vào các nút `Mưa`, `Đĩa Than`, `Lò Sưởi` nhưng không có tiếng phát ra. | Biến trạng thái kiểm tra `window.lastStatus.state === 'running'` bị `undefined`. | Sửa hàm `selectAmbientSound()` để khi bấm nút lập tức phát âm thanh ngay. Tự động đồng bộ bật/tắt tiếng nền theo nhịp học và nghỉ. |
| **3** | **Sổ Ý Tưởng (Tab 2)** | Xóa hoặc bấm hoàn thành một ghi chú ở trên cùng thì lại xóa/đổi nhầm ghi chú ở dưới cùng. | Frontend dùng `unshift()` (thêm vào đầu mảng) trong khi Python dùng `append()` (thêm vào cuối), khiến chỉ số index bị đảo ngược hoàn toàn. | Đổi backend `BrainDumpManager.add_note()` sang `insert(0, ...)` để cả hai bên đều đồng bộ chuẩn Newest-First. |
| **4** | **Cài đặt Kỷ luật (Tab 4)** | Nút radio *"Tắt Màn Hình Hoàn Toàn"* không được tích chọn đúng khi khởi động ứng dụng. | Kiểm tra `checked = (mode === "turnoff")` trong khi config lưu `"screen_off"`. | Đồng bộ hóa `mode === "turnoff" \|\| mode === "screen_off"`. |
| **5** | **Hẹn giờ Custom (Header)** | Popup chỉnh giờ ở thanh tiêu đề chỉ cho chỉnh phút, không cho chỉnh số ca mục tiêu. | Thiếu hàng chọn số ca mục tiêu trong modal. | Bổ sung trực tiếp hàng nút chọn số ca (1 ca, 2 ca, 3 ca, 4 ca, Vô hạn) ngay trong popup custom giờ. |
| **6** | **Hàng rào xao nhãng (Friction)** | Khi đóng popup xao nhãng, bộ đếm 3 giây ngầm vẫn chạy. | Chưa gọi `clearInterval(frictionTimer)` khi đóng. | Thêm `clearInterval(frictionTimer)` triệt để vào `hideFrictionBarrier()`. |

---

## 3. Hình Ảnh Nghiệm Thu Trực Quan

- **Giao diện Bàn học khi đang chạy ca học (Đĩa than quay, cần gạt hạ, đếm giờ 49:59)**:
  `verified_turntable_running_active.png`
- **Popup Hết Giờ Nghỉ Mắt với đếm ngược tự động tắt màn hình (15s)**:
  `verified_eyecare_modal_countdown.png`
- **Giao diện Bàn học ấm cúng với Mèo Pixel & Khói Cà Phê**:
  `verified_eyecare_upgraded_desk.png`
