---
id: R08
title: Matt Pocock Skills: 27 skill nhỏ ghép được
topic: ky-thuat
date: 2026-10-31
---
# Matt Pocock Skills: 27 skill nhỏ ghép được

## Tóm tắt

Repo này là gì, dùng thế nào, và khác các bộ quy trình lớn ở đâu? README tự giới thiệu là "bộ skill tôi dùng hằng ngày để làm kỹ thuật thật, không phải vibe coding", và đặt mình đối lập với GSD, BMAD, Spec-Kit vì những bộ đó "sở hữu quy trình" nên người dùng mất quyền kiểm soát [S1]. Về hình thức, đây là một plugin gồm 27 skill được quảng bá (mỗi skill một tệp `SKILL.md`), chia làm 16 skill do người gõ lệnh gọi và 11 skill để mô hình tự gọi, cộng 11 skill thử nghiệm hoặc ít dùng không nằm trong plugin [S1] [S4]. Cài xong, bạn chạy `/setup-matt-pocock-skills` một lần cho mỗi repo để khai báo nơi chứa issue, nhãn triage và nơi đặt tài liệu [S1].

Bài đọc repo theo ba tầng. Tầng một là bản đồ: bốn "lỗi thường gặp" của agent lập trình và skill chữa từng lỗi, rồi dòng chảy từ ý tưởng đến mã (phỏng vấn, spec, ticket, thực thi) [S1] [S20]. Tầng hai là cơ chế: vòng phỏng vấn theo "cây quyết định", ngôn ngữ chung `GLOSSARY.md`, TDD ở các "seam" đã thỏa thuận, gỡ lỗi bắt đầu bằng vòng phản hồi, review hai trục [S7] [S10] [S12] [S13] [S18]. Tầng ba là cách repo tự giữ nhất quán và những chỗ nó chưa nhất quán: quy ước gọi skill, danh sách bị từ chối, và vài chỗ README, glossary hay CLAUDE.md nói chưa khớp với chính repo [S5] [S3] [S11] [S2] [S12] [S26].

Mỗi khẳng định mang một trong ba nhãn. **Nguồn: repo** nghĩa là đọc trực tiếp từ một tệp ở commit `a496f55` (29/10/2026, nhánh `main`). **Người viết đếm** là con số tính bằng lệnh trên bản đã tải; các lệnh nằm ở mục Lưu ý. **Suy luận** là nhận định của người viết, không phải điều repo tuyên bố. Người viết không cài và không chạy plugin; mọi mô tả hành vi là "đọc mã, chưa chạy".

Ba ý đáng mang theo. Thứ nhất, phần lớn giá trị nằm ở vài **nguyên thủy nhỏ**: `grilling` (329 từ) làm lõi cho cả `grill-me` lẫn `grill-with-docs`, hai skill này chỉ dài 22 và 35 từ và chỉ gọi nó [S7] [S8] [S9]. Thứ hai, repo kỷ luật hóa cả việc **viết skill**: quy ước gọi skill bằng công cụ `Skill`, phân loại người gọi hay mô hình gọi, và bản đồ `ask-matt` phải luôn khớp [S5] [S2] [S20]. Thứ ba, tác giả **từ chối nhận skill mới** và PR từ người ngoài, nên bộ này là quan điểm của một người chứ không phải khung chung [S3] [S23] [S25].

## Hồ sơ nhanh

| Mục | Giá trị | Nhãn |
|---|---|---|
| Là gì | Plugin 27 skill đã quảng bá + 11 skill chưa quảng bá | Người viết đếm [S1] [S4] |
| Phiên bản | 1.3.2; giấy phép MIT | Nguồn: repo [S4] [S29] |
| Tác giả | Matt Pocock | Nguồn: repo [S4] |
| Gọi bởi người | 16 skill (`disable-model-invocation: true`) | Người viết đếm [S5] |
| Gọi bởi mô hình | 11 skill (người cũng gọi được) | Người viết đếm [S5] |
| Quy mô | 176 tệp; 38 tệp `SKILL.md` với 26.689 từ | Người viết đếm |
| Kích thước skill | `grill-me` 22 từ, `ask-matt` 1.952 từ, `wayfinder` 2.080 từ | Người viết đếm |
| Đóng góp | Chỉ nhận lỗi và phản hồi; không nhận skill mới; PR chỉ cho cộng tác viên | Nguồn: repo [S3] [S23] [S25] |
| Số sao | Bài này không nêu: nguồn duy nhất là tệp ở commit đã ghim | Giới hạn của bài |

