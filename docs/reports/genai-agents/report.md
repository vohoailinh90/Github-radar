---
id: R01
title: GenAI Agents: bản đồ 59 notebook học xây agent AI
topic: ky-thuat
date: 2026-10-22
---
# GenAI Agents: bản đồ 59 notebook học xây agent AI

## Tóm tắt

Repo GenAI Agents có gì, nên học từ đâu, và cần cẩn thận chỗ nào? Câu trả lời ngắn: đây là một kho dạy học do Nir Diamant lập ra, gồm 59 notebook Jupyter chạy được, mỗi notebook dạy một agent AI hoặc một mẫu thiết kế, từ chatbot nhớ hội thoại đến hệ thống nhiều agent [S2]. Nó **không phải framework**: không có gói để cài và không có API ổn định, đơn vị giá trị là một notebook đọc và chạy từ đầu đến cuối [S2]. Bảng README ghi LangGraph ở 40 trên 57 hàng [S1], và 40 trên 59 notebook dùng biến môi trường OPENAI_API_KEY (người viết đếm bằng script, xem mục Cách học và chạy).

Bài này đọc repo theo ba tầng. Tầng một là bản đồ: repo chứa gì, chia nhóm thế nào, một notebook được dựng ra sao [S1] [S3]. Tầng hai là tám ý tưởng cốt lõi mà các notebook dạy, mỗi ý lấy một notebook làm ví dụ đọc kỹ: vòng lặp agent, đồ thị LangGraph, bộ nhớ, tự cải thiện, nhiều agent, giao thức MCP, cổng phê duyệt của con người và đánh giá bằng dấu vết [S7] [S9] [S11] [S12] [S13] [S14] [S15] [S16]. Tầng ba là điều ít người đọc: giấy phép chỉ cho dùng phi thương mại, chỗ quảng cáo khóa học, các tài liệu trong repo lệch nhau ở vài con số, và phiên bản thư viện đã cũ [S4] [S1] [S5].

Mỗi khẳng định trong bài mang một trong ba nhãn. **Nguồn: repo** nghĩa là đọc trực tiếp từ file của repo ở commit 1b45571 (17/10/2026). **Người viết đếm** nghĩa là một con số tính bằng script trên thư mục đã tải về, bạn tự kiểm lại được. **Suy luận** là nhận xét của người viết, không phải lời của tác giả repo. Bài **chưa chạy** notebook nào, vì không có khóa API; mọi mô tả hành vi là đọc mã và văn bản, không phải kết quả thực nghiệm.

Ba ý đáng mang theo. Thứ nhất, agent chỉ là một vòng lặp quanh một mô hình: "bản ghi hội thoại chính là trí óc" của nó, và quy tắc nào bắt buộc phải đúng thì phải nằm trong mã, không nằm trong prompt [S7]. Thứ hai, repo này là sổ bài tập để hiểu cơ chế, còn muốn đưa agent vào sản phẩm thì chính tác giả chỉ sang một repo khác [S2]. Thứ ba, trước khi dùng mã của repo trong công việc có thu tiền, hãy đọc giấy phép: quyền thương mại được tác giả giữ lại [S4].

## Repo này là gì

**Mục tiêu (nguồn: repo).** README tự giới thiệu là "một trong những bộ sưu tập hướng dẫn và cài đặt agent AI tạo sinh (GenAI) rộng nhất", dẫn người học từ chatbot đơn giản đến hệ nhiều agent phức tạp, và nhắm cả người mới lẫn người đã có kinh nghiệm [S1]. AGENTS.md nói gọn hơn: đây là "kho dạy học, không phải framework", không có gói cài đặt, không có API ổn định, và đơn vị giá trị là một notebook mà người đọc chạy trọn vẹn rồi học được điều gì đó [S2].

**Bố cục thư mục (nguồn: repo).** Thư mục `all_agents_tutorials/` chứa các notebook, mỗi notebook một agent hoặc một mẫu; `all_agents_tutorials/data/` và `data/` chứa dữ liệu mẫu; `scripts/` chứa công cụ cấp repo; `tests/` chứa kiểm thử import và kiểm thử khói (smoke test), không phải bộ kiểm thử hành vi; `images/` chứa sơ đồ; `requirements.txt` là hợp của các phụ thuộc, còn từng notebook tự cài thứ nó cần [S2].

**Sáu luật làm việc (nguồn: repo).** AGENTS.md ghi: một agent một notebook, không gộp hai bài và không tách một bài ra nhiều file; notebook phải chạy từ trên xuống dưới trên kernel sạch; thiết kế trước, mã sau, nên một notebook chỉ có mã thì không thuộc về đây; framework khác nhau là cố ý (LangGraph, AutoGen, PydanticAI và vòng lặp tự viết đều có mặt); khóa API lấy từ biến môi trường, không ghi cứng; và xóa đầu ra có chứa bí mật hoặc dữ liệu lớn trước khi commit [S2].

**Hệ sinh thái quanh nó (nguồn: repo).** README liệt kê bốn dự án liên quan của cùng tác giả: RAG Techniques (hơn 40 notebook về truy xuất tăng cường sinh), Agents Towards Production (đưa agent vào sản phẩm), Prompt Engineering Techniques và Agent Memory Techniques [S1]. AGENTS.md lặp lại điều đó theo hướng dẫn cho trợ lý AI: muốn đưa agent vào sản phẩm thì dùng agents-towards-production, muốn học truy xuất thì RAG_Techniques, muốn học bộ nhớ thì Agent_Memory_Techniques [S2]. Cộng đồng gồm Discord, Reddit r/EducationalAI và bản tin của tác giả [S1].

