# Deployment Information

## Public URL
https://day12-agent-deployment-production.up.railway.app

## Nền tảng triển khai (Platform)
Railway (hoặc Render / GCP Cloud Run)

## Các câu lệnh kiểm thử dịch vụ (Test Commands)

### 1. Kiểm tra sức khỏe hệ thống (Health Check)
```bash
curl https://day12-agent-deployment-production.up.railway.app/health
# Kết quả mong đợi: {"status": "ok", ...}
```

### 2. Kiểm tra tính sẵn sàng (Readiness check)
```bash
curl https://day12-agent-deployment-production.up.railway.app/ready
# Kết quả mong đợi: {"ready": true}
```

### 3. Kiểm tra yêu cầu xác thực (Authentication Required)
```bash
curl -X POST https://day12-agent-deployment-production.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
# Kết quả mong đợi: 401 Unauthorized (Do thiếu X-API-Key)
```

### 4. Gửi câu hỏi hợp lệ (API Test with authentication)
```bash
curl -X POST https://day12-agent-deployment-production.up.railway.app/ask \
  -H "X-API-Key: dev-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
# Kết quả mong đợi: 200 OK với câu trả lời từ Mock LLM
```

## Các biến môi trường đã thiết lập (Environment Variables Set)
- `PORT`: 8000
- `ENVIRONMENT`: production
- `AGENT_API_KEY`: dev-key-change-me (hoặc api-key tùy cấu hình)
- `REDIS_URL`: redis://redis:6379/0
- `LLM_MODEL`: gpt-4o-mini
- `DAILY_BUDGET_USD`: 5.0

## Ảnh chụp màn hình (Screenshots)
- **Deployment dashboard**: `screenshots/dashboard.png`
- **Service running**: `screenshots/running.png`
- **Test results**: `screenshots/test.png`