## Bốn lỗi thường gặp và skill chữa từng lỗi

README tổ chức cả bộ skill quanh bốn thất bại mà tác giả thấy ở Claude Code, Codex và các agent khác [S1]:

1. **Agent không làm điều tôi muốn.** Nguyên nhân là lệch hiểu biết, nên cách chữa là một buổi "grilling": agent hỏi chi tiết trước khi làm. Skill: `/grill-me` (cho việc không phải mã) và `/grill-with-docs` [S1].
2. **Agent quá dài dòng.** Agent bị thả vào dự án và phải tự đoán biệt ngữ, nên dùng 20 chữ thay cho 1. Cách chữa là một **ngôn ngữ chung**: một tài liệu giải mã thuật ngữ của dự án. README đưa ví dụ "materialization cascade" thay cho cả một câu dài về "bài học trong một phần của khóa học được làm thật" [S1].
3. **Mã không chạy.** Cần vòng phản hồi: kiểu tĩnh, trình duyệt, test tự động. Skill: `/tdd` cho red-green và `/diagnosing-bugs` cho vòng gỡ lỗi chia pha [S1].
4. **Mã thành một cục bùn.** Agent đẩy nhanh việc viết mã nên cũng đẩy nhanh entropy. Cách chữa là quan tâm tới thiết kế: `/to-spec` hỏi bạn đang chạm vào module nào trước khi lập spec, và `/improve-codebase-architecture` khảo sát tìm cơ hội "làm sâu" module, khuyên chạy "vài ngày một lần" nhưng nói thẳng nó là "một cuộc khảo sát, không phải cứu hộ" [S1].

Mỗi lỗi đi kèm một câu trích sách kinh điển (Pragmatic Programmer, Domain-Driven Design, Extreme Programming, A Philosophy of Software Design) [S1]. Suy luận: tác giả dùng các trích dẫn này để nói rằng bộ skill không phát minh phương pháp, chỉ đóng gói các nguyên tắc cũ thành thao tác lặp lại được.

## Grilling và ngôn ngữ chung của dự án

**Nguyên thủy `grilling`.** Skill này dài 329 từ và chứa toàn bộ cơ chế phỏng vấn [S7]. Phiên phỏng vấn được xem là một **cây quyết định**: mỗi quyết định rẽ ra các quyết định phụ thuộc vào nó. Agent làm việc theo **vòng**: "frontier" là mọi quyết định mà điều kiện tiên quyết đã được giải quyết, và cả frontier được hỏi trong một vòng, đánh số, kèm **câu trả lời đề xuất** của agent. Câu hỏi phải viết sao cho "đồng ý" nghĩa là chấp nhận đề xuất [S7]. Sự kiện trong môi trường (tệp, công cụ) là việc của agent, giao cho một subagent có ngữ cảnh mới; quyết định mới là việc của người dùng. Phiên xong khi frontier rỗng, và agent không hành động cho tới khi người dùng xác nhận đã hiểu chung [S7].

**Hai lớp vỏ mỏng.** `grill-me` chỉ gồm một dòng "gọi công cụ Skill với grilling" [S8]. `grill-with-docs` gọi công cụ Skill hai lần, cho `grilling` và `domain-modeling` [S9]. Theo CLAUDE.md và README, người gọi chỉ thấy lệnh nhỏ, còn phần kỷ luật nằm ở một chỗ duy nhất (suy luận từ [S5] [S7] [S8] [S9]).

