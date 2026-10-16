# Mẫu tệp thiết kế (ba bài)

Thư mục này là **mẫu để xem trước và so sánh**, không phải kết quả của `digests/`. Mỗi bài có hai tệp mà `python3 radar.py rerender` sẽ thêm cho bài cũ:

| Bài | `board-vi.excalidraw` | `moda-vi.xml` |
|---|---|---|
| `2026-10-12/agent-reach` | [excalidraw.com](https://excalidraw.com): *Open* hoặc kéo tệp vào | Moda: tạo canvas 1200x1789 rồi áp markup |
| `2026-10-13/voicestudio` | như trên | Moda: tạo canvas 1200x1620 rồi áp markup |
| `2026-10-16-2/flowkit` | như trên | Moda: tạo canvas 1200x1534 rồi áp markup |

Cách áp markup lên Moda: `docs/design-files.md`.

Cách tạo: đọc `digests/<ngày>/<repo>/draft-vi.json`, vẽ bằng đúng hàm `digest.render_repo` mà `rerender` dùng, vào một thư mục tạm, rồi chép **chỉ hai tệp mới** vào đây. Mọi tệp khác của bài (`vi.md`, `card/flow/steps-vi.svg`, `draft-vi.json`) được vẽ lại giống hệt từng byte với tệp có sẵn (đã so từng tệp cho cả ba bài), nên không có gì trong `digests/` bị đổi.

Lưu ý khi so sánh với bản cũ (`card/flow/steps-vi.svg` trong `digests/`):
- `agent-reach` là bản **dựng lại** (`draft-vi.json` có khoá `note: RECONSTRUCTED`): các cạnh của `flow` được đọc từ ảnh gốc, không phải câu trả lời nguyên bản của model. `voicestudio` và `flowkit` là draft thật.
- Bảng Excalidraw và infographic Moda xếp thẻ theo thứ tự chỉ số, không theo độ sâu phụ thuộc như `flow-vi.svg`, và không có nhãn hay icon trên mũi tên (xem "Giới hạn của hình" trong `docs/design-files.md`).

Nếu mẫu ổn, chạy `python3 radar.py rerender` cho mọi bài cũ (thêm 2 tệp cho mỗi bài vào `digests/`), rồi xoá thư mục này.
