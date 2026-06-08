# 💎 BÁO CÁO KỸ THUẬT TOÀN DIỆN: LINUX DOCTOR HYBRID AI

**Ngày phát hành:** 02/06/2026
**Trạng thái:** Đồ án môn học (Academic Project)
**Phân loại:** Tài liệu công khai — phát hành kèm mã nguồn theo giấy phép MIT

---

## 📑 TÓM TẮT DỰ ÁN (EXECUTIVE SUMMARY)

**Linux Doctor** là bước đột phá trong tự động hóa vận hành IT, định hình lại cách các kỹ sư SRE (Site Reliability Engineering) xử lý sự cố. Thay vì những chuỗi lệnh kiểm tra thủ công, rời rạc và tốn thời gian, Linux Doctor cung cấp một "Bộ Não Lai" (Hybrid AI):
*   **Tốc độ:** Lớp Machine Learning xử lý và khoanh vùng vấn đề (Domain) từ log chỉ trong vài mili-giây.
*   **Sâu sắc:** Lớp Expert System (Hệ thống Chuyên gia) tự động hóa việc thu thập bằng chứng, suy luận nhân quả (RCA - Root Cause Analysis) minh bạch.
*   **Trực quan:** Bảng điều khiển Mission Control mang lại trải nghiệm phân tích sự cố ở đẳng cấp cao nhất.

Báo cáo này công bố chi tiết về hiệu năng mô hình AI và cung cấp **hồ sơ thực chứng (Evidences)** toàn diện nhất của hệ thống qua 11 Domain sự cố Linux cốt lõi.

---

## 1. ⚙️ KIẾN TRÚC LÕI HỢP NHẤT (UNIFIED ARCHITECTURE)

Hệ thống được thiết kế theo tư tưởng "Không phụ thuộc" (Zero-dependency architecture ngoài NumPy/Rich) nhằm đảm bảo tối đa tính bảo mật và dễ dàng kiểm toán.

```mermaid
graph TD
    %% Định nghĩa Style đẳng cấp
    classDef input fill:#fdfbfb,stroke:#ebedee,stroke-width:2px,color:#333;
    classDef mlLayer fill:#f0f9ff,stroke:#0284c7,stroke-width:2px,color:#0369a1;
    classDef expertLayer fill:#f0fdf4,stroke:#16a34a,stroke-width:2px,color:#15803d;
    classDef output fill:#fffbeb,stroke:#d97706,stroke-width:2px,color:#b45309;

    A[⚠️ Lời gọi Sự cố / Log]:::input -->|Vector hóa Text| B(Engine Xử lý Ngôn ngữ Tự nhiên - NLP):::mlLayer
    B -->|Trích xuất Đặc trưng| C(Mô hình Phân loại ML):::mlLayer
    C -->|Quyết định Domain & Điểm tự tin| D{Bộ Chọn Lọc Tri Thức}:::expertLayer
    
    D -->|Khớp Rule YAML| E(Động Cơ Suy Luận Tiến - Forward Chaining):::expertLayer
    E -->|Kích hoạt Giả thuyết| F[Shell Executor - Thu thập Chứng cứ]:::expertLayer
    F -->|Đánh giá bằng thuật toán Bayes| G(Động Cơ Xếp Hạng Giả Thuyết):::expertLayer
    
    G -->|Truy vết Suy luận| H[💻 Trạm Điều Khiển Mission Control TUI]:::output
    H --> I((💡 Chẩn Đoán Cốt Lõi & Giải Pháp Tối Ưu)):::output
```

---

## 2. 🧠 HIỆU NĂNG MÔ HÌNH HỌC MÁY (ML BENCHMARKS)

Với việc mở rộng quy mô dữ liệu huấn luyện lên **101.758 mẫu** (Scale-up), hệ thống đã giải quyết triệt để tình trạng Overfitting. Đội ngũ đã tự xây dựng toàn bộ thuật toán từ thư viện Toán học `NumPy` nhằm giữ kiểm soát hoàn toàn thuật toán.

### 2.1. Đỉnh Cao Chính Xác: Multinomial Naive Bayes (🏆 Tốt nhất)
Đạt điểm số tuyệt đối **F1-Score 99.49%**. Mô hình này có khả năng phân tách ranh giới ngữ nghĩa của log với sự chính xác gần như hoàn hảo, là "Bộ não nhận thức" chính của hệ thống.
![Đánh giá Naive Bayes](../Pictures/model/naive_bayes.png)

### 2.2. Phân Tách Siêu Phẳng: Linear SVM
Sức mạnh của SVM (`F1: 99.4%`) nằm ở khả năng phân tách các Domain có từ vựng dễ nhầm lẫn như (SSH vs Network, Systemd vs Docker).
![Đánh giá Linear SVM](../Pictures/model/linear_svm.png)

### 2.3. Tinh Chỉnh Độ Tự Tin: Logistic Regression
Mô hình Logistic (`F1: 99.2%`) cung cấp khả năng đánh giá xác suất mượt mà nhất nhờ hàm Softmax, là công cụ không thể thiếu để đo lường độ chắc chắn của dự đoán.
![Đánh giá Logistic Regression](../Pictures/model/logistic_regression.png)

---

## 3. 🔬 HỒ SƠ THỰC CHỨNG TOÀN DIỆN (COMPREHENSIVE MISSION CONTROL LOGS)

Dưới đây là bộ sưu tập **toàn bộ 20 minh chứng thực nghiệm** chi tiết nhất của hệ thống trên 11 Domains sự cố phổ biến của Linux. Mỗi hình ảnh đại diện cho khả năng phân tích chuỗi nguyên nhân - kết quả cực kỳ sâu sắc của Expert System.

