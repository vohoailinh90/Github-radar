# Công cụ cho AI agent làm giao diện và duyệt web: ba repo, ba bài hướng dẫn

Bộ này gom **3 repo mã nguồn mở** do bạn chọn tay, mỗi repo có một bài **làm theo từng bước** kèm các hình (thẻ tóm tắt, lộ trình, sơ đồ các mảnh ghép, các bước bên trong).
Quét ngày **16/10/2026**; số sao đọc từ trang repo hôm đó và làm tròn theo trang. Bài nào cũng có phần *Lưu ý trước khi dùng* (nhược điểm, giới hạn) và *Ai nên xem*
(dùng cho việc gì, không hợp với ai).

## Bạn muốn làm gì?

| Mục tiêu | Repo | Sao | Giấy phép | Cần có | Hướng dẫn |
|---|---|---:|---|---|---|
| Cho agent AI **tự điều khiển trình duyệt**: mở trang, bấm, gõ, điền form, đọc nội dung | Playwright MCP | 38.200 | Apache-2.0 | Node.js 18 trở lên, một MCP client | [Xem bài](../digests/2026-10-16-4/playwright-mcp/vi.md) |
| Cho AI **vẽ giao diện có chủ đích**, rồi rà soát, đánh giá, chỉnh lần cuối và dò lỗi thiết kế | Impeccable | 82.000 | Apache-2.0 | Một công cụ AI được hỗ trợ; Node.js nếu dùng `npx` | [Xem bài](../digests/2026-10-16-4/impeccable/vi.md) |
| Cho AI một **kho tri thức thiết kế** để sinh hệ thống thiết kế (kiểu trang, màu, phông) theo loại sản phẩm | UI UX Pro Max | 136.600 | MIT | Python 3, một công cụ AI được hỗ trợ; Node.js và npm nếu cài bằng `uipro` | [Xem bài](../digests/2026-10-16-4/ui-ux-pro-max-skill/vi.md) |

Mục lục của lần quét: [`digests/2026-10-16-4/README.md`](../digests/2026-10-16-4/README.md).

## Ba repo khác nhau thế nào

| | Playwright MCP | Impeccable | UI UX Pro Max |
|---|---|---|---|
| **Là gì** | Máy chủ MCP: bộ công cụ cho agent gọi | Skill: một lệnh `/impeccable` với 24 lệnh con, kèm CLI dò lỗi | Skill kèm kho dữ liệu và script tìm kiếm bằng Python |
| **Chạy ở đâu** | Trong MCP client (VS Code, Cursor, Claude Desktop...), khởi chạy bằng `npx`, HTTP hoặc Docker | Trong công cụ AI (Claude Code, Cursor, Codex, Gemini CLI...); CLI chạy riêng bằng `npx impeccable` | Trong công cụ AI; script chạy được riêng bằng `python3` |
| **Đầu ra** | Hành động trên trình duyệt và cấu trúc của trang (accessibility snapshot) | Lệnh thiết kế, `PRODUCT.md`, báo cáo phát hiện lỗi | Bảng hệ thống thiết kế; có thể lưu thành file để dùng lại |
| **Cần mạng / khóa API** | README không nói cần khóa API | CLI dò lỗi không cần LLM và không cần khóa API; engine nằm cạnh launcher hoặc được tải một lần vào `~/.impeccable/bin/`; có yêu cầu roll tới API khi bắt đầu thiết kế mới (telemetry tắt được) | Script chỉ dùng thư viện chuẩn và không gọi mạng |

Cách nhìn của bài này (không phải của README): Playwright MCP cho agent **khả năng làm** (thao tác trình duyệt), còn Impeccable và UI UX Pro Max cho agent **tri thức và quy trình thiết kế**.
README của hai skill thiết kế không nói gì về việc dùng chung với nhau; nếu thử cả hai trong một dự án, hãy xem từng skill kích hoạt khi nào.

## Ưu điểm, nhược điểm và phạm vi (theo README của từng repo)

### Playwright MCP

- **Ưu điểm:** agent đọc cấu trúc của trang thay vì ảnh chụp nên không cần mô hình xử lý hình; nhiều cách chạy (`npx`, HTTP, Docker, nhúng vào mã); nhóm công cụ mở rộng bật bằng `--caps`; ba kiểu hồ sơ trình duyệt (lưu bền, isolated, nối vào trình duyệt đang chạy).
- **Nhược điểm và lưu ý:** README nói đây không phải ranh giới bảo mật; coding agent thường chuộng Playwright CLI kèm SKILLS vì tiết kiệm token hơn; `browser_run_code_unsafe` được README gọi là tương đương RCE; bản Docker chỉ hỗ trợ chromium headless.
- **Phạm vi:** điều khiển trình duyệt qua MCP. README mô tả công cụ điều hướng, bấm, gõ, snapshot, quản lý tab, và các nhóm bật thêm như mạng, lưu trữ, devtools, pdf, kiểm thử. README không nói tới thiết kế giao diện.