**Hai con số 57 và 59.** README nói "57 tutorial" ở dòng thông báo gần đây [S1], trong khi AGENTS.md nói 59 notebook [S2]. Người viết đếm lại bằng script: thư mục có 59 file `.ipynb`; bảng README có 57 hàng, nhưng một hàng (Controllable RAG Agent) trỏ sang repo khác, hai notebook (hội thoại đơn giản và phân tích dữ liệu đơn giản) có thêm bản PydanticAI nằm trong phần mô tả chi tiết, và một notebook `Hr_AI_Agent.ipynb` không được liên kết trong README. Vậy 56 + 2 + 1 = 59. Đây là suy luận từ phép đếm, không phải lời giải thích của tác giả [S1] [S2].

## Bản đồ 59 notebook

**Bảng README (nguồn: repo).** Bảng chính có 57 hàng chia 11 nhóm, mỗi hàng ghi nhóm, tên agent, framework và tính năng chính [S1]. Theo số hàng mỗi nhóm (người viết đếm): Analysis 13, Business 9, Creative 8, QA 6, Educational 5, News 5, Beginner 4, và ba nhóm nhỏ Framework, Shopping, Task Management mỗi nhóm 2 hàng, cuối cùng Advanced 1 hàng [S1].

**Mỗi nhóm có gì (nguồn: repo).** Nhóm Beginner gồm hội thoại đơn giản, hỏi đáp đơn giản, phân tích dữ liệu đơn giản và bài "Agent từ con số không: vòng lặp while". Nhóm Framework gồm nhập môn LangGraph và Model Context Protocol. Nhóm Business có hỗ trợ khách hàng, chấm bài luận, lập kế hoạch du lịch, trợ lý quản lý dự án, phân tích hợp đồng và trợ lý nhân sự. Nhóm Creative có tạo ảnh GIF, đọc thơ thành tiếng, soạn nhạc, tạo meme và game phá án. Nhóm QA có kiểm thử hệ thống LangGraph, tuân thủ Thỏa thuận Xanh châu Âu, rà soát tài liệu khoa học, cổng phê duyệt của con người, đánh giá theo dấu vết và bộ định tuyến quyết định một bước [S1].

**Framework nào xuất hiện (nguồn: repo, người viết đếm).** Cột framework của bảng ghi đúng "LangGraph" ở 38 hàng, thêm hai hàng kết hợp LangGraph với LightRAG hoặc với Ollama, tức 40 trên 57 hàng có LangGraph. Còn lại: LangChain 6 hàng, LangChain cùng PydanticAI 2 hàng, Transformers 2 hàng, và mỗi loại một hàng cho MCP, AutoGen, OpenAI Swarm, CrewAI, "Custom", "Python" và "Pure Python" [S1]. Suy luận: ai học xong LangGraph thì đọc được phần lớn kho này.

**Quy mô (người viết đếm).** Toàn bộ 59 notebook có 823 ô mã và 1.100 ô văn bản (markdown). Notebook dài nhất là hệ thống quản lý thiên tai thời tiết với 131 ô; ngắn nhất là phân tích dữ liệu đơn giản với 12 ô. Nghĩa là có bài đọc xong trong một buổi tối, có bài là cả một dự án nhỏ [S1].

**Phần mới nhất (nguồn: repo).** Dòng thông báo của README nêu năm mục thêm gần đây: "Read vs Write", đánh giá agent theo dấu vết, agent phê duyệt có con người, agent tiếp nhận tài liệu và trợ lý nhân sự [S1]. Bảy hàng cuối của bảng (số 51 đến 57) cũng là phần mới: tiếp nhận tài liệu, đăng mạng xã hội, cổng phê duyệt, đánh giá dấu vết, vòng lặp while, bộ định tuyến một bước, và chi phí đọc so với viết [S1]. Suy luận: năm trong bảy bài này (số 53 đến 57) xoay quanh phê duyệt, đo lường và chi phí, khác với các bài cũ thiên về ghép các bước thành ứng dụng.

## Một notebook được dựng thế nào

**Chín phần theo CONTRIBUTING (nguồn: repo).** Hướng dẫn đóng góp yêu cầu notebook mới có chín phần theo thứ tự: tiêu đề và tổng quan; giải thích chi tiết (động cơ, thành phần chính, kiến trúc, lợi ích); sơ đồ trực quan; gói cần cài; cài đặt từng bước; ví dụ sử dụng; so sánh với agent đơn giản hơn; cân nhắc thêm; tài liệu tham khảo [S3]. Sơ đồ nên viết bằng cú pháp Mermaid, xuất ra SVG và lưu trong `images/` [S3].

**Có script kiểm tra (nguồn: repo).** `scripts/validate_notebook.py` kiểm các notebook được chọn trước khi đóng góp, và yêu cầu đủ tám tiêu đề: Overview, Detailed Explanation, Required Packages, Implementation, Usage Example, Comparison, Additional Considerations, References [S6]. Script cũng thu thập nguồn của các ảnh nhúng trong notebook để kiểm tra [S6]. Đây là phần cứng hóa của luật "thiết kế trước, mã sau" trong AGENTS.md [S2].

