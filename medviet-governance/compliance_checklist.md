# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [x] Tất cả patient data lưu trên servers đặt tại Việt Nam — deploy trên VPS/cloud region ap-southeast-1 (Singapore) hoặc on-premise tại VN
- [x] Backup cũng phải ở trong lãnh thổ VN — backup định kỳ vào storage bucket đặt tại VN
- [x] Log việc transfer data ra ngoài nếu có — OPA rule `deny` block export restricted data ra ngoài VN; mọi transfer đều có audit log

## B. Explicit Consent
- [x] Thu thập consent trước khi dùng data cho AI training — form consent điện tử khi đăng ký, lưu vào DB với timestamp và phiên bản consent
- [x] Có mechanism để user rút consent (Right to Erasure) — endpoint `DELETE /api/patients/{patient_id}` cho phép xóa toàn bộ dữ liệu; chỉ admin thực hiện theo yêu cầu bệnh nhân
- [x] Lưu consent record với timestamp — bảng `consent_log(patient_id, consent_version, consented_at, revoked_at)`

## C. Breach Notification (72h)
- [x] Có incident response plan — tài liệu IRP định nghĩa các cấp độ sự cố, người phụ trách, và SLA phản hồi
- [x] Alert tự động khi phát hiện breach — Prometheus + Alertmanager giám sát bất thường (rate đọc API tăng đột biến, failed auth liên tục); PagerDuty notify on-call trong vòng 5 phút
- [x] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h — template báo cáo sẵn có; DPO chịu trách nhiệm gửi đến Bộ Công an/PDPD trong vòng 72h kể từ khi phát hiện

## D. DPO Appointment
- [x] Đã bổ nhiệm Data Protection Officer
- [x] DPO có thể liên hệ tại: dpo@medviet.vn | +84-xxx-xxx-xxx

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) — loại bỏ ho_ten, cccd, so_dien_thoai, email, dia_chi trước khi đưa vào training | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) — 4 roles: admin/ml_engineer/data_analyst/intern; FastAPI enforce tại mỗi endpoint | ✅ Done | Platform Team |
| Encryption at rest | AES-256-GCM envelope encryption (SimpleVault) — KEK quản lý tách biệt, DEK rotate theo session | ✅ Done | Infra Team |
| Encryption in transit | TLS 1.3 bắt buộc trên toàn bộ API gateway; HSTS enabled | 🚧 In Progress | Infra Team |
| Audit logging | FastAPI middleware ghi mọi request (user, endpoint, timestamp, IP) vào append-only log; export sang SIEM (Elasticsearch) | 🚧 In Progress | Platform Team |
| Breach detection | Prometheus thu thập metrics API; Grafana dashboard giám sát; alert khi failed_auth_rate > 10/phút hoặc data_export_volume bất thường | 🚧 In Progress | Security Team |

## F. Technical Solution cho các mục In Progress

### Audit Logging
- Implement FastAPI middleware log toàn bộ request/response metadata (không log body chứa PII)
- Log format: `{timestamp, user_id, role, method, path, status_code, ip, latency_ms}`
- Lưu vào file append-only + ship sang Elasticsearch qua Filebeat
- Retention: 12 tháng theo yêu cầu NĐ13

### Breach Detection
- Prometheus scrape `/metrics` endpoint mỗi 15 giây
- Alert rules:
  - `failed_login_rate > 10/phút` trong 3 phút liên tiếp → cảnh báo brute force
  - `api_request_rate{endpoint="/api/patients/raw"} > 100/phút` → cảnh báo data exfiltration
  - `http_5xx_rate > 5%` → cảnh báo system compromise
- Alertmanager gửi webhook đến PagerDuty + email DPO
