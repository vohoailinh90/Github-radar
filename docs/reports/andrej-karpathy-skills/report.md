---
id: R09
title: Karpathy Skills: bốn nguyên tắc trong một tệp
topic: ky-thuat
date: 2026-10-31
---
# Karpathy Skills: bốn nguyên tắc trong một tệp

## Tóm tắt

Repo này là gì, dùng thế nào, và có gì để học? README mô tả đây là "một tệp `CLAUDE.md` duy nhất" nhằm cải thiện hành vi của Claude Code, rút từ những quan sát của Andrej Karpathy về lỗi khi mô hình viết mã [S1]. Nội dung thực chất là **bốn nguyên tắc ứng xử** viết thành chỉ dẫn cho agent: nghĩ trước khi viết mã, giữ mã đơn giản, sửa đúng chỗ cần sửa, và đặt mục tiêu kiểm chứng được [S2] [S3]. Cùng một nội dung được đóng gói ba kiểu: tệp `CLAUDE.md` cho từng dự án, một skill cho plugin Claude Code, và một quy tắc `.mdc` cho Cursor [S2] [S3] [S4] [S7] [S8]. Repo không chứa mã chương trình nào cần chạy; chỉ có Markdown, JSON và một tệp quy tắc.

Bài đọc repo theo ba tầng. Tầng một là bản đồ: bốn nguyên tắc nói gì và mỗi nguyên tắc chữa lỗi nào [S1] [S2]. Tầng hai là cách đóng gói và sử dụng: ba bản sao nội dung, hai cách cài đặt, và chín ví dụ "sai và đúng" trong `EXAMPLES.md` [S5] [S6] [S7] [S8]. Tầng ba là phản biện: tên repo, giấy phép, và chuyện bộ nguyên tắc này chưa có phép đo nào [S1] [S7].

Mỗi khẳng định mang một trong ba nhãn. **Nguồn: repo** nghĩa là đọc trực tiếp từ một tệp ở commit `2c60614` (20/04/2026, nhánh mặc định). **Người viết đếm** là con số tính bằng lệnh trên bản đã tải; các lệnh nằm ở mục Lưu ý. **Suy luận** là nhận định của người viết, không phải điều repo tuyên bố. Người viết không cài plugin và không chạy thử với agent nào; mọi mô tả hành vi là "đọc mã, chưa chạy".

Ba ý đáng mang theo. Thứ nhất, bộ nguyên tắc ngắn đến mức đọc hết trong vài phút: phần cốt lõi chỉ khoảng 360 từ (người viết đếm) [S2]. Thứ hai, các nguyên tắc đều có "phép thử" cụ thể (ví dụ "mỗi dòng đổi phải truy ra được yêu cầu của người dùng"), nên dùng được làm tiêu chí review diff [S2]. Thứ ba, repo **không có bằng chứng đo được** rằng chúng giúp ích; phần "cách biết nó có tác dụng" chỉ là bốn dấu hiệu định tính [S1].

## Hồ sơ nhanh

| Mục | Giá trị | Nhãn |
|---|---|---|
| Là gì | Bốn nguyên tắc ứng xử cho agent lập trình, đóng gói thành `CLAUDE.md`, skill và quy tắc Cursor | Nguồn: repo [S1] [S2] [S3] [S4] |
| Phiên bản | 1.0.0 (plugin và marketplace) | Nguồn: repo [S7] [S8] |
| Giấy phép | MIT, ghi trong README, `plugin.json` và phần đầu `SKILL.md`; không có tệp `LICENSE` | Nguồn: repo [S1] [S3] [S7]; người viết đếm |
| Quy mô | 9 tệp, 37.694 byte | Người viết đếm |
| Phần cốt lõi | 358 từ (`CLAUDE.md`), 371 từ (`SKILL.md`), 393 từ (`.mdc`) | Người viết đếm |
| Ví dụ | 9 ví dụ, mỗi ví dụ một cặp sai và đúng | Người viết đếm [S6] |
| Ngôn ngữ | README tiếng Anh và bản dịch tiếng Trung giản thể | Nguồn: repo [S1] [S9] |
| Số sao | Bài này không nêu: nguồn duy nhất là tệp ở commit đã ghim | Giới hạn của bài |