**Hai thế hệ notebook (suy luận).** Các bài cũ như hội thoại đơn giản mở đầu bằng một khối văn bản gồm Overview, Motivation, Key Components, Method Details và Conclusion, rồi mới đến mã, và trước mỗi ô mã có một dòng markdown ngắn [S8] [S10]. Các bài mới như cổng phê duyệt và đánh giá dấu vết theo đúng tám tiêu đề mà script kiểm, có sơ đồ SVG riêng [S15] [S16]. Khi đọc, hãy bắt đầu từ phần tổng quan và phần "Detailed Explanation", sau đó mới chạy từng ô.

**Nhịp quen thuộc của mã (nguồn: repo).** Nhiều notebook (37 trên 59 có nhập `dotenv`, người viết đếm) mở đầu bằng cài gói, rồi `load_dotenv()` để nạp khóa API từ file `.env`, rồi khởi tạo mô hình với nhiệt độ cho trước, ví dụ `ChatOpenAI(model="gpt-4o-mini", max_tokens=1000, temperature=0)` trong bài hội thoại [S8]. Biết nhịp này giúp bạn đọc nhanh các bài sau: phần khó thường nằm ở thiết kế, không ở dòng khởi tạo.

## Agent thật ra là gì: một vòng lặp

Notebook "AI Agents Are Just While Loops" là bài nên đọc đầu tiên, vì nó dựng agent nhỏ nhất có thể, không dùng framework nào [S7].

**Một mô hình, ba công cụ, một vòng while (nguồn: repo).** Agent trong bài có ba công cụ: liệt kê file, đọc file, chạy lệnh shell. Việc được giao là có ba hóa đơn trong một thư mục và câu hỏi "hóa đơn nào quá hạn, quá bao nhiêu". Tác giả nói cả chương trình khoảng 80 dòng Python [S7].

**Một lượt của vòng lặp (nguồn: repo).** Mã gửi toàn bộ hội thoại cho mô hình; mô hình trả lời bằng chữ hoặc yêu cầu gọi công cụ; nếu có yêu cầu thì mã chạy công cụ, dán kết quả trở lại hội thoại, rồi đi vòng mới; nếu không còn yêu cầu thì dừng. Có một giới hạn cứng `MAX_TURNS = 10`, đặt trong vòng lặp chứ không trong prompt [S7].

**Bản ghi hội thoại là trí óc (nguồn: repo).** Giữa hai lượt, mô hình không nhớ gì; trông như liên tục chỉ vì vòng lặp gửi lại cả đống chữ mỗi lần. Tác giả gọi đó là "the transcript is the mind", và nói agent là "một file văn bản gắn thêm động cơ" [S7]. Cùng ý này xuất hiện ở bài hội thoại đơn giản dưới dạng khác: một dictionary lưu lịch sử theo `session_id`, và `RunnableWithMessageHistory` tự chèn lịch sử vào prompt ở mỗi lượt [S8]. Hai bài làm cùng một việc, một bên viết tay, một bên dùng thư viện.

**Cái bẫy (nguồn: repo, lời tác giả).** Bài bật cờ `FLAKY` để mọi lần đọc hóa đơn trả về lỗi "tạm thời không dùng được, hãy thử lại". Lỗi đó rơi vào hội thoại y hệt một kết quả thật. Mô hình đọc lại "trí óc" của mình, thấy "thử lại", và thử lại. Tác giả mô tả một lần chạy trong video: ba lượt tốn tiền trước khi mô hình đổi sang dùng shell [S7]. Đây là lời kể của tác giả về lần chạy của họ; người viết chưa tái lập.

**Sửa bằng prompt hay bằng mã (nguồn: repo, lời tác giả).** Cách sửa thứ nhất là thêm vào system prompt một câu: đừng lặp lại lệnh đã lỗi. Theo tác giả, mô hình đọc luật đó mà vẫn thử lại ba lần, vì ba lỗi mới "ồn" hơn một luật cũ. Cách sửa thứ hai là cùng câu đó nhưng viết thành mã: hàm chạy công cụ ghi nhớ các lệnh đã lỗi và từ chối chạy lại, trả về "BLOCKED by the loop". Một lần bị chặn là mô hình đổi công cụ [S7]. Kết luận của bài, dịch sát: quy tắc viết vào prompt là lời khuyên, quy tắc viết vào vòng lặp là định luật [S7].

**Ba lời hứa của động cơ (nguồn: repo).** Bài chốt ba thứ phải nằm trong mã: trần chi tiêu và điểm dừng cứng; quy tắc không lặp lại lệnh đã lỗi; và bản ghi hội thoại được tóm tắt bớt (giữ sự kiện, bỏ phần thừa) vì "một trí óc ngắn mà đúng tốt hơn một trí óc đầy đủ" [S7]. Bài cần thư viện `anthropic` và biến `ANTHROPIC_API_KEY`; tác giả nói mỗi lần chạy trọn vẹn tốn vài cent [S7].

## LangGraph: agent là một đồ thị

**Ba khái niệm (nguồn: repo).** Bài nhập môn dạy LangGraph qua một đường ống xử lý văn bản. Trạng thái (state) là một `TypedDict` với bốn trường: văn bản, phân loại, danh sách thực thể, bản tóm tắt. Mỗi nút (node) là một hàm đọc trạng thái và trả về phần cần cập nhật. Các cạnh (edge) nối nút nọ với nút kia; điểm vào được đặt bằng `set_entry_point`, điểm ra là `END`, rồi `compile()` ra ứng dụng chạy bằng `invoke` [S9].

