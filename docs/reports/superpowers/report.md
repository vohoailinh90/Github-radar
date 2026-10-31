---
id: R07
title: Superpowers: skill tự kích hoạt cho agent lập trình
topic: ky-thuat
date: 2026-10-31
---
# Superpowers: skill tự kích hoạt cho agent lập trình

## Tóm tắt

Superpowers là gì, dùng thế nào, và chỗ nào cần dè dặt? README tự mô tả đây là "một phương pháp phát triển phần mềm hoàn chỉnh cho các agent lập trình", dựng trên một bộ kỹ năng (skill) ghép được và vài chỉ dẫn ban đầu để agent chắc chắn dùng chúng [S1]. Nhìn vào tệp thì nó là một plugin gồm 15 tệp `SKILL.md`, một hook chạy lúc mở phiên, và nhiều tệp khai báo để cùng một bộ skill cài được lên 16 môi trường agent khác nhau [S1] [S4] [S28]. Cài xong, bạn không phải gọi gì đặc biệt: hook nhét skill `using-superpowers` vào đầu phiên, skill đó buộc agent kiểm tra xem có skill nào áp dụng trước khi làm bất cứ việc gì [S2] [S3].

Bài đọc repo theo ba tầng. Tầng một là bản đồ: bảy bước từ ý tưởng đến nhánh đã xong, và cách một bộ skill duy nhất tự kích hoạt trên nhiều harness [S1] [S2] [S4]. Tầng hai là cơ chế tạo ra kỷ luật: các "luật sắt", bảng viện cớ, và quy trình giao việc cho subagent có sổ cái, giới hạn năm vòng sửa và một lượt review cuối [S8] [S9] [S13] [S14] [S15]. Tầng ba là phản biện: những chỗ README lệch khỏi chính các skill, những con số do dự án tự đo, và quyền riêng tư của phần "visual companion" [S1] [S7] [S16] [S22] [S25].

Mỗi khẳng định mang một trong ba nhãn. **Nguồn: repo** nghĩa là đọc trực tiếp từ một tệp ở commit `2ce8aa1` (21/10/2026, nhánh `main`). **Người viết đếm** là con số tính bằng lệnh chạy trên bản đã tải; bạn tự kiểm lại được bằng các lệnh ghi ở mục Lưu ý. **Suy luận** là nhận định của người viết, không phải điều repo tuyên bố. Người viết **không cài và không chạy** Superpowers; mọi mô tả hành vi là "đọc mã, chưa chạy".

Ba ý đáng mang theo. Thứ nhất, Superpowers đặt cược vào việc **ép quy trình bằng văn bản có cổng chặn**: không xây gì khi chưa có tài liệu thiết kế được duyệt, không sửa lỗi khi chưa tìm nguyên nhân gốc, không báo xong khi chưa có bằng chứng chạy lệnh [S5] [S14] [S15]. Thứ hai, phần khó nhất của dự án không nằm ở ý tưởng mà ở **giữ các quy tắc sống sót qua nén ngữ cảnh**: giới hạn 20.000 byte cho mỗi `SKILL.md` được một bài kiểm tra canh giữ [S22] [S24]. Thứ ba, nhiều con số hiệu quả (tỷ lệ 94% PR bị từ chối, 24/24 xuống 3/24 lần bỏ qua tài liệu thiết kế) **do chính dự án nêu**, người viết không có cách kiểm độc lập [S21] [S22].

## Hồ sơ nhanh

| Mục | Giá trị | Nhãn |
|---|---|---|
| Là gì | Plugin gồm 15 skill, một hook `SessionStart`, nhiều tệp khai báo cho từng harness | Nguồn: repo [S1] [S4] [S28] |
| Phiên bản | 7.0.1, ngày 21/10/2026; giấy phép MIT | Nguồn: repo [S1] [S22] [S28] |
| Tác giả | Jesse Vincent và nhóm Prime Radiant | Nguồn: repo [S1] [S28] |
| Môi trường hỗ trợ | 16 mục cài đặt trong README, từ Claude Code đến Muse | Người viết đếm [S1] |
| Quy mô | 231 tệp: 84 trong `skills/`, 70 trong `tests/`, 31 trong `docs/` | Người viết đếm |
| Văn bản skill | 15 tệp `SKILL.md`, tổng 21.816 từ; dài nhất là `executing-plans` với 2.892 từ | Người viết đếm |
| Skill sát giới hạn nhất | `subagent-driven-development`: 19.506 byte, còn cách mốc 20.000 là 494 byte | Người viết đếm [S24] |
| Luồng chính | brainstorming, worktree, kế hoạch, thực thi, TDD, review, kết thúc nhánh | Nguồn: repo [S1] |
| Đóng góp | PR vào nhánh `dev`; AGENTS.md nêu tỷ lệ PR bị từ chối 94% | Nguồn: repo [S21] |
| Số sao | Bài này không nêu: nguồn duy nhất là tệp ở commit đã ghim | Giới hạn của bài |

