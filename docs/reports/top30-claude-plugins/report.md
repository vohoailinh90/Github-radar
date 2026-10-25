---
id: R05
title: Top 30 Claude Code Plugins: bản đồ 30 repo
topic: ky-thuat
date: 2026-10-25
---
# Top 30 Claude Code Plugins: bản đồ 30 repo

## Tóm tắt

Báo cáo này đọc một ảnh chụp có tên "Top 30 Claude Code Plugins" của Charlie Hills: 30 repo GitHub xếp thành năm nhóm, mỗi nhóm sáu repo, kèm số sao đọc ngày 23/10/2026 và một dòng mô tả cho từng repo (nguồn: ảnh [S1]). Ảnh chỉ cho tên, số sao và một câu. Để biết mỗi repo thật sự là gì, cài thế nào và cần cẩn thận điều gì, người viết đã đọc file README của cả 30 repo ở một commit ghim ngày 25/10/2026, chỉ đọc, không chạy lệnh nào của các repo đó [S1].

Ba nhãn dùng xuyên suốt. **Nguồn: repo** là điều đọc thẳng từ README ở commit ghim, luôn kèm nhãn nguồn như [S2]. **Người viết đếm** là con số do người viết tự đếm bằng script trên cây thư mục hoặc trên README, và câu đó nói rõ đã đếm gì. **Suy luận** là nhận định của người viết, không phải lời của tác giả repo. Số sao và dòng mô tả trong ảnh là **nguồn: ảnh**, người viết không đo lại chúng.

Năm điều rút ra sau khi đọc cả 30 README:

1. Hầu hết là bộ "skill" hoặc plugin cho coding agent: văn bản hướng dẫn cộng vài script, cài bằng một hoặc hai lệnh. Một số ít là công cụ đầy đủ, ví dụ proxy nén ngữ cảnh Headroom [S17], studio video OpenMontage cài bằng `make setup` [S27] và bộ dựng PowerPoint PPT Master [S24].
2. Có bốn cách cài khác nhau: marketplace của Claude Code, lệnh `npx skills add`, trình cài riêng của từng repo, hoặc dán một câu cho agent tự cài. Mỗi cách đòi hỏi mức tin tưởng khác nhau (phần "Bốn cách cài").
3. "All free" ở chân ảnh đúng với mã nguồn, nhưng người viết đếm được tám repo có README nhắc thẳng một lớp trả phí hoặc dịch vụ đám mây ngay cạnh bản miễn phí, và vài repo có điều khoản giấy phép đáng đọc (phần "Miễn phí nghĩa là gì").
4. Hai mục trong ảnh lệch với thực tế. `gsd-build/get-shit-done` chỉ còn một thông báo "đã chuyển repo" [S18]. Số sao 371k của REA trong ảnh lệch rất xa số radar đã đo ngày 17/10/2026 [S1][S32].
5. Để học trước khi cài, người viết **suy luận** rằng ba repo nhỏ nên đọc đầu tiên là `forrestchang/andrej-karpathy-skills`, `blader/humanizer` và `obra/superpowers`, theo thứ tự từ một file quy tắc, đến một skill, đến một chuỗi skill ghép nhau (phần "Chọn ba repo đầu tiên").

Báo cáo là tài liệu đọc, không phải lời khuyên cài đặt: mỗi lệnh cài chạy mã của người khác trên máy bạn.

## Ảnh nói gì, report đọc thế nào

Ảnh có tiêu đề "Top 30 Claude Code Plugins" và dòng phụ "The 30 most-starred skill repos on GitHub" của Charlie Hills. Năm nhóm, theo thứ tự trong ảnh: "Code like a senior", "Research and understanding", "Big projects, fewer tokens", "Design and visuals" và "Writing and video". Chân ảnh ghi: "GitHub stars read 23/10/2026. All free. Find each one on GitHub by its name." (nguồn: ảnh [S1]). Ảnh không ghi địa chỉ GitHub của repo nào, nên người viết phải khớp tên với owner/repo; kết quả khớp và commit đã đọc nằm trong `facts-snapshot.json` cạnh báo cáo.

Phương pháp: với mỗi repo, người viết clone nông, không tải nội dung file (`git clone --depth 1 --filter=blob:none --no-checkout`), ghi commit `HEAD`, đếm file bằng `git ls-tree` và đọc README bằng `git show`. Người viết đếm: 30 repo, 30 README, 33 nguồn trong danh sách cuối bài (30 README, ảnh, và hai file của repo GitHub Radar) [S1][S32][S33].

Radar của repo này đã viết bài học cho 5 trong 30 repo: ECC, REA, Agent Reach, UI UX Pro Max và Impeccable; 25 repo còn lại chưa có bài (người viết đếm từ trạng thái "done" và "todo" trong danh sách kiểm) [S33]. Báo cáo này không thay thế các bài đó: nó là bản đồ chung, còn bài radar đi sâu từng repo.

Kiểm tra độ tin của số sao trong ảnh bằng số radar từng đo [S32]. Người viết đếm: tám repo (Ponytail, Graphify, Career Ops, Claude-Mem, Headroom, Taste, Archify, I Have ADHD) có hai mốc đo quanh ngày 23/10, ngày 21/10 và ngày 24/10, và số làm tròn trong ảnh nằm giữa hai mốc ở cả tám repo. Ví dụ Ponytail đo được 170.154 sao ngày 21/10 và 174.930 sao ngày 24/10, ảnh ghi 174k [S32][S1]. Ba ví dụ khác: Graphify 130.545 và 133.991 sao (ảnh 133k), Career Ops 76.062 và 76.863 sao (ảnh 77k), Archify 86.603 và 88.372 sao (ảnh 88k) [S32][S1]. ECC đo được 285.034 sao ngày 21/10, ảnh ghi 287k; chênh khoảng 2.000 sao sau hai ngày, **suy luận** là hợp lý với nhịp tăng của repo [S32][S1]. REA là ngoại lệ: radar đo 293.881 sao ngày 17/10, ảnh ghi 371k, chênh 77.119 sao trong sáu ngày, lớn hơn nhiều nhịp của mọi repo khác, nên người viết không dùng số sao của REA ở bất cứ chỗ nào (người viết đếm; lý do chưa rõ) [S32][S1].

## Nhóm 1: Viết code như dân senior

Sáu repo cùng giải một bài toán: agent viết code nhanh nhưng làm sai thói quen của kỹ sư giỏi, như đoán ý, làm quá tay, quên kiểm tra. Mỗi repo chọn một cách khác nhau để kéo agent về kỷ luật, từ một file quy tắc đến cả một quy trình.

### Superpowers · 304k sao trong ảnh

Ảnh mô tả: "Plans, tests and checks its work" (nguồn: ảnh [S1]). README tự gọi mình là "a complete software development methodology" cho coding agent, xây trên các skill ghép được [S2]. Khi agent thấy bạn đang xây thứ gì, nó không lao vào viết code mà hỏi lại mục đích, đưa spec từng đoạn ngắn, lập kế hoạch rồi chạy quy trình *subagent-driven-development*, nhấn mạnh TDD "red/green", YAGNI và DRY [S2]. Cài cho Claude Code: `/plugin install superpowers@claude-plugins-official` [S2]. Người viết đếm: thư viện có 15 skill và đúng 15 thư mục `skills/*/SKILL.md`; README có 16 mục hướng dẫn cài theo từng agent [S2]. Cẩn thận: README có mục "Commercial Services" mời doanh nghiệp liên hệ để được hỗ trợ thương mại, và mục telemetry cho biết logo của tính năng visual companion mặc định tải từ website của tác giả kèm phiên bản Superpowers; tắt bằng biến `SUPERPOWERS_DISABLE_TELEMETRY` [S2].

