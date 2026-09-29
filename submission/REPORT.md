# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

## 1. Thông tin học viên

- **Họ và tên:** Trần Long Khánh
- **MSSV:** 2A202602538
- **Lớp:** K4-L3A
- **Repository:** https://github.com/khanhtrankuri/K4-L3A-Day13-TranLongKhanh-2A202602538-Monitoring-LLMOps
- **Commit nền tại lúc kiểm tra:** `13b6066` (các thay đổi hoàn thiện hiện chưa được commit)
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Project Langfuse cá nhân:** project ID `cmumdku060tu5ad0dohz2qe8z`, thuộc `khanhtrankuri's Organization`
- **Tên project yêu cầu:** `day13-k4-l3a-2A202602538`

## 2. Evidence index — đúng 14 ảnh

| # | Evidence | Ảnh | Dữ liệu nguồn |
|---:|---|---|---|
| 01 | Pytest cuối | [01-pytest.png](evidence/01-pytest.png) | [TXT](evidence/01-pytest.txt) |
| 02 | Log validator | [02-log-validator.png](evidence/02-log-validator.png) | [TXT](evidence/02-log-validator.txt) |
| 03 | Dashboard validator | [03-dashboard-validator.png](evidence/03-dashboard-validator.png) | [TXT](evidence/03-dashboard-validator.txt) |
| 04 | Structured log | [04-structured-log.png](evidence/04-structured-log.png) | [TXT](evidence/04-structured-log.txt) |
| 05 | PII redaction | [05-pii-redaction.png](evidence/05-pii-redaction.png) | [TXT](evidence/05-pii-redaction.txt) |
| 06 | Danh sách trace | [06-trace-list.png](evidence/06-trace-list.png) | [TXT](evidence/06-trace-list.txt) |
| 07 | Trace waterfall | [07-trace-waterfall.png](evidence/07-trace-waterfall.png) | [TXT](evidence/07-trace-waterfall.txt) |
| 08 | Trace metadata | [08-trace-metadata.png](evidence/08-trace-metadata.png) | [TXT](evidence/08-trace-metadata.txt) |
| 09 | Prompt v1/v2 | [09-prompt-versions.png](evidence/09-prompt-versions.png) | [TXT](evidence/09-prompt-versions.txt) |
| 10 | Promote/rollback | [10-prompt-rollback.png](evidence/10-prompt-rollback.png) | [TXT](evidence/10-prompt-rollback.txt) |
| 11 | Dashboard 6 panel | [11-dashboard-overview.png](evidence/11-dashboard-overview.png) | [TXT](evidence/11-dashboard-runtime.txt) |
| 12 | Incident metric | [12-incident-metric.png](evidence/12-incident-metric.png) | [TXT](evidence/12-incident-metric.txt) |
| 13 | Incident log | [13-incident-log.png](evidence/13-incident-log.png) | [TXT](evidence/13-incident-log.txt) |
| 14 | Incident trace | [14-incident-trace.png](evidence/14-incident-trace.png) | [TXT](evidence/14-incident-trace.txt) |

Ảnh `06`–`10` và `14` được render từ kết quả thật của Langfuse Observations API v2/Prompt API đã xác thực; không chứa secret và không dùng dữ liệu của học viên khác.

## 3. Kết quả cuối

| Hạng mục | Kết quả | Đánh giá |
|---|---:|---|
| `python -m pytest -q` | 27 passed | Đạt |
| `scripts/validate_logs.py` | 100/100 | Đạt |
| Log thiếu field/enrichment | 0 / 0 | Đạt |
| PII leak | 0 | Đạt |
| Correlation ID duy nhất | 19 | Đạt |
| `scripts/validate_dashboard.py` | 6/6 panel | Đạt |
| Trace thật | ≥ 12 ID đại diện | Đạt yêu cầu ≥ 10 |
| Prompt managed | v1 + v2 | Đạt |
| Promote và rollback | v2 production → v1 production | Đạt |
| Challenge | K4 `rag_slow`, feature `monitoring` | Đúng file được cấp |

## 4. Logging và bảo vệ PII

- Middleware nhận `x-request-id` hợp lệ theo mẫu `req-<8-hex>` hoặc tự sinh ID mới, bind vào `structlog`, lưu ở `request.state` và trả lại trong response header.
- Mỗi log có `service`, `event`, `level`, `ts`, `correlation_id`; request nghiệp vụ còn có `feature`, `model`, `env`, `session_id` và `user_id_hash`.
- `scrub_event` đệ quy qua mapping/list/tuple và che email, số điện thoại Việt Nam, CCCD và số thẻ trước khi serialize JSON.
- User ID được hash SHA-256 rút gọn. Validator độc lập xác nhận 40 record, không thiếu field/enrichment và không phát hiện PII thô.

## 5. Tracing và prompt versioning