## Bảy bước từ ý tưởng đến nhánh

README liệt kê quy trình cơ bản gồm bảy skill chạy lần lượt: brainstorming, using-git-worktrees, writing-plans, subagent-driven-development hoặc executing-plans, test-driven-development, requesting-code-review, finishing-a-development-branch [S1]. Mỗi skill tự gọi tên skill kế tiếp, nên chuỗi này là một đường ống chứ không phải một thực đơn (suy luận từ các câu "REQUIRED SUB-SKILL" trong [S7] và câu bàn giao cuối [S5]).

**Bước 1, brainstorming.** Skill này áp dụng trước mọi việc sáng tạo: tạo tính năng, thêm chức năng, đổi hành vi [S5]. Nếu mọi thứ cần biết đã nằm trong yêu cầu ("đổi icon sang màu xanh ngô"), nó coi đó là việc nhanh và làm luôn [S5]. Nếu thiếu điều quan trọng, nó phải đi đúng thứ tự: bày các cách làm trong một tin nhắn riêng và để người dùng chọn, viết tài liệu thiết kế, xin duyệt, rồi mới gọi `writing-plans` [S5]. Trong dự án thật, nó phải đọc mã và tài liệu người dùng chỉ tới trước khi hỏi câu đầu tiên, và "không bao giờ hỏi điều mà dự án hay ngữ cảnh đã trả lời" [S5]. Tài liệu thiết kế nằm ở `docs/superpowers/specs/YYYY-MM-DD-<chủ-đề>-design.md`, có phần "Approaches" ghi hai ba cách đã cân nhắc [S5]. Với dự án lớn, một subagent "người dựng" đọc tài liệu theo `builder-check-prompt.md` và chỉ trả về những câu hỏi mà nó buộc phải đoán [S5] [S6]. Đoạn `HARD-GATE` cấm viết mã sản phẩm, dựng khung, cài phụ thuộc cho tới khi tài liệu được duyệt; đọc và khám phá thì vẫn được [S5].

**Bước 2, using-git-worktrees.** Việc đầu tiên là phát hiện xem đã ở trong không gian cô lập chưa, bằng cách so `git rev-parse --git-dir` với `--git-common-dir`, kèm một chốt chặn để không nhầm submodule với worktree [S18]. Nếu chưa cô lập, skill hỏi xin phép; có công cụ worktree sẵn của harness thì dùng nó, không thì dùng `git worktree add` vào `.worktrees/` và bắt buộc kiểm tra thư mục đó đã bị `.gitignore` bằng `git check-ignore` [S18].

**Bước 3, writing-plans.** Kế hoạch lưu ở `docs/superpowers/plans/YYYY-MM-DD-<tính-năng>.md`, mở đầu bằng một tiêu đề cố định: Goal, Architecture, Tech Stack, Spec, Global Constraints và Review Focus [S7]. Mỗi bước là "một hành động có kết quả kiểm được": viết test thất bại, chạy cho thấy thất bại, viết mã tối thiểu, chạy cho thấy qua, commit [S7]. Kế hoạch chỉ ghi những quyết định mà người thực hiện không tự đưa ra được, và có năm mục tự soát: phủ spec, quét bước, nhất quán kiểu, Review Focus, tỷ lệ độ dài [S7]. Cuối cùng skill đề nghị chọn giữa chạy bằng subagent hay chạy "native" trong một phiên [S7].

**Bước 4, thực thi.** Có hai đường. `subagent-driven-development` cho mỗi nhiệm vụ một subagent mới, một lượt review sau mỗi nhiệm vụ, và một lượt review toàn nhánh ở cuối [S8]. `executing-plans` do chính agent chạy từng nhiệm vụ trong một phiên rồi nhờ một reviewer mới xem cả nhánh một lần [S12]. Hai skill tự so sánh chi phí: đường thứ nhất tốn một ngữ cảnh mới cho mỗi nhiệm vụ và mỗi lượt review; đường thứ hai chỉ tốn một ngữ cảnh cộng một reviewer [S8] [S12].

**Bước 5 và 6, TDD và review.** TDD được áp trong lúc làm [S13]; `requesting-code-review` điều một subagent review với các SHA đầu và cuối, còn `receiving-code-review` quy định cách agent đáp lại phản hồi [S16] [S17].

**Bước 7, finishing-a-development-branch.** Chạy toàn bộ test trước; nếu có test hỏng thì dừng, không hiện menu [S19]. Sau đó phát hiện môi trường, xác định nhánh gốc và đưa **đúng ba lựa chọn**: gộp cục bộ, đẩy và tạo PR, giữ nguyên nhánh; với HEAD tách rời chỉ còn hai lựa chọn [S19]. Bỏ công việc chỉ xảy ra khi người dùng tự yêu cầu, và vẫn phải xác nhận trước [S19].

