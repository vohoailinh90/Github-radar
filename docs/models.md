# Nguồn model miễn phí

Dùng đúng quy ước của [`docs/vps-team.md`](https://github.com/vohoailinh90/claude-agent-routing-template/blob/main/docs/vps-team.md)
(repo `claude-agent-routing-template`): tên biến key, dạng `provider/model`, "model đầu là chính, các model sau là dự phòng",
và **người viết với người soát lỗi khác họ model**. Khác biệt duy nhất: viết bài chỉ cần một lượt gọi API, nên không
dùng container OpenCode; `radar/llm.py` gọi thẳng endpoint tương thích OpenAI.

| Provider | Biến key | Endpoint (đổi bằng `RADAR_BASE_<PROVIDER>`) |
|---|---|---|
| `openrouter` | `OPENROUTER_API_KEY` | openrouter.ai/api/v1 |
| `google` | `GOOGLE_GENERATIVE_AI_API_KEY` | generativelanguage.googleapis.com/v1beta/openai |
| `mistral` | `MISTRAL_API_KEY` | api.mistral.ai/v1 |
| `groq` | `GROQ_API_KEY` | api.groq.com/openai/v1 |
| `deepseek` | `DEEPSEEK_API_KEY` | api.deepseek.com |
| `nvidia` | `NVIDIA_API_KEY` | integrate.api.nvidia.com/v1 |

Mặc định (`radar.yaml`): viết = `google/gemini-flash-latest`, dự phòng `google/gemini-flash-lite-latest`, `groq/openai/gpt-oss-120b` rồi `mistral/mistral-small-2603`; soát = `groq/openai/gpt-oss-120b`, `groq/openai/gpt-oss-20b`, rồi `mistral/mistral-small-2603`, rồi `google/gemini-flash-lite-latest` (người soát khác họ với model đã viết luôn được thử trước; cùng họ chỉ là phương án cuối). Mistral hiện báo hạn mức request/phút = 0 cho key của chủ repo (log ngày 12/10/2026), nên nó chỉ còn là dự phòng. Groq cần secret `GROQ_API_KEY`. Ngày 13/10/2026: Groq trả 403 của Cloudflare cho User-Agent mặc định của Python (đã sửa: mọi request gửi `User-Agent: github-radar/1.0`), rồi 404 cho `llama-3.3-70b-versatile`, và bước Doctor cho thấy key này không còn model Llama nào; chat dùng được là `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `openai/gpt-oss-safeguard-20b`, `qwen/qwen3.8-27b`. gpt-oss là model suy luận nên được gọi với `reasoning_effort: low`, để phần suy nghĩ không ăn hết `max_tokens`. Bước Doctor in `is offered` hoặc `is not offered` cho từng model và, khi có model bị gỡ, in danh sách tên key đó gọi được (`groq offers: ...`); một model trả 404 bị bỏ qua cho đến hết lần chạy. Danh sách model free
đổi liên tục; xem hiện trạng bằng `python3 radar.py models <provider>` (`--free` cho OpenRouter) rồi `doctor --ping`.
Có thể ghi đè không cần sửa file: `RADAR_MODELS_WRITER="google/x openrouter/vendor/y:free"`.

## Hành vi khi model lỗi

Lỗi 5xx (vd. Google 503 "high demand"): thử lại cùng model (tối đa 3 lần, chờ 2 s, 4 s). Treo quá thời gian hoặc không kết nối được: **sang model kế tiếp ngay** và model đó bị bỏ qua cho đến hết lượt chạy (mỗi model chỉ treo tối đa một lần, 120 s). Lỗi 4xx khác 408/425/429 (sai key, model không tồn tại) cũng không thử lại, sang model kế tiếp. Lỗi 429 (giới hạn theo phút): chờ theo `Retry-After` của server, tối thiểu 20 s, 40 s (tối đa 90 s), vì cửa sổ giới hạn là cả phút; rồi mới sang model kế tiếp. Lỗi 4xx (sai key...) không thử lại.
Thiếu key của một model thì bỏ qua model đó. Nếu **mọi** model đều lỗi, lượt chạy dừng sớm (không đốt quota cho các repo
còn lại), không ghi nhớ repo nào, và job báo đỏ. Hạn mức free (OpenRouter khoảng 50 lượt/ngày nếu chưa nạp credit) là giới hạn thật:
mỗi repo tốn 2-3 lượt cho mỗi ngôn ngữ.

## Quyền riêng tư

Dữ liệu gửi đi là README và cấu trúc thư mục của **repo công khai**, nên rủi ro huấn luyện trên dữ liệu thấp. Đừng thêm
nguồn riêng tư (README nội bộ) vào pipeline này mà không đổi sang endpoint không huấn luyện (xem báo cáo nghiên cứu trong repo template).
README của repo quét được là **dữ liệu không tin cậy**: prompt coi nó là dữ liệu, model không có công cụ nào, và đầu ra
phải qua các cổng kiểm tra trước khi được dùng.

## Một request quá lớn không bao giờ qua được

Lần chạy thật đầu tiên: bài viết thành công (Gemini Flash quá tải 503 nên chuyển sang Flash-Lite), nhưng Mistral trả 429 ngay lượt đầu và cả sau khi chờ 20 s, 40 s. Một request lớn gần bằng cả hạn mức phút (20.000 token) sẽ bị từ chối dù chờ bao lâu. Vì vậy README gửi đi giới hạn 8.000 ký tự (CJK tính khoảng 1 token/ký tự) và lượt soát chỉ xin tối đa 900 token trả lời. Log từng lượt gọi (`state/runs/*.json`, mục `models_log`) giờ ghi cả header `x-ratelimit-*` mà nhà cung cấp gửi kèm 429 để phân biệt "quá tải" với "request quá lớn".

Ngày 16/10/2026: giới hạn README nâng từ 8.000 lên 12.000 ký tự. Lần quét `crisng95/flowkit` đầu tiên cho bài thiếu lệnh cài đặt vì mục *Quick Start* của README nằm ở ký tự thứ 8.220, ngay sau mốc cắt. Mỗi request thêm khoảng 1.000 token README (README tiếng Anh, khoảng 3-4 ký tự/token); mỗi bài gửi README hai lần (viết và soát) và thêm một lần nữa nếu có vòng sửa. Ước tính một lượt soát khoảng 7-8,5 nghìn token (trước đó 5,5-6,5 nghìn): còn xa hạn mức 20.000 token/phút đã đo của Mistral, nhưng hạn mức token/phút của Groq (người soát đang dùng) cho key này **chưa được đo**; nếu chỉ 8.000 thì có thể vượt, khi đó code chuyển sang model soát kế tiếp (chậm hơn, có thể đổi họ model). Sau mỗi lần quét xem `models_log` trong `state/runs/*.json`: nếu thấy 429 hoặc lỗi kích thước request từ `groq/openai/gpt-oss-*` thì hạ `readme_max_chars` xuống (10.000 vẫn đủ cho Quick Start của flowkit).

Ngày 16/10/2026: mỗi lượt gọi trong `models_log` (`state/runs/*.json`) ghi thêm `seconds` (thời gian chờ trả lời, kể cả lượt lỗi: một timeout hiện ra khoảng 120) và `served` (tên model mà nhà cung cấp báo là đã trả lời, chỉ giữ ký tự của tên model, tối đa 80; để trống khi nhà cung cấp không nói). Lý do: `google/gemini-flash-latest` là alias luôn trỏ tới Flash mới nhất và timeout 4 trong 14 lượt gọi (13-16/10) mà log cũ không cho biết model thật là gì hay một lượt thành công mất bao lâu (ước tính từ thời gian cả bước quét: khoảng 30-90 giây, so với khoảng 3 giây của `flash-lite`). Sau một lần quét, đọc hai trường này để quyết định bước tiếp: giảm suy nghĩ (`reasoning_effort`), ghim tên model có ngày thay cho `-latest`, hay đổi thứ tự dự phòng. Các mục log trước ngày này không có hai trường đó.

Ngày 16/10/2026: bài học đổi thành **hướng dẫn làm theo từng bước** (khối `guide`: chuẩn bị, các bước có lệnh nguyên văn, kết quả mong đợi, lỗi thường gặp), và README được cắt **theo mục** (`radar/readme.py`) thay vì cắt đầu. Hai thay đổi này đổi kích thước request, **chưa đo bằng model thật**:
câu trả lời của model viết dài gần gấp đôi (khoảng 5-6 nghìn token tiếng Việt; `WRITE_MAX_TOKENS` đã nâng từ 4.500 lên 8.000), và request soát lỗi mang cả bản nháp dài hơn cộng README (ước tính 9-10 nghìn token, trước đó 7-8,5 nghìn). Với hạn mức 20.000 token/phút của Mistral vẫn còn chỗ,
nhưng hạn mức token/phút của Groq (người soát mặc định) vẫn chưa đo: nếu `models_log` có 429 hoặc lỗi kích thước từ `groq/openai/gpt-oss-*`, code chuyển sang người soát kế tiếp và có thể rơi vào họ model của người viết (xem `warnings` trong báo cáo: "checker shares the writer's model family").
Sau lần quét đầu theo định dạng mới, xem `models_log` và mục `written[].coverage` của `state/runs/*.json` (`used` / `readme_commands`: bài dùng bao nhiêu lệnh của README); nếu soát lỗi hay bị chuyển họ, hạ `readme_max_chars` (ví dụ 9.000) hoặc cho người soát chỉ nhận các mục README mà bài trích dẫn.

Ngày 17/10/2026: dữ liệu đầu tiên của `seconds`/`served` cho thấy endpoint tương thích OpenAI của Google trả về **chính tên alias đã gửi** (`served = gemini-flash-latest`), nên `served` không cho biết alias đang trỏ tới phiên bản nào (Groq thì trả tên đầy đủ, `openai/gpt-oss-120b`). Vì vậy `python3 radar.py doctor --ping` in thêm, cho mỗi model Google đang cấu hình, một dòng `info  google/<model> record: name=... version=... display=... thinking=... tokens in/out=... | <mô tả>` lấy từ **API gốc** của Google (`GET /v1beta/models/<model>`, key gửi trong header `x-goog-api-key`, không bao giờ nằm trong URL). **Đó là bản ghi metadata của model được hỏi, chưa phải bằng chứng về model đứng sau alias**: với một alias `-latest`, Google có thể trả bản ghi của chính alias (cùng tên, mô tả chung). Khi tên trong bản ghi trùng tên đã hỏi, dòng in kèm `[the record of the alias itself: it does not say which model the alias points to]`. Cái đáng đọc ở đó là `thinking` (model có suy nghĩ hay không) và giới hạn token; còn alias đổi sang phiên bản nào thì xem ghi chú phát hành của Google. Một cách chắc chắn hơn (chưa làm, cần một lượt gọi model thật): đọc `modelVersion` trong câu trả lời của API gốc. Nếu không tra được bản ghi thì in `WARN ... no model record` và doctor không đổi kết quả đạt/không đạt. Chưa kiểm chứng với key thật: mã chỉ in những trường có mặt và bỏ qua trường lạ. Bước "Doctor (is each model still offered?)" của workflow chạy `--ping` nên các dòng này xuất hiện trong log Actions.

## Giới hạn theo tài khoản (đo ngày 12/10/2026)

`mistral-small-2603`: 20.000 token/phút, 1 request/giây. Mỗi lượt soát tốn vài nghìn token, nên `pace_seconds: 45` (cộng thời gian model viết) giữ nhịp khoảng 1 lượt soát mỗi 60-75 giây, ước tính 7-9 nghìn token/phút. Xem số thật của bạn ở console Mistral, mục *Limites*; nếu cao hơn, giảm `pace_seconds` để chạy nhanh hơn.
