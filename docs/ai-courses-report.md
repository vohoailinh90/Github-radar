# Báo cáo: các repo GitHub dạy AI miễn phí được đánh giá cao nhất

Quét ngày **20/10/2026**. Báo cáo gom **7 repo** là khóa học, giáo trình hoặc lộ trình học AI, mã nguồn mở, đang được duy trì,
kèm lý do chọn, lý do loại, và cách học theo thứ tự. Số sao, fork lấy từ GitHub Search ngày quét; ngày commit cuối đọc từ bản
clone nông của từng repo; mọi mô tả về nội dung lấy từ README và cây thư mục của repo, không từ nguồn nào khác.

## Chọn học gì trước?

| Bạn đang ở đâu | Bắt đầu với | Vì sao |
|---|---|---|
| Chưa biết gì về AI | [AI-For-Beginners](#5-microsoftai-for-beginners) hoặc [ML-For-Beginners](#3-microsoftml-for-beginners) | 12 tuần, có bài kiểm tra trước và sau mỗi bài, chạy được trên Codespaces |
| Muốn **làm ứng dụng** với AI tạo sinh ngay | [generative-ai-for-beginners](#1-microsoftgenerative-ai-for-beginners) | 21 bài, mã Python và TypeScript |
| Muốn **làm AI agent** | [ai-agents-for-beginners](#4-microsoftai-agents-for-beginners) rồi [agents-course](#7-huggingfaceagents-course) | 18 bài, rồi 4 unit có bài cuối chấm tự động |
| Biết lập trình, muốn hiểu **LLM bên trong** | [LLMs-from-scratch](#2-rasbtllms-from-scratch) | Tự viết một mô hình kiểu GPT bằng PyTorch, chạy được trên laptop thường |
| Muốn một lộ trình dài, từ toán đến sản phẩm | [ai-engineering-from-scratch](#6-rohitg00ai-engineering-from-scratch) | 542 bài, 20 giai đoạn (đọc cờ cảnh báo bên dưới trước) |

## Bảng tổng hợp

| # | Repo | Sao | Fork | Giấy phép | Commit cuối | Khối lượng (theo README) | Cần có |
|--:|---|---:|---:|---|---|---|---|
| 1 | [microsoft/generative-ai-for-beginners](https://github.com/microsoft/generative-ai-for-beginners) | 121.651 | 64.110 | MIT | 19/10/2026 | 21 bài | Một trong: Azure OpenAI, Microsoft Foundry Models, OpenAI API, Foundry Local (chạy offline) |
| 2 | [rasbt/LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) | 106.889 | 16.457 | Apache-2.0 | 02/10/2026 | 7 chương + 5 phụ lục | Python vững; laptop thường là đủ cho các chương chính |
| 3 | [microsoft/ML-For-Beginners](https://github.com/microsoft/ML-For-Beginners) | 91.606 | 22.676 | MIT | 14/09/2026 | 12 tuần, 26 bài, 52 bài kiểm tra | Python (nhiều bài có bản R) |
| 4 | [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) | 77.475 | 25.408 | MIT | 17/10/2026 | 18 bài | Tài khoản Azure (Microsoft Foundry) để chạy mã mẫu |
| 5 | [microsoft/AI-For-Beginners](https://github.com/microsoft/AI-For-Beginners) | 70.017 | 13.579 | MIT | 04/09/2026 | 12 tuần, 24 bài | Python; TensorFlow hoặc PyTorch |
| 6 | [rohitg00/ai-engineering-from-scratch](https://github.com/rohitg00/ai-engineering-from-scratch) | 71.442 | 12.570 | MIT | 19/10/2026 | 542 bài, 20 giai đoạn | Biết viết code (ngôn ngữ nào cũng được) |
| 7 | [huggingface/agents-course](https://github.com/huggingface/agents-course) | 33.768 | 2.423 | Apache-2.0 | 06/10/2026 | 4 unit + bài thưởng | Python cơ bản, hiểu cơ bản về LLM |

Giấy phép đọc từ tệp `LICENSE` của từng repo.

## Từng repo

### 1. microsoft/generative-ai-for-beginners

**Là gì.** Khóa 21 bài của Microsoft Cloud Advocates về xây ứng dụng AI tạo sinh. README chia bài thành hai loại: bài **Learn** giải thích
khái niệm, bài **Build** giải thích khái niệm kèm mã Python và TypeScript. Mỗi bài có video giới thiệu ngắn, bài viết, mã mẫu và phần
"Keep Learning".

**Nội dung** (tên thư mục trong repo): thiết lập khóa học, nhập môn GenAI, so sánh các LLM, dùng GenAI có trách nhiệm, prompt cơ bản và
nâng cao, ứng dụng sinh văn bản, ứng dụng chat, ứng dụng tìm kiếm, ứng dụng ảnh, ứng dụng low-code, function calling, thiết kế UX cho AI,
bảo mật ứng dụng AI, vòng đời ứng dụng GenAI, RAG và cơ sở dữ liệu vector, mô hình mã nguồn mở, AI agents, fine-tuning, SLM, Mistral, Meta.

**Học thế nào.** README nói mỗi bài độc lập, có thể bắt đầu từ bài nào cũng được. Bài `00-course-setup` hướng dẫn dựng môi trường. Nên
fork repo về tài khoản GitHub của mình.

**Lưu ý.**
- Để chạy mã bạn cần **một** trong bốn lựa chọn: Azure OpenAI, Microsoft Foundry Models, OpenAI API, hoặc Foundry Local. Chỉ Foundry Local
  được README mô tả là chạy hoàn toàn offline, không cần thuê bao đám mây. Các lựa chọn còn lại là dịch vụ có thể tính phí.
- README ghi GitHub Models sẽ ngừng cuối tháng 7/2026 và khuyên dùng Microsoft Foundry Models.
- Repo có hơn 50 bản dịch nên rất nặng; README chỉ cách `git sparse-checkout` để bỏ qua thư mục `translations`.
- Có bản dịch tiếng Việt (`translations/vi`).

### 2. rasbt/LLMs-from-scratch

**Là gì.** Mã nguồn chính thức của cuốn sách *Build a Large Language Model (From Scratch)*: tự viết, huấn luyện trước và tinh chỉnh một LLM kiểu
GPT, từng bước, chỉ dùng PyTorch và **không dùng thư viện LLM bên ngoài**. README nói phương pháp mô phỏng cách tạo các mô hình nền lớn như
mô hình đứng sau ChatGPT, ở quy mô nhỏ cho mục đích học tập; sách cũng có mã nạp trọng số của các mô hình lớn đã huấn luyện để tinh chỉnh.

**Nội dung** (cây thư mục): `ch01` đến `ch07`, các phụ lục `appendix-A` đến `appendix-E`, thư mục `setup`, và `reasoning-from-scratch`.
Phụ lục A là phần nhập môn PyTorch.

**Điều kiện.** README nói điều kiện quan trọng nhất là nền Python vững; biết PyTorch thì tốt nhưng không bắt buộc. Mã ở các chương chính được
thiết kế để chạy trên laptop thông thường trong thời gian hợp lý và tự dùng GPU nếu có.

**Lưu ý quan trọng.** Đây là **mã miễn phí đi kèm một cuốn sách bán tiền** (README có liên kết Manning và Amazon). Mã chạy được độc lập, nhưng
phần văn bản giải thích từng bước nằm trong sách. Nếu chỉ muốn đọc mã và chạy notebook thì miễn phí; nếu muốn lời giải thích đầy đủ, cần sách.

### 3. microsoft/ML-For-Beginners

**Là gì.** Giáo trình **machine learning cổ điển**: 12 tuần, 26 bài, 52 bài kiểm tra (mỗi bài kiểm tra 3 câu). Cây thư mục theo thứ tự:
giới thiệu, hồi quy, ứng dụng web, phân loại, phân cụm, NLP, chuỗi thời gian, học tăng cường, ứng dụng thực tế.

**Cách học** (README): học theo dự án, có bài kiểm tra ngắn trước và sau mỗi bài. Mỗi bài có: sketchnote (tùy chọn), video (một số bài), bài kiểm tra
trước, bài viết, hướng dẫn làm dự án, kiểm tra kiến thức, thử thách, đọc thêm, bài tập, bài kiểm tra sau. Lời giải nằm trong thư mục `/solution`;
README khuyên hiểu bài rồi tự làm dự án thay vì chạy ngay đáp án. Phần lớn bài viết bằng Python, nhiều bài có bản R (`.rmd`).

**Cách chạy.** Fork và clone repo. README gợi ý dùng **GitHub Codespaces** để khỏi cài Python trên máy; ứng dụng bài kiểm tra nằm ở `quiz-app`
và có thể chạy cục bộ.

**Lưu ý.** Đây là ML **cổ điển** (scikit-learn), không phải LLM. Muốn LLM, đi sang repo 1, 2 hoặc 6.

### 4. microsoft/ai-agents-for-beginners

**Là gì.** Khóa 18 bài về xây dựng AI agent. Thư mục bài, theo thứ tự: thiết lập, nhập môn agent, khám phá các framework agent, mẫu thiết kế
agent, dùng công cụ (tool use), agentic RAG, agent đáng tin cậy, lập kế hoạch, đa agent, metacognition, đưa agent vào sản xuất, giao thức agent,
context engineering, bộ nhớ agent, Microsoft Agent Framework, duyệt web (browser use), triển khai agent mở rộng được, agent AI chạy cục bộ,
bảo mật agent.

**Cách học.** Mỗi bài có bài viết kèm video ngắn, mã Python và tài liệu đọc thêm. Mã mẫu nằm ở thư mục `code_samples`. README nói bắt đầu từ bài nào
cũng được, và nếu bạn chưa từng làm với mô hình sinh thì nên học repo 1 trước.

**Lưu ý.**
- Mã mẫu dùng **Microsoft Agent Framework** và **Microsoft Foundry Agent Service V2**; README ghi cần **tài khoản Azure**. Một số mã mẫu hỗ trợ nhà cung cấp
  tương thích OpenAI khác, ví dụ MiniMax; cấu hình ở bài thiết lập (`00-course-setup`).
- Nên đọc như một khóa **theo hệ Microsoft**: bài 14 và các mã mẫu gắn với công cụ của họ. Các khái niệm (tool use, RAG, đa agent, bộ nhớ) vẫn dùng được
  với framework khác, và repo 7 dạy ba framework khác.

### 5. microsoft/AI-For-Beginners

**Là gì.** Giáo trình **AI tổng quan** 12 tuần, 24 bài, có bài kiểm tra và bài lab; README nêu bao gồm TensorFlow, PyTorch và đạo đức AI.
Mỗi bài có tài liệu đọc trước, notebook Jupyter chạy được (có bản PyTorch hoặc TensorFlow), một số bài có lab, và liên kết tới các module MS Learn.
Các chủ đề (topic) của repo gồm CNN, RNN, GAN, thị giác máy tính và NLP.

**Cách học.** README khuyên người mới bắt đầu bằng thư mục `examples`: bốn ví dụ ngắn (nhận dạng mẫu, mạng nơ-ron đơn giản, phân loại ảnh, phân tích
cảm xúc văn bản) trước khi vào giáo trình đầy đủ. Bài thiết lập ở `lessons/0-course-setup`; có hướng dẫn chạy mã trong VS Code hoặc Codespaces.
Notebook cũng chứa nhiều lý thuyết, nên cần đi hết ít nhất một phiên bản (PyTorch hoặc TensorFlow) của mỗi bài.

**So với repo 3.** Repo 3 là ML cổ điển; repo này đi từ AI biểu tượng đến mạng nơ-ron và học sâu. Học một trong hai là đủ để bắt đầu; học cả hai
nếu muốn nền rộng.

### 6. rohitg00/ai-engineering-from-scratch

**Là gì.** Lộ trình rất dài: README ghi **542 bài, 20 giai đoạn**, bằng Python, TypeScript, Rust, Julia; "miễn phí, mã nguồn mở, MIT". Học trên website,
với một coding agent, hoặc chạy mã cục bộ. Các giai đoạn (tên thư mục `phases/`): thiết lập, toán, ML cơ bản, học sâu lõi, thị giác máy tính, NLP,
giọng nói và âm thanh, transformer, AI tạo sinh, học tăng cường, LLM từ đầu, kỹ thuật LLM, đa phương thức, công cụ và giao thức, kỹ thuật agent,
hệ tự động, đa agent, hạ tầng và sản xuất, đạo đức và an toàn, dự án tổng kết.

**Thời lượng theo README.** Từ đầu (Giai đoạn 0): khoảng **306 giờ**. Đã biết Python: Giai đoạn 1, khoảng 270 giờ. Đã biết học sâu và muốn LLM, agent:
Giai đoạn 10, khoảng 100 giờ. Chỉ muốn kỹ thuật agent: Giai đoạn 14, khoảng 60 giờ. Có thêm các lộ trình hẹp (ví dụ MCP khoảng 23 giờ 15 phút).

**Chạy thử.** README có lệnh kiểm môi trường và bài đầu tiên không cần thư viện ngoài: `python3 phases/00-setup-and-tooling/01-dev-environment/code/verify.py --route beginner`
rồi `python3 phases/01-math-foundations/01-linear-algebra-intuition/code/vectors.py`.

**Điều nên xem lại (quan sát, không phải kết luận).** Repo tạo ngày 18/03/2026 và đã có 71.442 sao sau 216 ngày, trung bình khoảng 331 sao mỗi ngày: rất nhanh so với
các repo khác trong báo cáo, dù một đợt lan truyền cũng có thể gây ra điều này. Số fork (12.570, khoảng 18% số sao) lại không thấp bất thường, nên con số không cho thấy
dấu hiệu mua sao. `state/stars.json` có ảnh chụp 70.659 sao ngày 17/10, tức thêm 783 sao trong 3 ngày (khoảng 261 sao mỗi ngày): vẫn nhanh, nhưng đó mới là một khoảng đo ngắn. README rất dài (khoảng 115.000 ký tự)
và nêu nhiều con số về quy mô. Chưa ai ở đây kiểm 542 bài có thật sự đầy đủ, đúng và chạy được. Trước khi dành hàng trăm giờ, hãy thử vài bài đầu và vài bài ở giai đoạn
bạn quan tâm.

### 7. huggingface/agents-course

**Là gì.** Khóa miễn phí của Hugging Face về AI agent, học trên `hf.co/learn/agents-course` (repo chứa nguồn bài viết). README chia **4 unit**, đi từ nền tảng đến bài cuối có đánh giá bằng benchmark:

| Unit | Nội dung (theo README) |
|---|---|
| 0 | Chào mừng, công cụ cần có, tổng quan khóa |
| 1 | Giới thiệu agent: định nghĩa, LLM, cây họ mô hình, token đặc biệt |
| 1 Bonus | Tinh chỉnh LLM cho function-calling |
| 2 | Framework cho agent: `smolagents`, `LlamaIndex`, `LangGraph` |
| 2 Bonus | Quan sát và đánh giá agent |
| 3 | Agentic RAG |
| 4 | Dự án cuối: tạo, thử và nhận chứng chỉ cho agent; chấm tự động, có bảng xếp hạng |
| 3 Bonus | Agent trong game với Pokémon |

**Điều kiện.** Python cơ bản và hiểu cơ bản về LLM. Đăng ký (miễn phí) qua liên kết trong README.

**Điểm khác.** Dạy **ba framework khác nhau** thay vì một, nên hợp để học sau repo 4 và so sánh cách làm.

## Đã quét nhưng không đưa vào

| Repo | Sao | Lý do (theo luật của Radar) |
|---|---:|---|
| [datawhalechina/hello-agents](https://github.com/datawhalechina/hello-agents) | 83.744 | Giấy phép **CC BY-NC-SA 4.0**, hạn chế thương mại, không nằm trong danh sách giấy phép miễn phí của `radar.yaml`. Vẫn đáng xem nếu bạn đọc được tiếng Trung: mô tả repo bằng tiếng Trung |
| [mlabonne/llm-course](https://github.com/mlabonne/llm-course) | 84.387 | Commit cuối 05/02/2026, cách 257 ngày, quá ngưỡng `max_days_since_push` 120. Nội dung vẫn là lộ trình LLM nổi tiếng (roadmap + notebook Colab) |
| [karpathy/nn-zero-to-hero](https://github.com/karpathy/nn-zero-to-hero) | 24.872 | Commit cuối 20/02/2024. Không còn cập nhật |
| [karpathy/LLM101n](https://github.com/karpathy/LLM101n) | 37.479 | Repo đã **lưu trữ** (archived) |
| [anthropics/courses](https://github.com/anthropics/courses) | 22.902 | Repo đã **lưu trữ** (archived) |
| [DataTalksClub/llm-zoomcamp](https://github.com/DataTalksClub/llm-zoomcamp) | 7.490 | Không có tệp giấy phép ở thư mục gốc, nên không xác nhận được là miễn phí theo luật. Khóa học miễn phí 10 tuần, hợp lệ để học |
| [openai/openai-cookbook](https://github.com/openai/openai-cookbook) | 76.704 | Là bộ ví dụ dùng API OpenAI, không phải khóa học có thứ tự |

Các repo khác đã thấy trong lượt quét nhưng chưa đọc kỹ: `Made-With-ML` (49.774 sao), `Data-Science-For-Beginners` (37.654), `happy-llm` (34.447),
`d2l-en` (29.887), `fastbook` (25.399), `mcp-for-beginners` (17.470), `mlops-zoomcamp` (15.446). Muốn viết bài cho một repo trong số này:
`python3 radar.py run --repo owner/tên`.

## Cách chọn

1. Tìm bằng GitHub Search theo chủ đề (`course`, `llm`, `ai-agents`, `machine-learning`, `deep-learning`, `tutorial`) và theo tên các khóa nổi tiếng đã biết,
   rồi xếp theo số sao.
2. Loại: repo lưu trữ, repo có commit cuối quá 120 ngày, repo không có giấy phép thuộc danh sách miễn phí, repo không phải khóa học có thứ tự.
3. Đọc README và cây thư mục của từng repo còn lại (bản clone nông, không tải nội dung bài).

## Điều cần biết trước khi tin báo cáo này

- **Chưa chạy thử bài nào.** Báo cáo chỉ đọc README, cây thư mục và tệp giấy phép. Chưa ai mở notebook, chạy mã, hay làm bài kiểm tra.
  Chất lượng giảng dạy bên trong từng bài **chưa được đánh giá**; "được đánh giá cao" ở đây nghĩa là số sao, số fork, và việc repo còn được cập nhật, không phải kết luận
  về độ hay của nội dung.
- **Không phải do team VPS viết.** Phiên này (môi trường đám mây) không với tới máy VPS của team agent và không có khóa API của các model miễn phí, nên bộ quét
  `radar.py run` không chạy được ở đây. Báo cáo do Claude viết trực tiếp trong phiên tương tác, **không có model họ khác soát lại** và không qua các cổng kiểm tra tự động
  của `radar/gates.py`. Muốn có bài kiểu "làm theo từng bước" đã qua cổng kiểm tra cho từng repo, chạy lại qua team (mục dưới).
- Số sao là ảnh chụp ngày 20/10/2026, lấy từ GitHub Search.
- "Miễn phí" chỉ nói về **giấy phép và quyền đọc/học**. Nhiều khóa cần dịch vụ bên thứ ba có thể tính phí (Azure, OpenAI, v.v.), và repo 2 đi kèm sách bán tiền.

## Chạy lại bằng team VPS

Để team tạo bài học đã qua cổng kiểm tra cho từng repo, trên VPS (theo [`TEAM.md`](TEAM.md)):

```bash
team new COURSES --repo vohoailinh90/Github-radar
nano /srv/team/work/COURSES/request.md
```

Nội dung gợi ý cho `request.md`:

```
Chạy `python3 radar.py run --repo <owner/tên>` cho từng repo sau, mỗi repo một lượt, rồi `python3 radar.py check`:
microsoft/generative-ai-for-beginners, rasbt/LLMs-from-scratch, microsoft/ML-For-Beginners,
microsoft/ai-agents-for-beginners, microsoft/AI-For-Beginners, huggingface/agents-course.
Không viết cho rohitg00/ai-engineering-from-scratch cho đến khi chủ repo đã xem mục "Điều nên xem lại" của repo đó trong docs/ai-courses-report.md.
Chỉ dùng digests/, export/studio/, state/ do radar.py ghi; không sửa tay. Bản nháp studio để ở trạng thái draft.
```

Hoặc trên GitHub: Actions → *Radar scan* → *Run workflow*, điền ô `repo`, bỏ chọn `dry_run` (xem [`README.md`](../README.md)).
