# Điều kiện quét: lưu, chọn, và quét theo yêu cầu

Lịch tự chạy vẫn là thứ Tư và thứ Bảy, dùng đúng `radar.yaml`. Ngoài lịch, bạn quét lúc nào cũng được với **điều kiện riêng cho lần quét đó**, không phải sửa `radar.yaml`.

## Cách quét ngay, không cần chờ ngày

**Trên GitHub (không cần token, không cài gì):** Actions → *Radar scan* → *Run workflow*.

| Ô | Dùng để |
|---|---|
| `dry_run` | Mặc định **bật**: chỉ xếp hạng, không gọi model, không ghi gì. Bỏ chọn để viết bài thật |
| `preset` | Chọn một bộ điều kiện đã lưu (bên dưới). `none` = `radar.yaml` nguyên trạng |
| `conditions` | Điều kiện dùng một lần, dạng JSON, **cộng vào** `preset`; chỗ nào cả hai đặt giá trị thì ô này thắng. Ví dụ `quet-nhanh` + `{"min_stars": 5000}` vẫn là 1 bài, sàn 5000 sao. `{}` không thêm gì |
| `picks`, `langs` | Ô cũ. Nếu điền, chúng thắng cả `preset` lẫn `conditions` (cụ thể hơn) |
| `repo`, `bucket` | Quét đúng một repo bạn chọn (xem README) |

**Trên máy có Python:** `python3 radar.py scan --preset ai-sau` (xem xếp hạng), `python3 radar.py run --dry-run --conditions '{"picks_per_run": 1}'`.
`python3 radar.py presets` liệt kê các bộ đã lưu kèm chi phí ước tính.

Chạy thật (bỏ `dry_run`) gọi model, ghi `digests/`, `export/studio/`, `state/` vào `main` và mở PR nháp vào studio, giống lượt theo lịch. Các lần quét không chạy chồng (`concurrency: radar`): một lần chạy, một lần chờ; theo cách GitHub xử lý nhóm đồng thời (chưa thử ở repo này), gửi thêm một lần nữa khi đã có lần đang chờ sẽ **thay** lần chờ cũ, nên lần cũ hiện là "cancelled".

## Điều kiện nào đổi được

| Khóa | Ý nghĩa | Khoảng cho phép |
|---|---|---|
| `picks_per_run` | Số repo viết bài | 1–10 |
| `min_stars` | Sàn sao của lượt tìm chính | 0–1.000.000 |
| `max_days_since_push` | Repo phải có commit trong bấy nhiêu ngày | 1–3650 |
| `langs` | Ngôn ngữ bài viết (mỗi ngôn ngữ thêm = thêm lượt gọi model) | `vi`, `en`, `ja` |
| `rising.enabled`, `rising.slots`, `rising.created_within_days`, `rising.min_stars` | Lượt tìm thứ hai cho repo trẻ và số suất dành cho chúng | slots 0–10, ngày 1–1825. Số suất thật là `min(slots, một nửa số bài)`: với 1 bài thì bằng 0 và lượt tìm repo trẻ không được gửi |
| `buckets` | Chỉ quét những nhóm này, với những topic này. Thay hẳn danh sách nhóm của `radar.yaml` | id phải có trong `radar.yaml`; topic: chữ thường, số, gạch ngang, tối đa 50 ký tự, tối đa 8 topic mỗi nhóm |

**Không đổi được từ điều kiện** (là luật nội dung và an toàn của bạn, nằm ở `radar.yaml` và `CLAUDE.md`): giấy phép được coi là miễn phí (`licenses`), model và họ model, studio, giới hạn README, nhịp nghỉ, thời gian chạy tối đa. Khóa lạ, kiểu sai, số ngoài khoảng, JSON lặp khóa hoặc có `NaN` đều bị từ chối **trước khi gọi GitHub hay model**, bằng một thông báo ngắn không lặp lại nguyên văn đầu vào.

Vì sao topic bị kiểm chặt: topic được ghép nguyên vào câu truy vấn tìm kiếm (`topic:<tên>`). Một "topic" như `llm stars:>0` sẽ thêm điều kiện lạ vào truy vấn, nên chỉ chấp nhận đúng dạng topic của GitHub, kiểm bằng `fullmatch` (kể cả `radar.yaml`).

## Thứ tự ưu tiên

`radar.yaml` → `preset` → `conditions` chồng lên preset (từng khóa; riêng `rising` từng thiết lập, còn `buckets` thay hẳn) → ô/biến cụ thể (`picks`, `langs`, `RADAR_SEARCH_INTERVAL`…). Kiểm tra hợp lệ **một lần, sau cùng**. Tên preset phải có thật kể cả khi có `conditions` đi kèm. Mỗi lần quét ghi vào `state/runs/<ngày>.json` khóa `conditions`: `label` (tên preset, `tên+custom` khi có điều kiện nhập thêm, `custom` khi chỉ có điều kiện nhập tay, hoặc `null` cho lượt theo lịch) và `resolved` (**giá trị cuối cùng**, không chỉ tên preset, vì preset có thể bị sửa sau này).

