---
id: R12
title: Replica Skill: mười một skill Claude để dựng lại một ứng dụng
topic: ky-thuat
date: 2026-11-08
---
# Replica Skill: mười một skill Claude để dựng lại một ứng dụng

## Tóm tắt

Repo này là gì, dùng thế nào, và cần cẩn thận ở đâu? README mô tả đây là "mười một skill Claude để nhân bản bất kỳ ứng dụng nào", miễn phí, giấy phép MIT, không cần đăng ký hay khóa API [S1]. Thực chất là một bộ **mười một thư mục skill**, mỗi thư mục một tệp `SKILL.md` viết như quy trình cho Claude, chạy theo một chuỗi cố định: `recon` (đọc ứng dụng gốc), `architect` (chọn công nghệ và lược đồ), `design` (dựng hệ thống thiết kế), `build` (dựng từng màn hình), `backend` (đăng nhập, cơ sở dữ liệu, thanh toán), `test`, `diff` (chấm điểm so với bản gốc), `entrepreneur` (đọc đánh giá thật của người dùng), `brand`, `launch` và `deploy` [S1]. Kèm theo là sáu công cụ Python chỉ dùng thư viện chuẩn, làm những việc mà một mô hình không nên tự "cảm nhận": tính điểm, so ảnh, xếp hạng phản hồi, quét thương hiệu còn sót, kiểm tra tin đăng cửa hàng, đo độ tương phản màu [S13] [S14] [S15] [S16] [S17] [S18].

Bài đọc repo theo bốn tầng. Tầng một là chuỗi mười một bước và tệp mà mỗi bước đọc, ghi trong thư mục `replica/` của dự án người dùng [S1] [S2]. Tầng hai là từng skill: luật riêng, đầu vào, đầu ra và điều kiện "xong" [S2] [S3] [S4] [S5] [S6] [S7] [S8]. Tầng ba là sáu công cụ và những con số đặt cứng trong mã: trọng số điểm, ngưỡng so ảnh, quy tắc xếp hạng đánh giá, giới hạn ký tự của cửa hàng ứng dụng [S13] [S14] [S15] [S17]. Tầng bốn là phản biện: "miễn phí" nghĩa là gì, "clean room" được bảo đảm đến đâu, và bài kiểm thử của repo kiểm cái gì [S1] [S22].

Mỗi khẳng định mang một trong ba nhãn. **Nguồn: repo** nghĩa là đọc trực tiếp từ một tệp ở commit `77c9436` (03/10/2026, nhánh mặc định). **Người viết đếm** là con số tính bằng script trên bản đã tải; cách đếm nằm ở mục Lưu ý. **Suy luận** là nhận định của người viết, không phải điều repo tuyên bố. Người viết không chạy công cụ hay skill nào: mọi hành vi là "đọc mã, chưa chạy".

Ba ý đáng mang theo. Thứ nhất, bộ này nghiêng mạnh về kỷ luật: phần lớn skill mở đầu bằng "luật" (chỉ đọc nguồn công khai, không chép mã, không bịa trích dẫn, không tự đăng ký dịch vụ), rồi mới đến các bước [S2] [S5] [S9]. Thứ hai, phần thắng của skill `entrepreneur` nằm ở công cụ: `reviews.py` bỏ mọi dòng đánh giá không có đường dẫn, và chỉ in ra đoạn trích là chuỗi con của dòng người dùng đưa vào [S15]. Thứ ba, "miễn phí" áp dụng cho bộ skill; Stripe, cơ sở dữ liệu, email, máy chủ và tài khoản cửa hàng ứng dụng thì người dùng vẫn phải tự mở và trả [S3] [S6] [S12].

## Hồ sơ nhanh

| Mục | Giá trị | Nhãn |
|---|---|---|
| Là gì | Mười một skill Claude theo chuỗi, đóng gói thành plugin và thư mục skill | Nguồn: repo [S1] [S19] |
| Tác giả | Jake Schincariol | Nguồn: repo [S19] [S21] |
| Đóng gói | Plugin `replica-skill` trong marketplace cùng tên, nhóm `productivity`, nguồn là thư mục gốc | Nguồn: repo [S19] [S20] |
| Phiên bản | 1.0.0 | Nguồn: repo [S19] |
| Giấy phép | MIT, có tệp `LICENSE`, bản quyền 2026 | Nguồn: repo [S21] |
| Quy mô | 39 tệp, 163.015 byte | Người viết đếm |
| Văn bản skill | 7.539 từ trong 11 tệp `SKILL.md`, từ 530 (`replica-test`) đến 929 (`replica-recon`) | Người viết đếm |
| Công cụ | 6 tệp Python, 1.505 dòng, chỉ dùng thư viện chuẩn | Người viết đếm [S13] [S14] [S15] [S16] [S17] [S18] |
| Kiểm thử | 6 tệp test, 57 hàm `def test_` | Người viết đếm |
| Yêu cầu | Python 3.8 trở lên, không cần cài gói nào | Nguồn: repo [S1] |
| Số sao | Bài này không nêu: nguồn duy nhất là tệp ở commit đã ghim | Giới hạn của bài |