**Ví dụ một (nguồn: repo).** Đường ống có ba nút nối tiếp: phân loại văn bản thành News, Blog, Research hoặc Other; trích thực thể gồm người, tổ chức, địa điểm; tóm tắt trong một câu ngắn. Sơ đồ đồ thị được vẽ bằng `draw_mermaid_png` [S9]. Đây là ví dụ đơn giản nhất của lối nghĩ "chia việc thành các bước nhỏ, mỗi bước một lời gọi mô hình".

**Ví dụ hai: đường rẽ (nguồn: repo).** Bài hỗ trợ khách hàng thêm điều mà chuỗi thẳng không làm được là rẽ nhánh. Trạng thái có bốn trường: câu hỏi, nhóm, cảm xúc, phản hồi. Nút `categorize` xếp câu hỏi vào Technical, Billing hoặc General; nút `analyze_sentiment` đánh giá Positive, Neutral hoặc Negative; rồi cạnh có điều kiện (`add_conditional_edges`) gọi hàm `route_query` để chọn một trong bốn nút xử lý, trong đó nút `escalate` chuyển câu hỏi có cảm xúc tiêu cực cho nhân viên thật [S10].

**Vì sao đồ thị (suy luận).** Chuỗi thẳng chỉ chạy các bước theo thứ tự cố định. Đồ thị cho phép rẽ nhánh theo trạng thái, quay lại, và dừng đúng chỗ. Với kho này, đó cũng là lý do LangGraph chiếm đa số: nó biến "luồng điều khiển" thành thứ nhìn thấy được và kiểm tra được, đúng với luật "thiết kế trước, mã sau" [S2] [S9] [S10].

## Bộ nhớ, tự cải thiện và đa agent

**Hai tầng nhớ (nguồn: repo).** Bài bộ nhớ có hai kho. Bộ nhớ ngắn hạn là lịch sử hội thoại theo từng phiên, y như bài hội thoại đơn giản [S8] [S11]. Bộ nhớ dài hạn là một dictionary `long_term_memory`: sau mỗi lượt, nếu câu của người dùng dài hơn 20 ký tự thì lưu dạng "User said: ...", và chỉ giữ 5 mục gần nhất. Khi trả lời, các mục này được ghép vào prompt qua một dòng hệ thống "Long-term memory: ..." [S11].

**Giới hạn của kiểu nhớ này (suy luận).** Quy tắc "dài hơn 20 ký tự" đo độ dài, không đo độ quan trọng; và vì kho nhớ là các dictionary trong bộ nhớ của kernel, nó mất khi kernel khởi động lại. Chính phần kết của bài thừa nhận hướng cải tiến là tiêu chí lưu tốt hơn, tóm tắt và nối với cơ sở tri thức [S11]. Muốn đi sâu về bộ nhớ thì README chỉ sang repo Agent Memory Techniques [S1].

**Tự cải thiện: phản chiếu rồi học (nguồn: repo).** Lớp `SelfImprovingAgent` có ba việc. `respond` trả lời có kèm "insights" hiện tại trong prompt. `reflect` đưa lịch sử hội thoại cho mô hình và xin nhận xét để cải thiện. `learn` tóm tắt các nhận xét thành những điểm cần nhớ rồi ghi vào lịch sử dưới dạng tin nhắn "[SYSTEM] Agent learned: ..." [S12]. Chu trình tương tác, phản chiếu, học này là lõi của "tự cải thiện" ở đây [S12].

**Điều bài chưa làm (suy luận).** Trong các ô đã đọc, phần ví dụ chỉ in câu trả lời trước và sau khi học, không có phép đo nào cho thấy câu trả lời tốt hơn thật. Vì vậy hãy xem đây là mô hình minh họa cơ chế, không phải bằng chứng rằng agent giỏi lên [S12]. Bài đánh giá dấu vết ở phần sau cho thấy cách đo nghiêm túc hơn [S16].

**Nhiều agent: hai vai, năm bước (nguồn: repo).** Bài cộng tác lịch sử và dữ liệu định nghĩa một lớp `Agent` có tên, vai trò và danh sách kỹ năng, rồi biến thành system prompt. Hai agent là Clio (chuyên gia nghiên cứu lịch sử) và Data (chuyên gia phân tích dữ liệu). Quy trình cố định gồm năm bước: Clio nêu bối cảnh lịch sử; Data xác định cần số liệu gì; Clio cung cấp số liệu lịch sử; Data phân tích xu hướng; Clio tổng hợp câu trả lời. Có giới hạn thời gian mặc định 300 giây [S13].

**"Đa agent" ở đây nghĩa là gì (suy luận).** Cả hai agent dùng chung một mô hình và chỉ khác system prompt, còn thứ tự lượt là một kịch bản viết sẵn, không phải sự thương lượng tự do [S13]. Đó là mẫu cộng tác đơn giản nhất, đủ để hiểu ý tưởng. README còn có các biến thể khác: nhóm nghiên cứu bằng AutoGen, nhóm viết blog bằng OpenAI Swarm và hệ thống quản lý tạp hóa bằng CrewAI [S1].

## MCP: cắm công cụ vào agent