### Matt Pocock Skills · 301k sao

Ảnh mô tả: "Grills your plan, then builds with tests" (nguồn: ảnh [S1]). README đặt tên "Skills For Real Engineers" và nói đây là skill tác giả dùng hằng ngày, "not vibe coding" [S3]. Điểm đáng chú ý là lập trường: README nêu GSD, BMAD và Spec-Kit như cách "owning the process", làm bạn mất kiểm soát, còn các skill này nhỏ, ghép được và dễ sửa [S3]. GSD và BMAD đứng ở nhóm 3 của chính ảnh này. Cài cho Claude Code: `claude plugin install mattpocock-skills@claude-plugins-official`, sau đó chạy `/setup-matt-pocock-skills` [S3]. README dặn chọn một đường cài cho mỗi agent, vì cài cả plugin lẫn bản chép file sẽ có mỗi skill hai lần [S3]. Cẩn thận (**suy luận**): README kèm lời mời đăng ký bản tin của tác giả, "~60,000" người đã đăng ký, nên đây vừa là bộ skill vừa là kênh của một người dạy học [S3].

### ECC · 287k sao

Ảnh mô tả: "Skills, memory and security in one" (nguồn: ảnh [S1]). README mô tả một hệ thống kỹ thuật phối hợp cho agent: lập kế hoạch, kiểm thử, tự review ở ngữ cảnh mới, ghi nhớ và biến thành công lặp lại thành skill, với chuỗi "plan -> test -> implement -> review -> verify -> remember -> improve" [S4]. README nêu 71 agent, 311 skill và 97 lệnh [S4]; người viết đếm được đúng 311 thư mục `skills/*/SKILL.md`, khớp con số của README. Cài cho Claude Code: `/plugin marketplace add https://github.com/affaan-m/ECC` rồi `/plugin install ecc@ecc`; README dặn chọn một đường duy nhất, đừng cài tay chồng lên plugin [S4]. Cẩn thận: README mở đầu bằng cảnh báo "Official sources only", vì bản sao không chính thức "may contain malware" [S4]. Người viết đếm: README dài 115.595 byte và repo có 4.627 file, nên đây là repo lớn nhất nhóm để đọc kỹ [S4]. Có thêm lớp thương mại: ECC Pro là GitHub App cho repo riêng tư, giá ghi "from $19/seat/mo" [S4].

### Karpathy Skills · 222k sao

Ảnh mô tả: "One CLAUDE.md for better code" (nguồn: ảnh [S1]). README tự mô tả là một file `CLAUDE.md` duy nhất, "derived from" các quan sát của Andrej Karpathy về lỗi của LLM khi viết code; repo nằm dưới tên chủ `forrestchang` và README mở đầu bằng lời giới thiệu dự án khác của tác giả [S5]. Bốn nguyên tắc: Think Before Coding, Simplicity First, Surgical Changes và Goal-Driven Execution [S5]. Cài cho Claude Code: `/plugin marketplace add forrestchang/andrej-karpathy-skills` rồi `/plugin install andrej-karpathy-skills@karpathy-skills`; hoặc tải thẳng file về từng dự án bằng `curl -o CLAUDE.md` [S5]. README có mục "Tradeoff Note": các nguyên tắc nghiêng về cẩn trọng hơn tốc độ [S5]. Người viết đếm: repo chỉ có 9 file và không có file LICENSE ở gốc, dù README ghi MIT; ngoài ra `multica-ai/andrej-karpathy-skills` trỏ tới cùng commit `2c60614` với repo này, nên ảnh không cho biết chính xác repo nào [S5]. Đây là repo nhỏ nhất của cả 30, dễ đọc hết trước khi cài.

### Ponytail · 174k sao

Ảnh mô tả: "Less code. The simplest fix wins" (nguồn: ảnh [S1]). README dùng hình ảnh một đồng nghiệp lâu năm nhìn năm mươi dòng code rồi thay bằng một dòng, và đặt người đó vào trong agent [S6]. Luật của repo: viết đúng thứ tác vụ cần, không bao giờ cắt kiểm tra đầu vào, xử lý lỗi, bảo mật hay khả năng truy cập [S6]. Ví dụ trong README: chọn ngày, agent thường cài thư viện hoặc tự dựng lịch dài 335 dòng, còn Ponytail dùng thành phần `Input` sẵn có cộng bộ chọn ngày của trình duyệt, 10 dòng [S6]. Số liệu tác giả tự công bố, người viết không kiểm: ít hơn 53% code, 41% thời gian, 26% chi phí, 45% token, và 98% logic rủi ro đi kèm test, so với 68% khi không dùng [S6]. Cài: `/plugin marketplace add DietrichGebert/ponytail` rồi `/plugin install ponytail@ponytail`; lệnh `/ponytail-review` và `/ponytail-audit` rà code đã có [S6]. Cẩn thận: README dặn chỉ cài từ `DietrichGebert/ponytail` và nói bản sao nào kèm file `.exe` hay `.dll` thì không phải của tác giả [S6].

### Agent Skills · 109k sao

Ảnh mô tả: "Senior engineering habits, step by step" (nguồn: ảnh [S1]). README định vị là "Production-grade engineering skills for AI coding agents", mã hóa quy trình, cổng chất lượng và thực hành của kỹ sư senior thành các skill, theo sáu bước DEFINE, PLAN, BUILD, VERIFY, REVIEW, SHIP [S7]. Có 9 lệnh gạch chéo ứng với vòng đời: `/spec`, `/plan`, `/build`, `/test`, `/constraints`, `/review`, `/webperf`, `/code-simplify` và `/ship` [S7]. Cài nhanh cho mọi agent: `npx skills add addyosmani/agent-skills`, README nói trình cài này vào được hơn 70 agent [S7]. Người viết đếm: README ghi 25 skill và cây thư mục có đúng 25 thư mục `skills/*/SKILL.md` [S7]. Cẩn thận: trong Claude Code, `/review` trùng tên lệnh có sẵn nên phải gọi dạng `/agent-skills:review` [S7]. Lệnh `/build auto` chạy cả kế hoạch trong một lượt sau khi bạn duyệt kế hoạch một lần; README nói nó vẫn dừng khi gặp lỗi hoặc bước rủi ro [S7].

## Nhóm 2: Nghiên cứu và hiểu

Sáu repo cho agent "mắt" và "trí nhớ ngoài": dịch ngược một ứng dụng, biến mã nguồn thành đồ thị, đọc những nơi agent bình thường không vào được, hoặc nghiên cứu một chủ đề từ nhiều nền tảng.

### REA · 371k sao trong ảnh