### Impeccable

- **Ưu điểm:** 24 lệnh làm từ vựng chung với AI; 59 quy tắc dò lỗi chạy không cần LLM, có đầu ra JSON thân thiện với CI và mã thoát rõ ràng; hỗ trợ nhiều công cụ AI qua một trình cài; có hook thiết kế và chế độ live.
- **Nhược điểm và lưu ý:** có telemetry ẩn danh khi bắt đầu thiết kế mới (tắt được); hook trên Claude Code chạy độc lập với việc duyệt công cụ và có thể tải engine ngay lần sửa file đầu; chế độ live chỉ dùng cho checkout cục bộ, và áp dụng chỉnh sửa chữ có thể chạy script `impeccable:manual-edit-validate` trong package.json dưới quyền của bạn; lần quét sạch của detector chỉ là bằng chứng, không chứng minh chất lượng.
- **Phạm vi:** thiết kế giao diện frontend do AI sinh ra. README không nói tới việc backend.

### UI UX Pro Max

- **Ưu điểm:** kho dữ liệu lớn (79 phong cách UI có thể tìm, trong đó 50 đang dùng; 192 bảng màu; 74 cặp phông; 22 tech stack; 119 hướng dẫn UX; 192 quy tắc theo ngành); sinh hệ thống thiết kế rồi lưu thành file master kèm file ghi đè từng trang; script không gọi mạng.
- **Nhược điểm và lưu ý:** cần Python 3; ví dụ trước và sau trong README chỉ là minh họa do cộng đồng đóng góp, không phải phép đo; vài lỗi cài đặt README tự nêu (ZIP cả repo bị Claude từ chối vì quá 200 file, Marketplace trước v2.5.1 lỗi symlink).
- **Phạm vi:** UI/UX cho nhiều stack. Thương hiệu, logo, slide, sinh ảnh và kiến trúc design token cho đội lớn thuộc bản Premium, README nói rõ đó không phải repo này.

## Điều cần biết trước khi tin các bài này

- **Chưa ai chạy thử từng bước trên máy thật.** Bài được viết bằng cách đọc README, không cài và chạy từng repo. Máy kiểm từng lệnh có nằm **nguyên văn** trong README hay không, nhưng một lệnh đúng trong README vẫn có thể lỗi trên máy bạn (phiên bản, hệ điều hành).
- Bài do **Claude viết trong một phiên tương tác**, không phải do các model miễn phí của bộ quét (phiên này không có khóa của chúng). Không có model **họ khác** soát lại: thay vào đó một Claude khác, chỉ đọc, đã đối chiếu từng bài với README; các điểm đúng đã được sửa, mỗi bản nháp (`draft-vi.json`) ghi điều này trong khóa `note`. Máy vẫn kiểm: số liệu phải có trong README hoặc dữ kiện repo, mỗi lệnh phải là một dòng hoặc đoạn mã nội dòng của README, chữ nằm giữa dấu backtick phải có trong README hoặc là đường dẫn có thật, không có URL do model viết, không có lời quảng cáo (kiểm bằng một danh sách từ khóa).
- **README là nguồn duy nhất.** Chỗ README không nói (màn hình xác nhận cài đặt, thông báo lỗi), bài cũng nói là README không nêu. README của Playwright MCP dài 61.190 ký tự sau khi làm sạch; bộ quét mặc định cắt ở 12.000 và sẽ bỏ mất mục *Tools*, nên bài này dùng nguyên văn README (`note` ghi số ký tự).
- Điều trang repo không cho thấy (số issue đang mở của Playwright MCP, ngôn ngữ chính, ngày tạo) được để trống, không đoán.
- **Ghi chú ngoài README** (từ việc mở bản clone, không có trong bài): trong repo `microsoft/playwright-mcp`, thư mục `src/` chỉ có một file README trỏ về kho Playwright chính; mã máy chủ không nằm ở đây. Hãy hiểu repo này là phần đóng gói, tài liệu và kiểm thử của máy chủ.
- Số sao là ảnh chụp ngày quét, đọc từ trang repo và làm tròn theo trang.
- Đây không phải đánh giá bảo mật. Các công cụ này cho agent chạy lệnh, sửa file hoặc điều khiển trình duyệt dưới quyền của bạn; hãy xem kỹ hook, quyền và điều khoản của từng công cụ.

## Ghi chú liên quan trong repo này

Repo này còn giữ một bản sao nguyên văn của skill Impeccable để chép sang repo khác khi cần thiết kế giao diện (không tham gia việc quét): [`docs/impeccable.md`](impeccable.md).

## Tạo bài kiểu này cho repo khác

`python3 radar.py run --repo owner/tên` (hoặc Actions → *Radar scan* → ô `repo`) viết một bài như vậy bằng các model miễn phí đã cấu hình; xem [`README.md`](../README.md).