## Bốn nguyên tắc

README mở đầu bằng ba đoạn trích từ một bài đăng của Karpathy, tóm tắt vấn đề: mô hình tự đưa ra giả định thay người dùng rồi chạy tiếp mà không kiểm tra; thích làm phức tạp mã và API, phình trừu tượng, "viết 1000 dòng khi 100 dòng là đủ"; và đôi khi sửa hoặc xóa chú thích và mã mà nó chưa hiểu hết, dù không liên quan tới việc được giao [S1]. Người viết không mở bài đăng gốc; các trích dẫn chỉ được tin theo lời README. Bốn nguyên tắc sau đây đáp lại từng lỗi đó [S1] [S2].

**1. Nghĩ trước khi viết mã** (Think Before Coding). Khẩu hiệu: không giả định, không giấu sự bối rối, nêu rõ các đánh đổi. Cụ thể: nêu giả định ra, nếu không chắc thì hỏi; nếu có nhiều cách hiểu thì trình bày chứ không chọn lặng lẽ; nếu có cách đơn giản hơn thì nói và phản biện khi cần; nếu chỗ nào chưa rõ thì dừng, gọi tên cái đang mơ hồ và hỏi [S2].

**2. Đơn giản trước tiên** (Simplicity First). Lượng mã tối thiểu giải được bài toán, không thêm gì mang tính suy đoán: không tính năng ngoài yêu cầu, không trừu tượng cho mã dùng một lần, không "linh hoạt" hay "cấu hình được" mà không ai đòi, không xử lý lỗi cho tình huống không thể xảy ra; và nếu viết 200 dòng mà có thể là 50 thì viết lại. Phép thử là hỏi liệu một kỹ sư senior có bảo "quá phức tạp" không [S2].

**3. Thay đổi như phẫu thuật** (Surgical Changes). Khi sửa mã có sẵn: không "cải thiện" mã, chú thích hay định dạng kế bên; không refactor chỗ chưa hỏng; theo kiểu của mã sẵn có dù bạn sẽ làm khác; thấy mã chết không liên quan thì chỉ nhắc, không xóa. Khi thay đổi của bạn tạo ra phần mồ côi (import, biến, hàm bỏ không), hãy xóa phần đó; còn mã chết có từ trước thì để nguyên trừ khi được yêu cầu. Phép thử: mỗi dòng đã đổi phải truy được tới yêu cầu của người dùng [S2].

**4. Thực thi theo mục tiêu** (Goal-Driven Execution). Đặt tiêu chí thành công và lặp tới khi kiểm chứng được. Ba phép biến đổi mẫu: "thêm validation" thành "viết test cho đầu vào sai rồi làm cho chúng qua"; "sửa lỗi" thành "viết test tái hiện lỗi rồi làm cho nó qua"; "refactor X" thành "bảo đảm test qua trước và sau". Với việc nhiều bước, nêu kế hoạch ngắn dạng `bước → kiểm: cách kiểm`. Tiêu chí mạnh cho phép agent tự lặp; tiêu chí yếu như "làm cho nó chạy" đòi hỏi hỏi lại liên tục [S2].

Có một **ghi chú đánh đổi** (đứng đầu `CLAUDE.md`, và gần cuối README): các nguyên tắc nghiêng về cẩn thận hơn là nhanh, và với việc nhỏ (sửa lỗi chính tả, một dòng hiển nhiên) thì tự phán đoán, vì không phải thay đổi nào cũng cần đủ độ nghiêm ngặt [S1] [S2]. Suy luận: repo không định nghĩa "việc nhỏ" ở đâu là ranh giới, nên chính agent phải tự đoán, và đó là chỗ nguyên tắc 1 ("hỏi khi chưa rõ") và ghi chú này có thể kéo ngược nhau.