Ảnh mô tả: "Shows how any app really works" (nguồn: ảnh [S1]). Số sao của ảnh bị loại khỏi báo cáo vì lệch với số radar đo (phần "Ảnh nói gì"). README: "One MCP for reverse engineering across binaries, applications, and runtime behavior", nối agent với công cụ phân tích file nhị phân gốc, ứng dụng JavaScript và Electron, assembly .NET và website; phân tích chạy trên máy bạn và kết quả kèm bằng chứng cùng giới hạn [S8]. Cài: `npx rea-agents setup` [S8]. Phân tích file gốc có thể dùng Hopper, Ghidra hoặc IDA đã cài, và README nhấn mạnh phải có quyền hợp pháp với công cụ thương mại [S8]. Cẩn thận: README nói REA dành cho nghiên cứu hợp pháp, giáo dục, tương tác, bảo tồn phần mềm và phân tích phần mềm bạn sở hữu hoặc được phép xem xét [S8]. README cũng cảnh báo tên repo giống hay README chép lại không chứng minh một bản tải về là chính thức [S8]. Người viết đếm: repo có 6.278 file [S8].

### Graphify · 133k sao

Ảnh mô tả: "Turns docs and code into a map" (nguồn: ảnh [S1]). Gõ `/graphify` trong trợ lý AI, nó lập bản đồ cả dự án (code, tài liệu, PDF, ảnh, video) thành đồ thị tri thức để truy vấn thay vì grep [S9]. Code được phân tích cục bộ bằng tree-sitter, không dùng LLM; tài liệu, PDF và ảnh dùng mô hình của trợ lý hoặc khóa API bạn cấu hình [S9]. Mỗi cạnh được gắn nhãn `EXTRACTED` (nằm sẵn trong nguồn) hoặc `INFERRED` (do graphify suy ra), nên phân biệt được điều đọc trực tiếp với điều suy diễn [S9]. Cài, cần Python 3.10+ và uv: `uv tool install graphifyy`, `graphify install`, rồi `/graphify .` [S9]. Kết quả là ba file: `graph.html`, `GRAPH_REPORT.md` và `graph.json` [S9]. README nói xử lý khoảng 40 ngôn ngữ và nêu "0.497 recall@10" làm điểm benchmark của tác giả [S9]. Cẩn thận: tên gói có hai chữ y (`graphifyy`), nên chép đúng từ README; repo có Graphify Cloud, bản chạy nền trả phí với 14 ngày dùng thử [S9].

### Agent Reach · 101k sao

Ảnh mô tả: "Reads X, Reddit and YouTube free" (nguồn: ảnh [S1]). README viết bằng tiếng Trung: giúp agent dùng những nơi nó thường không vào được, như tính năng cần đăng nhập, nội dung trong video, nền tảng tiếng Trung và dữ liệu có cấu trúc, qua lệnh dạng `agent-reach channels` [S10]. Người viết đếm: bảng nền tảng có 14 kênh, gồm 5 mặc định (bilibili, v2ex, github, youtube, web), 6 tùy chọn và 3 thử nghiệm (twitter, facebook, instagram) [S10]. Điều này làm mô tả "free" của ảnh cần đọc kỹ: Reddit là kênh tùy chọn cần đăng nhập, còn Twitter là kênh thử nghiệm cũng cần đăng nhập; YouTube chuyển giọng nói thành chữ cần khóa Groq hoặc OpenAI [S10]. Cài bằng cách đưa cho agent một câu yêu cầu cài từ file `docs/install.md` trên GitHub; README cảnh báo gói `agent-reach` trên PyPI không phải dự án này [S10]. Cẩn thận: với nền tảng cần đăng nhập, lần đầu dùng nó sao chép phiên đăng nhập của trang đó từ Chrome sang trình duyệt riêng của công cụ, và README khuyên dùng tài khoản phụ [S10].

### Understand Anything · 87k sao

Ảnh mô tả: "Explains any codebase visually" (nguồn: ảnh [S1]). README: plugin cho Claude Code chạy quy trình nhiều agent để dựng đồ thị tri thức của từng file, hàm, lớp và phụ thuộc, rồi mở bảng điều khiển tương tác để khám phá [S11]. Cài: `/plugin marketplace add Egonex-AI/Understand-Anything`, `/plugin install understand-anything`, rồi chạy `/understand`; đồ thị lưu ở `.ua/knowledge-graph.json` [S11]. Lệnh `/understand-knowledge` dựng đồ thị cho một wiki kiểu Karpathy [S11]. Cẩn thận (người viết đếm): README bảo thêm marketplace của `Egonex-AI`, còn repo người viết đọc nằm ở `Lum1104/Understand-Anything`; hai tên chủ khác nhau, nên hãy kiểm tên chủ trước khi cài [S11].

### Career Ops · 77k sao

Ảnh mô tả: "Scores job ads against your CV" (nguồn: ảnh [S1]). README kể câu chuyện của tác giả: 740 tin tuyển dụng được đánh giá, 68 lần nộp, 12 buổi phỏng vấn, 1 lời mời làm việc; đây là lời tác giả, người viết không kiểm [S12]. Bạn dán một tin tuyển dụng, nó kiểm tin còn mở không, chấm độ hợp với CV, soạn CV và câu trả lời để bạn đọc rồi tự bấm gửi [S12]. Cài: `npx @santifer/career-ops init` [S12]. README liệt kê điều nó sẽ không làm: tự nộp đơn, gửi email, gọi về máy chủ, và nó khuyên không nộp khi điểm dưới 4.0/5 [S12]. Cẩn thận: README cũng nói CV của bạn đi từ máy tới nhà cung cấp AI bạn chọn và không đi đâu khác; mã dùng giấy phép MIT còn tên và thương hiệu theo chính sách nhãn hiệu riêng [S12]. Người viết đếm: repo có 2.674 file, README dài 47.581 byte [S12].

### Last 30 Days · 65k sao

Ảnh mô tả: "Researches Reddit, X, YouTube and more" (nguồn: ảnh [S1]). README gọi nó là công cụ tìm kiếm do agent dẫn dắt, chấm điểm bằng lượt upvote, lượt thích và tiền thật, không phải biên tập viên [S13]. Cài cho Claude Code: `/plugin marketplace add mvanhorn/last30days-skill` rồi `/plugin install last30days`; cho các host khác: `npx skills add mvanhorn/last30days-skill -g` [S13]. Không cần cấu hình: Reddit, HN, Polymarket và GitHub dùng được ngay; trình hướng dẫn mở khóa X, YouTube, TikTok, arXiv và Techmeme sau đó [S13]. Có mục "Bring your own keys" nên nhiều nguồn cần khóa hoặc phiên trình duyệt của bạn [S13]. Về dữ liệu: mặc định chạy trên máy bạn; chỉ khi bạn đặt khóa của nhà cung cấp mô hình thì chủ đề và đoạn trích mới được gửi đi để xếp hạng lại [S13].

## Nhóm 3: Dự án lớn, ít token hơn

Sáu repo xử lý hai nỗi đau của dự án lớn: ngữ cảnh đắt và quy trình trôi. Ba repo giảm token (Caveman, Headroom, Claude-Mem), hai repo là khung quy trình (BMAD, GSD) và gstack là cả đội ảo.

### gstack · 137k sao

