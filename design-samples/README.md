# Mẫu tệp thiết kế (ba bài)

Thư mục này là **mẫu để xem trước và so sánh**, không phải kết quả của `digests/`. Mỗi bài có hai tệp mà `python3 radar.py rerender` sẽ thêm cho bài cũ:

| Bài | `board-vi.excalidraw` | `moda-vi.xml` |
|---|---|---|
| `2026-10-12/agent-reach` | [excalidraw.com](https://excalidraw.com): *Open* hoặc kéo tệp vào | Moda: tạo canvas 1200x1789 rồi áp markup |
| `2026-10-13/voicestudio` | như trên | Moda: tạo canvas 1200x1620 rồi áp markup |
| `2026-10-16-2/flowkit` | như trên | Moda: tạo canvas 1200x1534 rồi áp markup |

Cách áp markup lên Moda: `docs/design-files.md`.

## Bản draw.io có icon (cả ba bài)

`<ngày>/<repo>/drawio-vi.drawio` mở bằng [app.diagrams.net](https://app.diagrams.net) (*File → Open from → Device*). Chúng do bộ vẽ thật `radar/drawio.py` (nhánh `claude/drawio-icons`) vẽ từ `draft-vi.json`. So với bản Excalidraw/Moda:
- Mỗi thẻ là một khối giữ chữ của nó; kéo thẻ thì chữ, số bước, dấu tích và icon đi theo. Mũi tên giữa các thành phần là connector gắn vào thẻ, mỗi mũi tên một làn riêng, chỗ giao nhau có nét nhảy.
- Mỗi thành phần có một icon từ danh sách đóng 53 tên (Lucide, ISC) nằm ngay trong tệp. **Ba draft cũ chưa có trường `icon`** (bài mới sẽ do model chọn và gate kiểm); icon trong ba tệp này do người chọn tay: agent-reach: terminal, route, settings, stethoscope; voicestudio: monitor, server, cpu; flowkit: server, puzzle, globe. Các draft trong `digests/` không bị sửa.
- Chữ chỉ là trường của draft, nhãn của `labels.py` hoặc dữ kiện (có test), dùng font Helvetica của draw.io chứ không phải Be Vietnam Pro như Moda.

Cách tạo: đọc `digests/<ngày>/<repo>/draft-vi.json`, vẽ bằng đúng hàm `digest.render_repo` mà `rerender` dùng, vào một thư mục tạm, rồi chép **chỉ hai tệp mới** vào đây. Mọi tệp khác của bài (`vi.md`, `card/flow/steps-vi.svg`, `draft-vi.json`) được vẽ lại giống hệt từng byte với tệp có sẵn (đã so từng tệp cho cả ba bài), nên không có gì trong `digests/` bị đổi.

Lưu ý khi so sánh với bản cũ (`card/flow/steps-vi.svg` trong `digests/`):
- `agent-reach` là bản **dựng lại** (`draft-vi.json` có khoá `note: RECONSTRUCTED`): các cạnh của `flow` được đọc từ ảnh gốc, không phải câu trả lời nguyên bản của model. `voicestudio` và `flowkit` là draft thật.
- Bảng Excalidraw và infographic Moda xếp thẻ theo thứ tự chỉ số, không theo độ sâu phụ thuộc như `flow-vi.svg`, và không có nhãn hay icon trên mũi tên (xem "Giới hạn của hình" trong `docs/design-files.md`).

Nếu mẫu ổn, chạy `python3 radar.py rerender` cho mọi bài cũ (thêm 2 tệp cho mỗi bài vào `digests/`), rồi xoá thư mục này.