**Ý tưởng (nguồn: repo).** Model Context Protocol (MCP) là giao thức mở chuẩn hóa cách ứng dụng cung cấp ngữ cảnh và công cụ cho mô hình ngôn ngữ. Bài ví von nó như cổng USB-C: một chuẩn thay cho vô số đầu nối riêng. Lý do cần: mỗi nguồn dữ liệu một kiểu tích hợp thì khó mở rộng và khó bảo trì; MCP cho truy cập thống nhất, thêm công cụ kiểu cắm-là-chạy và khả năng khám phá công cụ khi đang chạy [S14].

**Kiến trúc (nguồn: repo).** Có host (ứng dụng AI như Claude Desktop, Cursor hoặc agent tự dựng), client (đầu nối giữ kết nối), server (chương trình nhẹ phơi ra dữ liệu, công cụ, prompt) và nguồn dữ liệu cục bộ hoặc từ xa [S14].

**Hai phần thực hành (nguồn: repo).** Phần một xây một MCP server tra giá tiền mã hóa bằng API CoinGecko: notebook dẫn tới file đi kèm `scripts/mcp_server.py` (người viết đọc thêm file này, nó không nằm trong danh sách nguồn), nơi công cụ `get_crypto_price` là một hàm gắn `@mcp.tool()` của thư viện FastMCP, rồi minh họa thêm một công cụ thứ hai theo cùng cách; server chạy bằng trình quản lý gói `uv`; rồi khai báo trong file cấu hình `claude_desktop_config.json` của Claude Desktop, khởi động lại và hỏi "giá Bitcoin bây giờ là bao nhiêu". Phần hai tự dựng host và client: agent kết nối server qua `stdio_client`, rồi đi qua bốn pha: khám phá công cụ, lập kế hoạch chọn công cụ, thực thi, diễn giải kết quả bằng ngôn ngữ tự nhiên [S14]. Mỗi lần gọi công cụ mở một kết nối mới; bài giải thích đó là cách làm đơn giản và bền, còn hệ thống thật nên giữ kết nối [S14].

**Hai chỗ cần để ý (nguồn: repo).** Một là phần kiến trúc viết rằng MCP dùng JSON-RPC 2.0 qua kết nối WebSocket, trong khi mã của chính bài lại dùng `stdio_client`, tức giao tiếp qua đầu vào và đầu ra chuẩn của một tiến trình con [S14]. Hai là ô cấu hình gán `ANTHROPIC_API_KEY` bằng một chuỗi giữ chỗ trong mã, trái với luật "khóa lấy từ môi trường, không ghi cứng" của AGENTS.md; hãy thay bằng biến môi trường thật và đừng dán khóa vào notebook [S14] [S2].

## An toàn và đánh giá

**Cổng phê duyệt đứng trước công cụ (nguồn: repo).** Bài human-in-the-loop (HITL, có con người trong vòng lặp) lập luận: một lời xác nhận trong chat sau khi công cụ đã chạy chỉ là thông báo, còn cổng phê duyệt thật phải chặn hành động trước tác dụng phụ. Ví dụ là công cụ hoàn tiền giả lập: tra cứu đơn hàng được xếp rủi ro thấp và chạy ngay; mọi lần hoàn tiền là rủi ro cao dù số tiền nhỏ, nên dừng lại chờ người duyệt [S15].

**Ba quyết định của người duyệt (nguồn: repo).** Người duyệt chỉ có thể trả lời approve, reject hoặc modify; modify bắt buộc kèm tham số mới, và tham số mới phải qua đúng bộ kiểm tra như đề xuất gốc. Từ chối không bao giờ vượt qua cổng. Hàm `execute_tool` độc lập từ chối hành động rủi ro cao nếu trạng thái chưa được cấp quyền, nên quy tắc vẫn đúng khi ai đó gọi vòng qua đồ thị. Nhật ký kiểm toán chỉ thêm vào, có dấu thời gian và tên người duyệt [S15].

**Dùng LangGraph interrupt (nguồn: repo).** Đồ thị gọi `interrupt` để dừng và `Command(resume=...)` để chạy tiếp cùng luồng. Bộ lưu `InMemorySaver` chỉ giữ trạng thái khi tiến trình còn sống; muốn khôi phục sau khi khởi động lại phải dùng bộ lưu bền vững. Notebook ghim `langgraph==0.2.76` để dùng API này và khuyên chạy trong môi trường riêng, vì `requirements.txt` của cả repo ghim phiên bản cũ hơn [S15] [S5].

**Cùng một bài học với vòng lặp (suy luận).** Cổng phê duyệt là ví dụ cụ thể của câu "quy tắc phải nằm trong động cơ": chính chính sách rủi ro và việc kiểm tra quyền là mã xác định, còn mô hình chỉ đề xuất hành động [S15] [S7].

**Đánh giá bằng dấu vết, không cần giám khảo AI (nguồn: repo).** Một câu trả lời cuối có thể trông hợp lý dù agent gọi sai công cụ, gửi sai tham số hoặc vượt ngân sách thời gian. Bài đánh giá dấu vết chấm chính lần thực thi: chuỗi công cụ đúng, tham số đúng, bằng chứng khớp kết quả công cụ, và độ trễ trong ngân sách, mỗi mục 25% điểm. Nếu có lỗi thực thi thì điểm bằng 0, vì lỗi nhanh không đáng điểm một phần [S16].