- Trace có cây `lab-agent-run` (root `AGENT`) → `retrieve-context` (`RETRIEVER`) + `fake-llm-generate` (`GENERATION`).
- Root/child metadata có `correlation_id`, feature, model, prompt name/label/version; generation có token, TTFT và cost. Input/output chỉ lưu preview đã scrub.
- Langfuse xác nhận trace baseline v1, candidate v2 và production-v2. Trace production-v2: `9b43f437dd8fc2a10a46fe22362e05fb`.
- Prompt `day13-chat` v1 dùng ba biến `feature`, `docs`, `message`. V2 thêm yêu cầu trả lời tối đa ba câu, súc tích và dựa trên context.
- Promote: v2 nhận label `production`, v1 mất label này. Rollback: v1 nhận lại `production`; trạng thái cuối v1=`baseline, production`, v2=`candidate, latest`.
- Langfuse Cloud mới không còn legacy Trace API; evidence dùng Observations API v2 với field groups `metadata`, `model`, `usage`, `prompt`, `metrics`, `trace_context`.

## 6. Dashboard, SLO và alerts

- `/dashboard` hiển thị đúng 6 panel: latency/TTFT, traffic, error/retrieval success, cost, tokens và quality; cửa sổ 60 phút, refresh 30 giây, có đơn vị và threshold.
- Dataset cuối: 17 request; P50 152 ms, P95/P99 5025 ms, TTFT P95 50 ms; error 0%, retrieval success 100%; cost USD 0.034221; 622 input/2157 output tokens; quality 0.859.
- SLO: 99.5% request trong cửa sổ 28 ngày phải thành công và latency ≤ 3000 ms. Error budget là `28 × 24 × 60 × 0.005 = 201.6 phút`.
- Ba alert symptom-based: `high_request_latency`, `elevated_error_or_retrieval_failure`, `degraded_answer_quality`; mỗi alert có severity, owner, channel và runbook trong [docs/alerts.md](../docs/alerts.md).

## 7. Điều tra CP3 chính thức

- **Khoảng sự cố:** `2026-09-29T09:10:03Z`–`09:10:19Z`.
- **Metric:** 5 request; P50 2652 ms, P95/P99 5025 ms, TTFT P95 50 ms, error breakdown `{}`, quality 0.84. P95 vượt threshold 2000 ms.
- **Log đại diện:** correlation ID `req-6c75580d`, `latency_ms=2652`, `ttft_ms=50`, `tool_name=retrieval`, `tool_success=true`.
- **Trace cùng request:** `d089bef446845b97b84278ccf663ca17`; root 2.653 s, retrieval 2.501 s, generation 0.152 s, TTFT 0.050 s, prompt production v1, 35 input/146 output token, cost USD 0.002295.
- **Root cause:** incident `rag_slow` làm `mock_rag.retrieve()` chờ khoảng 2.5 giây. Retrieval chiếm gần toàn bộ latency, trong khi generation/TTFT bình thường và request vẫn thành công.
- **Fix đã thực hiện:** disable incident ngay sau phép đo.
- **Fix production đề xuất:** retrieval timeout + circuit breaker + fallback có kiểm soát.
- **Phòng ngừa:** đo riêng retrieval duration/success, cảnh báo tail latency liên tục 5 phút, giữ `correlation_id` xuyên metric–log–trace và chạy dependency load test trước rollout.

## 8. Tự đánh giá

- Quan sát hiệu quả khi metric chỉ ra cửa sổ bất thường, log thu hẹp tới request, rồi trace xác định chính xác span gây chậm.
- Scrubber đặt ở logging processor tạo một ranh giới bảo vệ chung thay vì phụ thuộc từng call site.
- Prompt version/label làm hành vi có thể tái hiện và rollback; token/cost giúp phân biệt suy giảm chất lượng với tăng chi phí.
- Blocker Windows đối với `uvicorn.exe` được xử lý bằng `python -m uvicorn`; script incident nay báo lỗi kết nối ngắn gọn nếu API chưa chạy.
- Lưu ý còn lại: API xác nhận đây là project cá nhân trong organization của học viên, nhưng display name trên Langfuse đang là `My Project`; lệnh đổi tên bị cơ chế duyệt quyền mạng của môi trường chặn sau khi evidence đã thu thập. Cần đổi display name thành `day13-k4-l3a-2A202602538` trên Project Settings trước khi nộp nếu giảng viên kiểm tra trực tiếp UI.

## 9. Checklist nộp bài

- [x] Tests, log validator và dashboard validator đều đạt.
- [x] Có đúng 14 ảnh evidence, tên từ `01` đến `14`, tất cả mở được.
- [x] Có ít nhất 10 trace ID, waterfall, metadata, prompt v1/v2 và rollback.
- [x] Metric, log và trace incident nối bằng `req-6c75580d`.
- [x] `.env`, `config/challenge.json` và `data/logs.jsonl` đều bị `.gitignore` loại khỏi commit.
- [x] Không có secret hay PII thô trong evidence.
- [ ] Đổi display name của project Langfuse từ `My Project` sang `day13-k4-l3a-2A202602538`.
- [ ] Tạo commit nộp bài cuối, cập nhật SHA và push repository.