## Skill tự kích hoạt: bootstrap và một repo cho nhiều harness

**Skill mở đường.** `using-superpowers` chỉ dài 487 từ (người viết đếm) và ra lệnh rất gắt: nếu có dù 1% khả năng một skill áp dụng thì "BẮT BUỘC phải gọi", và việc kiểm skill đứng trước cả câu hỏi làm rõ [S2]. Nó có bảng 12 "dấu hiệu đang tự biện minh" (người viết đếm), ví dụ "đây chỉ là câu hỏi đơn giản" hay "để tôi khám phá mã trước" [S2]. Subagent được dặn bỏ qua skill này nhờ thẻ `SUBAGENT-STOP` [S2]. Chỉ dẫn của người dùng (CLAUDE.md, AGENTS.md, GEMINI.md) có quyền cao hơn skill [S2].

**Hook nhét skill đó vào phiên.** Tệp `hooks.json` đăng ký hook `SessionStart` cho các lần `startup`, `clear` và `compact`, chạy đồng bộ (`async: false`) [S4]. Script `session-start` đọc `using-superpowers/SKILL.md`, thoát ký tự cho JSON và in ra; **chỉ skill này được nhét sẵn**, các skill khác nạp qua công cụ `Skill` khi cần [S3]. Dạng JSON đổi theo môi trường: Cursor nhận `additional_context`, Claude Code nhận `hookSpecificOutput.additionalContext`, Copilot CLI và môi trường lạ nhận `additionalContext` ở cấp ngoài cùng; chú thích trong mã giải thích Claude Code đọc cả hai trường mà không khử trùng, nên hook chỉ được phát đúng một trường [S3]. Việc hook chạy lại sau `compact` cho thấy ý đồ nạp lại bootstrap khi ngữ cảnh bị nén (suy luận từ [S4]).

**Một repo, nhiều harness.** README có 16 mục cài đặt (người viết đếm) [S1]. Thư mục gốc chứa các thư mục khai báo riêng cho Claude, Codex, Cursor, Devin, Kimi, Antigravity, Muse và Hermes, cùng `.opencode`, `.pi` và `gemini-extension.json` (người viết đếm từ danh sách tệp) [S28] [S23]. `GEMINI.md` chỉ gồm hai dòng `@` nhập skill bootstrap và tệp công cụ của Gemini [S32]. Skill bootstrap kèm 7 tệp tham chiếu theo từng harness (người viết đếm), ví dụ `codex-tools.md` hay `gemini-tools.md`, để agent dịch tên công cụ của Claude sang công cụ sẵn có [S2].

**Giữ phiên bản đồng bộ.** `.version-bump.json` liệt kê 12 tệp mang số phiên bản (người viết đếm) [S23]. Số 7.0.1 xuất hiện khớp nhau ở 5 tệp mà người viết đối chiếu bằng `grep`, gồm `package.json` và các manifest Claude, Cursor, Codex, Gemini (người viết đếm) [S28] [S30]. Với README, Hermes là trường hợp có giới hạn rõ: Hermes không có hook sau nén, nên phiên rất dài có thể mất bootstrap và cần mở phiên mới [S1].

## Kỷ luật bằng luật sắt và bảng viện cớ

Bốn skill chứa mục "Iron Law" (người viết đếm bằng cách tìm chuỗi này trong các tệp `.md`): TDD, systematic-debugging, verification-before-completion và writing-skills [S13] [S14] [S15] [S20].

- **TDD:** "Không mã sản phẩm nào mà không có test thất bại trước." Viết mã trước test thì xóa, không giữ làm "tham khảo" [S13]. Ngoại lệ (hỏi người cộng tác) chỉ gồm bản mẫu bỏ đi, mã sinh tự động và tệp cấu hình [S13]. Chu trình RED-GREEN-REFACTOR có hai bước kiểm bắt buộc: thấy test thất bại đúng lý do, rồi thấy nó qua [S13].
- **Gỡ lỗi:** "Không sửa khi chưa điều tra nguyên nhân gốc." Quy trình bốn pha: điều tra nguyên nhân gốc, phân tích mẫu, giả thuyết và thử, cài đặt [S14]. Nếu đã thử từ ba cách sửa trở lên mà vẫn hỏng, skill cấm thử cách thứ tư và yêu cầu bàn lại kiến trúc với người cộng tác [S14].
- **Xác minh:** "Không tuyên bố hoàn thành khi chưa có bằng chứng mới." Hàm cổng gồm năm bước: xác định lệnh chứng minh, chạy đủ, đọc đầu ra, đối chiếu, rồi mới nói [S15]. Bảng chỉ ra "đủ" và "không đủ": test qua cần đầu ra 0 lỗi chứ không phải "chắc là qua", báo cáo thành công của agent phải đối chiếu với diff [S15].