## Chín ví dụ trong EXAMPLES.md

`EXAMPLES.md` (khoảng 1.860 từ, người viết đếm) minh họa bốn nguyên tắc bằng 9 ví dụ, mỗi cái có một khối "❌ Mô hình hay làm" và một khối "✅ Nên làm" [S6]:

- **Nghĩ trước khi viết mã (2 ví dụ):** yêu cầu "thêm tính năng xuất dữ liệu người dùng" bị hiểu ngầm là xuất tất cả người dùng, chọn sẵn tệp và trường; yêu cầu "làm cho tìm kiếm nhanh hơn" có thể là độ trễ, thông lượng hay cảm nhận. Cách đúng là liệt kê các cách hiểu và hỏi [S6].
- **Đơn giản trước tiên (2 ví dụ):** hàm tính giảm giá bị bọc trong mẫu Strategy kèm cấu hình, tốn hơn 30 dòng chỉ để thiết lập; và một ví dụ về tính năng suy đoán [S6].
- **Thay đổi như phẫu thuật (2 ví dụ):** sửa một lỗi nhưng tiện tay refactor; và trôi kiểu mã (đổi nháy, thêm gợi ý kiểu) khi sửa lỗi [S6].
- **Thực thi theo mục tiêu (3 ví dụ):** "sửa hệ thống xác thực" mơ hồ so với mục tiêu kiểm chứng được; kế hoạch nhiều bước có điểm kiểm; và kiểm chứng theo kiểu test trước [S6].

Cuối tệp là bảng "Anti-Patterns Summary" bốn dòng và một phần "Key Insight": các bản "quá phức tạp" không hề sai về hình thức, vì chúng theo đúng mẫu thiết kế; vấn đề là **thời điểm**, thêm độ phức tạp trước khi cần, khiến mã khó hiểu hơn, dễ lỗi hơn và chậm hơn; mã tốt là mã giải bài toán hôm nay một cách đơn giản chứ không giải bài toán ngày mai quá sớm [S6]. Các con số như "ước tính 2 giờ" hay "~500ms" trong ví dụ là minh họa tự đặt, không phải số đo [S6] (suy luận).

## Ba bản sao một nội dung

Cùng một bộ bốn nguyên tắc nằm ở ba tệp: `CLAUDE.md` [S2], `skills/karpathy-guidelines/SKILL.md` [S3] và `.cursor/rules/karpathy-guidelines.mdc` [S4]. Người viết so sánh bằng script: ba tệp có cùng bốn đề mục `##` theo cùng thứ tự, và phần thân từ mục 1 trở đi giống nhau từng ký tự giữa `CLAUDE.md` và `SKILL.md`, cũng như giữa `.mdc` và `CLAUDE.md` (người viết đếm). Khác biệt chỉ nằm ở phần đầu: `SKILL.md` có frontmatter `name`, `description`, `license: MIT`; `.mdc` có `description` và `alwaysApply: true`; `CLAUDE.md` mở bằng tiêu đề và câu giới thiệu [S2] [S3] [S4].

`CURSOR.md` ghi rõ hệ quả cho người bảo trì: khi đổi bốn nguyên tắc phải giữ `CLAUDE.md` và quy tắc `.mdc` đồng bộ, và cập nhật cả `SKILL.md` nếu muốn bản skill đã phát hành khớp [S5]. Suy luận: đây là ba nguồn sự thật phải sửa tay cùng lúc, không có script hay kiểm tra tự động nào trong repo bảo đảm chúng không lệch (người viết thấy danh sách tệp không có thư mục kiểm thử hay script).

## Cài đặt và đóng gói