## Chuỗi mười một bước và thư mục replica/

README nói rõ: chạy theo thứ tự, mỗi skill đọc những gì skill trước ghi trong thư mục `replica/` của dự án người dùng [S1]. Người viết lập bảng "ai đọc, ai ghi" từ phần mở đầu của từng `SKILL.md`:

| Bước | Đọc | Ghi |
|---|---|---|
| recon | trang công khai, ảnh chụp màn hình, tài khoản của chính người dùng | `replica/recon.md`, `replica/features.csv`, `replica/screens/` [S2] |
| architect | `recon.md`, `features.csv` | `replica/architecture.md`, `schema.sql` [S3] |
| design | `recon.md`, ảnh trong `screens/` | `design/tokens.json`, `tokens.css`, `components.md` [S4] |
| build | `recon.md`, `architecture.md`, `design/` | cột `clone` của `features.csv`, `build-log.md`, `clone-screens/` [S5] |
| backend | `architecture.md` | migration, mã máy chủ, `backend.md`, `.env.example` [S6] |
| test | các luồng trong `recon.md` | `test-plan.md`, `bugs.md`, tệp test trong `e2e/` [S7] |
| diff | `features.csv`, ảnh hai bên | `parity.md`, ảnh so sánh [S8] |
| entrepreneur | đánh giá người dùng thu thập tay | `reviews.csv`, `feedback.md`, `fixes.md` [S9] |
| brand | `fixes.md` | `brand.md`, `brand.json` [S10] |
| launch | `fixes.md`, `brand.md`, `brand.json` | thư mục `launch/` (landing, giá, tin đăng, kế hoạch) [S11] |
| deploy | mọi thứ trong `replica/` | `deploy.md` [S12] |

Suy luận: `features.csv` là xương sống của chuỗi. Nó sinh ra ở `recon`, được `build` điền cột `clone`, được `diff` chấm điểm, được `entrepreneur` thêm hàng mới, và được `deploy` gián tiếp kiểm qua điều kiện "must-have xong hết" [S2] [S5] [S8] [S9] [S12]. Người viết đếm: tệp mẫu `features.csv` có 18 hàng, gồm 9 `must`, 5 `should`, 4 `could`; 17 hàng có cột `clone` là `no` và 1 hàng là `skip` (chợ ứng dụng bên thứ ba, với ghi chú rằng mạng lưới đối tác không thuộc phần sản phẩm có thể dựng lại) [S23].

Mỗi skill kết thúc bằng mục "Output"; trừ `deploy` ở cuối chuỗi, skill nào cũng nêu skill kế tiếp [S2] [S3] [S4] [S5] [S6] [S7] [S8] [S9] [S10] [S11] [S12], nên chuỗi có thể chạy từng bước hoặc từng skill riêng lẻ: README viết rõ có thể chạy `replica-entrepreneur` một mình trên một ứng dụng mới chỉ định nhân bản, để biết có đáng làm hay không [S1].

## Ba bước đầu: recon, architect, design

**recon** là bước mà `SKILL.md` tự nhận mọi bước sau dựa vào ("bản đồ tệ thì bản sao tệ") [S2]. Skill có chín bước: xác định phạm vi (ứng dụng nào, nền tảng nào, lát cắt nào, cho ai), liệt kê nguồn có URL ở mọi hàng, kiểm kê màn hình (mã S01, S02...), luồng người dùng (F01, F02...), thành phần, mô hình dữ liệu suy luận có bằng chứng và độ tin cậy, ma trận tính năng, danh sách thứ không thể nhân bản, và ước lượng cỡ S, M, L hoặc XL [S2]. Mục "không thể nhân bản" đáng chú ý: nội dung có bản quyền (danh mục nhạc), mạng lưới người dùng, dữ liệu ứng dụng sở hữu, thỏa thuận đối tác, phần cứng và giấy phép quản lý (ngân hàng, y tế) đều phải ghi thành hàng `skip` kèm lý do [S2]. Luật riêng của recon: chỉ dùng nguồn công khai và tài khoản của chính người dùng; đọc chứ không cào; không đọc hay lưu mã JavaScript của ứng dụng, không ghi lại lời gọi mạng để chép endpoint riêng; xem điều khoản dịch vụ trước vì có sản phẩm cấm dùng tài khoản để làm sản phẩm cạnh tranh [S2].