**`domain-modeling`.** Đây là kỷ luật chủ động xây mô hình miền: thách thức thuật ngữ so với `GLOSSARY.md`, làm rõ chữ mơ hồ, thử bằng tình huống cụ thể, đối chiếu với mã, và cập nhật glossary ngay khi một thuật ngữ được chốt, không gom lại [S10]. Repo nhiều ngữ cảnh dùng `GLOSSARY-MAP.md`. Glossary phải "hoàn toàn không có chi tiết cài đặt". ADR chỉ được đề nghị khi đủ ba điều: khó đảo ngược, gây bất ngờ nếu thiếu bối cảnh, và là kết quả của một đánh đổi thật [S10].

**Glossary của chính repo.** `GLOSSARY.md` của repo định nghĩa **Issue tracker**, **Issue**, **Decision ticket** và **Triage role**, và ghi các thuật ngữ đã bị bỏ như "backlog" [S11]. Đó là cách repo tự ăn món của mình (suy luận).

## Từ ý tưởng đến mã: spec, ticket, thực thi

`ask-matt` là bộ định tuyến, mô tả **một dòng chính** từ ý tưởng đến phát hành: `/grill-with-docs`, rồi tùy chọn đi vòng qua prototype (nối bằng `/handoff` hai chiều), rồi nếu việc kéo dài nhiều phiên thì `/to-spec` và `/to-tickets`, sau đó `/implement` hoặc `/implement-spec`, và cuối cùng `/retro` [S20]. Nó khuyên giữ bước 1 đến 3 trong **một cửa sổ ngữ cảnh** và nhắc tới "vùng thông minh" khoảng 150.000 token, quá đó mô hình suy luận kém đi [S20].

**`to-spec`.** Không phỏng vấn, chỉ tổng hợp từ cuộc trò chuyện. Nó phác các **seam** sẽ kiểm thử (ưu tiên seam sẵn có, lý tưởng là một), hỏi người dùng xác nhận, rồi viết spec theo mẫu bảy phần: Problem Statement, Solution, User Stories (danh sách "rất dài"), Implementation Decisions, Testing Decisions, Out of Scope, Further Notes. Spec không chứa đường dẫn tệp hay đoạn mã vì chúng nhanh lỗi thời, trừ ngoại lệ cho đoạn mã từ prototype mã hóa một quyết định chính xác hơn lời. Spec được gắn nhãn `ready-for-agent` [S14].

**`to-tickets`.** Chia thành các ticket "tracer bullet": mỗi lát cắt một đường hẹp nhưng trọn vẹn qua mọi tầng, tự kiểm được, vừa một cửa sổ ngữ cảnh. Mỗi ticket khai báo các ticket **chặn** nó. Ngoại lệ là **wide refactor**, được xếp theo kiểu expand-contract: thêm dạng mới cạnh dạng cũ, di chuyển từng lô, rồi xóa dạng cũ. Người dùng phải duyệt bản chia trước khi xuất bản [S15].

**`implement`.** Chỉ 103 từ: tải ticket, gọi `tdd` ở các seam đã thỏa thuận, chạy kiểm tra kiểu và từng tệp test thường xuyên, chạy toàn bộ test một lần cuối, gọi `code-review`, rồi commit [S16].

**`implement-spec`.** Coi các ticket như một **đồ thị tác vụ**: luôn có một frontier các ticket sẵn sàng. Mỗi ticket giao cho một subagent mới trong worktree riêng, chạy nền để tối đa hóa song song; một subagent "merger" gộp vào nhánh tích hợp; sau cùng chạy `code-review` trên nhánh tích hợp và dùng **một** subagent sửa mọi lỗi. Giao tiếp giữa các subagent dùng "con trỏ ngữ cảnh" (tới spec, ticket, ghi chú) thay vì chép lại nội dung [S17].

**`wayfinder`.** Dành cho việc lớn hơn một phiên: lập một **bản đồ** là một issue gắn nhãn `wayfinder:map`, các **decision ticket** là issue con chứa câu hỏi cần quyết. Mặc định là *lập kế hoạch, không làm*; bản đồ là mục lục, mỗi quyết định chỉ nằm ở đúng một ticket [S22].

## TDD, gỡ lỗi và review