**Plugin Claude Code (README khuyến nghị).** Hai lệnh trong Claude Code: thêm marketplace bằng `/plugin marketplace add forrestchang/andrej-karpathy-skills`, rồi cài bằng `/plugin install andrej-karpathy-skills@karpathy-skills` [S1]. Khai báo marketplace đặt tên và id là `karpathy-skills`, nguồn plugin là `./`, phiên bản 1.0.0, nhóm `workflow` [S8]. `plugin.json` khai báo plugin `andrej-karpathy-skills`, giấy phép MIT, và đường dẫn skill `./skills/karpathy-guidelines` [S7].

**Tệp `CLAUDE.md` cho từng dự án.** Dự án mới tải về bằng `curl -o CLAUDE.md` từ địa chỉ raw của repo; dự án có sẵn thì nối vào cuối bằng `echo` và `curl >>` [S1]. Người viết không chạy các lệnh này.

**Cursor.** Sao chép `.cursor/rules/karpathy-guidelines.mdc` vào thư mục `.cursor/rules/` của dự án khác, và `CURSOR.md` nói thẳng rằng Cursor mặc định không đọc `.claude-plugin/` hay `CLAUDE.md` [S5]. Có thêm lựa chọn tùy chọn là chép `SKILL.md` vào thư mục skill cá nhân của Cursor [S5].

**Tùy biến.** README khuyên gộp bốn nguyên tắc vào `CLAUDE.md` có sẵn và thêm phần "Project-Specific Guidelines" của riêng dự án, ví dụ dùng TypeScript chế độ strict hay mọi endpoint phải có test [S1].

## Phản biện

1. **Tên gọi và nguồn gốc.** Tên repo là `andrej-karpathy-skills`, nhưng README nói đây là hướng dẫn "Karpathy-Inspired", rút từ quan sát của ông, và tác giả repo là `forrestchang` [S1] [S8]. Repo không nói Karpathy viết hay xác nhận nó. Suy luận: tên có thể bị đọc thành bản chính chủ.
2. **"Một tệp" so với bốn đường phát hành.** README tự gọi là "một tệp `CLAUDE.md` duy nhất", trong khi repo cung cấp cả plugin, skill, quy tắc Cursor và bản dịch tiếng Trung [S1] [S9]. Phần mô tả đã lạc hậu so với nội dung.
3. **Giấy phép.** MIT được nêu ở ba nơi nhưng không có tệp `LICENSE` ở gốc; văn bản giấy phép đầy đủ không có trong repo [S1] [S3] [S7] (người viết đếm).
4. **Chưa có phép đo.** README đưa bốn dấu hiệu "đang có tác dụng" (ít thay đổi thừa trong diff, ít viết lại vì làm phức tạp, câu hỏi làm rõ đến trước khi làm, PR gọn) nhưng không có số liệu, bài kiểm thử hay so sánh trước sau [S1]. Các ví dụ là kịch bản dựng sẵn [S6].
5. **Ba bản sao phải giữ đồng bộ bằng tay** (xem trên) [S5].
6. **Ranh giới "việc nhỏ" mơ hồ.** Nguyên tắc dặn hỏi khi mơ hồ nhưng cũng dặn tự phán đoán với việc nhỏ, và không định nghĩa ranh giới [S1] [S2].
7. **Quảng bá dự án khác.** Đầu README có lời giới thiệu dự án Multica và liên kết mạng xã hội của tác giả, đặt trước nội dung [S1]. Không phải lỗi, nhưng người đọc nên biết phần đó không thuộc bộ nguyên tắc.

## Điều cần nhớ