Cả ba có chung hai bộ phận: bảng **Red Flags** liệt kê câu tự nhủ báo hiệu sắp phá luật, và bảng **Common Rationalizations** ghép từng lời viện cớ với phản bác [S13] [S14] [S15]. Có 11 tệp `.md` dưới `skills/` chứa chữ "Rationalization" (người viết đếm). Suy luận: các bảng này nhắm vào đúng kiểu lập luận mà một mô hình hay dùng để tự miễn trừ, nên chúng là văn bản hành vi chứ không phải tài liệu giải thích. Dự án cũng coi chúng như vậy: AGENTS.md cấm sửa các bảng này nếu không có bằng chứng cải thiện [S21].

`receiving-code-review` áp cùng tinh thần cho việc nhận phản hồi: sáu bước đọc, hiểu, kiểm chứng, đánh giá, đáp, làm từng mục; câu "You're absolutely right!" được ghi rõ là vi phạm [S17]. Nếu một mục chưa rõ thì dừng, không làm mục nào cho tới khi hỏi xong, vì các mục có thể liên quan nhau [S17].

## Giao việc cho subagent

`subagent-driven-development` (SDD) là phần phức tạp nhất. Nguyên lý: mỗi nhiệm vụ một subagent mới không thừa hưởng lịch sử phiên, thêm review nhiệm vụ (khớp spec và chất lượng mã) và review toàn nhánh cuối [S8]. Một số quy tắc đáng chú ý:

- **Liên tục, không dừng hỏi.** Giữa các nhiệm vụ agent không được hỏi "tiếp tục không?". Chỉ bốn việc làm nó dừng: thao tác không thể hoàn tác hoặc phá hủy, hành động nhạy cảm về bảo mật, tác dụng phụ ngoài worktree như merge hay đẩy lên nhánh dùng chung, và kế hoạch hỏng đến mức mọi đường đều là đoán [S8]. Mọi xung đột khác phải được "phán quyết" và ghi vào sổ cái theo mẫu `Ruling: <quyết định> — <vì sao> — <sai thì tốn gì>` [S8].
- **Sổ cái làm trí nhớ.** Mỗi kế hoạch có một thư mục làm việc bị git bỏ qua dưới `.superpowers/sdd/`, chứa `progress.md`; sổ này là bản đồ phục hồi khi ngữ cảnh bị nén, và `git clean -fdx` sẽ xóa nó [S8]. Skill nói thẳng rằng việc điều phối viên mất chỗ rồi giao lại cả chuỗi nhiệm vụ đã xong là lỗi đắt nhất từng quan sát [S8].
- **Quét trước khi chạy.** Trước nhiệm vụ 1 phải lập một bảng: mỗi cặp nhiệm vụ dùng chung tệp hoặc giao diện một hàng, và mỗi nhiệm vụ một hàng kiểm xem văn bản của nó có tự nhất quán không; "quét sạch" mà không có các hàng này thì chưa phải đã quét [S11].
- **Chọn mô hình rẻ nhất đủ dùng.** Nhiệm vụ cơ học dùng mô hình rẻ; review cuối dùng mô hình mạnh nhất; phải ghi rõ mô hình khi giao việc vì bỏ trống là kế thừa mô hình đắt nhất của phiên [S8]. Skill cũng nhắc "số lượt quan trọng hơn giá token": mô hình rẻ nhất thường cần gấp 2 đến 3 lần số lượt [S8].
- **Không chạy song song các bên cài đặt.** Skill cấm giao nhiều subagent cài đặt cùng lúc vì xung đột [S8]. Song song chỉ dành cho điều tra độc lập, do skill `dispatching-parallel-agents` lo [S29].
- **Vòng sửa tối đa năm vòng.** Vòng 1 đến 3 gọi lại chính bên cài đặt cũ; vòng 4 và 5 giao cho bên cài đặt mới trên mô hình mạnh hơn một bậc; nếu vòng 5 vẫn còn lỗi thì "bộ ngắt" bắt điều phối viên tự phân xử từng lỗi: đỗ lại kèm phán quyết hoặc quyết định thay đổi nhỏ nhất để gỡ nghẽn [S9]. Review lại chỉ xem phần diff của lần sửa [S9].
- **Review cuối chỉ một đợt sửa.** Nếu review toàn nhánh có lỗi, giao **một** subagent sửa toàn bộ danh sách, rồi một lượt review lại; không có đợt sửa thứ hai, lỗi còn lại đến tay người cộng tác ở bước kết thúc nhánh [S10]. Trước khi xóa thư mục làm việc, mọi dòng `Ruling:` phải gom vào mục "Rulings I made" của tin nhắn cuối, vì đó là nơi duy nhất các quyết định thay mặt người dùng đến được tay họ [S10].
- **Giao việc bằng tệp.** Brief, báo cáo và gói review truyền qua đường dẫn chứ không dán vào lời nhắn, để ngữ cảnh điều phối không phình ra [S8]. Mẫu reviewer đọc diff một lần và trả hai phán quyết: khớp spec và chất lượng mã [S33].

