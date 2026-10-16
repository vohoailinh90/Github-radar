# Tệp thiết kế: bảng Excalidraw và markup Moda

Mỗi bài học còn có hai tệp vẽ cùng nội dung bằng hai công cụ chỉnh sửa, để bạn tinh chỉnh bằng tay hoặc đăng lại với giao diện đẹp hơn SVG:

| Tệp (cạnh `<ngôn ngữ>.md`) | Là gì | Mở bằng |
|---|---|---|
| `board-<ngôn ngữ>.excalidraw` | Bảng nét vẽ tay: 3 khung (các mảnh ghép, các bước, bài học), mũi tên theo `flow` | [excalidraw.com](https://excalidraw.com): *Open* hoặc kéo tệp vào. Sửa tay được từng thẻ |
| `moda-<ngôn ngữ>.xml` | Markup Moda của một infographic dọc 1200 px: dải tiêu đề tối, thẻ màu, bước đánh số | Một phiên Claude có connector Moda (xem bên dưới) |

Cả hai do **script** vẽ từ `draft-<ngôn ngữ>.json` (`radar/boards.py` dựng bố cục, `radar/excalidraw.py` và `radar/moda.py` chỉ ghi ra từng định dạng), không có model nào viết một ký tự của chúng. Chúng được vẽ lúc quét và vẽ lại bởi `python3 radar.py rerender` (byte-for-byte, cùng draft thì cùng tệp).

## Chữ trên hình lấy từ đâu

Mọi chữ là một trường của draft, một nhãn cố định trong `radar/labels.py` (đúng ngôn ngữ), hoặc một dữ kiện (`stars`, giấy phép, ngày quét). `tests/test_boards.py` kiểm điều đó bằng máy cho cả ba ngôn ngữ.

Vì vậy hình **không có**:
- nhãn trên mũi tên: `flow` trong draft chỉ là cặp chỉ số, không có tên; mũi tên chỉ cho biết ai nối ai;
- icon hay hình minh hoạ: chọn icon "hợp ngữ nghĩa" cho từng thành phần là một điều model hoặc người phải quyết, không phải script;
- liên kết: repo gốc nằm ở dòng nguồn trong `.md` và trong bài studio (`links:` + `{link}`).

Markup Moda chỉ đặt chữ vào *nội dung* phần tử, đã escape XML và bỏ ký tự điều khiển; một câu README có chứa `<image src=...>` hay `]]>` vẫn chỉ là chữ (có test).

## Áp markup Moda lên một canvas

Moda **không** chạy được trong lượt quét: connector Moda nằm trong tài khoản Claude của bạn và repo này không giữ khóa nào cho nó. Lượt quét chỉ lưu markup; bạn (hoặc Claude trong một phiên có connector) áp nó khi cần:

1. Đọc dòng đầu của tệp: `<!-- radar: Moda canvas 1200x1534; ... -->` cho kích thước canvas.
2. `canvas_create(width=1200, height=<chiều cao>, category="other", visibility="private", skip_brand_kit=true)`, hoặc gắn brand kit của bạn bằng `brand_kit_id`. Hình dùng bảng màu riêng (nền kem, xanh đen, san hô), không theo brand kit nào.
3. `canvas_apply_markup(canvas_ref, page="p_a", markup=<toàn bộ nội dung tệp>)`, rồi `canvas_screenshot` để xem. Mọi hàm trên miễn phí; sinh ảnh AI của Moda (`canvas_edit_image`) tính credit và không được dùng ở đây.

Kiểm tay ngày 2026-10-16 với bài `flowkit` (`digests/2026-10-16-2/`) qua connector Moda: nhận cả dòng chú thích đầu tệp, tạo 51 phần tử, không cảnh báo, không co cỡ chữ. Phép kiểm này cần connector nên **không nằm trong bộ test**; bộ test chỉ chứng minh những gì không cần Moda (chữ, bố cục, escape, tính lặp lại).

### Giới hạn của hình
- Hai cạnh ngược chiều (A→B và B→A) được vẽ chồng lên nhau thành một mũi tên hai đầu, và nhiều cung bắc qua cùng một hàng dùng chung một làn: không mất cạnh nào, nhưng khó phân biệt khi `flow` dày.
- Thẻ "các mảnh ghép" xếp theo thứ tự chỉ số (2 hoặc 3 cột), không theo độ sâu phụ thuộc như `flow-<ngôn ngữ>.svg`.

### Điều chưa kiểm
- Font tiếng Nhật: `moda.FONTS["ja"]` ghi `Noto Sans JP`, **chưa** đối chiếu với danh sách font của Moda. Vietnamese/English dùng `Be Vietnam Pro` (đã thấy hiển thị đúng dấu).
- Hệ số đo chữ (`boards.Style.wscale = 1.15` cho Moda) đo trên tiếng Việt. Một bài tiếng Anh hay tiếng Nhật có thể được Moda co chữ nhẹ; Moda báo `text_auto_shrunk` nhưng không cắt chữ.
- Bảng Excalidraw: kiểm tay bằng cách dựng ảnh qua `@excalidraw/excalidraw` 0.18.1 trong Chromium (10 bài thật, bố cục đúng, dấu tiếng Việt đúng); chưa mở trên excalidraw.com bản web hiện tại.

## Ảnh PNG

Lượt quét không xuất PNG: dựng ảnh Excalidraw cần trình duyệt, và Moda cần phiên có connector. Muốn PNG: trong excalidraw.com chọn *Export image*; trong Moda dùng `export` (png, `pixel_ratio=2`).

## Vẽ cho các bài cũ

`python3 radar.py rerender` thêm hai tệp vào mọi bài đã lưu `draft-*.json`. Nó cũng vẽ lại phần còn lại bằng bộ vẽ hiện tại; thử trên bản sao ngày 2026-10-16 (10 bài), kết quả chỉ là 20 tệp mới, không tệp có sẵn nào đổi. Vẫn nên xem `git status` trước khi commit, vì bộ vẽ có thể đã đổi từ lần đó.
