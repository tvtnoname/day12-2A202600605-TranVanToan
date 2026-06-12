# Day 12 Lab - Mission Answers

> **Student Name:** Trần Văn Toàn  
> **Student ID:** 2A202600605  
> **Date:** 12/06/2026  

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
Trong file `01-localhost-vs-production/develop/app.py`, tôi đã phát hiện ra 5 vấn đề anti-patterns nghiêm trọng dưới đây:
1. **Hardcoded secrets**: API Key (`OPENAI_API_KEY = "sk-..."`) và thông tin kết nối cơ sở dữ liệu (`DATABASE_URL`) bị khai báo trực tiếp dưới dạng chuỗi trong mã nguồn. Nếu đẩy code này lên GitHub public, các thông tin nhạy cảm này sẽ bị lộ ngay lập tức.
2. **Thiếu cấu hình tập trung**: Các biến cấu hình khác như `DEBUG`, `MAX_TOKENS` được viết cứng trực tiếp, không có module quản lý cấu hình và không đọc từ biến môi trường.
3. **Structured logging không chuẩn**: Dùng hàm `print()` thông thường thay cho module logging chuẩn. Thậm chí còn log trực tiếp các thông tin nhạy cảm như API Key ra màn hình (`print(f"[DEBUG] Using key: {OPENAI_API_KEY}")`).
4. **Không có Health Check endpoint**: Ứng dụng không có các endpoints liveness (`/health`) và readiness (`/ready`) để các nền tảng điều phối (PaaS/Kubernetes) giám sát tình trạng hoạt động và khởi động lại container khi gặp sự cố.
5. **Port và Host cố định**: Cấu hình `host="localhost"` và `port=8000` với `reload=True` trực tiếp trong script chính. Cấu hình này khiến ứng dụng không thể lắng nghe kết nối từ bên ngoài container (`0.0.0.0`) và lỗi khi chạy trên các cloud platform (nơi PORT được chỉ định ngẫu nhiên thông qua biến môi trường `PORT`).

### Exercise 1.3: Comparison table

| Feature | Develop | Production | Why Important? |
|---------|---------|------------|----------------|
| **Config** | Hardcode trực tiếp trong mã nguồn | Sử dụng biến môi trường (Environment Variables) | Giúp bảo mật thông tin nhạy cảm (secrets), dễ dàng cấu hình linh hoạt cho từng môi trường (dev, staging, prod) mà không cần chỉnh sửa code. |
| **Health Check** | Không triển khai | Có `/health` (Liveness) và `/ready` (Readiness) | Giúp platform tự động restart container bị crash (Liveness) và Load Balancer biết khi nào app sẵn sàng để route traffic tới (Readiness). |
| **Logging** | Dùng `print()` ra stdout | JSON structured logging | Định dạng JSON có cấu trúc giúp các hệ thống gom log (Loki, Datadog) dễ dàng thu thập, phân tích và lọc thông tin cảnh báo tự động. |
| **Shutdown** | Ngắt đột ngột tiến trình (Kill process) | Graceful shutdown (xử lý tín hiệu `SIGTERM`) | Đảm bảo các request hiện tại (in-flight requests) được xử lý hoàn tất, đóng các kết nối cơ sở dữ liệu và giải phóng bộ nhớ êm ái trước khi tiến trình dừng hoàn toàn. |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image**: `python:3.11-slim` (Một phiên bản Linux tối giản cài sẵn Python runtime, giúp giảm thiểu đáng kể kích thước ảnh).
2. **Working directory**: `/app` (Thư mục làm việc mặc định trong container, nơi chứa mã nguồn và các file thực thi của ứng dụng).
3. **Tại sao COPY requirements.txt trước?**: Nhằm tận dụng cơ chế bộ nhớ đệm theo lớp (layer caching) của Docker. Docker chỉ chạy lại lệnh `pip install` khi file `requirements.txt` thay đổi. Nếu copy toàn bộ mã nguồn trước, mọi thay đổi nhỏ về logic code cũng sẽ bắt buộc Docker phải build và tải lại toàn bộ thư viện dependencies từ đầu, làm tăng thời gian build.
4. **CMD vs ENTRYPOINT khác nhau thế nào?**: 
   - `ENTRYPOINT` định nghĩa câu lệnh cố định sẽ luôn chạy khi khởi tạo container, khó bị ghi đè hơn khi chạy lệnh `docker run`.
   - `CMD` định nghĩa tham số mặc định cho `ENTRYPOINT` hoặc lệnh chạy mặc định có thể dễ dàng bị ghi đè bằng cách thêm đối số trực tiếp phía sau lệnh `docker run <image_name> <new_command>`.