### 🐳 3.1. Hệ Sinh Thái Container (Docker)
Hệ thống chứng minh sức mạnh phân tích đa dạng từ lỗi Quyền hạn (Permission), lỗi khởi động Daemon, cho đến các sự cố không thể truy cập mạng ảo (Bridge/Network).
*   **Góc độ quyền hạn & cấu hình:**
    ![Docker Test 1](../Pictures/test/docker-test1.png)
    ![Docker Test 2](../Pictures/test/docker-test2.png)
*   **Góc độ vòng đời Container & Network:**
    ![Docker Test 3](../Pictures/test/docker-test3.png)
    ![Docker Test 4](../Pictures/test/docker-test4.png)
    ![Docker Test Basic](../Pictures/test/docker-test.png)

### 💻 3.2. Cốt Lõi Hệ Thống (CPU & Memory)
Chẩn đoán các hiện tượng thắt cổ chai tài nguyên, process bị kẹt (Zombie/D-state), rò rỉ bộ nhớ (OOM Killer) hoặc CPU Throttling.
*   **Báo cáo tài nguyên CPU:**
    ![CPU Test 1](../Pictures/test/cpu-test1.png)
    ![CPU Test 2](../Pictures/test/cpu-test2.png)
*   **Báo cáo tài nguyên RAM/Swap:**
    ![Memory Test 1](../Pictures/test/memory-test.png)
    ![Memory Test 2](../Pictures/test/memory-test2.png)

### 💽 3.3. Lưu Trữ & Phân Vùng (Disk)
Đánh giá độ sâu IOPS, tình trạng cạn kiệt Inode, và phân tích Bad Block trên ổ cứng vật lý.
![Disk Test 1](../Pictures/test/disk-test.png)
![Disk Test 2](../Pictures/test/disk-test2.png)

### 🌐 3.4. Định Tuyến Mạng & Tên Miền (Network & DNS)
Kiểm tra độ trễ (Latency), rớt gói tin (Packet Loss), xung đột bảng định tuyến (Routing Table) và các sự cố truy vấn DNS phân giải thất bại.
*   **Sự cố Mạng Cốt lõi:**
    ![Network Test](../Pictures/test/network-test.png)
*   **Sự cố Phân giải Tên miền:**
    ![DNS Test](../Pictures/test/dns-test.png)

### 🔐 3.5. Bảo Mật & Kết Nối (SSH)
Phát hiện việc cấu hình sai SSH Key, sai quyền hạn truy cập thư mục `.ssh`, cấu hình Daemon bị lỗi, hoặc bị chặn bởi Tường lửa.
![SSH Test 1](../Pictures/test/ssh-test1.png)
![SSH Test 2](../Pictures/test/ssh-test2.png)

### 🌍 3.6. Cổng Giao Tiếp Web (Nginx)
Truy vết cấu hình sai cú pháp (Syntax error), sự cố tranh chấp cổng (Bind Port), hoặc Backend Upstream (PHP-FPM/Node) không phản hồi.
![Nginx Test 1](../Pictures/test/nginx-test.png)
![Nginx Test 2](../Pictures/test/nginx-test2.png)

### ⚙️ 3.7. Dịch Vụ Hệ Thống & Quản Lý Gói (Systemd & Package)
Bóc tách nguyên nhân khởi động thất bại của Systemd (Coredump/Timeout) và phát hiện các thư viện bị hỏng (Broken Dependencies) của APT/YUM.
*   **Trạng thái Systemd:**
    ![Systemd Test](../Pictures/test/systemd-test.png)
*   **Trạng thái Quản lý Gói (Package):**
    ![Package Test](../Pictures/test/package-test1.png)

### 🐙 3.8. Quản Lý Phiên Bản (Git)
Xử lý các mâu thuẫn trong môi trường CI/CD hoặc lỗi cấu hình hệ thống quản lý mã nguồn nội bộ.
![Git Test](../Pictures/test/git-test.png)

---

## 4. 🛠️ KIỂM TOÁN VÀ LỘ TRÌNH ĐỘT PHÁ (AUDIT & ROADMAP)

Để chuyển hóa hoàn toàn hệ thống này từ "Công cụ chẩn đoán xuất sắc" trở thành "Nền tảng Vận hành Cấp Doanh nghiệp" (Enterprise Operation Platform), lộ trình năm 2026 sẽ tập trung vào 3 trụ cột cốt lõi:

1.  🛡️ **Bảo Mật Kín Khít (P0):** Chuyển đổi toàn diện cơ chế `Shell Executor` sang mô hình **Allowlist khắt khe**, triệt tiêu hoàn toàn khả năng khai thác Command Injection.
2.  ⚡ **Tốc Độ Xuyên Không (P1):** Kiến trúc lại Module thu thập bằng chứng từ Tuần tự (Sequential) sang Song song (Parallel/Async), đặt mục tiêu trả về kết quả phân tích hệ thống dưới **2.0 giây**.
3.  🗄️ **Bền Vững & Truy Vết (P2):** Thay thế State bộ nhớ tạm thời bằng kiến trúc Database hoàn chỉnh, cung cấp khả năng theo dõi Lịch sử Sự cố (Incident History) và Audit Trail dành cho quản lý.

---
*Báo cáo được hoàn thiện bằng chuẩn hóa dữ liệu cao nhất, minh chứng cho sức mạnh tuyệt đối của Linux Doctor Hybrid AI.*