Ảnh mô tả: "A CEO, designer and QA team" (nguồn: ảnh [S1]). Tác giả là Garry Tan, README biến Claude Code thành đội kỹ thuật ảo: CEO nghĩ lại sản phẩm, quản lý kỹ thuật chốt kiến trúc, nhà thiết kế bắt "AI slop", người review tìm lỗi, QA mở trình duyệt thật, người kiểm bảo mật chạy OWASP và STRIDE, kỹ sư phát hành đẩy PR [S14]. README nói có hai mươi ba chuyên gia và tám công cụ, toàn lệnh gạch chéo và Markdown [S14]. Tác giả tự công bố tốc độ năm 2026 gấp khoảng 810 lần năm 2013 theo thước đo "dòng code logic"; số này là của tác giả và có tài liệu phương pháp riêng, người viết không kiểm [S14]. Cài: dán cho Claude Code một câu bảo nó chạy `git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup` và thêm một mục vào CLAUDE.md [S14]. Cẩn thận (**suy luận**): đây là kiểu cài đưa chuỗi lệnh cho agent chạy, nên đọc script `./setup` trước; người viết chưa chạy nó. Telemetry mặc định tắt, hỏi một lần ở lần chạy đầu [S14]. Người viết đếm: README dài 89.520 byte, repo có 3.959 file [S14].

### Caveman · 114k sao

Ảnh mô tả: "Shorter replies, fewer tokens" (nguồn: ảnh [S1]). Ví dụ của README: cùng một cách sửa lỗi React render lại, câu trả lời thường tốn 63 token, bản "caveman" tốn 20 token, mã vẫn giữ nguyên [S15]. Cài: `npx @caveman-ai/cli@latest`, cần Node.js 22.13+, chạy được trên Mac, Linux và Windows [S15]. README chia thành sáu phần (nói ngắn, đọc ít, tự động, khối mã...) và nêu số đo của chính tác giả như 33,2% token đầu vào ít hơn và 54% rẻ hơn với điểm số như cũ [S15]. Cẩn thận: README dẫn các thử nghiệm bên ngoài (Adobe Research, Elastic, JetBrains) nhưng người viết không mở các liên kết đó [S15]. Giấy phép Apache-2.0 cho cả repo, riêng tên "Caveman" và logo là nhãn hiệu của tác giả, và có Caveman Cloud cho agent do bạn tự xây [S15].

### Claude-Mem · 102k sao

Ảnh mô tả: "Remembers past sessions" (nguồn: ảnh [S1]). README: lưu lại ngữ cảnh giữa các phiên bằng cách tự ghi các quan sát về lần dùng công cụ, tạo tóm tắt ngữ nghĩa và đưa cho phiên sau [S16]. Cài: `npx claude-mem install` [S16]. Bộ cài mở trình duyệt để đăng nhập và mở khóa "claude-mem observer" với 30 ngày dùng thử; hết thời hạn, bộ nhớ tự quay lại dùng gói Anthropic của bạn trừ khi bạn đăng ký; có thể bỏ qua đăng nhập bằng cờ `--provider` hoặc đặt `CLAUDE_MEM_ONLINE_OPTIN=false` [S16]. Cẩn thận: mục cuối README nhắc một token tiền mã hóa "CMEM" do bên thứ ba tạo và được tác giả "officially embraced"; người viết ghi lại để bạn biết, không đánh giá gì về nó [S16]. Giấy phép Apache-2.0; người viết đếm: repo có 2.735 file [S16].

### Headroom · 77k sao

Ảnh mô tả: "Shrinks files before Claude reads them" (nguồn: ảnh [S1]). README: nén kết quả công cụ, log, đoạn RAG, file và lịch sử hội thoại trước khi tới LLM, và nói việc nén chạy trên máy bạn [S17]. Có nhiều chế độ: thư viện `compress(messages)`, proxy `headroom proxy --port 8787`, bọc agent bằng `headroom wrap claude`, hoặc MCP server [S17]. Cài: `uv tool install --python 3.13 "headroom-ai[all]"` [S17]. Bốn kịch bản benchmark của README (đã gieo hạt, chạy offline được) tiết kiệm từ 21% đến 57% token tùy mức lặp của dữ liệu [S17]. Cẩn thận: có một beacon ẩn danh bật mặc định, tắt bằng `HEADROOM_TELEMETRY=off`; và có bản Enterprise cho đội ngũ bên cạnh bản mã nguồn mở [S17]. So với Caveman: Headroom nén thứ agent đọc, Caveman rút gọn thứ agent viết ra (**suy luận**).

### GSD · 64k sao

Ảnh mô tả: "Plans big builds so nothing drifts" (nguồn: ảnh [S1]). Nhưng README của repo này chỉ còn một thông báo "GSD Has Moved": repo không còn là nơi phát triển chính, dự án tiếp tục với tên GSD Core ở kho `open-gsd/gsd-core` [S18]. Người viết đếm: README dài 329 byte trong khi cây thư mục vẫn còn 1.854 file [S18]. Vì README không mô tả tính năng nào, báo cáo này không mô tả GSD và chưa đọc kho mới. **Suy luận**: nếu muốn dùng GSD, hãy bắt đầu từ kho được README chỉ tới, không phải từ tên trong ảnh. Cũng cần lưu ý số 64k sao trong ảnh gắn với repo cũ [S1].

### BMAD Method · 54k sao

Ảnh mô tả: "An agile team of AI agents" (nguồn: ảnh [S1]). README định nghĩa "Agile Ai Driven Development": biến ý tưởng hoặc yêu cầu thay đổi thành phần mềm chạy được mà không bỏ phần suy nghĩ; việc nhỏ đi thẳng tới build, việc phức tạp được đào sâu [S19]. Có hai nhánh: bản ổn định v6.12 cài bằng `npx bmad-method install` (cần Node.js 20.12+ và Python 3.10+), và V7 bản xem trước alpha cài bằng `npx skills add bmad-code-org/BMAD-METHOD --skill '*'` [S19]. Cẩn thận: README ghi ngày phát hành V7 dự kiến là 16/10/2026, đã qua so với ngày người viết đọc (25/10/2026) mà README vẫn gọi V7 là bản xem trước alpha; **suy luận** là lịch đã trượt hoặc README chưa được cập nhật [S19]. "BMad" và "BMAD-METHOD" là nhãn hiệu của BMad Code, LLC [S19].

## Nhóm 4: Thiết kế và hình ảnh

Sáu repo dạy agent những thứ nó hay làm xấu: giao diện, định hướng thẩm mỹ, sơ đồ và slide. Điểm chung là cố ép đầu ra khỏi "mặt trung bình" của mô hình.

### UI UX Pro Max · 139k sao

Ảnh mô tả: "A designer's eye for apps and sites" (nguồn: ảnh [S1]). README: skill cung cấp "design intelligence" cho UI/UX trên nhiều nền tảng; tính năng chính của v2.0 là bộ sinh hệ thống thiết kế, phân tích yêu cầu dự án rồi sinh một hệ thống thiết kế riêng [S20]. Cài: `npm install -g ui-ux-pro-max-cli`, vào dự án rồi `uipro init --ai claude` [S20]. README mô tả 192 loại sản phẩm, 79 kiểu giao diện (50 đang bật) và hướng dẫn cho 22 framework [S20]. Cẩn thận: README có mục so sánh bản Basic (chính repo này) với bản Premium, bản Premium thêm nhận diện thương hiệu, logo, ảnh do AI sinh, kiến trúc design token cho đội lớn và hỗ trợ ưu tiên [S20]. Một số lệnh thiết kế cần Python [S20].

### Taste · 101k sao