Suy luận: toàn bộ thiết kế coi ngữ cảnh của người điều phối là tài nguyên khan hiếm, nên mọi đầu ra lớn bị đẩy ra tệp, và mọi quy tắc quan trọng bị đẩy xuống tệp riêng để đọc lại đúng lúc.

## Giữ quy tắc qua nén ngữ cảnh

Release notes 7.0.1 giải thích vấn đề: sau khi nén, Claude Code gắn lại mỗi skill đã gọi nhưng cắt ở 20.000 ký tự, nên phần quá mốc đó biến mất khỏi ngữ cảnh cho đến hết phiên [S22]. Dự án nêu một phiên thật mà SDD mất giới hạn năm vòng sửa và chạy 18 vòng cho một nhiệm vụ (do dự án thuật lại, người viết không kiểm) [S22]. Phản ứng gồm ba việc:

1. Dời vòng sửa, review cuối, xử lý báo cáo, tiếp tục phiên, quét trước và gộp lô của SDD vào thư mục `references/`; skill đọc từng tệp từ đĩa đúng ở bước cần [S22] [S8].
2. Dời tài liệu phụ của `writing-skills` vào `references/` và bỏ phần ví dụ lặp trong `executing-plans` [S22].
3. Thêm `tests/skill-size/test-skill-size.sh`, thất bại khi có `SKILL.md` đạt 20.000 byte; script đo **byte**, nghiêm hơn ký tự đối với chữ không ASCII [S24].

Kết quả hiện tại, theo số người viết đo: `subagent-driven-development` 19.506 byte (còn 494), `executing-plans` 18.103 (còn 1.897), `writing-skills` 16.738 (còn 3.262), `brainstorming` 13.602 (còn 6.398). Suy luận: SDD gần như hết chỗ, nên mọi quy tắc mới thêm vào đó buộc phải dời sang `references/`, và đó là lý do chính các điều khoản quan trọng của nó nằm ngoài tệp chính. Chính SDD dặn "đọc lại `fix-loop.md` trước mỗi vòng, kể cả khi đã đọc" vì ký ức về nó không sống qua nén [S8].

## Viết và đóng góp skill

`writing-skills` phát biểu rằng viết skill là TDD áp cho tài liệu quy trình: ca kiểm thử là kịch bản gây áp lực với subagent, "mã sản phẩm" là `SKILL.md`, RED là agent vi phạm khi chưa có skill, GREEN là agent tuân thủ khi có skill, REFACTOR là bịt các lỗ hổng mới phát hiện [S20]. Skill không phải câu chuyện về một lần giải quyết; ràng buộc cơ học thực thi được bằng regex hay kiểm tra thì nên tự động hóa, tài liệu chỉ dành cho phán đoán [S20]. Thư mục `references/` của skill này có một tệp `anthropic-best-practices.md` 46.197 byte (người viết đếm), người viết không đọc nội dung nó [S20].

AGENTS.md là tệp hướng dẫn đóng góp, mở đầu bằng phần "nếu bạn là AI agent" [S21]. Những điểm chính:

- Nêu tỷ lệ PR bị từ chối là 94% (dự án tự nêu) [S21].
- Trước khi mở PR, agent phải đọc cả mẫu PR, tìm PR đang mở và đã đóng cùng vấn đề, xác nhận đây là vấn đề người cộng tác thực sự gặp, đánh giá liệu thay đổi có thuộc lõi, tự khai mô hình, harness và các plugin đã cài, và cho người cộng tác xem toàn bộ diff [S21].
- PR phải nhắm nhánh `dev`; phần "tóm tắt do con người viết" không được để agent viết [S21].
- Không nhận: phụ thuộc bên thứ ba (plugin được thiết kế không phụ thuộc), thay đổi "tuân thủ" hướng dẫn viết skill của Anthropic nếu thiếu bằng chứng đánh giá, cấu hình riêng của dự án, PR sửa lỗi do người khác báo, và PR hàng loạt [S21].
- Hỗ trợ harness mới phải qua phép thử cố định: mở phiên sạch, gửi đúng câu "Let's make a react todo list" và `brainstorming` phải tự kích hoạt trước khi có mã [S21].