**`tdd`.** Skill này là tài liệu tham chiếu cho vòng red-green. Bài kiểm tra tốt xác minh hành vi qua giao diện công khai, không qua chi tiết cài đặt. **Seam** là ranh giới công khai nơi test đặt; trước khi viết bất kỳ test nào, agent phải ghi lại các seam và **xác nhận với người dùng**: "không test nào được viết ở seam chưa xác nhận". Ba phản mẫu: gắn với cài đặt, **tautological** (khẳng định tự tính lại giá trị như mã), và **cắt ngang** (viết hết test rồi mới viết mã). Quy tắc: red trước green, mỗi lần một lát cắt dọc [S12].

**`diagnosing-bugs`.** Luận điểm trung tâm: "**Đây là skill**" là giai đoạn 1, xây vòng phản hồi chặt cho lỗi. Có 10 cách dựng vòng, xếp gần theo thứ tự ưu tiên (test thất bại, curl, CLI với fixture, trình duyệt headless, phát lại trace, harness tạm, fuzz, bisect, so sánh khác biệt, và cuối cùng là script cho người ngồi bấm) [S13]. Giai đoạn 1 chỉ xong khi có **một lệnh** đã chạy, "red-capable" (khẳng định đúng triệu chứng), tất định, nhanh và agent chạy được không cần người. Không có vòng thì phải dừng và nói rõ, không được đoán [S13]. Skill còn mở đầu bằng mục **Redact**: che mọi bí mật bằng `<REDACTED>` trước khi hiển thị lệnh hay đầu ra [S13].

**`code-review`.** Review diff từ một **điểm cố định** (so ba chấm với merge-base) theo hai trục: **Standards** và **Spec**, chạy ở hai subagent song song, ngữ cảnh mới, rồi tổng hợp [S18]. Trục Standards luôn mang theo "đường cơ sở mùi mã" gồm 12 mùi của Fowler (Mysterious Name, Duplicated Code, Feature Envy, Data Clumps, Primitive Obsession, Repeated Switches, Shotgun Surgery, Divergent Change, Speculative Generality, Message Chains, Middle Man, Refused Bequest); tiêu chuẩn của repo luôn thắng, và mỗi mùi chỉ là phán đoán, không phải vi phạm cứng [S18]. Mục refactor được giao cho giai đoạn review này chứ không nằm trong vòng TDD [S12] [S18].

## Thiết kế sâu, triage và bản đồ

**`codebase-design`.** Từ vựng chung cho **module sâu**: nhiều hành vi sau một giao diện nhỏ, đặt ở một seam sạch. Tám thuật ngữ: module, interface, implementation, depth, seam, adapter, leverage, locality, và lời dặn dùng chúng đúng nghĩa, không thay bằng "component", "service" hay "boundary" [S19]. `tdd` và `to-spec` mượn từ vựng này (đọc từ [S12] [S19]).

**`triage`.** Chuyển issue qua một máy trạng thái: 2 vai **phân loại** (`bug`, `enhancement`) và 5 vai **trạng thái** (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). PR ngoài được coi là "issue kèm mã". Mọi bình luận do AI đăng trong lúc triage phải mở đầu bằng một dòng tuyên bố "do AI tạo" [S21].

**Mọi thứ phải vào bản đồ.** `ask-matt` buộc các skill người gọi và quan hệ giữa chúng luôn được cập nhật: thêm, đổi tên hay xóa một skill gọi được bởi người thì phải sửa bản đồ, "không thì bộ định tuyến nói dối" [S2] [S20].

## Cách repo giữ nhất quán

**Các quy tắc trong CLAUDE.md.** Tệp `AGENTS.md` là liên kết tượng trưng tới `CLAUDE.md` (người viết kiểm bằng `ls -la`) [S2]. Các quy tắc chính [S2]:

- Skill chia theo thư mục bucket: `engineering/`, `productivity/` (được quảng bá), `misc/`, `in-progress/`, `deprecated/`.
- Skill được quảng bá phải có mặt trong README và trong mảng `skills` của `plugin.json`; skill không quảng bá thì không được xuất hiện ở cả hai.
- Mỗi skill được quảng bá có một trang tài liệu bốn mục: What it does, When to reach for it, Common questions, It's working if.
- Cấm dấu gạch ngang dài (em dash) trong văn xuôi của repo.
- Mọi skill giao việc cho subagent phải dặn bắt đầu với cửa sổ ngữ cảnh mới, vì vài harness (như Codex) mặc định fork ngữ cảnh cha.