## Bộ điều kiện đã lưu

Nằm ở [`radar/presets.json`](../radar/presets.json). Thêm một bộ: thêm một mục vào file, rồi thêm tên vào danh sách `options` của ô `preset` trong `.github/workflows/radar.yml` (GitHub không cho đọc danh sách từ file). Một test (`tests/test_workflow.py`) báo lỗi nếu hai nơi lệch nhau, và một test khác chạy từng preset qua `radar.yaml` thật.

| Tên | Làm gì |
|---|---|
| `ai-sau` | Chỉ nhóm AI, 3 bài |
| `repo-moi-noi` | 4 bài, 2 suất cho repo tạo trong 90 ngày gần nhất, sàn 200 sao |
| `khoi-nghiep-saas` | Chỉ nhóm khởi nghiệp, 2 bài |
| `cong-cu-dev` | Chỉ nhóm công cụ phần mềm, 2 bài |
| `quet-nhanh` | 1 bài, tắt lượt tìm repo trẻ |

## Quét hiệu quả nhất: thời gian đi đâu

`python3 radar.py presets` tính (không gọi mạng) từ chính cấu hình:

- **Phần tìm** là lượt gọi Search API cách nhau 2,1 giây (hạn mức 30 lượt/phút): mặc định 16 topic × 2 lượt = 32 lượt, khoảng 67 giây. Lượt thứ ba chỉ thêm khi topic nóng (trang đầu của lượt "repo trẻ" đầy repo đã trên sàn sao).
- **Phần viết** là thứ lâu: mỗi bài ít nhất 2 lượt gọi model (viết + soát), cộng `pace_seconds` (45 giây) nghỉ sau mỗi bài trừ bài cuối. 3 bài tiếng Việt = ít nhất 6 lượt gọi và 90 giây nghỉ, chưa kể thời gian model trả lời và vòng sửa. Số giây thật của từng lượt gọi nằm trong `models_log` của báo cáo (`seconds`, `served`).
- Vì vậy **thu hẹp nhóm chỉ tiết kiệm dưới một phút**; thứ đổi thời gian chạy và hạn mức free nhiều nhất là `picks_per_run` × số ngôn ngữ. Thu hẹp nhóm có ích vì **chọn đúng mảng bạn muốn học**, không phải vì nhanh.

Kết quả đọc tài liệu GitHub (github/docs, đọc trực tiếp nguồn): một truy vấn tìm trả tối đa 1.000 kết quả; truy vấn dài quá 256 ký tự hoặc quá 5 toán tử AND/OR/NOT bị từ chối; hạn mức 30 lượt/phút khi đã đăng nhập; khi chạm giới hạn phụ thì chờ `retry-after`, hoặc ít nhất một phút nếu không có.

Những thứ **cố ý chưa làm** (lý do):

- *Đếm `incomplete_results`* (kết quả tìm bị cắt vì quá thời gian): chỉ là quan sát, chưa đổi quyết định nào.
- *Chờ 60 giây khi gặp giới hạn phụ không có `Retry-After`*: tài liệu bảo thế, nhưng giai đoạn tìm chưa có ngân sách thời gian riêng, nên 32 lượt tìm có thể cộng dồn đến 32 phút. Cần một trần tổng cho thời gian chờ ở giai đoạn tìm trước khi làm.
- *Yêu cầu có điều kiện (ETag, 304 không tính vào hạn mức)*: lợi khi đọc lại đúng URL cũ; mỗi lần quét đọc dữ liệu mới nên gần như không lợi.
- *GraphQL gộp nhiều repo*: Search đã trả sẵn số sao; chỉ cần khi theo dõi hàng nghìn repo.

## Kiểm tra tay lần đầu (những gì chưa kiểm được ngoài GitHub thật)

Đã kiểm bằng máy (không cần GitHub): toàn bộ kiểm tra điều kiện, thứ tự ưu tiên, bộ cài sẵn hợp lệ với `radar.yaml` thật, workflow chỉ đưa hai ô mới qua `env:`, báo cáo ghi `conditions`.

**Chưa kiểm được ở đây, bạn thử một lần:**

1. Actions → *Radar scan* → *Run workflow*: ô `preset` hiện đủ 6 lựa chọn và ô `conditions` có chỗ nhập.
2. Chọn `quet-nhanh`, giữ `dry_run` bật, chạy. Mở *Radar run* trong phần Summary: `conditions.label` là `quet-nhanh`, `picks` có đúng 1 repo.
3. Dán `{"picks_per_run": 99}` vào `conditions`, chạy: bước *Scan* phải đỏ ngay với thông báo `picks_per_run must be between 1 and 10`, không có bài nào được viết.
4. Chạy không chọn gì (dry_run bật, `preset` = `none`): kết quả như lượt theo lịch.