Ảnh mô tả: "Gives Claude art direction" (nguồn: ảnh [S1]). README: skill giúp agent thiết kế website và màn hình ứng dụng thay vì ghép "trang đích trung bình", với định hướng nghệ thuật, ảnh thật và cách tự kiểm bằng trình duyệt thật [S21]. Một lượt dựng gồm sáu bước: đọc brief, một script chia ba trong 20 hướng đã nghiên cứu cho agent chọn, tìm ý tưởng, dựng với ảnh và video từ kho mở có ghi nguồn, kiểm trên trình duyệt ở ba chiều rộng, rồi tự xem ảnh chụp và sửa tối đa ba vòng [S21]. Cài: `npx skills add https://github.com/Leonxlnx/taste-skill --skill "design-taste-frontend"`; cần Node 22+ và Chrome, Edge hoặc Chromium [S21]. Cẩn thận: README nói một lượt dựng mất khoảng 30 đến 45 phút và vài trăm nghìn token [S21]. Repo hiện chỉ giữ một skill; các skill cũ đã chuyển sang kho khác với cùng tên cài [S21].

### Archify · 88k sao

Ảnh mô tả: "Turns any idea into a diagram" (nguồn: ảnh [S1]). README: bạn mô tả ý tưởng, agent vẽ sơ đồ kiến trúc; không cần có repo, hoặc nhờ agent đọc một repo để ra sơ đồ có dẫn nguồn [S22]. Cài: `npx skills add tt-a1i/archify -g` [S22]. Ngoài sơ đồ còn có kiểu "explainer": trả lời một câu hỏi bằng một trang, kết luận trước, mỗi ô một câu hỏi, sơ đồ đã kiểm; xuất một file HTML với bốn phong cách, sáng hoặc tối, và xuất ảnh PNG, WebP, JPG hoặc in ra PDF [S22]. Cẩn thận: README có mục "Official channels and third-party services" và nói dịch vụ trực tuyến của bên thứ ba cùng gói trả phí không thuộc dự án [S22].

### Impeccable · 85k sao

Ảnh mô tả: "A design language for Claude" (nguồn: ảnh [S1]). README: 1 skill, 24 lệnh, 62 quy tắc phát hiện xác định cho giao diện do AI sinh [S23]. Nó xuất phát từ skill frontend-design của Anthropic và nhắm vào các "dấu hiệu" quen thuộc, như Inter cho mọi thứ, gradient tím sang xanh, thẻ lồng thẻ [S23]. Cài: `npx impeccable install`, rồi chạy `/impeccable init` trong công cụ AI để ghi `PRODUCT.md`; `DESIGN.md` ghi hệ thống thị giác của dự án [S23]. Cẩn thận: README có mục Telemetry, khi bắt đầu một thiết kế, skill gọi API của impeccable.style để chia "ván bài" các thế giới thị giác, và nếu bạn không từ chối thì còn gửi một bản ghi ẩn danh về lựa chọn [S23]. Giấy phép Apache 2.0 [S23].

### PPT Master · 67k sao

Ảnh mô tả: "Real, editable PowerPoint decks" (nguồn: ảnh [S1]). README: AI tạo PowerPoint gốc từ tài liệu bất kỳ, với slide master, hình gốc, biểu đồ và bảng có dữ liệu thật, không phải hộp chữ phẳng hay mẫu điền sẵn [S24]. Cách chạy là quy trình bên trong một công cụ AI có agent, dữ liệu ở lại máy bạn [S24]. Chỉ cần Python 3.10+, rồi `pip install -r requirements.txt` sau khi tải dự án [S24]. Cẩn thận: README mở đầu bằng thông tin tác giả đang tìm cơ hội việc và nhiều nhà tài trợ có liên kết giới thiệu (có tham số `aff=`), nên phần đầu README dài hơn phần kỹ thuật [S24]. Người viết đếm: repo có 13.111 file, lớn nhất trong 30 repo, nên không thể đọc hết trong một buổi [S24].

### Diagram Design · 60k sao

Ảnh mô tả: "Clean editorial diagrams" (nguồn: ảnh [S1]). README: skill vẽ sơ đồ thành một file HTML kèm SVG tự chứa, theo thương hiệu của bạn, với 45 kiểu sơ đồ và "No Mermaid slop" [S25]. Cài: `npx skills add cathrynlavery/diagram-design`, hoặc trong Claude Code `/plugin marketplace add cathrynlavery/diagram-design` rồi `/plugin install diagram-design@diagram-design` [S25]. Bạn có thể nhập từ draw.io, Mermaid hay Excalidraw và xuất PNG hoặc SVG [S25]. Cẩn thận: README nói bản chính thức chỉ đến từ repo này, một danh mục plugin dưới tên khác là bản sao không chính thức, và `PRIVACY.md` liệt kê những gì skill gửi qua mạng [S25]. Ghi chú: bản đọc không có mục License trong README; giấy phép nằm ở file LICENSE (xem phần Lưu ý) [S25].

## Nhóm 5: Viết lách và video

Sáu repo mở rộng agent ra ngoài code: viết sạch hơn, trả lời gọn hơn, làm marketing, làm video và học cách Anthropic tự viết skill. Người viết đếm số file của sáu repo: Skills của Anthropic 445, OpenMontage 2.208, HyperFrames 9.179, Humanizer 14, I Have ADHD 74 và Marketing Skills 770, nên hai xưởng video là hai repo nặng nhất nhóm [S26][S27][S28][S29][S30][S31].

### Skills (Anthropic) · 183k sao

Ảnh mô tả: "Word, Excel, PowerPoint and PDF" (nguồn: ảnh [S1]). README: đây là bản cài đặt skill của Anthropic cho Claude, gồm các skill từ sáng tạo (nghệ thuật, âm nhạc, thiết kế) đến kỹ thuật (kiểm thử ứng dụng web, tạo máy chủ MCP) và quy trình doanh nghiệp [S26]. Mỗi skill là một thư mục có file `SKILL.md`; người viết đếm: 19 thư mục dưới `skills/` [S26]. Đăng ký làm marketplace trong Claude Code bằng `/plugin marketplace add anthropics/skills`, rồi cài `/plugin install document-skills@anthropic-agent-skills` hoặc `/plugin install example-skills@anthropic-agent-skills` [S26]. Cẩn thận: README nói nhiều skill dùng Apache 2.0, nhưng các skill tài liệu `docx`, `pdf`, `pptx`, `xlsx` là "source-available, not open source"; mọi skill chỉ để minh họa và giáo dục, phải tự kiểm trước khi dùng cho việc quan trọng [S26]. Người viết đếm: ở gốc repo không có file LICENSE [S26]. Đây cũng là chỗ học cách viết skill, vì README có mục "Creating a Basic Skill" [S26].

### OpenMontage · 71k sao

Ảnh mô tả: "A full AI video studio" (nguồn: ảnh [S1]). README: biến trợ lý code thành xưởng sản xuất video, bạn mô tả bằng lời, agent lo nghiên cứu, kịch bản, tạo tài nguyên, dựng và ghép cuối [S27]. Cài: `git clone https://github.com/calesthio/OpenMontage.git`, `cd OpenMontage`, rồi `make setup` [S27]. Có đường không cần khóa API trả phí: giọng đọc Piper TTS offline, cảnh quay mở từ Archive.org, NASA và Wikimedia Commons, kho miễn phí Pexels, Unsplash, Pixabay [S27]. Chi phí các ví dụ khi dùng nhà cung cấp trả phí được README ghi: một phim 60 giây hết 1,33 đô la, một phim khác khoảng 4 đô la [S27]. Cẩn thận: giấy phép là GNU AGPLv3, giấy phép copyleft mạnh, nên điều kiện dùng khi sửa và cung cấp dịch vụ khác với MIT hay Apache [S27]. Người viết đếm: 2.208 file [S27].

