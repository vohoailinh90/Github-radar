# Hướng dẫn làm video AI từ các repo GitHub mã nguồn mở

Bộ hướng dẫn này gom **5 repo mã nguồn mở, miễn phí** về làm video bằng AI, mỗi repo có một bài **làm theo từng bước**:
việc cần chuẩn bị, từng lệnh để gõ (chép nguyên văn từ README của repo), cái bạn sẽ thấy khi bước đó thành công, và cách
xử lý khi lỗi. Quét ngày **16/10/2026**; số sao lấy từ trang repo hôm đó và làm tròn theo trang.

## Bạn muốn làm gì?

| Mục tiêu | Repo | Sao | Giấy phép | Cần có | Hướng dẫn |
|---|---|---:|---|---|---|
| Tạo video ngắn từ **một chủ đề** (tự viết kịch bản, chọn clip, đọc lời, phụ đề, nhạc) | MoneyPrinterTurbo | 131.800 | MIT | Khóa API của một dịch vụ LLM và của nguồn clip; card đồ họa không bắt buộc | [Xem bài](../digests/2026-10-16-3/moneyprinterturbo/vi.md) |
| Tự chạy **mô hình tạo video** từ câu mô tả hoặc ảnh ngay trên máy | Wan2.2 | 18.000 | Apache-2.0 | Card đồ họa từ 24GB VRAM (bản TI2V-5B); bản lớn từ 80GB | [Xem bài](../digests/2026-10-16-3/wan2-2/vi.md) |
| Dựng video **nhiều cảnh** từ ý tưởng hoặc kịch bản bằng nhóm agent AI | ViMax | 12.700 | MIT | Khóa API cho mô hình chat, mô hình ảnh và mô hình video; Linux hoặc Windows | [Xem bài](../digests/2026-10-16-3/vimax/vi.md) |
| Làm **phụ đề và lồng tiếng** cho một video có sẵn | VideoLingo | 18.800 | Apache-2.0 | Dịch vụ LLM tương thích OpenAI; Internet cho lần cài đầu | [Xem bài](../digests/2026-10-16-3/videolingo/vi.md) |
| **Dịch video** sang ngôn ngữ khác, kèm phụ đề và giọng đọc | pyVideoTrans | 19.400 | GPL-3.0 | Windows có bản chạy ngay; hệ khác cần Python 3.10, FFmpeg, uv | [Xem bài](../digests/2026-10-16-3/pyvideotrans/vi.md) |

**Chưa biết bắt đầu từ đâu?** Máy không có card đồ họa lớn: bắt đầu với MoneyPrinterTurbo, README của nó ghi card đồ họa không bắt buộc.
Có card đồ họa từ 24GB VRAM và muốn tự chạy mô hình: bắt đầu với Wan2.2.

Mục lục đầy đủ của lần quét: [`digests/2026-10-16-3/README.md`](../digests/2026-10-16-3/README.md).

## Một bài hướng dẫn gồm những gì

1. **Bạn sẽ làm ra được gì**: kết quả cuối cùng, nói cụ thể.
2. **Lưu ý trước khi dùng** và **Chuẩn bị**: danh sách đánh dấu được (phần mềm, phần cứng, tài khoản, khóa API), có liên kết lấy từ README.
3. **Lộ trình**: một hình tóm tắt các bước, mỗi bước cho biết có bao nhiêu lệnh.
4. **Làm theo từng bước**: mỗi bước có *mục đích*, việc cần làm, khối lệnh để chép, *bạn sẽ thấy*, *nếu không được* và *căn cứ* (README hoặc một đường dẫn có thật trong repo).
5. **Kiểm tra kết quả**, **Lỗi thường gặp** (chỉ những lỗi README tự nêu), **Làm tiếp**.
6. Phần giải thích cách nó chạy bên trong, bài học thiết kế và từ khóa nằm **sau** phần hướng dẫn.

## Cách chọn 5 repo

Dùng đúng luật của bộ quét (`radar.yaml`): giấy phép miễn phí, không phải bản fork hay đã lưu trữ, có commit trong 120 ngày gần
nhất, và README có hướng dẫn cài đặt chạy được. Trong các repo tìm được, có hai repo bị loại vì quá cũ:

- `gyoridavid/short-video-maker`: commit cuối ngày 21/06/2025.
- `Lightricks/LTX-Video`: commit cuối ngày 06/01/2026.

Hai repo mô hình lớn khác (HunyuanVideo, LTX-2) **chưa được đánh giá**: các nguồn thứ cấp cho biết trọng số của chúng dùng giấy phép riêng,
không phải giấy phép mã nguồn mở chuẩn, nên chưa đưa vào. Muốn thêm repo khác: `python3 radar.py run --repo owner/tên`.

## Điều cần biết trước khi tin các bài này

- **Chưa ai chạy thử từng bước trên máy thật.** Bài được viết bằng cách đọc README, không cài và chạy từng repo (môi trường tạo bài không có card đồ họa
  và không có khóa API của các dịch vụ). Các bài bám sát README của repo và máy kiểm tra từng lệnh có nằm **nguyên văn** trong README hay không, nhưng một lệnh đúng
  trong README vẫn có thể lỗi trên máy bạn (phiên bản, hệ điều hành, hạn mức dịch vụ). Nếu một bước lỗi, hãy xem phần **Lỗi thường gặp** rồi README gốc.
- Bài do **Claude viết trong một phiên tương tác**, không phải do các model miễn phí của bộ quét, và **không có model họ khác soát lại**.
  Mỗi bản nháp (`draft-vi.json`) ghi rõ điều này trong khóa `note`. Máy vẫn kiểm: số liệu phải có trong README hoặc dữ kiện repo, mỗi
  lệnh phải là một dòng của README, chữ nằm giữa dấu backtick phải có trong README hoặc là đường dẫn có thật, không có URL do model viết
  (liên kết được máy in ra từ danh sách liên kết của README), không có lời quảng cáo.
- **README là nguồn duy nhất.** Chỗ README không nói (tên nút trên giao diện, vị trí tệp kết quả, dung lượng mô hình), bài cũng nói là README không nêu.
- Số sao là ảnh chụp ngày quét, đọc từ trang repo và làm tròn theo trang.
- Đây không phải đánh giá bảo mật. Các repo này gọi dịch vụ bên thứ ba (LLM, nguồn clip, giọng đọc) có thể tính phí; hãy xem điều khoản của từng nhà cung cấp và bản quyền của clip, nhạc, video bạn xử lý.

## Tạo bài kiểu này cho repo khác

Bộ quét hằng tuần (thứ Tư và thứ Bảy) giờ viết **hướng dẫn làm theo từng bước** thay cho bài giải thích ngắn: xem [`README.md`](../README.md).
Để viết cho đúng một repo: `python3 radar.py run --repo owner/tên` (hoặc Actions → *Radar scan* → ô `repo`).
