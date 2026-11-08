# 📖 CẨM NANG HƯỚNG DẪN SỬ DỤNG TOÀN DIỆN • FOCUS FLOW v1.0
> **Precision Desktop Study & Eye Care Tool • Chuẩn Thẩm Mỹ Lofi & Khoa Học 50/10**

Chào mừng bạn đến với **Focus Flow**! Đây là công cụ quản trị thời gian tập trung học tập sâu và bảo vệ mắt theo chu kỳ khoa học **Pomodoro 50/10**, được thiết kế 100% Native Desktop chạy mượt mà 60 FPS với triết lý tối giản, thẩm mỹ cao và không dính quảng cáo gián đoạn.

Dưới đây là cẩm nang chi tiết hướng dẫn từng tính năng, cách chuyển đổi giao diện, cách dùng Mini HUD ghim nổi góc màn hình và lời khuyên thiết lập tối ưu nhất cho từng nhu cầu.

---

## 📑 MỤC LỤC
1. [Khởi Động & Thao Tác Cơ Bản](#1-khởi-động--thao-tác-cơ-bản)
2. [Hướng Dẫn Mini HUD (Thanh Ghim Nổi Góc Màn Hình)](#2-hướng-dẫn-mini-hud-thanh-ghim-nổi-góc-màn-hình)
3. [Bộ Sưu Tập Giao Diện & Cách Chuyển Đổi Nền Động](#3-bộ-sưu-tập-giao-diện--cách-chuyển-đổi-nền-động)
4. [Chi Tiết Tab Cài Đặt (Settings) & Gợi Ý Thiết Lập Tối Ưu](#4-chi-tiết-tab-cài-đặt-settings--gợi-ý-thiết-lập-tối-ưu)
5. [Hai Chế Độ Sử Dụng: Học Tập Sâu vs Nghỉ Mắt 50/10](#5-hai-chế-độ-sử-dụng-học-tập-sâu-vs-nghỉ-mắt-5010)
6. [Sổ Bắt Ý Tưởng Bất Chợt (Brain Dump) & Micro-Checklist](#6-sổ-bắt-ý-tưởng-bất-chợt-brain-dump--micro-checklist)
7. [Hàng Rào Chống Xao Nhãng & Hỗ Trợ Học Trên YouTube/Facebook](#7-hàng-rào-chống-xao-nhãng--hỗ-trợ-học-trên-youtubefacebook)
8. [Hẹn Giờ Xem Phim / Anime (Movie Timer)](#8-hẹn-giờ-xem-phim--anime-movie-timer)
9. [Bảng Phím Tắt Toàn Năng (Quick Shortcuts)](#9-bảng-phím-tắt-toàn-năng-quick-shortcuts)

---

## 1. KHỞI ĐỘNG & THAO TÁC CƠ BẢN

### Cách mở ứng dụng & Tạo biểu tượng ngoài Desktop:
- **Người dùng tải bản ZIP (.exe)**:
  - Giải nén thư mục và nhấp đúp vào **`Chay_Focus_Flow.bat`**: File sẽ tự động gỡ cảnh báo bảo mật, **tự động tạo biểu tượng Focus Flow siêu nét ngoài Desktop**, và mở app ngay!
  - Hoặc nhấp đúp vào file **`Tao_Shortcut_Desktop.bat`** để tạo lại biểu tượng ngoài Desktop bất cứ lúc nào.
- **Người dùng chạy bằng Python**: Nhấp đúp vào shortcut `Focus Flow` ngoài Desktop hoặc chạy `scripts/Chay_Pomodoro_Khong_Hien_Console.vbs`.

### Thao tác điều khiển chính:
- **Bắt đầu / Tạm dừng ca học**: Bấm nút Play tròn lớn ở giữa màn hình hoặc nhấn phím <kbd>Space</kbd> (Phím cách).
- **Bỏ qua ca hiện tại (Skip)**: Bấm nút mũi tên đôi `⏭` ở góc đồng hồ để chuyển ngay từ ca học sang ca nghỉ hoặc ngược lại.
- **Di chuyển cửa sổ**: Nhấn giữ chuột trái vào thanh tiêu đề trên cùng (Titlebar) để kéo ứng dụng đến vị trí bất kỳ.

---

## 2. HƯỚNG DẪN MINI HUD (THANH GHIM NỔI GÓC MÀN HÌNH)

Mini HUD là tính năng độc quyền giúp bạn theo dõi thời gian đếm ngược mà **không chiếm dụng diện tích màn hình** khi đang viết code, đọc tài liệu PDF, làm bài tập Word hay chơi game.

<p align="center">
  <em>Mini HUD siêu nhỏ gọn (320x64px), tự động ghim nổi trên mọi cửa sổ (Always-On-Top).</em>
</p>

### Cách chuyển đổi qua lại giữa Cửa Sổ Lớn và Mini HUD:
- **Cách 1 (Nhanh nhất)**: Nhấn phím <kbd>F8</kbd> hoặc tổ hợp <kbd>Ctrl + M</kbd>.
- **Cách 2**: Nhấp đúp chuột vào bất kỳ khoảng trống nào trên thanh tiêu đề trên cùng.
- **Cách 3**: Bấm vào biểu tượng thu nhỏ hình ô vuông `◱` ở góc trên bên phải cửa sổ lớn.
- **Để phóng to lại cửa sổ lớn**: Nhấp đúp vào thanh Mini HUD hoặc bấm nút `◱` trên thanh Mini HUD.

### Các nút điều khiển trên Mini HUD:
1. **Kéo thả tự do**: Giữ chuột trái vào phần nền hoặc chữ số của Mini HUD và rê chuột để đặt thanh ở góc dưới cùng, góc trên màn hình tùy ý.
2. **Nút Play/Pause (▶ / ⏸)**: Bật/tắt đếm ngược nhanh.
3. **Nút Ngôi Sao (★) - Đổi hiệu ứng nền 1-Click**:
   - Mỗi lần nhấp chuột vào nút `★`, nền Mini HUD sẽ lập tức đổi sang một phong cách hạt động 60 FPS khác nhau (Mưa Laser, Hoa Anh Đào, Đèn Trời, Tuyết Rơi, Sao Băng...).
4. **Nút Bỏ Qua (⏭)**: Nhảy nhanh sang giờ nghỉ nếu bạn hoàn thành mục tiêu sớm.
5. **Nút Phóng To (◱)**: Trở lại giao diện đầy đủ để xem thống kê, ghi chú hoặc đổi cài đặt.
6. **Thanh tiến độ đáy**: Dải sáng gradient ở mép dưới Mini HUD sẽ tự động thu ngắn dần theo từng giây, giúp bạn nhận biết tiến độ ca học chỉ bằng ánh nhìn thoáng qua.

---

## 3. BỘ SƯU TẬP GIAO DIỆN & CÁCH CHUYỂN ĐỔI NỀN ĐỘNG

Focus Flow tích hợp sẵn **8 không gian nghệ thuật (Dynamic Ambient Canvases)** chạy 100% bằng Canvas GPU nội bộ, hoàn toàn không tốn CPU hay pin máy tính.

### Cách mở Bảng Chọn Giao Diện:
- Bấm vào nút **`☕ Lofi`** (hoặc biểu tượng bảng màu) ở chính giữa thanh tiêu đề trên cùng.
- Hoặc vào **Tab Cài Đặt** ➔ Bấm nút **`Mở Bộ Sưu Tập`**.

### Chi tiết 8 Không Gian Nghệ Thuật:
| Tên Chủ Đề | Phong Cách & Màu Nhấn | Hiệu Ứng Hạt 60 FPS | Cảm Xúc & Phù Hợp Cho |
| :--- | :--- | :--- | :--- |
| 🌌 **Biển Sao Đêm (Twilight)** | Lam ngọc vũ trụ (Cyan / Deep Blue) | Bong bóng thủy tinh phản quang & Vệt sao băng lướt nhẹ | Tập trung sâu vào ban đêm, làm việc yên tĩnh |
| 🏮 **Đèn Trời Hoa Đăng (Lanterns)** | Hổ phách ấm áp (Amber / Golden Glow) | Đèn hoa đăng phát sáng đung đưa bốc lên trời cao | Cảm giác ấm cúng, thư thái sau những giờ căng thẳng |
| 🌸 **Hoa Anh Đào (Sakura)** | Hồng đào xuân (Pastel Rose / Blossom) | Cánh hoa anh đào lượn sóng êm ả & Đom đóm mùa xuân | Học tập nhẹ nhàng, đọc sách văn học, thư giãn |
| 🔥 **Bếp Lửa Ấm Áp (Fireplace)** | Gỗ mun & Lửa ấm (Rustic Wood / Ember) | Tàn lửa cam bập bùng bay lơ lửng trong không gian | Mùa đông lạnh giá, đêm khuya ngồi bên bàn học |
| ⚡ **Mưa Laser Cyber (Cyber)** | Neon Cyberpunk (Cyan #00f3ff & Pink #ff0080) | Mưa vệt laser công nghệ cao & Gợn sóng phản chiếu | Code phần mềm, giải thuật toán, thiết kế đồ họa |
| 🌲 **Cực Quang Zen (Aurora)** | Rừng thông & Xanh ngọc (Nordic Matcha) | Dải lụa cực quang Bắc Cực uốn lượn huyền ảo | Thiền định, thanh lọc tâm trí, tránh kiệt sức |
| ❄️ **Bão Tuyết Pha Lê (Snow)** | Pha lê băng tuyết (Crystal Ice & Sky Blue) | 3 tầng bông tuyết đa chiều rơi chậm chạp | Không gian tĩnh lặng tuyệt đối, giải toán tư duy |
| 👾 **Vũ Trụ 8-Bit Pixel (Pixel)** | Arcade cổ điển (Indigo & Retro Gold) | Sao lấp lánh phong cách máy chơi game hoài niệm | Fan phong cách retro, sáng tạo nội dung |

### Bộ phát âm thanh nền Lofi Offline (Không cần mở YouTube):
- Ở góc trên giao diện, bấm nút chiếc loa `🔊` để mở menu âm thanh:
  - 🌧️ **Tiếng Mưa Rơi**: Tiếng mưa rả rích bên khung cửa kính.
  - 📻 **Tiếng Đĩa Than**: Tiếng xèo xèo ấm cúng của đầu đọc đĩa than vinyl vintage.
  - 🔥 **Tiếng Lò Sưởi**: Tiếng gỗ nổ tanh tách êm tai.
- Tự do tăng giảm âm lượng tiếng nền phù hợp để át đi tiếng ồn xung quanh.

---

## 4. CHI TIẾT TAB CÀI ĐẶT (SETTINGS) & GỢI Ý THIẾT LẬP TỐI ƯU

Nhấp vào biểu tượng bánh răng **`Cài Đặt`** ở thanh điều hướng để mở bảng thiết lập:

### 1. Chu Kỳ Học & Nghỉ (Pomodoro Presets)
- **`50/10'` (Mặc định & Khuyên dùng hàng đầu)**:
  - *Đặc điểm*: 50 phút tập trung học sâu + 10 phút nghỉ ngơi rời mắt khỏi màn hình.
  - *Phù hợp nhất*: Sinh viên đại học, học sinh ôn thi tốt nghiệp/đại học, lập trình viên code dự án dài, nghiên cứu tài liệu nặng. Chu kỳ 50 phút đủ dài để não đạt trạng thái dòng chảy tư duy (Flow State).
- **`25/5'` (Chuẩn Pomodoro truyền thống)**:
  - *Đặc điểm*: 25 phút làm việc + 5 phút nghỉ ngắn.
  - *Phù hợp nhất*: Giải quyết các tác vụ ngắn, trả lời email, dọn dẹp hòm thư, làm bài tập trắc nghiệm nhanh, người mới bắt đầu luyện tập thói quen kỷ luật.
- **`90/20'` (Chu kỳ nhịp sinh học Ultradian)**:
  - *Đặc điểm*: 90 phút tập trung cao độ + 20 phút nghỉ phục hồi toàn diện.
  - *Phù hợp nhất*: Luyện đề thi thử đúng thời gian thực, vẽ đồ họa, thiết kế kiến trúc.
- **Mục Tiêu Ca Trong Ngày**: Nên chọn **`3 ca`** hoặc **`4 ca`** (tương đương 2.5 - 3.5 giờ học tập trung tinh khiết mỗi ngày là mức lý tưởng của các thủ khoa).

---

### 2. Cơ Chế Ép Buộc Khi Đến Giờ Nghỉ (Enforcement Mode)
Khi đồng hồ đếm ngược hết 50 phút, ứng dụng sẽ áp dụng cơ chế bạn đã chọn:
- **`Rèm Đen Phủ Màn Hình (Overlay) - KHUYÊN DÙNG NHẤT`**:
  - Toàn bộ màn hình sẽ được phủ một lớp rèm đen dịu mắt hiển thị đồng hồ đếm ngược 10 phút, kèm hướng dẫn bài tập mắt 20-20-20.
  - *Lý do khuyên dùng*: Vừa đủ nghiêm khắc để bạn rời mắt khỏi màn hình, nhưng vẫn giữ quyền chủ động (có nút gia hạn 5 phút nếu bạn đang cần bấm lưu bài tập dở dang).
- **`Khóa Máy Trạm (Lock Windows)`**:
  - Tự động kích hoạt màn hình khóa Windows (`Win + L`).
  - *Phù hợp nhất*: Những bạn hay bị "ngứa tay" ngồi lướt tiếp dù đã đến giờ nghỉ. Bắt buộc bạn phải đứng dậy đi lại uống nước.
- **`Tắt Màn Hình Hoàn Toàn (Turn Off Monitor)`**:
  - Gửi lệnh tắt tín hiệu màn hình ngay lập tức (tiết kiệm điện năng).
  - *Đặc điểm*: Chỉ cần khẽ chạm vào chuột hoặc phím bất kỳ, màn hình sẽ sáng lại ngay.

---

### 3. Trợ Năng Tập Trung & Sức Khỏe
- **Hàng Rào Trì Hoãn 3s (Friction Barrier - NÊN BẬT)**:
  - Khi bạn vô tình mở các trang web gây nghiện (Facebook, TikTok, YouTube...), ứng dụng sẽ chặn lại bằng một màn hình chánh niệm trong 3 giây.
  - Giúp bạn khựng lại 3 giây để tỉnh táo tự hỏi: *"Mình mở trang này làm gì?"*.
- **Nhắc Nhở Bảo Vệ Thị Giác 20-20-20 (NÊN BẬT)**:
  - Cứ vào giờ nghỉ, hệ thống sẽ nhắc bạn: *Nhìn ra xa 6 mét (ngoài cửa sổ) trong 20 giây* để các cơ mi mắt giãn ra, chống cận thị và khô giác mạc.
- **Nhắc Nhở Nửa Chặng Đường (Phút 25 - NÊN BẬT)**:
  - Một tiếng chuông gõ nhẹ vào phút thứ 25 nhắc bạn kiểm tra: *"Mình đã đi được 1/2 thời gian, tiến độ mục tiêu bước nhỏ đang đến đâu rồi?"*.
- **Nhắc Nhở Đóng Gói (Phút 48 - NÊN BẬT)**:
  - Rung chuông báo trước 2 phút trước khi hết ca học, nhắc bạn lưu lại mã nguồn, đóng nắp bút hoặc đúc kết kiến thức vừa học.

---

### 4. Âm Thanh & Chuông Báo
- **Thanh trượt âm lượng**: Khuyên đặt ở mức **70% - 80%**.
- **Nút "Nghe thử"**: Bấm để nghe thử tiếng chuông kết thúc ca xem có vừa vặn với tai nghe hay loa ngoài của bạn không.

---

## 5. HAI CHẾ ĐỘ SỬ DỤNG: HỌC TẬP SÂU VS NGHỈ MẮT 50/10

Ngay phía trên giao diện có công tắc chuyển đổi giữa 2 chế độ:

1. **🎓 Chế Độ 1: Tập Trung Học Tập (Study Focus Mode)**:
   - Áp dụng đầy đủ kỷ luật Pomodoro: Bảng mục tiêu bước nhỏ (Micro-checklist), Hàng rào chặn xao nhãng, Chuông báo đóng gói và Đánh giá tổng kết sau ca.
   - Thích hợp khi bạn ngồi vào bàn học bài, ôn thi hoặc làm việc nghiêm túc.

2. **👁️ Chế Độ 2: Nghỉ Mắt 50/10 (Eye Rest Mode)**:
   - Dành riêng cho những lúc bạn dùng máy tính để đọc báo, xem phim, giải trí hoặc làm việc văn phòng thông thường.
   - **Hoàn toàn không chặn web, không ép mục tiêu checklist**.
   - Cứ sau 50 phút sử dụng máy, ứng dụng chỉ nhẹ nhàng nhắc bạn nghỉ mắt 10 phút, chớp mắt uống nước và xoay cổ vai gáy rồi cho phép dùng tiếp.

---

## 6. SỔ BẮT Ý TƯỞNG BẤT CHỢT (BRAIN DUMP) & MICRO-CHECKLIST

### 💡 Sổ Bắt Ý Tưởng (Phím tắt: Ctrl + Shift + D)
Trong lúc đang tập trung cao độ, não bộ chúng ta rất hay nảy ra các ý nghĩ bất chợt: *"Tối nay phải mua sữa"*, *"Ý tưởng đề tài này hay này"*, *"Phải nhắn tin cho bạn A"*. Nếu mở Facebook hay điện thoại để ghi lại, bạn sẽ bị cuốn vào mạng xã hội và mất tập trung ngay!
- **Giải pháp**: Nhấn ngay <kbd>Ctrl + Shift + D</kbd>, nhập nhanh dòng suy nghĩ trong 2 giây rồi bấm <kbd>Enter</kbd>.
- Ý tưởng sẽ được cất an toàn vào sổ. Não bạn sẽ an tâm không sợ quên và lập tức quay lại mạch học tập.
- Cuối ngày, bạn vào Tab **Ý Tưởng** để xem lại toàn bộ những điều đã ghi.

### 📝 Micro-Checklist (Chia nhỏ mục tiêu ca học)
Đừng đặt mục tiêu quá lớn như *"Học hết chương 3"*. Hãy chia thành 3 bước nhỏ trên giao diện:
1. Đọc xong từ trang 20 đến 30.
2. Tóm tắt 5 công thức quan trọng ra vở.
3. Giải xong 3 bài tập ví dụ.
Mỗi khi tích chọn hoàn thành một bước, thanh tiến độ sẽ sáng lên tạo động lực rất lớn cho não bộ!

---

## 7. HÀNG RÀO CHỐNG XAO NHÃNG & HỖ TRỢ HỌC TRÊN YOUTUBE/FACEBOOK

Focus Flow nhận diện thông minh các phần mềm và website bạn sử dụng trong ca học:

### Nếu bạn cần xem bài giảng hoặc livestream học tập trên YouTube / Facebook:
Bạn **không cần tắt app hay tắt tính năng chống xao nhãng**:
1. **Cách 1**: Bấm nút gạt **`[🎓 YouTube/FB học]`** ngay trên thanh công cụ bàn học. Khi bật nút này, hệ thống sẽ tự động tính thời gian lướt YouTube/FB vào hạng mục **Học Trực Tuyến** thay vì xao nhãng.
2. **Cách 2**: Khi Hàng Rào Chánh Niệm hiện ra khi bạn mở link video, hãy bấm vào nút:
   ➔ **`[🎓 Tôi đang học bài / Xem bài giảng]`**
   Hệ thống sẽ lập tức nhường màn hình cho bạn học tiếp mà không nhắc lại nữa!

### Tab Thống Kê & Báo Cáo Độ Thuần Khiết (Purity Report):
- Vào Tab **📊 Thống Kê** để xem biểu đồ tròn phân tích ngày hôm nay bạn đã dành:
  - Bao nhiêu phút cho **Học tập sâu** (VS Code, Word, PDF Reader...).
  - Bao nhiêu phút cho **Học trực tuyến** (YouTube bài giảng, tài liệu khóa học).
  - Bao nhiêu phút bị **Xao nhãng** (Mạng xã hội, game...).
- Bạn có thể nhấp chuột trực tiếp vào nhãn `[🎓 Học sâu]` hoặc `[⚠️ Xao nhãng]` bên cạnh mỗi ứng dụng để đổi phân loại nếu hệ thống nhận diện chưa đúng ý bạn.

---

## 8. HẸN GIỜ XEM PHIM / ANIME (MOVIE TIMER)

Khi bạn muốn xem một tập phim anime giải trí hoặc một bộ phim điện ảnh mà sợ bị xem quên giờ, hãy dùng tính năng **Movie Timer**:
- Nhấn phím <kbd>F9</kbd> để mở nhanh menu Hẹn giờ xem phim.
- Chọn một trong các mốc:
  - **45 Phút**: 1 tập Anime / Sitcom / Phim truyền hình.
  - **90 Phút**: 1 phim điện ảnh vừa.
  - **120 Phút**: 1 phim rạp bom tấn dài.
- Trong thời gian này, ứng dụng sẽ **tạm ngưng tất cả các thông báo chặn**. Khi phim kết thúc, chuông báo sẽ rung lên để nhắc bạn đi ngủ hoặc đứng dậy vận động bảo vệ mắt.

---

## 9. BẢNG PHÍM TẮT TOÀN NĂNG (QUICK SHORTCUTS)

| Phím tắt | Chức năng thực hiện |
| :--- | :--- |
| <kbd>Space</kbd> (Phím cách) | Bắt đầu ca học / Tạm dừng / Tiếp tục đếm ngược |
| <kbd>F8</kbd> hoặc <kbd>Ctrl + M</kbd> | Bật / Tắt thanh Widget Mini HUD ghim nổi góc màn hình |
| <kbd>Ctrl + Shift + D</kbd> | Mở nhanh ô Cất giữ ý tưởng tức thì (Brain Dump) |
| <kbd>F9</kbd> | Mở nhanh menu Hẹn giờ xem phim / Tạm ngưng chặn |
| <kbd>Enter</kbd> | Thêm nhanh mục tiêu bước nhỏ tiếp theo trong danh sách |
| Nhấp đúp vào thanh tiêu đề | Phóng to / Thu nhỏ giữa Cửa sổ chính và Mini HUD |
| Giữ chuột trái trên Mini HUD | Kéo thả di chuyển thanh Mini HUD đến mọi góc màn hình |
| Nhấp vào nút ★ trên Mini HUD | Đổi hiệu ứng động nền 60 FPS tức thì |

---

> 💡 **Lời khuyên vàng**: Hãy cài đặt **Preset 50/10'** cùng cơ chế **Rèm Đen Phủ Màn Hình**, sau đó bấm <kbd>F8</kbd> để đưa về **Mini HUD** ghim ở góc dưới màn hình. Bạn sẽ có một không gian học tập và làm việc siêu tập trung, thẩm mỹ và bảo vệ thị giác trọn vẹn mỗi ngày!