**architect** chọn công nghệ mặc định theo nguyên tắc "mọi phần đều được quản lý, có tài liệu, rẻ khi chưa có người dùng", và buộc ghi một dòng lý do cho mỗi lựa chọn [S3]. Bảng mặc định có 11 tầng (người viết đếm): ứng dụng web Next.js với TypeScript, Tailwind, Expo cho di động, Postgres trên Supabase hoặc Neon, Drizzle hoặc Prisma, Supabase Auth hoặc Auth.js, Stripe, Resend hoặc Postmark, Vercel Cron hoặc Inngest hoặc Trigger.dev, Supabase Storage hoặc Cloudflare R2, và Vercel làm máy chủ [S3]. Skill dặn "một cơ sở dữ liệu, không vi dịch vụ" và "bản sao không cần kiến trúc của bản gốc, chỉ cần tính năng của bản gốc" [S3]. Quy tắc lược đồ cụ thể: khóa `uuid`, cột chủ sở hữu trên mọi thứ người dùng sở hữu, quy tắc `on delete` phải được quyết định chứ không để mặc định, chỉ mục trên mọi khóa ngoại và cột lọc, thời gian luôn là `timestamptz` lưu UTC, tiền là số nguyên cent kèm mã tiền tệ [S3]. Ví dụ đưa ra là bảng `bookings` của ứng dụng đặt lịch, và dặn việc hai khách đặt trùng một khung giờ là vấn đề của cơ sở dữ liệu (ràng buộc loại trừ hoặc chỉ mục duy nhất) chứ không phải của giao diện [S3]. Thứ tự dựng: một lát cắt dọc chạy suốt lõi sản phẩm trước, rồi must-have, should-have, could-have, cuối cùng là các bản sửa do `entrepreneur` tìm ra [S3].

**design** dựng lại *hệ thống* chứ không lấy tài sản: vai trò màu (bg, surface, border, text, accent, danger...), thang chữ, thang khoảng cách (thường nền 4 hoặc 8), bo góc, bóng đổ, chuyển động [S4]. Điều cấm: logo, biểu tượng, hình minh họa, ảnh, âm thanh của ứng dụng gốc; phông có bản quyền; câu chữ; và màu thương hiệu (ghi như một vai trò `accent`, dùng màu trung tính tạm, để `brand` đổi sau) [S4]. Tệp `tokens.json` mẫu định nghĩa 10 vai trò màu, 6 cỡ chữ từ `xs` đến `display`, thang khoảng cách 9 bậc và danh sách `pairs` gồm 9 cặp chữ và nền cần kiểm (người viết đếm) [S4]. Công cụ `contrast.py` kiểm các cặp đó theo WCAG 2: chữ thường cần 4,5, chữ lớn cần 3, thành phần giao diện và vòng focus cần 3, và thoát với mã 1 nếu có cặp nào trượt mức AA [S18].

## Bốn bước làm ra sản phẩm: build, backend, test, diff

**build** viết lại từng màn hình theo "clean room": mọi dòng mã viết tại chỗ từ bản đồ recon và đặc tả, không dán HTML, CSS, JavaScript, SVG hay ảnh của bản gốc, không tải gì từ miền hoặc CDN của nó, không "xem nguồn rồi sửa" [S5]. Thứ tự: khung ứng dụng (định tuyến cho mọi màn hình, bố cục, token, thành phần nguyên thủy, dữ liệu mẫu), lát cắt dọc, rồi từng màn hình theo thứ tự trong `architecture.md` [S5]. Mỗi màn hình có danh sách "xong" gồm 7 mục (người viết đếm): đủ mọi trạng thái, chạy ở 390px và 1440px, hoàn thành luồng chỉ bằng bàn phím, không lỗi console, không chép câu chữ gốc, đã cập nhật `features.csv`, đã lưu ảnh chụp để `diff` [S5]. Mỗi màn hình một commit dạng `build: S07 booking page`, và nếu một tính năng lớn hơn dự tính thì phải ghi vào build-log và nói trong chat, không âm thầm giao nửa vời [S5].

**backend** có luật đáng chú ý nhất về an toàn: Claude **không bao giờ** tự đăng ký dịch vụ, gõ mật khẩu, thẻ hay khóa chạy thật; người dùng tự tạo dự án Stripe, Supabase, Resend hay Google Cloud rồi đặt khóa vào `.env.local`, còn Claude viết `.env.example` chỉ có tên biến [S6]. Thanh toán dùng Stripe Checkout và Customer Portal chứ không tự dựng form thẻ; webhook phải xác minh chữ ký, lưu mã sự kiện, mọi handler idempotent; bốn sự kiện được liệt kê là `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted` và `invoice.payment_failed`; trạng thái gói sống trong cơ sở dữ liệu của mình, không tin client [S6]. Skill còn viết "hủy gói phải một cú nhấp; thanh toán khó hủy là một trong những phàn nàn hàng đầu về hầu hết ứng dụng, và ở nhiều nơi là bất hợp pháp" [S6]. Danh sách kiểm bảo mật có 9 mục (người viết đếm): bí mật trong biến môi trường, kiểm tra đầu vào phía máy chủ, kiểm quyền trên mọi đọc và ghi (thử bằng người dùng thứ hai), giới hạn tần suất, xác minh chữ ký webhook, giới hạn tải lên, không để dữ liệu người dùng trong URL hay log, kiểm tra phụ thuộc, và chính sách riêng tư liệt kê mọi bên xử lý [S6]. Với tích hợp Google Calendar, skill cảnh báo phải qua xác minh OAuth của Google trước khi ra công chúng và mất nhiều tuần, nên bắt đầu sớm [S6].