Về kiểm thử: `tests/` kiểm mã không phải LLM (máy chủ brainstorm, nạp plugin OpenCode, đồng bộ Codex...), còn đánh giá hành vi agent nằm ở kho riêng `superpowers-evals` được clone vào `evals/`, không có trong commit này [S21] [S27]. Có 18 thư mục con trong `tests/` (người viết đếm). Vì thế các con số kiểu 24/24 xuống 3/24 không kiểm được từ repo này (suy luận). Ngoài ra `diagnosing-superpowers` là skill dùng ngược lại: đọc bản ghi một phiên đã qua, báo cáo điều xảy ra, và mọi phát hiện phải dẫn `path:line`, "không dẫn thì không phải phát hiện" [S26].

## An toàn và quyền riêng tư

**Hook.** Script `session-start` chỉ đọc một tệp skill trong plugin và in JSON; trong tệp người viết đọc không thấy lệnh mạng nào (đọc mã, chưa chạy) [S3].

**Visual companion.** Đây là máy chủ web cục bộ để skill brainstorming đưa mockup cho người dùng xem [S5]. Mặc định nó nghe ở `127.0.0.1` (có thể đổi bằng `BRAINSTORM_HOST`), tạo khóa bí mật 32 byte ngẫu nhiên mỗi phiên, mang trong `?key=` và cookie, và kiểm nguồn gốc WebSocket; chú thích trong mã nói mục tiêu là chặn tiêm từ tab khác và DNS rebinding [S25]. Máy chủ tự thoát khi chủ tiến trình chết hoặc rảnh quá thời hạn, mặc định 4 giờ theo tài liệu skill [S25] [S31].

**Telemetry tùy chọn.** README nêu thẳng: logo Prime Radiant trong visual companion được tải từ website của họ và có kèm số phiên bản Superpowers, không kèm thông tin dự án, prompt hay agent; tắt bằng biến môi trường [S1]. Mã khớp với lời đó: địa chỉ ảnh là `primeradiant.com/brand/...png?v=<phiên bản>`; nếu một trong ba biến `SUPERPOWERS_DISABLE_TELEMETRY`, `DISABLE_TELEMETRY` hay `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` đúng, thẻ ảnh được thay bằng chuỗi rỗng và chỉ còn chữ [S25]. Suy luận: yêu cầu mạng này chỉ xảy ra khi bạn đồng ý dùng visual companion, vì skill chỉ mở nó sau khi hỏi [S5].

**Văn bản nhắm vào agent.** Skill là chỉ dẫn mà agent sẽ tuân theo, và bootstrap bọc trong thẻ `EXTREMELY_IMPORTANT` [S3]. Suy luận: cài plugin này nghĩa là tin tác giả nó, giống tin mã chạy lúc cài; nên đọc `using-superpowers` và các skill trước khi bật, như bài này đã làm.

## Phản biện

Các điểm dưới đây là chỗ hai tệp của chính repo nói không giống nhau hoặc chưa khớp, nên chúng được báo chứ không chọn bên:

1. **"2 đến 5 phút" so với "một hành động kiểm được".** README vẫn viết `writing-plans` chia việc thành nhiệm vụ nhỏ "2 đến 5 phút mỗi cái" [S1]. Skill hiện hành định cỡ bước là "một hành động có kết quả kiểm được" và release notes ghi thay đổi này là thay cho "2-5 phút" [S7] [S22]. README lạc hậu so với skill (suy luận).
2. **`HEAD~1` so với "không bao giờ `HEAD~1`".** Ví dụ trong `requesting-code-review` lấy `BASE_SHA=$(git rev-parse HEAD~1)` [S16], còn SDD dặn dùng BASE ghi trước khi giao việc, "không bao giờ `HEAD~1`" vì nó làm rơi các commit trước của nhiệm vụ nhiều commit [S8]. Hai ngữ cảnh khác nhau (một commit so với nhiều commit), nhưng ví dụ dễ bị sao chép sai (suy luận).
3. **Thứ tự worktree.** README xếp worktree là bước 2, "kích hoạt sau khi duyệt thiết kế" [S1]; skill `brainstorming` thì quy định sau khi duyệt là gọi `writing-plans` "và không skill nào khác" [S5], còn `writing-plans` nói worktree nên được tạo "lúc thực thi" [S7] và SDD đặt nó ở phần Setup [S8]. Thứ tự thực tế theo skill là kế hoạch trước, worktree lúc thực thi (suy luận).
4. **"Hai giai đoạn review".** README mô tả SDD có review hai giai đoạn (khớp spec, rồi chất lượng) [S1], còn mẫu reviewer đọc diff một lần và trả hai phán quyết [S33]. Có thể chỉ là cách nói; người viết không chạy để xác nhận.
5. **Số liệu tự đo.** 94% PR bị từ chối [S21], 24/24 so với 3/24 [S22] và 18 vòng sửa [S22] đều do dự án nêu, không có dữ liệu đánh giá trong commit này. Ngay cả README cũng chỉ nói bộ skill thiết yếu "không gì cần làm đặc biệt" mà không đưa số đo hiệu quả [S1].
6. **Chi phí quy trình.** Dự án thừa nhận SDD tốn một ngữ cảnh mới cho mỗi nhiệm vụ và mỗi lượt review [S8] [S12]; ngoài ra các cổng chặn (thiết kế, test, xác minh) thêm lượt trao đổi cho việc nhỏ. Skill có lối thoát cho việc rõ ràng và cho người dùng tự bỏ qua câu hỏi [S5], nhưng mức độ phiền thế nào thì repo chỉ cho thấy qua lời phàn nàn trong release notes: v7.0.1 tồn tại vì "câu hỏi mặc định gây khó chịu và có vẻ công thức" [S22].
7. **Quá phụ thuộc vào mệnh lệnh viết hoa.** Bootstrap dùng ngôn ngữ cực mạnh ("không thương lượng") [S2]. Suy luận: cách này có lẽ thắng được thói quen bỏ qua skill của mô hình, nhưng cũng đồng nghĩa hành vi phụ thuộc vào mô hình cụ thể, điều mà các đánh giá nằm ngoài repo mới trả lời được.