**Thiết kế để so sánh được (nguồn: repo).** Bộ chấm đứng ngoài agent và chỉ đọc một hợp đồng dữ liệu nhỏ, nên có thể so sánh một đồ thị LangGraph, một vòng lặp tự viết hay một agent đặt trên dịch vụ ngoài miễn là bộ chuyển đổi (adapter) xuất đủ trường. Bài chạy hoàn toàn offline với thư viện chuẩn của Python, so một agent mắc lỗi định tuyến với bản đã sửa, và cho ra cổng chất lượng dùng được trong kiểm thử hồi quy [S16].

## Đo chi phí và độ tin cậy

**Quyết định trong một lần chạy mô hình (nguồn: repo).** Bài "One-Step Decision Router" nhận xét nhiều bước của agent là quyết định, không phải viết lách: ticket này về đội nào, bình luận này có phải spam không. Thay vì bắt mô hình viết câu trả lời rồi phân tích chữ, bài đọc xác suất của token đầu tiên của từng lựa chọn sau một lần chạy mô hình, rồi chuẩn hóa trên các lựa chọn [S17].

**Biết mình sai (nguồn: repo).** Một bộ định tuyến sai 3 trên 10 lần vẫn dùng được nếu nó biết 3 lần nào, vì những ca đó chuyển cho người. Điều này chỉ đúng khi độ tự tin có ý nghĩa: nói 90% thì phải đúng chừng 9 trên 10, gọi là hiệu chỉnh (calibration). Bài đo bằng bảng độ tin cậy và sai số hiệu chỉnh kỳ vọng ECE, rồi thử temperature scaling và cổng độ tin cậy [S17].

**Dữ liệu và mô hình (nguồn: repo).** Bài chạy mô hình mở `Qwen/Qwen3-1.7B` ngay trên máy hoặc Colab miễn phí, không cần khóa API; video dùng bản 8B cần khoảng 16 GB bộ nhớ. Dữ liệu là tập kiểm tra banking77 gồm tin nhắn khách hàng ngân hàng, với 77 ý định được người viết bài gộp thành 7 đội; tối đa 3.080 tin [S17]. Phép gộp 77 thành 7 là của tác giả bài, và bài nói rõ có tin có thể thuộc hai đội [S17].

**Đọc rẻ, viết đắt (nguồn: repo).** Bài "Read vs Write" đo một câu trả lời tốn gì. Một câu trả lời có hai pha: đọc prompt (prefill) chạy song song nên chip bận tính toán và rẻ trên mỗi token; viết từng token (decode) cần đi qua toàn bộ trọng số cho chỉ một token, nên phần lớn thời gian chip chờ dữ liệu từ bộ nhớ. Bốn đòn bẩy quyết định chi phí: số token viết ra, cỡ mô hình, độ dài hội thoại đã có (bộ nhớ đệm KV lớn dần), và số câu trả lời dùng chung một lượt tải trọng số [S18].

**Đo trên máy bạn (nguồn: repo).** Notebook bấm giờ từng pha trên máy của người đọc, dùng văn bản truyện Sherlock Holmes từ Project Gutenberg làm đầu vào, và có bước đo năng lượng tùy chọn cho GPU NVIDIA bằng `pynvml`. Mặc định chạy xong trong vài phút trên laptop [S18]. Hai bài này cùng là bài mới của kho và cùng không cần khóa API [S1] [S17] [S18].

## Cách học và chạy

**Lộ trình năm bước (suy luận của người viết, dựa trên các nhóm trong bảng).** Bước một: đọc bài vòng lặp while để hiểu agent không có phép màu [S7]. Bước hai: bài hội thoại có nhớ rồi nhập môn LangGraph, để quen với trạng thái và đồ thị [S8] [S9]. Bước ba: chọn một ứng dụng hợp lĩnh vực của bạn, ví dụ hỗ trợ khách hàng, rồi sửa nhỏ để chạy trên dữ liệu của bạn [S10]. Bước bốn: đọc cổng phê duyệt và đánh giá dấu vết, để biết cách làm agent an toàn và kiểm được [S15] [S16]. Bước năm: MCP để nối công cụ thật, và hai bài đo chi phí khi cần quyết định về mô hình [S14] [S17] [S18].

**Môi trường (nguồn: repo).** `requirements.txt` ghim `langchain==0.2.16`, `langgraph==0.2.18`, `openai==1.43.0`, `autogen==0.3.0`, `pydantic==2.8.2` cùng nhiều gói khác [S5]. Suy luận: đây là dòng 0.2 của LangChain, khá cũ so với việc repo vẫn được cập nhật đến tháng 10/2026; notebook phê duyệt cần `langgraph==0.2.76` và khuyên dùng môi trường riêng [S15]. Suy luận: hãy tạo một môi trường ảo cho mỗi nhóm notebook thay vì cài hết `requirements.txt` vào một chỗ.

**Khóa API (người viết đếm).** Quét toàn bộ nội dung 59 notebook: `OPENAI_API_KEY` xuất hiện trong 40 notebook (khớp nguyên tên biến; một notebook nữa chỉ có `AZURE_OPENAI_API_KEY`), `LANGCHAIN_API_KEY` và `TAVILY_API_KEY` mỗi loại trong 6, `GROQ_API_KEY` trong 4, `ANTHROPIC_API_KEY` trong 4. Tên mô hình hay gặp nhất là `gpt-4o-mini` (26 notebook), rồi `gpt-4o` (9). Bài vòng lặp while dùng mô hình Claude, bài router và bài đọc-viết chạy mô hình mở trên máy [S7] [S17] [S18]. Suy luận: nếu bạn dùng nhà cung cấp khác, việc đổi lớp mô hình là phần của bạn.