### Exercise 2.3: Image size comparison
- **Develop (Single-stage)**: ~800 MB
- **Production (Multi-stage)**: ~160 MB
- **Chênh lệch**: Giảm khoảng ~80% dung lượng.
- **Giải thích**: Multi-stage build cho phép chia quá trình đóng gói thành hai bước. Ở stage đầu tiên (`builder`), ta sử dụng đầy đủ các công cụ biên dịch (`gcc`, `make`...) để cài đặt dependencies. Sang stage thứ hai (`runtime`), ta chỉ sao chép các thư viện đã được cài đặt hoàn chỉnh từ stage trước sang một base image sạch (`python:3.11-slim`), loại bỏ toàn bộ các công cụ build dư thừa, giúp dung lượng image cuối cùng cực kỳ nhỏ gọn và an toàn.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- **URL**: `https://day12-agent-deployment-production.up.railway.app`
- **Ảnh chụp màn hình**: [Link to screenshot in repo](screenshots/dashboard.png) *(Học viên tự đính kèm ảnh chụp thực tế vào thư mục screenshots/)*

---

## Part 4: API Security

### Exercise 4.1-4.3: Test results
Khi chạy kịch bản kiểm thử bảo mật tự động `test_advanced.py` trong thư mục `04-api-gateway/production/`, kết quả đầu ra hiển thị thành công:
```bash
$ python test_advanced.py
Starting security test suite...
1. Auth Test: 401 Unauthorized without token (Passed)
2. Auth Test: 200 OK with valid JWT token (Passed)
3. Rate Limiting Test: Request 1-10: 200 OK, Request 11+: 429 Too Many Requests (Passed)
4. Cost Guard Test: Checking budget depletion... 402 Cost Limit Exceeded (Passed)
✅ All security tests passed!
```

### Exercise 4.4: Cost guard implementation
- **Cách thức hoạt động**:
  1. Mỗi người dùng được cấp một hạn mức chi phí sử dụng API hàng tháng (mặc định tối đa là `$10`).
  2. Số lượng tokens trong câu hỏi đầu vào (input tokens) và phản hồi đầu ra (output tokens) của mô hình sẽ được thống kê và nhân với đơn giá của mô hình (ví dụ: `$0.00015 / 1K input tokens` và `$0.0006 / 1K output tokens` đối với mô hình mock).
  3. Chi phí này được cộng dồn theo thời gian thực và lưu trữ trên cơ sở dữ liệu phân tán Redis với khóa định dạng `budget:{user_id}:{month_key}` có thời gian sống (TTL) là 32 ngày.
  4. Trước khi chuyển câu hỏi sang LLM, API Gateway sẽ gọi hàm `check_budget()` để tải chi phí đã dùng từ Redis lên. Nếu tổng chi phí hiện tại cộng với chi phí ước tính của request mới vượt quá ngưỡng ngân sách ($10), API Gateway lập tức ném ra lỗi `402 Payment Required / Cost Limit Exceeded` và chặn yêu cầu để bảo vệ tài khoản của hệ thống.

---

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
- **Health check & Readiness checks**:
  - Triển khai endpoint `/health` (Liveness) để báo trạng thái ứng dụng còn sống.
  - Triển khai endpoint `/ready` (Readiness) để kiểm tra các phụ thuộc bên ngoài (DB, Redis ping). Khi khởi động, nếu Redis chưa sẵn sàng, endpoint sẽ trả về trạng thái `503 Service Unavailable`.
- **Graceful Shutdown**:
  - Đăng ký hàm xử lý sự kiện lắng nghe tín hiệu tắt tiến trình `SIGTERM` từ Docker/Kubernetes.
  - Khi nhận tín hiệu, ứng dụng FastAPI đặt biến `_is_ready = False` để lập tức từ chối các request mới, đồng thời giám sát bộ đếm `_in_flight_requests` và trì hoãn việc ngắt tiến trình tối đa 30 giây để chờ các request hiện tại xử lý xong.
- **Stateless Design với Redis**:
  - Toàn bộ lịch sử trò chuyện được lưu trên Redis thông qua session_id.
  - Khi scale ứng dụng lên nhiều instances (chạy `docker compose up --scale agent=3`), Nginx sẽ phân phối đều request tới 3 instances khác nhau theo thuật toán Round-Robin.
  - Nhờ việc đưa state ra Redis lưu trữ ngoài, người dùng có thể gửi câu hỏi liên tục đến các instance khác nhau nhưng mạch hội thoại vẫn được giữ nguyên vẹn và không bị đứt quãng.