## Điều cần nhớ

- Superpowers là **thư viện skill + một hook**, không phải ứng dụng: sức mạnh nằm ở việc skill `using-superpowers` được nhét vào đầu mỗi phiên và ép agent kiểm skill trước mọi việc [S2] [S3] [S4].
- Quy trình mặc định: **thiết kế được duyệt, kế hoạch, thực thi có review, rồi chọn cách kết thúc nhánh**; không có mã sản phẩm trước khi thiết kế được duyệt [S1] [S5] [S19].
- Ba luật sắt (test trước, nguyên nhân gốc trước, bằng chứng trước) đi cùng bảng viện cớ; đó là kỹ thuật chính để định hình hành vi [S13] [S14] [S15].
- SDD là phần đáng học nhất cho ai giao việc cho nhiều agent: **sổ cái, phán quyết có ghi sổ, năm vòng sửa, một đợt sửa cuối** [S8] [S9] [S10].
- Giới hạn 20.000 byte và thư mục `references/` là bài học thực tế về nén ngữ cảnh [S22] [S24].
- Đọc kèm README với chút nghi ngờ: ít nhất bốn chỗ README và skill không khớp, và các số đo hiệu quả là do dự án tự nêu [S1] [S7] [S16] [S22].

## Lưu ý

- **Phạm vi đọc.** Bài đọc bản clone nông (`--depth 1`) ở commit `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b` (21/10/2026, nhánh `main`). Chỉ các tệp nằm trong danh sách nguồn được trích; phần lớn `tests/`, `.opencode/`, `.pi/`, các script đồng bộ Codex, `references/` của `writing-skills` và phần lớn `RELEASE-NOTES.md` không được đọc kỹ. Bài không nêu số sao, số fork hay lịch sử issue vì chúng không nằm trong commit.
- **Chưa chạy.** Người viết không cài Superpowers, không chạy hook, máy chủ brainstorm hay bất kỳ test nào; mọi hành vi là "đọc mã, chưa chạy".
- **Lệnh đếm.** 231 tệp: `git ls-files | wc -l`. 15 skill: `git ls-files 'skills/*/SKILL.md'`. Từ và byte của `SKILL.md`: `wc -w`, `wc -c`. 16 mục cài đặt: đếm tiêu đề `###` giữa "Installation" và "The Basic Workflow" của README. 12 tệp phiên bản: đọc khóa `files` của `.version-bump.json`. 12 hàng dấu hiệu: đếm các hàng bảng của `using-superpowers`.
- **Giấy phép.** README ghi MIT và `plugin.json` ghi `license: MIT`; người viết không đọc tệp `LICENSE` [S1] [S28].
- **Tính chất.** Đây là tài liệu hỗ trợ đọc repo, không phải khuyến nghị cài đặt. Nội dung skill là chỉ dẫn dành cho agent; trong bài này nó là đối tượng để mô tả chứ không phải lệnh cho người viết.

## Nguồn tham khảo

