# Alert và Runbook

Mỗi alert dựa trên triệu chứng mà người dùng quan sát được hoặc mức tiêu thụ error budget. Cả ba gửi tới Slack `#llmops-alerts` và chỉ kích hoạt khi điều kiện duy trì đủ lâu để tránh nhiễu.

## Alert 1: High request latency

- Tên: `high_request_latency`
- Severity: `critical`
- Duration: `5m`
- SLI/SLO: P95 latency ≤ 3000 ms; SLO request nhanh và thành công 99.5%/28 ngày.
- Điều kiện: `latency_p95_ms > 3000` liên tục 5 phút.
- Ảnh hưởng: người dùng phải chờ lâu, có thể timeout hoặc gửi lại request.
- Kiểm tra: (1) xác nhận P50/P95/P99 và TTFT trong đúng cửa sổ; (2) lọc `response_sent` chậm trong `data/logs.jsonl` và lấy `correlation_id`; (3) mở trace cùng ID, so sánh retrieval với generation.
- Mitigation: giảm concurrency, tắt incident practice, dùng prompt/version ổn định hoặc fallback retrieval đã kiểm soát.
- Owner: `llm-platform-oncall`

## Alert 2: Elevated error or retrieval failure

- Tên: `elevated_error_or_retrieval_failure`
- Severity: `critical`
- Duration: `5m`
- SLI/SLO: error rate ≤ 2%, retrieval success ≥ 90%.
- Điều kiện: `error_rate_pct > 2` hoặc `retrieval_success_rate_pct < 90` liên tục 5 phút.
- Ảnh hưởng: request trả HTTP 500 hoặc câu trả lời thiếu ngữ cảnh truy xuất.
- Kiểm tra: (1) xác nhận tỷ lệ lỗi, breakdown `error_type` và retrieval success; (2) lọc `request_failed`, kiểm tra `tool_name`, `tool_success` và lấy `correlation_id`; (3) kiểm tra retrieval span cùng ID, status và lỗi.
- Mitigation: chuyển sang corpus/fallback lành mạnh, giảm tải dependency và rollback thay đổi vừa triển khai.
- Owner: `llm-platform-oncall`

## Alert 3: Degraded answer quality

- Tên: `degraded_answer_quality`
- Severity: `warning`
- Duration: `15m`
- SLI/SLO: quality proxy trung bình ≥ 0.75.
- Điều kiện: `quality_score_avg < 0.75` liên tục 15 phút.
- Ảnh hưởng: câu trả lời ít liên quan hoặc không đủ căn cứ dù API vẫn thành công.
- Kiểm tra: (1) phân đoạn quality theo feature, model và prompt version; (2) lấy request chất lượng thấp từ log rồi nối sang trace; (3) kiểm tra document count, prompt version và generation usage.
- Mitigation: rollback label `production` về prompt baseline đã xác nhận và giới hạn traffic tới candidate.
- Owner: `ai-quality-oncall`