**Chạy thế nào (nguồn: repo).** AGENTS.md yêu cầu chạy notebook từ trên xuống dưới trên kernel sạch [S2]. Bài hội thoại cho thấy cách quen thuộc: tạo file `.env` chứa khóa, gọi `load_dotenv()`, rồi chạy từng ô [S8]. Hãy bắt đầu bằng bài ngắn để biết chi phí thực tế trước khi chạy bài hơn một trăm ô [S1].

## Giấy phép, quảng cáo và theo dõi

**Giấy phép tùy chỉnh, chỉ phi thương mại (nguồn: repo).** LICENSE không phải giấy phép nguồn mở thông dụng mà là "Custom License Agreement" của Nir Diamant. Người dùng được dùng, sao chép, sửa đổi và phân phối nội dung cho mục đích không thương mại, với điều kiện ghi tên tác giả, dẫn liên kết repo và nêu rõ nếu đã sửa. Mọi quyền thương mại đều được tác giả giữ riêng; muốn dùng thương mại phải xin phép bằng văn bản [S4]. AGENTS.md cũng dặn đọc LICENSE trước khi tái sử dụng mã trong bối cảnh thương mại [S2].

**Với người đóng góp (nguồn: repo).** Điều khoản về đóng góp cho tác giả quyền cấp phép độc quyền, vĩnh viễn, không thể thu hồi, trên toàn thế giới đối với phần bạn gửi lên, kể cả cho mục đích thương mại; bạn giữ quyền dùng phần của mình cho mục đích phi thương mại, nhưng không có quyền thương mại nào với nó [S4]. Đây là tóm tắt văn bản gốc để bạn biết đi đọc ở đâu, không phải tư vấn pháp lý.

**Quảng cáo và tài trợ (nguồn: repo).** Đầu README là khối giới thiệu khóa học "Prompt to Production" của tác giả với giá nêu rõ 199 đô la, thanh toán một lần, truy cập trọn đời, kèm lời chứng thực và nút mua. Tiếp theo là nhà tài trợ CodeRabbit và Qodo, bản tin mà tác giả nói có hơn 50.000 người đọc, và các video YouTube [S1]. Đó là quyền của tác giả; điều đáng nhớ là phần "học miễn phí" và phần "bán khóa học" nằm cạnh nhau trên cùng một trang.

**Liên kết có theo dõi (nguồn: repo, người viết đếm).** Nhiều liên kết trong README đi qua một địa chỉ trung gian tên `rag-techniques-tracker` với tham số ghi lại nút nào được bấm [S1]. Ngoài ra 52 trong 59 notebook kết thúc bằng một ảnh nhúng gọi tới địa chỉ có tên `genai-agents-views-tracker`, ví dụ ở cuối bài hội thoại [S8]. Tên gọi cho thấy mục đích là đếm lượt xem; bài này không kiểm tra máy chủ đó nhận gì. Nếu bạn không muốn gửi yêu cầu đó, hãy đọc notebook bản tải về ở chế độ không tải ảnh ngoài.

## Điểm yếu và có nên dùng không

**Sáu điểm yếu (suy luận từ các nguồn).** Một, phiên bản thư viện trong `requirements.txt` đã cũ và không đồng nhất với notebook phê duyệt [S5] [S15]. Hai, đa số bài gắn với một nhà cung cấp mô hình trả phí (OpenAI), nên chạy thử tốn tiền và đổi nhà cung cấp là việc của bạn (người viết đếm) [S1]. Ba, nhiều bài ở quy mô đồ chơi: bộ nhớ trong dictionary [S11], đa agent theo kịch bản cố định [S13], tự cải thiện không có phép đo [S12]. Bốn, kiểm thử chỉ ở mức import và khói, theo chính AGENTS.md [S2]. Năm, các bài mới hơn (phê duyệt, dấu vết, router) tốt hơn hẳn về độ chặt chẽ nhưng là thiểu số [S15] [S16] [S17]. Sáu, giấy phép phi thương mại làm kho này không dùng nguyên văn được trong sản phẩm [S4].

**Tài liệu lệch nhau (nguồn: repo).** README nói 57 tutorial còn AGENTS.md nói 59 notebook [S1] [S2]; bài MCP viết WebSocket nhưng mã dùng stdio [S14]; `requirements.txt` ghim LangGraph 0.2.18 còn bài phê duyệt ghim 0.2.76 [S5] [S15]; luật "không ghi cứng khóa" đi cùng một ô gán chuỗi giữ chỗ [S2] [S14]. Cả bốn chỗ lệch đều nhỏ nhưng nên biết để không mất thời gian gỡ lỗi khi chạy. Thêm một quan sát khi đọc cây thư mục (không phải chỗ lệch): thư mục `.github/workflows` chỉ có một file, đổi dòng giá khóa học trong README theo mùa giảm giá, không có quy trình chạy thử các notebook.

