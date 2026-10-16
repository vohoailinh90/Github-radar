# Tệp thiết kế: bảng Excalidraw, markup Moda và sơ đồ draw.io

Mỗi bài học còn có ba tệp vẽ cùng nội dung bằng ba công cụ chỉnh sửa, để bạn tinh chỉnh bằng tay hoặc đăng lại với giao diện đẹp hơn SVG:

| Tệp (cạnh `<ngôn ngữ>.md`) | Là gì | Mở bằng |
|---|---|---|
| `board-<ngôn ngữ>.excalidraw` | Bảng nét vẽ tay: 3 khung (các mảnh ghép, các bước, bài học), mũi tên theo `flow` | [excalidraw.com](https://excalidraw.com): *Open* hoặc kéo tệp vào. Sửa tay được từng thẻ |
| `moda-<ngôn ngữ>.xml` | Markup Moda của một infographic dọc 1200 px: dải tiêu đề tối, thẻ màu, bước đánh số | Một phiên Claude có connector Moda (xem bên dưới) |
| `drawio-<ngôn ngữ>.drawio` | Sơ đồ draw.io cùng bố cục: mỗi thẻ là một khối giữ chữ của nó, mũi tên là connector gắn vào thẻ, mỗi thành phần có icon | [app.diagrams.net](https://app.diagrams.net): *File → Open from → Device*, hoặc kéo tệp vào |

Cả hai do **script** vẽ từ `draft-<ngôn ngữ>.json` (`radar/boards.py` dựng bố cục, `radar/excalidraw.py`, `radar/moda.py` và `radar/drawio.py` chỉ ghi ra từng định dạng), không có model nào viết một ký tự của chúng. Chúng được vẽ lúc quét và vẽ lại bởi `python3 radar.py rerender` (byte-for-byte, cùng draft thì cùng tệp).

## Chữ trên hình lấy từ đâu

Mọi chữ là một trường của draft, một nhãn cố định trong `radar/labels.py` (đúng ngôn ngữ), hoặc một dữ kiện (`stars`, giấy phép, ngày quét). `tests/test_boards.py` kiểm điều đó bằng máy cho cả ba ngôn ngữ.

Vì vậy hình **không có**:
- nhãn trên mũi tên: `flow` trong draft chỉ là cặp chỉ số, không có tên; mũi tên chỉ cho biết ai nối ai;
- hình minh hoạ do model tự vẽ hay đặt tên: icon duy nhất trên hình là một **tên chọn từ danh sách đóng** (mục dưới);
- liên kết: repo gốc nằm ở dòng nguồn trong `.md` và trong bài studio (`links:` + `{link}`).

Markup Moda chỉ đặt chữ vào *nội dung* phần tử, đã escape XML và bỏ ký tự điều khiển; một câu README có chứa `<image src=...>` hay `]]>` vẫn chỉ là chữ (có test).

## Icon: model chọn tên, script vẽ

Mỗi thành phần trong `how_it_works.components` có thể có `icon`: **một tên trong danh sách đóng `radar/icons/index.json`** (hơn 50 icon, mỗi tên kèm một dòng nghĩa mà prompt đưa cho model). Model chỉ trả tên; hình là tệp SVG của [Lucide](https://lucide.dev) (giấy phép ISC, `docs/third-party/lucide/`) chép nguyên byte vào `radar/icons/`, có sha256 trong `index.json`.

- `gates.schema` từ chối tên ngoài danh sách (lỗi `components[i]`, vòng sửa lỗi nói rõ thành phần nào), và bắt buộc **tất cả hoặc không thành phần nào** có icon: một hàng thẻ lẻ loi một thẻ trơn nhìn như lỗi.
- Bản nháp cũ không có `icon` vẫn hợp lệ: chúng vẽ không icon, chữ chiếm cả thẻ. Chỉ `drawio-<ngôn ngữ>.drawio` vẽ icon (Excalidraw và Moda không đổi một byte).
- **Bài cũ có icon qua một tệp riêng.** Sửa một draft đã lưu là đổi câu trả lời gốc của model, nên icon của bài cũ nằm trong `icons-<ngôn ngữ>.json` cạnh `draft-<ngôn ngữ>.json`: `{"note": ..., "components": [{"name": "<đúng tên thành phần>", "icon": "<tên trong danh sách>"}, ...]}`, đúng thứ tự và đủ mọi thành phần. Tệp do người hoặc một phiên Claude chọn, không phải model viết bài; `gates.icon_file` kiểm nó như kiểm draft (tên ngoài danh sách, sai số dòng, sai tên thành phần đều bị từ chối), và `rerender` **bỏ qua cả lượt quét đó** (không vẽ gì) khi một tệp không còn khớp draft hoặc không phải JSON. Draft đã có `icon` thì thắng tệp. `rerender` không bao giờ ghi hay xoá tệp này, và `draft-*.json` vẫn đúng từng byte.
- `icons.svg()` chỉ ghi lại các hình (`path`, `circle`, `rect`...) có trong tệp, qua một danh sách cho phép; tệp bị thay bằng cái có `<script>`, `href` hay thuộc tính lạ bị từ chối và `icons.verify()` báo. Icon nằm **trong** tệp `.drawio` (data URI), không có đường dẫn ngoài.
- Để thêm một icon: xem `docs/third-party/lucide/NOTICE.md`.

## Áp markup Moda lên một canvas

Moda **không** chạy được trong lượt quét: connector Moda nằm trong tài khoản Claude của bạn và repo này không giữ khóa nào cho nó. Lượt quét chỉ lưu markup; bạn (hoặc Claude trong một phiên có connector) áp nó khi cần:

1. Đọc dòng đầu của tệp: `<!-- radar: Moda canvas 1200x1534; ... -->` cho kích thước canvas.
2. `canvas_create(width=1200, height=<chiều cao>, category="other", visibility="private", skip_brand_kit=true)`, hoặc gắn brand kit của bạn bằng `brand_kit_id`. Hình dùng bảng màu riêng (nền kem, xanh đen, san hô), không theo brand kit nào.
3. `canvas_apply_markup(canvas_ref, page="p_a", markup=<toàn bộ nội dung tệp>)`, rồi `canvas_screenshot` để xem. Mọi hàm trên miễn phí; sinh ảnh AI của Moda (`canvas_edit_image`) tính credit và không được dùng ở đây.

Kiểm tay ngày 2026-10-16 với bài `flowkit` (`digests/2026-10-16-2/`) qua connector Moda: nhận cả dòng chú thích đầu tệp, tạo 51 phần tử, không cảnh báo, không co cỡ chữ. Phép kiểm này cần connector nên **không nằm trong bộ test**; bộ test chỉ chứng minh những gì không cần Moda (chữ, bố cục, escape, tính lặp lại).

### Giới hạn của hình
- Excalidraw và Moda: hai cạnh ngược chiều (A→B và B→A) được vẽ chồng lên nhau thành một mũi tên hai đầu, và nhiều cung bắc qua cùng một hàng dùng chung một làn: không mất cạnh nào, nhưng khó phân biệt khi `flow` dày. Bản draw.io tách chúng: mỗi mũi tên một cổng ra/vào và một làn ngang riêng trong khoảng trống giữa hai hàng, chỗ giao nhau có nét nhảy; `tests/test_drawio.py` thử hàng trăm `flow` ngẫu nhiên (2-6 thành phần, tối đa 12 cạnh, cả hai chiều) để không hai đường nào nằm chồng lên nhau và không đường nào đi qua một thẻ. Khi `flow` rất dày (hơn khoảng 8 mũi tên qua cùng một khoảng trống) các làn chỉ cách nhau vài px.
- Thẻ "các mảnh ghép" xếp theo thứ tự chỉ số (2 hoặc 3 cột), không theo độ sâu phụ thuộc như `flow-<ngôn ngữ>.svg`.
- Chữ draw.io dùng Helvetica (mặc định của draw.io, tự thay font khác cho tiếng Việt và tiếng Nhật), không phải Be Vietnam Pro như Moda.

### Điều chưa kiểm
- Font tiếng Nhật: `moda.FONTS["ja"]` ghi `Noto Sans JP`, **chưa** đối chiếu với danh sách font của Moda. Vietnamese/English dùng `Be Vietnam Pro` (đã thấy hiển thị đúng dấu).
- Hệ số đo chữ (`boards.Style.wscale = 1.15` cho Moda) đo trên tiếng Việt. Một bài tiếng Anh hay tiếng Nhật có thể được Moda co chữ nhẹ; Moda báo `text_auto_shrunk` nhưng không cắt chữ.
- Bảng Excalidraw: kiểm tay bằng cách dựng ảnh qua `@excalidraw/excalidraw` 0.18.1 trong Chromium (10 bài thật, bố cục đúng, dấu tiếng Việt đúng); chưa mở trên excalidraw.com bản web hiện tại.
- Sơ đồ draw.io: kiểm tay bằng cách dựng ảnh qua một bản editor draw.io 14.6.12 (gói npm `drawio-offline`, không phải của JGraph) trong Chromium không có mạng, và qua `@drawio/mcp` 1.7.0 (`open_drawio_xml` nhận XML và trả về URL, giải mã ra giống hệt từng byte). Dịch vụ draw.io (`create_diagram` của connector draw.io) nhận cùng XML đó mà không báo lỗi và trả về một liên kết mở editor; hình do editor hiện tại của app.diagrams.net vẽ ra **chưa được nhìn thấy** trong phép kiểm này, và bản 14.6.12 là bản cũ (2021). Nếu một icon hay mũi tên hiện sai trên bản mới, đó là lỗi cần báo.

## Ảnh PNG

Lượt quét không xuất PNG: dựng ảnh Excalidraw và draw.io cần trình duyệt, và Moda cần phiên có connector. Muốn PNG: trong excalidraw.com chọn *Export image*; trong app.diagrams.net *File → Export as → PNG*; trong Moda dùng `export` (png, `pixel_ratio=2`).

## Vẽ cho các bài cũ

`python3 radar.py rerender` thêm ba tệp (`board-`, `moda-`, `drawio-`) vào mọi bài đã lưu `draft-*.json`; bản draw.io của bài cũ có icon khi bài có `icons-<ngôn ngữ>.json` (mục Icon ở trên). Nó cũng vẽ lại phần còn lại bằng bộ vẽ hiện tại; chạy trên 10 bài hiện có (2026-10-12 đến 2026-10-16), kết quả chỉ là 30 tệp mới (3 mỗi bài), không tệp có sẵn nào đổi. Vẫn nên xem `git status` trước khi commit, vì bộ vẽ có thể đã đổi từ lần đó.
