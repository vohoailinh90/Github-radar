---
id: R-impeccable
title: Impeccable: bộ “từ vựng thiết kế” để trợ lý AI làm giao diện có gu hơn
date: 2026-11-16
audience: người không chuyên IT/AI (chủ sản phẩm, nội dung, designer nhờ AI dựng giao diện)
language: vi
---
# Impeccable: bộ “từ vựng thiết kế” để trợ lý AI làm giao diện có gu hơn

**Ngày lấy dữ liệu: 16/11/2026.** Số sao, fork, issue từ GitHub [S2]; mô tả từ README ở commit `d41d986` [S1]. Người viết **chưa cài và chưa chạy** công cụ.

## Kết luận ngắn

Impeccable là một kỹ năng miễn phí (Apache-2.0 [S3]) cài thêm cho **trợ lý lập trình AI** (Claude Code, Cursor, Codex…) để nó hiểu các yêu cầu thiết kế như “bolder”, “quieter”, “polish”, biết **chấm điểm** giao diện (`critique`, `audit`) và có **62 quy tắc** bắt lỗi giao diện chạy không cần AI [S1]. Hợp với người nhờ AI dựng trang web hoặc ứng dụng. Độ khó: **Trung bình**; rủi ro lớn nhất là hook tự chạy (xem dưới).

## Hồ sơ nhanh (16/11/2026)

| Mục | Giá trị | Nguồn |
|---|---|---|
| Sao | 111.170 | [S2] |
| Fork | 6.644 | [S2] |
| Giấy phép | Apache-2.0 | [S2] [S3] |
| Cập nhật gần nhất | 16/11/2026 | [S1] [S2] |
| Issue đang mở | 48 | [S2] |
| Phiên bản kỹ năng | skill-v4.9.1 (221 thẻ) | [S4] |

## Nó là gì, giải quyết gì

**Repo này giúp bạn nhờ trợ lý AI làm giao diện có gu hơn, mà không cần là nhà thiết kế.** README nêu các dấu hiệu AI hay lặp lại: phông Inter cho mọi thứ, gradient tím sang xanh, thẻ lồng thẻ, chữ xám trên nền màu [S1]. Nói “làm cho nổi bật” thì AI phải đoán; Impeccable cho bạn **từ vựng rõ** (24 lệnh), **một người chấm** (critique cho điểm, audit xếp lỗi P0 đến P3) và **một máy bắt lỗi** (62 quy tắc) [S1].

## Hoạt động thế nào (3 bước)

1. Cài một lần, chạy `/impeccable init`: nó đọc dự án, chỉ hỏi điều không tự suy ra được (sản phẩm cho ai, ràng buộc) và ghi vào `PRODUCT.md` [S1].
2. Gọi một lệnh kèm đối tượng, ví dụ `/impeccable critique the pricing cards` [S1].
3. Nó nạp “sổ tay” riêng của lệnh đó rồi chấm hoặc sửa đúng phần bạn chỉ [S1]. Hình dung như thuê một biên tập viên: bạn nói “gọn hơn”, “mạnh hơn” thay vì “làm cho đẹp”.

## Vì sao được đánh giá cao

- Hơn 111 nghìn sao; commit mới nhất ngày 16/11/2026; 221 thẻ phiên bản [S2] [S4].
- Từ vựng rõ (24 lệnh), có người chấm, có máy bắt lỗi chạy ở dòng lệnh/CI hoặc tiện ích Chrome [S1].
- Ảnh so sánh “có và không có Impeccable” trong README là ví dụ do dự án chọn; người viết chưa kiểm độc lập [S1].

## Ba tình huống ứng dụng

*Ví dụ minh họa suy ra từ các lệnh trong README; mức cải thiện chưa được đo.*

- **Làm trang giới thiệu:** thay vì nhận trang AI dựng trông giống mọi trang khác, nhờ trợ lý chạy `critique` rồi sửa theo danh sách ưu tiên.
- **Rà soát trước khi gửi khách:** chạy `audit` về lỗi truy cập, hiệu năng, co giãn màn hình, xếp từ P0 đến P3.
- **Tự động bắt lỗi:** chạy `detect` trong CI, hoặc quét trang bất kỳ bằng tiện ích Chrome.

## Cách bắt đầu

**Độ khó: Trung bình. Thời gian ước tính: 15–30 phút** (ước tính của người viết).

1. Có công cụ lập trình AI (Claude Code, Cursor, Codex…) và Node.js (chỉ cần để chạy `npx`) [S1].
2. Trong thư mục dự án chạy `npx impeccable install` [S1].
3. Đọc kỹ rồi mới đồng ý cài “hook” tự kiểm tra (xem rủi ro) [S1].
4. Khởi động lại công cụ AI, gõ `/impeccable init` [S1].
5. Thử `/impeccable critique` một thành phần của trang [S1].

## Hạn chế và rủi ro (đều do README nêu)

- **Hook tự chạy:** hook cài sẵn vẫn chạy cả khi bạn từ chối lệnh của AI; cần đọc hook trước khi chạy không người giám sát [S1].
- **Chế độ live (Apply):** có thể chạy `codex` hoặc `claude` khi đã tắt phê duyệt và sandbox; đặt `IMPECCABLE_LIVE_COPY_AGENT=chat` để giữ trong chat. Chỉ dùng trên bản mã trên máy, không dùng trên trang đang chạy thật [S1].
- **Tải thêm chương trình:** lần đầu chạy có thể tải một tệp engine về `~/.impeccable/bin/` [S1].
- **Ghi nhận ẩn danh:** lúc bắt đầu thiết kế mới, kỹ năng lấy danh mục hướng thiết kế từ impeccable.style; tắt ghi nhận bằng `npx impeccable telemetry off` [S1].
- Mạnh nhất với giao diện đã có sẵn; dựng trang hoàn toàn mới là chế độ khó hơn [S1].

## Phù hợp và không phù hợp

- **Phù hợp:** nhờ AI dựng trang web hoặc ứng dụng; chủ sản phẩm hay designer muốn chấm và sửa theo ưu tiên; muốn danh sách kiểm tra thiết kế chạy tự động.
- **Chưa nên dùng:** chưa dùng công cụ lập trình AI; việc của bạn không có giao diện; máy công ty không cho tải chương trình hoặc cài hook.

## Lộ trình

- **30 phút đầu:** cài đặt, `/impeccable init`, chấm thử một thành phần bằng `critique`.
- **Ngày 1–2:** quét thư mục hoặc địa chỉ trang bằng `npx impeccable detect`.
- **Ngày 3–4:** thử lệnh chỉnh `bolder`, `quieter`, `polish` trên một màn hình.
- **Ngày 5–7:** chạy `audit`, sửa lỗi P0–P1, lưu gu thiết kế vào `DESIGN.md` bằng `/impeccable document`.

## Thuật ngữ

Trợ lý lập trình AI: chương trình tự viết mã và chạy lệnh giúp bạn. Skill (kỹ năng): gói chỉ dẫn cài thêm cho AI. Hook (móc): đoạn lệnh tự chạy khi AI sửa tệp. AI slop: giao diện AI dựng na ná nhau. CI: máy tự kiểm tra mỗi lần cập nhật mã. Apache-2.0: giấy phép cho dùng, sửa, chia sẻ miễn phí.

## Điều chưa xác minh

- Hiệu quả “có và không có Impeccable” là ví dụ của dự án.
- Mọi mô tả hành vi dựa trên README, chưa chạy thử; số sao và issue đổi từng ngày.