**test** có một luật gốc: kiểm bản sao của mình, không bao giờ dồn tải, fuzz hay "đập" máy chủ của ứng dụng gốc; dùng bản gốc bằng tay như người dùng thường thì được [S7]. Kế hoạch kiểm thử sinh từ các luồng trong recon, mỗi luồng có đường vui, trường hợp biên và trường hợp tiêu cực, đánh số kiểu F01-H1, F01-E3, F01-N2 [S7]. Danh sách biên gồm đầu vào rỗng hoặc rất dài, emoji và dấu, hai tab cùng lúc, bấm đúp nút gửi, nút quay lại giữa luồng, mất mạng, phiên hết hạn, dữ liệu của người dùng khác (phải vô hình), múi giờ và giờ mùa hè, màn hình hẹp, chỉ dùng bàn phím [S7]. Tự động hóa bằng Playwright, một tệp mỗi luồng, chọn phần tử theo vai trò và nhãn chứ không theo class CSS, thêm kiểm lỗi console, lỗi 5xx và quét trợ năng bằng axe [S7] [S26]. Lỗi xếp bốn mức S1 đến S4; chỉ báo lỗi đã tái hiện, còn "có thể là lỗi" vào danh sách riêng; sửa theo vòng viết test hỏng trước, sửa, giữ test [S7].

**diff** nói thẳng "tương đồng nghĩa là làm cùng việc, không phải trông giống nhau", và cố ý bỏ qua màu vì `brand` sẽ đổi mọi màu [S8]. Nó có ba phép đo: điểm tính năng từ `parity.py`, điểm bố cục từ `imgdiff.py`, và so sánh hành vi bằng tay (số lần bấm, xử lý lỗi, thứ được nhớ giữa các lần, email nhận được) [S8]. Phán quyết ba mức: **không thể phát hành** nếu thiếu must-have hoặc còn lỗi S1; **có thể phát hành** nếu xong mọi must-have, điểm tính năng từ 80, không còn S1 hoặc S2; **tốt hơn bản gốc** nếu có thêm các bản sửa từ `entrepreneur`, và README viết rằng đó là mục tiêu vì "bản sao y nguyên không có lý do tồn tại" [S1] [S8]. Dặn thêm: "bản sao đạt 62% thì là 62%" [S8].

## Entrepreneur: đọc đánh giá thật

Đây là skill mà README đặt thành điểm bán: một bản sao thẳng không có lý do tồn tại, nên skill tìm lý do bằng cách đọc người dùng của bản gốc nói gì bằng lời của họ [S1] [S9]. Luật "không thương lượng": không bịa đánh giá, trích dẫn, điểm, số lượng hay nguồn (có 14 đánh giá thì nói 14); mọi trích dẫn nguyên văn và có đường dẫn; đọc chứ không cào; không bao giờ tạo đánh giá giả (skill nêu quy định năm 2024 của FTC Mỹ); và người đánh giá không phải lời chứng thực cho sản phẩm của mình [S9].

Quy trình: thu thập từ 100 đánh giá trở lên qua ít nhất ba nguồn (App Store, Google Play, G2, Capterra, Trustpilot, Reddit, Hacker News, bảng yêu cầu tính năng của chính ứng dụng, nhật ký thay đổi), mỗi hàng `source,url,date,rating,text` với văn bản chép đúng nguyên văn, đọc cả đánh giá 3 và 4 sao vì "yêu mà..." là nơi giấu các bản sửa tốt nhất [S9]. Sau đó chạy `reviews.py` để xếp hạng, rồi viết ba danh sách: *điều họ ghét*, *điều còn thiếu*, *điều chưa ai giải* (những công việc hay nhóm người mà ứng dụng bỏ qua, và đây thành định vị) [S9]. Kết thúc là kế hoạch sửa 5 đến 8 mục theo "bằng chứng nhân với độ rẻ khi sửa" và ba phương án định vị theo mẫu "Dành cho ai, ghét điều gì, sản phẩm làm gì thay vào đó, bằng chứng bao nhiêu đánh giá, bao nhiêu nguồn" [S9].

Phần công cụ xem ở mục sau. Một điểm cần biết: skill cấm cào các cửa hàng và trang đánh giá có điều khoản cấm, nhưng cho phép nguồn công khai chính thức trong phạm vi điều khoản: nguồn cấp RSS đánh giá của Apple, API tìm kiếm của Hacker News qua Algolia, và API chính thức của Reddit [S9].

## Brand, launch, deploy: từ bản sao thành sản phẩm riêng

**brand** mở đầu: "không gì được ra mắt dưới danh tính của bản gốc" [S10]. Quy trình sáu bước: tạo 20 tên ứng viên theo nhiều kiểu rồi lọc còn 5, chạy (chứ không giả định) kiểm tra nhãn hiệu Mỹ, EU, Canada, toàn cầu, tên miền, cửa hàng ứng dụng, tài khoản mạng xã hội, tìm web; dựng bảng màu mới thuộc họ màu khác bản gốc và chạy lại `contrast.py`; viết bản mô tả logo (không phải logo) với điều kiện không giống nhãn hiệu gốc; viết giọng thương hiệu và viết lại 10 chuỗi hiển thị nhiều nhất; cuối cùng chạy `sweep.py` đến khi sạch [S10]. Skill ghi rõ các kiểm tra này là sàng lọc, không phải thẩm định pháp lý, và khuyên nhờ luật sư nhãn hiệu trước khi tốn tiền cho tên [S10].