**Kết luận: có nên dùng không.** Dùng như bản đồ và sổ bài tập; đừng dùng như thư viện hay nguồn mã cho sản phẩm có thu tiền. Repo hợp với người đã biết Python cơ bản, muốn hiểu agent chạy bên trong ra sao và xem nhiều mẫu thiết kế đặt cạnh nhau [S1] [S2]. Nếu mục tiêu là đưa agent vào sản phẩm, chính tác giả chỉ sang repo agents-towards-production, và giấy phép của repo này đòi bạn xin phép trước khi dùng thương mại [S2] [S4].

## Điều cần nhớ

Bốn điều đáng mang theo. Một: agent là vòng lặp quanh mô hình, và quy tắc bắt buộc phải nằm trong mã chứ không trong prompt [S7]. Hai: LangGraph biến luồng điều khiển thành đồ thị nhìn thấy được, và có mặt ở khoảng bảy phần mười bảng README (40 trên 57 hàng) [S1] [S9]. Ba: theo người viết, bài đáng đọc nhất là các bài về an toàn và đo lường (cổng phê duyệt, dấu vết, router, chi phí), vì chúng dạy cách biết agent có đáng tin hay không [S15] [S16] [S17] [S18]. Bốn: giấy phép chỉ cho dùng phi thương mại, quảng cáo và liên kết theo dõi là có thật, hãy đọc LICENSE trước khi dùng mã [S4] [S1].

## Lưu ý

Giới hạn nguồn: bài đọc bản sao nông (shallow clone) của repo tại commit 1b45571, ngày 17/10/2026. Người viết không mở trang GitHub, nên không đọc số sao, số fork, issue hay lịch sử commit; không có con số nào về mức độ phổ biến trong bài này. Ngoài sáu file tài liệu và công cụ (S1 đến S6), người viết đọc 12 notebook (S7 đến S18); với bài đánh giá dấu vết chỉ đọc phần mô tả và các ô mã đầu, với bài router và bài đọc-viết chỉ đọc phần mô tả. Người viết chưa chạy notebook nào vì không có khóa API trả phí, nên các câu về hành vi (ví dụ "mô hình bỏ qua luật trong prompt") là lời kể của tác giả notebook, không phải kết quả đã tái lập. Các con số đếm (59 notebook, 823 ô mã, 1.100 ô văn bản, 40 notebook có biến OPENAI_API_KEY, 52 notebook có ảnh theo dõi) tính bằng script trên thư mục đã tải, dễ kiểm lại; chúng thay đổi khi repo cập nhật. Phần giấy phép chỉ là tóm tắt, không phải tư vấn pháp lý. Repo đang được cập nhật thường xuyên nên có thể đã khác khi bạn đọc.

## Nguồn tham khảo

- [S1] Nir Diamant, README.md: giới thiệu, bảng 57 hàng, khóa học, tài trợ, dự án liên quan, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/README.md
- [S2] Nir Diamant, AGENTS.md: 59 notebook, bố cục, luật làm việc, hướng dẫn cho trợ lý AI, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/AGENTS.md
- [S3] Nir Diamant, CONTRIBUTING.md: cấu trúc chín phần của một notebook, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/CONTRIBUTING.md
- [S4] Nir Diamant, LICENSE: giấy phép tùy chỉnh chỉ phi thương mại, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/LICENSE
- [S5] Nir Diamant, requirements.txt: phiên bản thư viện được ghim, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/requirements.txt
- [S6] Nir Diamant, scripts/validate_notebook.py: tám tiêu đề bắt buộc, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/scripts/validate_notebook.py
- [S7] Nir Diamant, notebook Agent từ con số không: vòng lặp while, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/all_agents_tutorials/agent_while_loop_from_scratch.ipynb
- [S8] Nir Diamant, notebook Simple Conversational Agent, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/all_agents_tutorials/simple_conversational_agent.ipynb
- [S9] Nir Diamant, notebook Introduction to LangGraph, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/all_agents_tutorials/langgraph-tutorial.ipynb
- [S10] Nir Diamant, notebook Customer Support Agent với LangGraph, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/all_agents_tutorials/customer_support_agent_langgraph.ipynb
- [S11] Nir Diamant, notebook Memory-Enhanced Conversational Agent, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/all_agents_tutorials/memory_enhanced_conversational_agent.ipynb
- [S12] Nir Diamant, notebook Self-Improving Agent, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/all_agents_tutorials/self_improving_agent.ipynb
- [S13] Nir Diamant, notebook Multi-Agent Collaboration System, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/all_agents_tutorials/multi_agent_collaboration_system.ipynb
- [S14] Nir Diamant, notebook Building an Agent with MCP, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/all_agents_tutorials/mcp-tutorial.ipynb
- [S15] Nir Diamant, notebook Human-in-the-Loop Approval Agent, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/all_agents_tutorials/human_in_the_loop_approval_agent.ipynb
- [S16] Nir Diamant, notebook Trace-Based Agent Evaluation, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/all_agents_tutorials/trace_based_agent_evaluation.ipynb
- [S17] Nir Diamant, notebook One-Step Decision Router, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/all_agents_tutorials/one_step_decision_router.ipynb
- [S18] Nir Diamant, notebook Read vs Write: What One AI Answer Costs, 2026, https://github.com/NirDiamant/GenAI_Agents/blob/1b455719952dd3bf1ff90d8eb54a1d7870cce7af/all_agents_tutorials/read_vs_write_cost.ipynb