**Phân loại gọi.** Skill người gọi dùng `disable-model-invocation: true` cho Claude Code và `policy.allow_implicit_invocation: false` trong `agents/openai.yaml` cho Codex; mô tả của chúng dành cho người đọc. Skill mô hình gọi giữ mô tả giàu cụm kích hoạt. Skill người gọi có thể gọi skill mô hình gọi, nhưng **không bao giờ** gọi được skill người gọi khác. Phụ thuộc được diễn đạt bằng câu "Call the Skill tool with ..." chứ không phải `/tên`, vì cách này "bắn trúng" nhiều hơn; công cụ nhận một skill mỗi lần gọi [S5].

**Plugin và Codex.** ADR 0002 ghi lý do giao bản plugin Claude Code trước: plugin Codex ban đầu chỉ nhận `skills` là một chuỗi đường dẫn, không chọn được tập con từ repo chia bucket. Bản cập nhật ngày 7/10/2026 của chính ADR nói ràng buộc đó không còn đúng, và đã thử cài trên Codex 0.161.0 [S6]. Đó là lý do README hiện có lệnh cài Codex [S1] [S6].

## Phạm vi và cách đóng góp

`SCOPE.md` đặt một ngưỡng kép: một ý tưởng chỉ còn mở nếu (1) mô tả một **thất bại quan sát được** trong phiên thật, và (2) hợp triết lý, không phải tùy chọn cấu hình hay chỉnh cho một người [S3]. `misc/` bị đóng băng, và đề xuất skill mới bị đóng vì "nếu hành vi ghép được từ skill sẵn có thì không được skill mới" [S3] [S23]. Nhiều thứ bị từ chối công khai trong `.out-of-scope/`, ví dụ không đặt trần số câu hỏi khi grilling vì "có kế hoạch cần ba câu, có kế hoạch cần năm mươi" [S24]. Pull request chỉ mở cho cộng tác viên; người ngoài mô tả lỗi trong issue [S25]. Một workflow đóng issue gắn `needs-info` sau 14 ngày không phản hồi [S30]. Có 9 tệp trong `.out-of-scope/` (người viết đếm).

Suy luận: đây là mô hình "một người giữ cửa" cho một catalog nhỏ. Lợi ích là catalog ngắn và nhất quán; cái giá là bạn sẽ không đẩy được skill của mình lên đây và nên fork hoặc tự viết.

## Phản biện

Các điểm dưới đây là chỗ các tệp của chính repo không khớp nhau, được báo chứ không chọn bên:

1. **"Red-green-refactor" so với "refactor không thuộc vòng".** README nói "vòng red-green-refactor là then chốt" và mô tả của `tdd` còn dùng cụm đó làm cụm kích hoạt [S1] [S12]. Nhưng thân skill nói "TDD là vòng red → green" và "refactoring không thuộc vòng", nó thuộc giai đoạn review [S12]. Tên gọi quen thuộc che đi một thiết kế khác (suy luận).
2. **"Ticket" bị tránh nhưng vẫn là tên skill.** Glossary ghi Issue với ghi chú "tránh dùng ticket", trừ khi trích hệ thống ngoài hoặc dùng cho Decision ticket [S11]. Thế nhưng skill tên `to-tickets` và `implement-spec` nói "tickets" khắp nơi [S15] [S17]. Repo không giải thích ngoại lệ này (suy luận).
3. **Cấm em dash nhưng changelog có.** CLAUDE.md liệt kê `CHANGELOG.md` trong những nơi cấm em dash [S2]; người viết đếm 68 dòng của `CHANGELOG.md` chứa ký tự đó, còn các tệp Markdown khác thì không [S26].
4. **Khoảng trống của chính `tdd`.** Trang tài liệu `docs/engineering/tdd.md` thừa nhận skill quyết định seam nằm đâu nhưng không quyết định thay đổi nào đáng chạy vòng; chạy trên thay đổi không có nguồn chân lý độc lập sẽ cho ra test tautological [S27].
5. **Số liệu tự nêu.** "Khoảng 60.000 dev trong bản tin" là lời README [S1]; người viết không kiểm.
6. **Độ dài không đều.** Skill dài nhất (`wayfinder`, `ask-matt`) gần 2.000 từ trong khi `grill-me` chỉ 22 từ; người viết không đánh giá hành vi thực tế của chúng (người viết đếm).