**launch** viết trang đích dựng quanh định vị, định giá và tin đăng cửa hàng [S11]. Luật: không bằng chứng giả (không lời chứng, số người dùng, điểm sao hay logo "được tin dùng" bịa; một mục bằng chứng trống còn hơn một mục giả), không dùng lời người đánh giá làm lời chứng, và tên ứng dụng gốc không xuất hiện trong tên, tin đăng, từ khóa hay quảng cáo [S11]. Phần giá yêu cầu bảng so với trang giá công khai của bản gốc kèm ngày đọc, vì giá thay đổi; tối đa ba gói; sửa ngay trong sản phẩm các phàn nàn về thanh toán (hủy một cú nhấp, email gia hạn rõ ràng, không tăng giá theo ghế đột ngột) [S11]. Skill cũng nhắc hướng dẫn 4.1 (sao chép) của App Review: ứng dụng chỉ sao chép hoặc sửa nhẹ tên hay giao diện của ứng dụng nổi tiếng sẽ bị từ chối, nên các bản sửa và thương hiệu riêng phải lộ rõ ở ảnh chụp và những dòng đầu của mô tả [S11].

**deploy** có ba luật: không gì lên mạng khi người dùng chưa nói "đi"; người dùng tự mua tên miền, tự nhập thẻ, tự gõ mật khẩu, còn Claude viết bản ghi DNS, tên biến và lệnh; và không triển khai khi chưa đổi thương hiệu, tức `sweep.py` phải sạch, "không ngoại lệ" [S12]. Bước kiểm trước khi triển khai gồm năm lệnh (bộ Playwright, `parity.py`, `sweep.py`, `listing.py` nếu lên cửa hàng, và `npm run build`) cộng các kiểm tay như chính sách riêng tư, xóa tài khoản thật sự xóa, favicon và ảnh OG là của mình [S12]. Phần dịch vụ sản xuất: dự án cơ sở dữ liệu riêng cho sản xuất có sao lưu, Stripe chuyển sang chế độ thật rồi mua thử một lần và hoàn tiền, thêm miền sản xuất vào mọi URL chuyển hướng OAuth, xác thực miền gửi email [S12]. Bảng DNS gồm bản ghi A, CNAME `www`, TXT xác minh, cùng SPF, DKIM và DMARC bắt đầu ở `p=none` rồi siết dần [S12]. Tệp mẫu `preflight.md` biến đó thành danh sách đánh dấu với các nhóm Preflight, Production, Domain, Watch [S25].

## Sáu công cụ Python

Tất cả là thư viện chuẩn. Người viết đếm các dòng `import` ở đầu tệp của sáu công cụ: chỉ có `argparse`, `csv`, `datetime`, `json`, `math`, `os`, `re`, `struct`, `sys`, `unicodedata`, `zlib` (cho ảnh PNG), không có mô-đun mạng nào, khớp với câu README "không cái nào chạm mạng" [S1] [S13] [S14] [S15] [S16] [S17] [S18].

**`parity.py`** (228 dòng) đọc `features.csv` và tính điểm với trọng số must 3, should 2, could 1; `yes` được 1, `partial` được 0,5, `no` được 0; hàng `skip` và hàng có `original` là `no` (tính năng mình thêm) bị loại khỏi điểm và liệt kê riêng, nên con số chỉ đo độ tương đồng [S13]. Với `--visual`, điểm tổng là 80% tính năng cộng 20% bố cục, và có `--fail-under`; thoát mã 2 khi lỗi ma trận [S13]. Kết quả in ra điểm, số must-have xong, điểm từng khu vực yếu nhất trước, và danh sách còn thiếu theo thứ tự cần dựng; nếu còn must-have chưa xong thì in "chưa thể phát hành" [S13].

**`imgdiff.py`** (456 dòng) tự đọc PNG 8 và 16 bit không cần thư viện ngoài, từ chối PNG xen kẽ (interlaced) kèm thông báo [S14]. Chế độ `layout` (mặc định) đổi hai ảnh thành bản đồ cạnh, cắt thành lưới và so mật độ cạnh từng ô, chỉ tính ô có nội dung ở ít nhất một ảnh, nên lề trống không làm đẹp điểm; tham số mặc định trong hàm `compare` là rộng 480, 12 cột, dung sai 24, ngưỡng cạnh 40 [S14]. Phán quyết theo điểm: từ 90 là "khớp", từ 75 là "gần", từ 50 là "một phần", dưới đó là "khác" [S14]. Chế độ `pixel` dành để so bản của chính mình giữa hai thời điểm, không phải để đuổi theo điểm ảnh của bản gốc [S8] [S14]. Chiều cao khác nhau được báo cáo chứ không giấu [S14].

