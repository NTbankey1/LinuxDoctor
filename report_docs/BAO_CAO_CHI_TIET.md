     1|# 📊 BÁO CÁO HỆ THỐNG TRỰC QUAN: LINUX DOCTOR HYBRID AI
     2|
     3|Báo cáo này cung cấp cái nhìn sâu sắc, trực quan về hệ thống **Linux Doctor**, từ luồng hoạt động tổng thể (Architecture Flow), hiệu suất của các mô hình Machine Learning (được viết từ đầu), cho đến các bằng chứng thực nghiệm (Test Evidences) của Hệ thống Chuyên gia (Expert System).
     4|
     5|---
     6|
     7|## 1. ⚙️ Luồng Hệ Thống Tổng Thể (System Architecture Flow)
     8|
     9|Luồng hoạt động của hệ thống được chia thành 2 giai đoạn chính: **Machine Learning** (dự đoán domain) và **Expert System** (tìm kiếm nguyên nhân gốc rễ và đưa ra giải pháp).
    10|
    11|```mermaid
    12|graph TD
    13|    A[Người dùng nhập sự cố] -->|Ví dụ: 'docker permission denied'| B(Text Processing Engine)
    14|    B -->|Tokenize & Stem| C(TF-IDF Vectorizer)
    15|    C -->|Vector Text| D{ML Classifier}
    16|    
    17|    D -->|Naive Bayes/SVM| E[Xác định Domain & Độ tin cậy]
    18|    
    19|    E -->|Domain: 'docker', Conf: 95%| F(Knowledge Base Loader)
    20|    F -->|Load docker.yaml| G(Rule Engine - Forward Chaining)
    21|    
    22|    G -->|Tạo giả thuyết| H[Shell Executor]
    23|    H -->|Chạy lệnh 'groups'| I(Thu thập Bằng chứng)
    24|    
    25|    I --> J{Hypothesis Ranker}
    26|    J -->|Cập nhật điểm Bayesian| K(Reasoning Chain)
    27|    
    28|    K --> L[Rich CLI - Giao diện Báo cáo]
    29|    L --> M((Nguyên nhân gốc rễ & Giải pháp))
    30|
    31|    style A fill:#f9f,stroke:#333,stroke-width:2px
    32|    style D fill:#bbf,stroke:#333,stroke-width:2px
    33|    style G fill:#bfb,stroke:#333,stroke-width:2px
    34|    style L fill:#fbb,stroke:#333,stroke-width:2px
    35|```
    36|
    37|---
    38|
    39|## 2. 🧠 Đánh Giá Hiệu Suất Mô Hình Machine Learning
    40|
    41|Các mô hình được huấn luyện bằng tập dữ liệu **100.000+ samples**, sử dụng code xây dựng hoàn toàn từ **NumPy** (không dùng framework như Scikit-learn). Dưới đây là phân tích Confusion Matrix và biểu đồ trực quan của từng thuật toán.
    42|
    43|### 2.1. Multinomial Naive Bayes (Mô Hình Tốt Nhất 🏆)
    44|> **Độ chính xác (F1-Score):** 99.49%  
    45|> **Ưu điểm:** Khả năng mở rộng tuyệt vời với dữ liệu văn bản (Text Data), ổn định và cực kỳ nhanh.
    46|
    47|![Đánh giá Naive Bayes](../Pictures/model/naive_bayes.png)
    48|
    49|### 2.2. Linear SVM
    50|> **Độ chính xác (F1-Score):** ~99.4%  
    51|> **Ưu điểm:** Tách biệt các mặt phẳng siêu hình tốt (Margin optimization), sức mạnh vượt trội khi đối mặt với các domain có ranh giới từ vựng chồng chéo.
    52|
    53|![Đánh giá Linear SVM](../Pictures/model/linear_svm.png)
    54|
    55|### 2.3. Logistic Regression
    56|> **Độ chính xác (F1-Score):** ~99.2%  
    57|> **Ưu điểm:** Cho ra điểm xác suất (Probability) rất mượt mà thông qua hàm Softmax, hỗ trợ đắc lực cho việc Calibration (hiệu chuẩn độ tin cậy của AI).
    58|
    59|![Đánh giá Logistic Regression](../Pictures/model/logistic_regression.png)
    60|
    61|---
    62|
    63|## 3. 🔬 Minh Chứng Thực Nghiệm (Mission Control TUI)
    64|
    65|Hệ thống chuyên gia đã được thử nghiệm thực tế qua nhiều sự cố Linux khác nhau. Dưới đây là giao diện Mission Control tương tác, giải trình chi tiết nguyên nhân sự cố thông qua hệ thống log và reasoning chain.
    66|
    67|### 🐳 Domain: Docker
    68|Hệ thống có khả năng phân tách lỗi quyền hạn (Permission), lỗi Daemon, hay sự cố mất kết nối mạng lưới container.
    69|
    70|![Kiểm thử Docker 1](../Pictures/test/docker-test1.png)
    71|
    72|### 💻 Domain: CPU & System
    73|Phân tích hiện tượng quá tải CPU (CPU Throttling), Load Average tăng vọt, hoặc tiến trình bị kẹt (Zombie/D-state).
    74|
    75|![Kiểm thử CPU](../Pictures/test/cpu-test1.png)
    76|
    77|### 🌐 Domain: Nginx (Web Server)
    78|Nhận diện sự cố ở file cấu hình, lỗi bind port, hoặc backend upstream không phản hồi.
    79|
    80|![Kiểm thử Nginx](../Pictures/test/nginx-test.png)
    81|
    82|### 💽 Domain: Disk (Storage)
    83|Theo dõi các trường hợp đầy ổ cứng, cạn kiệt inode, hay IOPS quá cao dẫn tới treo ổ (I/O wait).
    84|
    85|![Kiểm thử Disk](../Pictures/test/disk-test.png)
    86|
    87|### 🔐 Domain: SSH & Network
    88|Tìm ra nguyên nhân từ chối kết nối SSH do firewall chặn, sai quyền thư mục `.ssh/`, hoặc DNS Resolution thất bại.
    89|
    90|**Network Routing / Port Status:**
    91|![Kiểm thử Network](../Pictures/test/network-test.png)
    92|
    93|**SSH Connection Issues:**
    94|![Kiểm thử SSH](../Pictures/test/ssh-test1.png)
    95|
    96|---
    97|
    98|## 4. 📝 Tổng Kết Đánh Giá
    99|
   100|1. **Machine Learning Layer:** Pipeline tự tạo đã chứng minh độ mạnh mẽ ở Scale 100k samples. Biểu đồ Heatmap (Confusion Matrix) cho thấy tỷ lệ dự đoán nhầm (False Positives) ở các rìa là cực kỳ thấp.
   101|2. **Expert System Layer:** Như quan sát trên màn hình test, quá trình bóc tách bằng chứng (Evidence Collection) và chấm điểm Bayesian được trình bày minh bạch, tăng độ tin cậy tuyệt đối cho Admin.
   102|3. **Mục tiêu tiếp theo:** Chuyển đổi Shell Executor sang dạng Allowlist (bảo mật tuyệt đối), và tiến hành tăng tốc độ thu thập bằng chứng bằng Parallelling Processing.
   103|
   104|---
   105|*Tài liệu Báo cáo được tự động tạo nhằm mục đích trình diễn và lưu trữ.*
   106|