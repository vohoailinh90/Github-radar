# Mẫu tệp thiết kế (một bài)

Thư mục này là **mẫu để xem trước**, không phải kết quả của `digests/`. Nó chứa hai tệp mà `python3 radar.py rerender` sẽ thêm cho bài cũ:

| Tệp | Mở bằng |
|---|---|
| `2026-10-16-2/flowkit/board-vi.excalidraw` | [excalidraw.com](https://excalidraw.com): *Open* hoặc kéo tệp vào |
| `2026-10-16-2/flowkit/moda-vi.xml` | Moda: tạo canvas 1200x1534 rồi áp markup (xem `docs/design-files.md`) |

Cách tạo: đọc `digests/2026-10-16-2/flowkit/draft-vi.json`, vẽ bằng đúng hàm `digest.render_repo` mà `rerender` dùng, vào một thư mục tạm, rồi chép **chỉ hai tệp mới** vào đây. Mọi tệp khác của bài (`vi.md`, `card/flow/steps-vi.svg`, `draft-vi.json`) được vẽ lại giống hệt từng byte với tệp có sẵn, nên không có gì trong `digests/` bị đổi.

Nếu mẫu ổn, chạy `python3 radar.py rerender` cho mọi bài cũ (thêm 20 tệp vào `digests/`), rồi xoá thư mục này.