**`reviews.py`** (311 dòng) loại hàng không có đường dẫn `http` hoặc không có văn bản và đếm số bị loại; loại trùng theo văn bản đã chuẩn hóa [S15]. Trọng số một đánh giá là (6 trừ số sao) chia 5: 1 sao được 1,0, 5 sao được 0,2, chưa có sao được 0,6; đánh giá cũ hơn 18 tháng (mặc định, đổi được bằng `--months`) bị giảm một nửa [S15]. Một chủ đề bị đánh dấu "mỏng" nếu có dưới 3 đánh giá hoặc dưới 2 nguồn [S15]. Mỗi trích dẫn in ra là câu đầu tiên khớp mẫu của đúng dòng người dùng cung cấp, kèm đường dẫn; đánh giá một hai sao không khớp chủ đề nào được liệt kê riêng để người dùng đọc tay [S15]. Tệp `themes.json` có 16 chủ đề (người viết đếm): 12 loại phàn nàn (giá, thanh toán, lỗi, chậm, mất dữ liệu, khó dùng, hỗ trợ, tài khoản, thông báo, quảng cáo, cập nhật làm tệ đi, quyền riêng tư) và 4 loại yêu cầu (tích hợp, nền tảng, tùy biến, cộng tác), cùng 13 mẫu "yêu cầu" như "i wish" hay "please add" [S24].

**`sweep.py`** (177 dòng) tìm tên, miền và màu của bản gốc trong nội dung lẫn tên tệp; tên khớp không phân biệt hoa thường kể cả bên trong định danh (ví dụ `CalendlyButton`), màu khớp cả dạng ngắn (`#06f` khớp `#0066ff`); bỏ qua `.git`, `node_modules`, thư mục dựng, tệp khóa, tệp nhị phân và thư mục `replica/` (nơi tên gốc hợp lệ nằm); thoát mã 1 nếu còn sót [S16].

**`listing.py`** (181 dòng) kiểm giới hạn cửa hàng: App Store tên 30, phụ đề 30, văn bản quảng bá 170, từ khóa 100, mô tả 4.000, "có gì mới" 4.000; Google Play tiêu đề 30, mô tả ngắn 80, mô tả đầy đủ 4.000 [S17]. Nó đếm ký tự như người đếm (emoji ghép là một), cảnh báo tuyên bố xếp hạng và giá trong trường ngắn, emoji, ký tự từ khóa phí phạm, và bất kỳ tên nào trong danh sách `avoid` xuất hiện ở bất cứ đâu trong tin đăng; thoát mã 1 khi có lỗi, mã 0 khi chỉ có cảnh báo [S17] [S11].

**`contrast.py`** (152 dòng) đã mô tả ở trên [S18].

## Ranh giới pháp lý và đạo đức mà repo tự đặt

README có mục "Fine print" nói bản dựng lại *chức năng và mẫu trải nghiệm* theo kiểu clean room, không bao giờ chép mã nguồn, tài sản độc quyền, logo, nhãn hiệu, câu chữ hay API riêng của mục tiêu; chỉ đọc những gì được phép đọc; luôn đổi thương hiệu trước khi ra mắt; "nhân bản bất kỳ ứng dụng nào" nghĩa là tính năng và luồng, không phải nội dung, mạng lưới hay giấy phép mà ứng dụng sở hữu [S1]. Mục cuối khuyên chạy các kiểm tra nhãn hiệu, đọc điều khoản của mọi thứ đã dùng, và hỏi luật sư trước khi ra mắt nếu có tiền ở trong cuộc, và nói rõ "đây không phải tư vấn pháp lý" [S1].

Suy luận: những luật này được lặp lại ở nhiều skill (recon, build, design, backend, test, launch, deploy) chứ không chỉ ở README, tức phần lớn skill tự mang ràng buộc của mình nếu người dùng chỉ dán một `SKILL.md` vào cuộc trò chuyện, điều mà README cho phép ("không có Claude Code thì dán một `SKILL.md` ở đầu cuộc trò chuyện, mất công cụ Python nhưng phương pháp vẫn chạy") [S1] [S2] [S5] [S6] [S7] [S11] [S12].

## Phản biện