### HyperFrames · 70k sao

Ảnh mô tả: "Turns HTML into video" (nguồn: ảnh [S1]). README: khung mã nguồn mở biến HTML, CSS, media và hoạt ảnh tua được thành video MP4 xác định, dùng qua CLI, qua agent có skill, hoặc làm lõi dựng cho quy trình soạn thảo trên đám mây [S28]. Cài cho Claude Code: `claude plugin marketplace add heygen-com/hyperframes` rồi `claude plugin install hyperframes@hyperframes`; cho skill rời: `npx skills add heygen-com/hyperframes` [S28]. Người viết đếm: README ghi 7 skill và cây thư mục có đúng 7 thư mục `skills/*/SKILL.md` [S28]. README có mục "HyperFrames vs Remotion" so sánh với một khung dựng video React quen thuộc. Giấy phép Apache 2.0 [S28]. Người viết đếm: repo có 9.179 file [S28]. OpenMontage cũng dùng HyperFrames như một đường dựng, nên hai repo này chạm nhau (**suy luận** từ README của OpenMontage) [S27].

### Humanizer · 59k sao

Ảnh mô tả: "Strips the AI tells from writing" (nguồn: ảnh [S1]). README: làm văn bản do AI viết nghe như người viết mà không đổi ý, dựa trên hướng dẫn "Signs of AI writing" của Wikipedia, gồm 26 mẫu [S29]. Năm dấu hiệu mạnh nhất: "Not X but Y", câu chốt một dòng, câu nghe sâu sắc, màn dẫn dắt dàn dựng, và tranh cãi với một người không có mặt [S29]. Cài cho Claude Code: `/plugin marketplace add blader/humanizer` rồi `/plugin install humanizer@humanizer`; cần Claude Code 2.1.142 trở lên, bản cũ hơn dùng `npx skills add blader/humanizer --global --agent claude-code` [S29]. Tác giả nêu một thử nghiệm mù, giám khảo chọn bản viết lại 16 trên 16 lần; đây là số của tác giả [S29]. Cẩn thận: README nói rõ vượt qua bộ phát hiện AI không phải mục tiêu và các bộ phát hiện vẫn đánh dấu phần lớn đầu ra của nó [S29]. Người viết đếm: 14 file, repo nhỏ thứ hai sau Karpathy Skills [S29].

### I Have ADHD · 58k sao

Ảnh mô tả: "Puts the answer first" (nguồn: ảnh [S1]). README: skill ngăn trợ lý chôn câu trả lời; hành động trước, các bước đánh số, không có "Hope this helps!" [S30]. Mười quy tắc, như dẫn bằng bước tiếp theo, đánh số tác vụ nhiều bước, giới hạn danh sách ở 5 mục, và không mở bài, không tóm tắt, không câu chốt [S30]. Cài: dán cho agent câu `Install the i-have-adhd skill/plugin from https://github.com/ayghri/i-have-adhd, refer to the repo's AGENTS.md for instructions.` [S30]. Muốn chỉnh, tạo bản sao rồi sửa `skills/i-have-adhd/SKILL.md` [S30]. Cẩn thận: README ghi "ADHD-friendly outputs. No ADHD diagnosis needed!" và nói nó dựa lỏng lẻo trên một cuốn sách về ADHD ở người lớn; đây là cách định dạng câu trả lời, không phải công cụ y tế [S30]. Người viết đếm: repo có 74 file [S30].

### Marketing Skills · 56k sao

Ảnh mô tả: "Copywriting, SEO and CRO skills" (nguồn: ảnh [S1]). README: bộ skill cho tác vụ marketing, nhắm vào người làm marketing kỹ thuật và nhà sáng lập, gồm tối ưu chuyển đổi, viết quảng cáo, SEO, phân tích và kỹ thuật tăng trưởng [S31]. Người viết đếm: bảng "Available Skills" có 52 skill, khớp 52 thư mục `skills/*/SKILL.md`, chia thành 9 nhóm như Conversion Optimization và Content & Copy [S31]. Cài: `npx skills add coreyhaines31/marketingskills`, thêm `--list` để xem trước danh sách [S31]. Cẩn thận: thư viện miễn phí và dùng giấy phép MIT, nhưng README liệt kê "Verified Partners" tài trợ cho công việc, kèm dịch vụ của chính tác giả như công ty tư vấn và khóa học [S31]. README nói đối tác không ảnh hưởng nội dung skill lõi; người viết không kiểm điều đó [S31].

## Bốn cách cài và điều chúng đòi hỏi

Người viết đếm bốn cách cài trong 30 README, và nhiều repo có nhiều cách song song.

Cách một, marketplace của Claude Code: `/plugin marketplace add <owner>/<repo>` rồi `/plugin install <plugin>@<marketplace>`. Dùng ở Ponytail [S6], Karpathy Skills [S5], Humanizer [S29], Diagram Design [S25], Last 30 Days [S13], Understand Anything [S11] và ECC [S4]. Superpowers [S2] và Matt Pocock Skills [S3] còn cài qua marketplace tên `claude-plugins-official`, và HyperFrames dùng dạng `claude plugin marketplace add` [S28]. Ưu điểm: Claude Code quản lý cập nhật.

Cách hai, `npx skills add <owner>/<repo>`: trình cài dùng chung cho nhiều agent. Dùng ở Agent Skills [S7], Taste [S21], Archify [S22], Marketing Skills [S31], Diagram Design [S25], HyperFrames [S28], Last 30 Days [S13] và BMAD V7 [S19]. Ưu điểm: một lệnh cho nhiều agent.

Cách ba, trình cài riêng: `npx rea-agents setup` [S8], `npx @santifer/career-ops init` [S12], `npx claude-mem install` [S16], `npx @caveman-ai/cli@latest` [S15], `npx bmad-method install` [S19], `npx impeccable install` [S23], `uv tool install graphifyy` [S9], `npm install -g ui-ux-pro-max-cli` [S20], `make setup` [S27]. Mỗi trình cài làm nhiều việc hơn một lệnh ghi file: có cái mở trình duyệt để đăng nhập [S16], có cái đăng ký một máy chủ MCP [S8].

Cách bốn, dán một câu cho agent tự cài: Agent Reach [S10], I Have ADHD [S30] và gstack [S14] đi theo hướng này. **Suy luận**: đây là cách ít kiểm soát nhất, vì agent sẽ chạy lệnh dựa trên văn bản mà bạn chưa đọc; hãy mở script hoặc file hướng dẫn được nêu trước khi bảo agent chạy.

Điểm chung đáng chú ý: người viết đếm tám README có câu cảnh báo về bản sao không chính thức hoặc đòi cài từ đúng nguồn, gồm ECC [S4], Ponytail [S6], REA [S8], Graphify [S9], Agent Reach [S10], Archify [S22], PPT Master [S24] và Diagram Design [S25]. **Suy luận**: repo nổi tiếng thu hút bản sao giả, nên việc đầu tiên là kiểm đúng owner và tên repo. Hai ví dụ trong chính danh sách này là hai repo cùng một commit cho Karpathy Skills [S5] và hai tên chủ khác nhau của Understand Anything [S11].

## "Miễn phí" nghĩa là gì ở 30 repo này

Chân ảnh ghi "All free" (nguồn: ảnh [S1]). Đọc README, người viết thấy chữ này đúng ở nghĩa "mã nguồn tải được, cài được không tốn tiền bản quyền", nhưng không đủ để biết bạn sẽ tốn gì.