- Đây là **một bộ bốn nguyên tắc ngắn** viết cho agent, đóng gói thành `CLAUDE.md`, skill và quy tắc Cursor có cùng nội dung [S2] [S3] [S4].
- Bốn nguyên tắc: nghĩ trước khi viết mã; đơn giản trước tiên; thay đổi như phẫu thuật; thực thi theo mục tiêu có kiểm chứng [S2].
- Mỗi nguyên tắc có một phép thử dùng được khi review diff, nổi bật nhất là "mỗi dòng đổi phải truy được tới yêu cầu" [S2].
- Chín ví dụ trong `EXAMPLES.md` là kịch bản minh họa, không phải số đo [S6].
- Chưa có bằng chứng định lượng, tên repo dễ gây hiểu nhầm về nguồn gốc, và ba bản sao phải sửa tay [S1] [S5] [S7].

## Lưu ý

- **Phạm vi đọc.** Bản clone nông (`--depth 1`) ở commit `2c606141936f1eeef17fa3043a72095b4765b9c2` (20/04/2026). Cả 9 tệp trong repo đều được mở; `README.zh.md` chỉ được đọc tiêu đề mục, và phần sau của `EXAMPLES.md` chỉ được đọc qua tiêu đề, bảng tóm tắt và phần đầu mỗi ví dụ. Bài không nêu số sao, số fork hay lịch sử issue vì chúng không nằm trong commit.
- **Chưa chạy.** Người viết không cài plugin, không thử các lệnh `curl`, không chạy agent nào với bộ nguyên tắc; mọi hành vi là "đọc mã, chưa chạy".
- **Lệnh đếm.** 9 tệp và 37.694 byte: `git ls-files | xargs wc -c`. Từ: đếm theo khoảng trắng. So sánh ba bản sao: tách phần từ mục `## 1.` đến dấu `---` đầu tiên (nếu có) và so từng ký tự. 9 ví dụ: đếm tiêu đề `### Example` và các ký hiệu ❌ và ✅ trong `EXAMPLES.md`.
- **Giấy phép.** README, `plugin.json` và `SKILL.md` ghi MIT; không có tệp `LICENSE` nên người viết không đọc được văn bản giấy phép.
- **Trích dẫn.** Các đoạn trích của Karpathy là lời README; người viết không kiểm bài đăng gốc.
- **Tính chất.** Đây là tài liệu hỗ trợ đọc repo, không phải khuyến nghị cài đặt. Nội dung `CLAUDE.md` và `SKILL.md` là chỉ dẫn cho agent; trong bài này nó chỉ là đối tượng để mô tả.

## Nguồn tham khảo

- [S1] forrestchang, README.md: giới thiệu, bốn nguyên tắc, cài đặt, phép thử, 2026, https://github.com/forrestchang/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/README.md
- [S2] forrestchang, CLAUDE.md: bốn nguyên tắc dạng tệp dự án, 2026, https://github.com/forrestchang/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/CLAUDE.md
- [S3] forrestchang, skills/karpathy-guidelines/SKILL.md: bản skill của bốn nguyên tắc, 2026, https://github.com/forrestchang/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/skills/karpathy-guidelines/SKILL.md
- [S4] forrestchang, .cursor/rules/karpathy-guidelines.mdc: quy tắc Cursor luôn bật, 2026, https://github.com/forrestchang/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/.cursor/rules/karpathy-guidelines.mdc
- [S5] forrestchang, CURSOR.md: cách dùng với Cursor và lưu ý đồng bộ, 2026, https://github.com/forrestchang/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/CURSOR.md
- [S6] forrestchang, EXAMPLES.md: chín ví dụ sai và đúng, 2026, https://github.com/forrestchang/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/EXAMPLES.md
- [S7] forrestchang, .claude-plugin/plugin.json: khai báo plugin và giấy phép, 2026, https://github.com/forrestchang/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/.claude-plugin/plugin.json
- [S8] forrestchang, .claude-plugin/marketplace.json: khai báo marketplace, 2026, https://github.com/forrestchang/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/.claude-plugin/marketplace.json
- [S9] forrestchang, README.zh.md: bản README tiếng Trung giản thể, 2026, https://github.com/forrestchang/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/README.zh.md