1. **"Miễn phí, không đăng ký, không khóa API" chỉ đúng cho bộ skill.** Chính `architect`, `backend` và `deploy` đặt Stripe, Supabase hoặc Neon, Resend, Vercel, miền, và tài khoản nhà phát triển của Apple (99 đô la một năm) và Google (25 đô la một lần) lên đường đi [S3] [S6] [S12]. README thực ra nói "không đăng ký, không khóa API" về chính bộ skill [S1]; người đọc cần tách hai tầng.
2. **Phần lớn là văn bản hướng dẫn, ít phần kiểm chứng được.** Người viết đếm: 7.539 từ của repo là văn bản `SKILL.md`; hành vi của chúng phụ thuộc mô hình làm theo. Chỉ sáu công cụ Python có test [S22]. Suy luận: chất lượng cuối cùng phụ thuộc vào việc Claude có tuân thủ luật khi chạy, điều repo không đo.
3. **Bài kiểm thử cấu trúc kiểm tên, không kiểm hiệu quả.** `test_repo.py` kiểm có đúng 11 thư mục skill, phần đầu tệp có `name` và mô tả đủ dài, tệp `plugin.json` trỏ về gốc, README còn nguyên một số câu cố định (tên hàm test là "reel copy") và không tệp nào chứa dấu gạch dài [S22]. Suy luận: bài này ghim nội dung README theo một bản chữ có sẵn (người viết đoán là chữ cho video ngắn), nên sửa README là phải sửa cả test.
4. **`sweep.py` chỉ bắt thứ bạn khai báo.** Công cụ tìm tên, miền, màu trong các danh sách `avoid`, `domains`, `colors`; nó không phát hiện cấu trúc, bố cục hay câu chữ giống bản gốc [S16]. Suy luận: phần "đã đổi hết" thật sự vẫn dựa vào kiểm tra bằng mắt mà `brand` dặn thêm (favicon, tiêu đề trang, email, ảnh OG, biểu tượng ứng dụng) [S10].
5. **Ngưỡng nguồn của `reviews.py` thấp hơn lời khuyên của skill.** Skill khuyên 100 đánh giá từ ít nhất ba nguồn, còn công cụ chỉ đánh dấu "mỏng" khi dưới 3 đánh giá hoặc dưới 2 nguồn [S9] [S15]. Một chủ đề có hai nguồn không bị gắn "mỏng" dù mẫu nhỏ; người dùng phải tự nhớ nêu cỡ mẫu, điều `fixes.md` yêu cầu [S9].
6. **Một đánh giá có thể tính vào nhiều chủ đề.** Vòng lặp trong `analyse` cộng trọng số cho mọi chủ đề mà đánh giá khớp, không dừng ở chủ đề đầu tiên, nên tổng điểm các chủ đề không phải số đánh giá riêng biệt [S15]. Suy luận: điểm chỉ dùng để xếp hạng, không nên cộng lại.
7. **`imgdiff.py` chỉ đọc PNG.** Ảnh chụp ở định dạng khác hoặc PNG xen kẽ phải chuyển trước; văn bản skill `diff` chỉ minh họa bằng tệp `.png`, còn việc từ chối PNG xen kẽ nằm ở phần mô tả đầu tệp công cụ [S8] [S14].
8. **Nhãn "clean room" là cam kết quy trình, không phải bảo đảm pháp lý.** README tự nói phải hỏi luật sư [S1]. Một bản sao giữ nguyên luồng và bố cục có thể vẫn gặp vấn đề trade dress mà `design` nhắc tới nhưng không có công cụ nào kiểm [S4].

## Điều cần nhớ

- Đây là **chuỗi mười một skill** đọc và ghi trong thư mục `replica/`, từ đọc ứng dụng gốc đến triển khai trên miền riêng [S1] [S2] [S12].
- `features.csv` là xương sống: mọi bước chạm vào nó, và `parity.py` biến nó thành một con số có trọng số 3, 2, 1 [S13] [S23].
- Mỗi skill mở bằng luật: chỉ nguồn công khai, không chép mã hay tài sản, không bịa trích dẫn, Claude không tự đăng ký hay nhập thẻ [S2] [S5] [S6] [S9] [S12].
- `entrepreneur` là phần khác biệt: ba danh sách (ghét, thiếu, chưa ai giải) từ đánh giá có đường dẫn, xếp hạng bằng mã chứ không bằng cảm nhận [S9] [S15].
- Sáu công cụ chỉ dùng thư viện chuẩn và có 57 hàm test; còn mười một `SKILL.md` thì chỉ được kiểm về hình thức [S22].
- "Miễn phí" là bộ skill; dịch vụ ở phía sau thì không, và chưa phải tư vấn pháp lý [S1] [S6] [S12].

## Lưu ý

- **Phạm vi đọc.** Bản clone nông (`--depth 1`) ở commit `77c9436fb3d18c3d58169efb8caf4fe906b0dc51` (03/10/2026). Cả 39 tệp được mở hoặc đếm; sáu tệp Python công cụ được đọc phần đầu mô tả và các hàm chính, không đọc từng dòng; các tệp test chỉ đếm số hàm và đọc `test_repo.py`. Bài không nêu số sao, số fork, issue hay lịch sử phát hành.
- **Chưa chạy.** Người viết không cài plugin, không chạy skill hay công cụ nào, không chạy test: mọi hành vi là "đọc mã, chưa chạy". Yêu cầu Python 3.8 trở lên lấy từ README, người viết không kiểm.
- **Cách đếm.** Số tệp và byte: `git ls-files` rồi cộng kích thước. Số từ: đếm theo khoảng trắng. Số dòng: đếm dòng của từng tệp Python. Số hàm test: đếm dòng bắt đầu bằng `def test_` trong `tests/test_*.py`. Chủ đề, mẫu yêu cầu và hàng ma trận: đọc JSON và CSV bằng script. Danh sách import: đọc các dòng `import` và `from` ở đầu tệp của sáu công cụ.
- **Giấy phép.** `LICENSE` ghi MIT, "Copyright (c) 2026 Jake Schincariol".
- **Trích dẫn.** Các câu trong ngoặc kép lấy từ README và `SKILL.md`, dịch sang tiếng Việt; người viết không kiểm các quy định pháp luật (như quy tắc của FTC) hay chính sách cửa hàng mà skill nhắc tới.
- **Tính chất.** Đây là tài liệu hỗ trợ đọc repo, không phải khuyến nghị cài đặt hay lời khuyên pháp lý. Nội dung `SKILL.md` là chỉ dẫn cho một mô hình; trong bài này nó chỉ là đối tượng để mô tả, không phải lệnh cho người đọc.