Một điều **không** phải mâu thuẫn dù thoạt nhìn có vẻ vậy: trang `resolving-merge-conflicts.md` còn trong `docs/` dù không còn skill tương ứng. Trang đó mở đầu bằng "Archived" và giải thích skill đã bị gỡ khỏi plugin từ v1.3.0, đúng theo quy tắc trong CLAUDE.md [S28] [S2].

## Điều cần nhớ

- Bộ skill này là **thư viện 27 skill nhỏ, ghép được**, không phải một quy trình khép kín; skill người gọi điều phối, skill mô hình gọi giữ kỷ luật [S1] [S5].
- Lõi giá trị nằm ở **grilling** (hỏi theo cây quyết định, kèm đề xuất) và **GLOSSARY** (ngôn ngữ chung) [S7] [S10].
- Dòng chính: grill, spec, ticket, implement (TDD ở seam đã thỏa thuận), review hai trục, retro [S20] [S12] [S18].
- Gỡ lỗi bắt đầu bằng **vòng phản hồi chặt, đỏ đúng triệu chứng**, không phải bằng giả thuyết [S13].
- Tác giả không nhận skill mới hay PR ngoài; muốn đổi thì fork hoặc tự viết [S3] [S25].
- Đọc kèm sự nghi ngờ vừa phải: tên "red-green-refactor" và quy tắc "refactor ngoài vòng" không khớp [S1] [S12].

## Lưu ý

- **Phạm vi đọc.** Bản clone nông (`--depth 1`) ở commit `a496f5513d4a4cf889bc48e189e579f4b0bdf6aa` (29/10/2026, nhánh `main`). Chỉ các tệp trong danh sách nguồn được trích. Phần lớn các tệp phụ của từng skill (như `tests.md`, `mocking.md`), `skills/in-progress/`, `skills/misc/`, các tệp `agents/openai.yaml` còn lại, phần lớn `CHANGELOG.md` và phần lớn `docs/` không được đọc kỹ. Bài không nêu số sao hay lịch sử issue.
- **Chưa chạy.** Người viết không cài plugin, không chạy `claude plugin validate`, không thử skill nào; mọi hành vi là "đọc mã, chưa chạy".
- **Lệnh đếm.** 176 tệp: `git ls-files | wc -l`. 38 tệp `SKILL.md`: `git ls-files 'skills/**/SKILL.md'`. 27 skill quảng bá: các liên kết trong README và mảng `skills` của `plugin.json`. 16 và 11 skill: tìm `disable-model-invocation: true` trong frontmatter của `engineering/` và `productivity/`. Từ: `wc -w`. Em dash: đếm ký tự U+2014 trong mọi tệp `.md`.
- **Giấy phép.** `plugin.json` ghi `license: MIT` [S4]; người viết không đọc tệp `LICENSE`.
- **Tính chất.** Đây là tài liệu hỗ trợ đọc repo, không phải khuyến nghị cài đặt. Nội dung skill là chỉ dẫn cho agent; trong bài này nó chỉ là đối tượng để mô tả.

## Nguồn tham khảo