- [S1] Jesse Vincent, README.md: tổng quan, cài đặt 16 môi trường, quy trình cơ bản, telemetry, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/README.md
- [S2] Jesse Vincent, skills/using-superpowers/SKILL.md: skill bootstrap và bảng dấu hiệu tự biện minh, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/using-superpowers/SKILL.md
- [S3] Jesse Vincent, hooks/session-start: script hook nhét bootstrap vào phiên, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/hooks/session-start
- [S4] Jesse Vincent, hooks/hooks.json: đăng ký hook SessionStart, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/hooks/hooks.json
- [S5] Jesse Vincent, skills/brainstorming/SKILL.md: quy trình làm rõ ý, cổng chặn thiết kế, visual companion, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/brainstorming/SKILL.md
- [S6] Jesse Vincent, skills/brainstorming/builder-check-prompt.md: lời nhắc kiểm tra người dựng, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/brainstorming/builder-check-prompt.md
- [S7] Jesse Vincent, skills/writing-plans/SKILL.md: cấu trúc kế hoạch và tự soát, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/writing-plans/SKILL.md
- [S8] Jesse Vincent, skills/subagent-driven-development/SKILL.md: vòng lặp nhiệm vụ, sổ cái, chọn mô hình, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/subagent-driven-development/SKILL.md
- [S9] Jesse Vincent, skills/subagent-driven-development/references/fix-loop.md: vòng sửa năm vòng và bộ ngắt, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/subagent-driven-development/references/fix-loop.md
- [S10] Jesse Vincent, skills/subagent-driven-development/references/final-review.md: review toàn nhánh và kết thúc, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/subagent-driven-development/references/final-review.md
- [S11] Jesse Vincent, skills/subagent-driven-development/references/preflight.md: bảng quét trước khi chạy, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/subagent-driven-development/references/preflight.md
- [S12] Jesse Vincent, skills/executing-plans/SKILL.md: thực thi kế hoạch trong một phiên, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/executing-plans/SKILL.md
- [S13] Jesse Vincent, skills/test-driven-development/SKILL.md: luật sắt TDD và bảng viện cớ, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/test-driven-development/SKILL.md
- [S14] Jesse Vincent, skills/systematic-debugging/SKILL.md: bốn pha gỡ lỗi, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/systematic-debugging/SKILL.md
- [S15] Jesse Vincent, skills/verification-before-completion/SKILL.md: hàm cổng xác minh, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/verification-before-completion/SKILL.md
- [S16] Jesse Vincent, skills/requesting-code-review/SKILL.md: yêu cầu review bằng subagent, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/requesting-code-review/SKILL.md
- [S17] Jesse Vincent, skills/receiving-code-review/SKILL.md: cách đáp phản hồi review, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/receiving-code-review/SKILL.md
- [S18] Jesse Vincent, skills/using-git-worktrees/SKILL.md: phát hiện và tạo không gian cô lập, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/using-git-worktrees/SKILL.md
- [S19] Jesse Vincent, skills/finishing-a-development-branch/SKILL.md: kết thúc nhánh và menu lựa chọn, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/finishing-a-development-branch/SKILL.md
- [S20] Jesse Vincent, skills/writing-skills/SKILL.md: viết skill như TDD cho tài liệu, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/writing-skills/SKILL.md
- [S21] Jesse Vincent, AGENTS.md: hướng dẫn đóng góp và những điều không nhận, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/AGENTS.md
- [S22] Jesse Vincent, RELEASE-NOTES.md: ghi chú phát hành v7.0.1 và các thay đổi trước đó, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/RELEASE-NOTES.md
- [S23] Jesse Vincent, .version-bump.json: danh sách tệp mang số phiên bản, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/.version-bump.json
- [S24] Jesse Vincent, tests/skill-size/test-skill-size.sh: bài kiểm tra giới hạn 20.000 byte, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/tests/skill-size/test-skill-size.sh
- [S25] Jesse Vincent, skills/brainstorming/scripts/server.cjs: máy chủ visual companion, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/brainstorming/scripts/server.cjs
- [S26] Jesse Vincent, skills/diagnosing-superpowers/SKILL.md: chẩn đoán phiên đã qua, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/diagnosing-superpowers/SKILL.md
- [S27] Jesse Vincent, docs/testing.md: hai loại kiểm thử tests và evals, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/docs/testing.md
- [S28] Jesse Vincent, .claude-plugin/plugin.json: khai báo plugin Claude Code, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/.claude-plugin/plugin.json
- [S29] Jesse Vincent, skills/dispatching-parallel-agents/SKILL.md: giao việc song song cho điều tra độc lập, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/dispatching-parallel-agents/SKILL.md
- [S30] Jesse Vincent, package.json: khai báo gói Pi và phiên bản, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/package.json
- [S31] Jesse Vincent, skills/brainstorming/visual-companion.md: hướng dẫn dùng visual companion, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/brainstorming/visual-companion.md
- [S32] Jesse Vincent, GEMINI.md: nhập skill bootstrap cho Gemini, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/GEMINI.md
- [S33] Jesse Vincent, skills/subagent-driven-development/task-reviewer-prompt.md: mẫu lời nhắc reviewer nhiệm vụ, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/subagent-driven-development/task-reviewer-prompt.md