## Nguồn tham khảo

- [S1] [Jakeschincariol, README.md](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/README.md): giới thiệu, chuỗi mười một bước, công cụ, fine print, 2026
- [S2] [Jakeschincariol, replica-recon/SKILL.md](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-recon/SKILL.md): chín bước đọc ứng dụng gốc, 2026
- [S3] [Jakeschincariol, replica-architect/SKILL.md](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-architect/SKILL.md): công nghệ, lược đồ, API, thứ tự dựng, 2026
- [S4] [Jakeschincariol, replica-design/SKILL.md](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-design/SKILL.md): hệ thống thiết kế và token, 2026
- [S5] [Jakeschincariol, replica-build/SKILL.md](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-build/SKILL.md): dựng từng màn hình, clean room, 2026
- [S6] [Jakeschincariol, replica-backend/SKILL.md](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-backend/SKILL.md): đăng nhập, cơ sở dữ liệu, thanh toán, bảo mật, 2026
- [S7] [Jakeschincariol, replica-test/SKILL.md](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-test/SKILL.md): kế hoạch kiểm thử, Playwright, báo lỗi, 2026
- [S8] [Jakeschincariol, replica-diff/SKILL.md](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-diff/SKILL.md): điểm tương đồng và phán quyết, 2026
- [S9] [Jakeschincariol, replica-entrepreneur/SKILL.md](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-entrepreneur/SKILL.md): đọc đánh giá thật, ba danh sách, định vị, 2026
- [S10] [Jakeschincariol, replica-brand/SKILL.md](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-brand/SKILL.md): đặt tên, bảng màu, giọng, quét thương hiệu, 2026
- [S11] [Jakeschincariol, replica-launch/SKILL.md](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-launch/SKILL.md): trang đích, giá, tin đăng cửa hàng, 2026
- [S12] [Jakeschincariol, replica-deploy/SKILL.md](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-deploy/SKILL.md): kiểm trước, dịch vụ sản xuất, DNS, theo dõi, 2026
- [S13] [Jakeschincariol, replica-diff/parity.py](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-diff/parity.py): điểm tương đồng tính năng, 2026
- [S14] [Jakeschincariol, replica-diff/imgdiff.py](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-diff/imgdiff.py): so ảnh chụp theo bố cục, 2026
- [S15] [Jakeschincariol, replica-entrepreneur/reviews.py](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-entrepreneur/reviews.py): xếp hạng phản hồi, 2026
- [S16] [Jakeschincariol, replica-brand/sweep.py](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-brand/sweep.py): quét thương hiệu còn sót, 2026
- [S17] [Jakeschincariol, replica-launch/listing.py](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-launch/listing.py): kiểm tin đăng cửa hàng, 2026
- [S18] [Jakeschincariol, replica-design/contrast.py](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-design/contrast.py): độ tương phản WCAG của token, 2026
- [S19] [Jakeschincariol, .claude-plugin/plugin.json](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/.claude-plugin/plugin.json): khai báo plugin, phiên bản, giấy phép, 2026
- [S20] [Jakeschincariol, .claude-plugin/marketplace.json](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/.claude-plugin/marketplace.json): khai báo marketplace, 2026
- [S21] [Jakeschincariol, LICENSE](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/LICENSE): giấy phép MIT, 2026
- [S22] [Jakeschincariol, tests/test_repo.py](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/tests/test_repo.py): kiểm cấu trúc repo, 2026
- [S23] [Jakeschincariol, replica-recon/features.csv](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-recon/features.csv): ma trận tính năng mẫu, 2026
- [S24] [Jakeschincariol, replica-entrepreneur/themes.json](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-entrepreneur/themes.json): chủ đề phản hồi và mẫu yêu cầu, 2026
- [S25] [Jakeschincariol, replica-deploy/preflight.md](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-deploy/preflight.md): danh sách kiểm triển khai, 2026
- [S26] [Jakeschincariol, replica-test/e2e.example.spec.ts](https://github.com/Jakeschincariol/replica-skill/blob/77c9436fb3d18c3d58169efb8caf4fe906b0dc51/replica-test/e2e.example.spec.ts): ví dụ Playwright kèm axe, 2026