Lớp trả phí hoặc dịch vụ cạnh bản miễn phí, người viết đếm được tám repo: Superpowers có "Commercial Services" cho doanh nghiệp [S2]; ECC có ECC Pro, GitHub App cho repo riêng tư giá từ 19 đô la mỗi chỗ mỗi tháng [S4]; Graphify có Graphify Cloud với 14 ngày dùng thử [S9]; Claude-Mem có observer lưu trữ với 30 ngày dùng thử [S16]; Caveman có Caveman Cloud [S15]; Headroom có bản Enterprise [S17]; UI UX Pro Max có bản Premium [S20]; Marketing Skills có đối tác tài trợ và dịch vụ tư vấn của tác giả [S31]. Điều này không có gì sai, và README đều nói rõ; chỉ là "free" trong ảnh chưa chạm tới các lớp đó.

Giấy phép cần đọc kỹ ở bốn nơi. OpenMontage dùng GNU AGPLv3 [S27]. Skills của Anthropic nói các skill tài liệu là source-available, không phải mã nguồn mở, và ở gốc repo không có file LICENSE [S26]. Karpathy Skills ghi MIT trong README nhưng gốc repo cũng không có file LICENSE (người viết đếm) [S5]. REA yêu cầu bạn tự có quyền hợp pháp với các công cụ thương mại như Hopper hay IDA [S8]. Career Ops và BMAD cũng giữ nhãn hiệu riêng cho tên của mình dù mã là MIT [S12][S19].

Chi phí khác không nằm ở giấy phép: Taste nói một lượt dựng cần vài trăm nghìn token [S21]; OpenMontage nêu chi phí API cho video [S27]; Agent Reach và Last 30 Days cần khóa hoặc phiên đăng nhập cho nhiều nền tảng [S10][S13]. Về dữ liệu gửi đi, người viết tìm các từ khóa telemetry, beacon và analytics trong 30 README. Người viết đếm: bốn README nói thẳng một lời gọi mạng hoặc số liệu dùng được gửi mặc định, gồm Superpowers [S2], Headroom [S17], Impeccable [S23] và Caveman, nơi CLI gửi thống kê dùng kèm ID cài đặt ngẫu nhiên, hệ điều hành và IP, tắt bằng `caveman telemetry off` [S15]. gstack hỏi một lần và mặc định tắt [S14]; Graphify nói không có telemetry [S9] và Career Ops nói không gọi về máy chủ của tác giả [S12]. Các repo còn lại có thể vẫn có lời gọi mạng mà README không dùng những từ đó, nên hãy đọc mục riêng của từng README trước khi bật.

## Chọn ba repo đầu tiên

Cách chọn dưới đây là **suy luận** của người viết cho mục tiêu "hiểu cách skill hoạt động trước, cài sau", không phải xếp hạng chất lượng.

Một: `forrestchang/andrej-karpathy-skills`. Chỉ 9 file, một file `CLAUDE.md` và bốn nguyên tắc [S5]. Bạn đọc hết trong vài phút và hiểu một "file quy tắc" khác một "skill" thế nào. Nhớ rằng repo không có file LICENSE và cùng commit với một repo khác tên [S5].

Hai: `blader/humanizer`. 14 file, một skill duy nhất, 26 mẫu mô tả rõ [S29]. Đây là ví dụ gọn về một skill hoàn chỉnh: tên lệnh, mô tả, danh mục mẫu và ví dụ trước và sau. Nó còn có ích ngay cho việc viết tài liệu.

Ba: `obra/superpowers`. 15 skill ghép nối thành một quy trình từ hỏi ý, lập kế hoạch, viết test đến review [S2]. Sau hai repo nhỏ, bạn sẽ đọc được cách các skill gọi nhau, đó là điều Matt Pocock phê bình ở các khung "sở hữu quy trình" và là chỗ bạn nên tự cân nhắc [S3].

Nếu mục tiêu của bạn khác thì cách chọn khác: muốn bớt token thì bắt đầu từ Caveman hoặc Headroom và đo trên việc của chính bạn, vì mọi số tiết kiệm trong README là số của tác giả [S15][S17]; muốn có sơ đồ hay slide thì Diagram Design, Archify hoặc PPT Master [S25][S22][S24]; muốn làm video thì HyperFrames hoặc OpenMontage, nhớ điều kiện giấy phép [S28][S27].

## Điều cần nhớ

- Ảnh chỉ cho tên, số sao và một câu. Muốn biết thật thì đọc README, và README cũng chỉ là lời của tác giả [S1].
- Hầu hết 30 repo là bộ skill cho coding agent; ba mẫu cần phân biệt là file quy tắc (Karpathy Skills), skill đơn (Humanizer) và chuỗi skill (Superpowers) [S5][S29][S2].
- Cài một repo là chạy mã của người khác. Kiểm đúng owner và tên repo, đọc script cài, và biết lệnh nào mở trình duyệt hay đăng ký MCP [S4][S16][S8].
- "Free" đúng với mã nguồn; tám repo có thêm lớp trả phí, và vài repo có điều khoản giấy phép đặc biệt [S2][S4][S9][S16][S15][S17][S20][S31][S27][S26].
- Mọi số tiết kiệm token trong README là số của tác giả; đo lại trên việc của bạn trước khi tin [S6][S15][S17].
- GSD trong ảnh đã chuyển sang kho khác, và số sao của REA trong ảnh lệch so với số radar đo [S18][S32].
- Năm repo đã có bài radar riêng; 25 repo còn lại chưa có [S33].

## Lưu ý

Giới hạn của nguồn: người viết chỉ đọc README của từng repo ở commit ghim và đếm file trên cây thư mục; không chạy bất kỳ lệnh cài nào, không mở các liên kết ngoài trong README, không đọc mã nguồn bên trong skill. Một README có thể lệch với mã. Mọi con số trong README mà báo cáo nêu (như phần trăm tiết kiệm, số lần phỏng vấn, tốc độ làm việc) là lời tác giả, người viết không kiểm.

Số sao và các dòng mô tả là của ảnh do một người khác dựng; người viết chỉ lấy tên và nhóm và khớp tên với owner/repo. Ảnh không ghi địa chỉ, nên có thể một tên trong ảnh ứng với repo khác, như trường hợp hai repo cùng commit của Karpathy Skills [S1][S5]. Số sao của REA trong ảnh bị bỏ qua (phần "Ảnh nói gì") [S32].

Giấy phép: các câu về giấy phép trong báo cáo là chữ đọc từ đầu file LICENSE và từ README, không phải trường `license` mà GitHub hiển thị; hai repo không có file LICENSE ở gốc là Karpathy Skills và Skills của Anthropic (người viết đếm) [S5][S26]. Báo cáo không phải tư vấn pháp lý.

Một số README chứa chỉ dẫn viết cho agent, ví dụ "paste this" của gstack hay câu cài của I Have ADHD. Người viết coi chúng là đối tượng được mô tả, không phải lệnh để làm theo [S14][S30]. Đây là tài liệu đọc, không phải khuyến nghị cài đặt.

Cách tái lập: facts-snapshot.json ghi commit, tên file README, số byte, số file và số thư mục skill của từng repo; sources.json ghi liên kết ghim commit cho cả 33 nguồn.