- [S1] Matt Pocock, README.md: giới thiệu, cài đặt, bốn lỗi thường gặp, danh sách skill, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/README.md
- [S2] Matt Pocock, CLAUDE.md: quy tắc tổ chức repo (AGENTS.md là liên kết tới tệp này), 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/CLAUDE.md
- [S3] Matt Pocock, SCOPE.md: ngưỡng chấp nhận ý tưởng và phạm vi, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/SCOPE.md
- [S4] Matt Pocock, .claude-plugin/plugin.json: khai báo plugin và 27 skill, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/.claude-plugin/plugin.json
- [S5] Matt Pocock, .agents/invocation.md: phân loại người gọi và mô hình gọi, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/.agents/invocation.md
- [S6] Matt Pocock, .agents/adr/0002-ship-as-a-claude-code-plugin.md: ADR về cách phát hành plugin, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/.agents/adr/0002-ship-as-a-claude-code-plugin.md
- [S7] Matt Pocock, skills/productivity/grilling/SKILL.md: nguyên thủy phỏng vấn, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/skills/productivity/grilling/SKILL.md
- [S8] Matt Pocock, skills/productivity/grill-me/SKILL.md: vỏ gọi grilling, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/skills/productivity/grill-me/SKILL.md
- [S9] Matt Pocock, skills/engineering/grill-with-docs/SKILL.md: vỏ gọi grilling và domain-modeling, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/skills/engineering/grill-with-docs/SKILL.md
- [S10] Matt Pocock, skills/engineering/domain-modeling/SKILL.md: xây mô hình miền, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/skills/engineering/domain-modeling/SKILL.md
- [S11] Matt Pocock, GLOSSARY.md: thuật ngữ của chính repo, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/GLOSSARY.md
- [S12] Matt Pocock, skills/engineering/tdd/SKILL.md: seam, phản mẫu và vòng red-green, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/skills/engineering/tdd/SKILL.md
- [S13] Matt Pocock, skills/engineering/diagnosing-bugs/SKILL.md: vòng gỡ lỗi chia pha, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/skills/engineering/diagnosing-bugs/SKILL.md
- [S14] Matt Pocock, skills/engineering/to-spec/SKILL.md: mẫu spec, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/skills/engineering/to-spec/SKILL.md
- [S15] Matt Pocock, skills/engineering/to-tickets/SKILL.md: chia ticket tracer bullet, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/skills/engineering/to-tickets/SKILL.md
- [S16] Matt Pocock, skills/engineering/implement/SKILL.md: thực thi một ticket, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/skills/engineering/implement/SKILL.md
- [S17] Matt Pocock, skills/engineering/implement-spec/SKILL.md: thực thi cả spec bằng subagent song song, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/skills/engineering/implement-spec/SKILL.md
- [S18] Matt Pocock, skills/engineering/code-review/SKILL.md: review hai trục và mùi mã, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/skills/engineering/code-review/SKILL.md
- [S19] Matt Pocock, skills/engineering/codebase-design/SKILL.md: từ vựng module sâu, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/skills/engineering/codebase-design/SKILL.md
- [S20] Matt Pocock, skills/engineering/ask-matt/SKILL.md: bộ định tuyến và dòng chính, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/skills/engineering/ask-matt/SKILL.md
- [S21] Matt Pocock, skills/engineering/triage/SKILL.md: máy trạng thái triage, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/skills/engineering/triage/SKILL.md
- [S22] Matt Pocock, skills/engineering/wayfinder/SKILL.md: bản đồ quyết định, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/skills/engineering/wayfinder/SKILL.md
- [S23] Matt Pocock, .out-of-scope/new-skills.md: lý do không nhận skill mới, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/.out-of-scope/new-skills.md
- [S24] Matt Pocock, .out-of-scope/question-limits.md: lý do không đặt trần số câu hỏi, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/.out-of-scope/question-limits.md
- [S25] Matt Pocock, CONTRIBUTING.md: nơi gửi từng loại yêu cầu, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/CONTRIBUTING.md
- [S26] Matt Pocock, CHANGELOG.md: lịch sử phiên bản, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/CHANGELOG.md
- [S27] Matt Pocock, docs/engineering/tdd.md: trang tài liệu của tdd, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/docs/engineering/tdd.md
- [S28] Matt Pocock, docs/engineering/resolving-merge-conflicts.md: trang lưu trữ của skill đã gỡ, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/docs/engineering/resolving-merge-conflicts.md
- [S29] Matt Pocock, package.json: phiên bản và giấy phép, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/package.json
- [S30] Matt Pocock, .github/workflows/needs-info.yml: tự đóng issue needs-info, 2026, https://github.com/mattpocock/skills/blob/a496f5513d4a4cf889bc48e189e579f4b0bdf6aa/.github/workflows/needs-info.yml