## Nguồn tham khảo
- [S1] Ảnh "Top 30 Claude Code Plugins" của Charlie Hills (số sao đọc ngày 23/10/2026), chủ repo gửi; chép lại trong artifacts/plans/top30-claude-plugins.json, 2026
- [S2] obra, README.md của obra/superpowers ở commit 2ce8aa1, 2026, https://github.com/obra/superpowers/blob/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/README.md
- [S3] mattpocock, README.md của mattpocock/skills ở commit 5beb35b, 2026, https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/README.md
- [S4] affaan-m, README.md của affaan-m/ECC ở commit 90606c8, 2026, https://github.com/affaan-m/ECC/blob/90606c8315ee09cafc303515c5f33024db6b9882/README.md
- [S5] forrestchang, README.md của forrestchang/andrej-karpathy-skills ở commit 2c60614, 2026, https://github.com/forrestchang/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/README.md
- [S6] DietrichGebert, README.md của DietrichGebert/ponytail ở commit 09c434a, 2026, https://github.com/DietrichGebert/ponytail/blob/09c434ab73ca43761c5d8b0c5d341926c2fba710/README.md
- [S7] addyosmani, README.md của addyosmani/agent-skills ở commit aeac41d, 2026, https://github.com/addyosmani/agent-skills/blob/aeac41d4d005999432bb7312f7ff06383a91d59d/README.md
- [S8] morluto, README.md của morluto/rea ở commit 80673b2, 2026, https://github.com/morluto/rea/blob/80673b22a46d01899718e22584cf95d9f0529ab7/README.md
- [S9] Graphify-Labs, README.md của Graphify-Labs/graphify ở commit 92741d1, 2026, https://github.com/Graphify-Labs/graphify/blob/92741d162b2094ffc2fed58cfbd8ee823e9da62c/README.md
- [S10] Panniantong, README.md của Panniantong/Agent-Reach ở commit 14c2134, 2026, https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/README.md
- [S11] Lum1104, README.md của Lum1104/Understand-Anything ở commit e24fcf6, 2026, https://github.com/Lum1104/Understand-Anything/blob/e24fcf6d371bcfa529bc110bacb1bb43de1b8d33/README.md
- [S12] career-ops-hq, README.md của career-ops-hq/career-ops ở commit 95b9d50, 2026, https://github.com/career-ops-hq/career-ops/blob/95b9d507da2104c2b30577463cac16b5d1c6bc58/README.md
- [S13] mvanhorn, README.md của mvanhorn/last30days-skill ở commit f3cd06a, 2026, https://github.com/mvanhorn/last30days-skill/blob/f3cd06a620e385ce15109ed6d3b70fc20c89eccc/README.md
- [S14] garrytan, README.md của garrytan/gstack ở commit db87940, 2026, https://github.com/garrytan/gstack/blob/db87940e244fbeb82a6a9e2d02e45f73b9aa17a7/README.md
- [S15] JuliusBrussee, README.md của JuliusBrussee/caveman ở commit 9444131, 2026, https://github.com/JuliusBrussee/caveman/blob/944413127101fc816451571c169dc1eeb3194bed/README.md
- [S16] thedotmack, README.md của thedotmack/claude-mem ở commit a4469fd, 2026, https://github.com/thedotmack/claude-mem/blob/a4469fd4fc036461c05257184fe6445755f8e370/README.md
- [S17] headroomlabs-ai, README.md của headroomlabs-ai/headroom ở commit 3fef15d, 2026, https://github.com/headroomlabs-ai/headroom/blob/3fef15d376d9899f77a28464e2e91f8b99514930/README.md
- [S18] gsd-build, README.md của gsd-build/get-shit-done ở commit bdcaab2, 2026, https://github.com/gsd-build/get-shit-done/blob/bdcaab2c752d9a33a1a1ca9acf3a3c81fb991815/README.md
- [S19] bmad-code-org, README.md của bmad-code-org/BMAD-METHOD ở commit 61e01f8, 2026, https://github.com/bmad-code-org/BMAD-METHOD/blob/61e01f82644c4bb533750cfa0d6d61ab61d2cc9b/README.md
- [S20] nextlevelbuilder, README.md của nextlevelbuilder/ui-ux-pro-max-skill ở commit d14efff, 2026, https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/d14efff8ed1faa4187f004f79926f428c8074ec7/README.md
- [S21] Leonxlnx, README.md của Leonxlnx/taste-skill ở commit 12af471, 2026, https://github.com/Leonxlnx/taste-skill/blob/12af471f627f866411b4bd785b19646d3672784c/README.md
- [S22] tt-a1i, README.md của tt-a1i/archify ở commit 25cf370, 2026, https://github.com/tt-a1i/archify/blob/25cf37080fc8b1dbe758a4efc3935b55f3327083/README.md
- [S23] pbakaus, README.md của pbakaus/impeccable ở commit 9368675, 2026, https://github.com/pbakaus/impeccable/blob/936867543ac2576920d663cc9803597f6044f3ac/README.md
- [S24] hugohe3, README.md của hugohe3/ppt-master ở commit 78759bf, 2026, https://github.com/hugohe3/ppt-master/blob/78759bf62e9a1ef43e926ff9e50afa4cfe9a63cb/README.md
- [S25] cathrynlavery, README.md của cathrynlavery/diagram-design ở commit 0b9b10c, 2026, https://github.com/cathrynlavery/diagram-design/blob/0b9b10cab3dbf695642fa1a6c4b4f60df9083689/README.md
- [S26] anthropics, README.md của anthropics/skills ở commit dbd4588, 2026, https://github.com/anthropics/skills/blob/dbd4588f9e1033efb41dad4bef2f7947c8993d44/README.md
- [S27] calesthio, README.md của calesthio/OpenMontage ở commit e01dbf4, 2026, https://github.com/calesthio/OpenMontage/blob/e01dbf433f46eeb91d39bf905e194162921019a3/README.md
- [S28] heygen-com, README.md của heygen-com/hyperframes ở commit 7bc363c, 2026, https://github.com/heygen-com/hyperframes/blob/7bc363c87c8524e547c5b759d2471d96183b67f3/README.md
- [S29] blader, README.md của blader/humanizer ở commit 8c307f3, 2026, https://github.com/blader/humanizer/blob/8c307f367c91bd974002f10f2be2965d642c13df/README.md
- [S30] ayghri, README.md của ayghri/i-have-adhd ở commit 1ecea19, 2026, https://github.com/ayghri/i-have-adhd/blob/1ecea1993b7fce257ffbd686c070948b5e07eda6/README.md
- [S31] coreyhaines31, README.md của coreyhaines31/marketingskills ở commit e85f3cb, 2026, https://github.com/coreyhaines31/marketingskills/blob/e85f3cbc2e4a79bf33b2a12e9bdd9087d414735b/README.md
- [S32] vohoailinh90, state/stars.json (số sao radar từng đo) của vohoailinh90/Github-radar ở commit 239577b, 2026, https://github.com/vohoailinh90/Github-radar/blob/239577ba26348f5e1516be7d576cde9a66e7b00d/state/stars.json
- [S33] vohoailinh90, artifacts/plans/top30-claude-plugins.json (kiểm repo nào đã có bài) của vohoailinh90/Github-radar ở commit 239577b, 2026, https://github.com/vohoailinh90/Github-radar/blob/239577ba26348f5e1516be7d576cde9a66e7b00d/artifacts/plans/top30-claude-plugins.json
