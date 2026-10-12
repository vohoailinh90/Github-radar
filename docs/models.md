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

Mặc định (`radar.yaml`): viết = `google/gemini-flash-latest`, soát = `mistral/mistral-small-2603` (tên cụ thể có trong mục *Limites* của console Mistral; alias `-latest` có thể không có). Danh sách model free
đổi liên tục; xem hiện trạng bằng `python3 radar.py models <provider>` (`--free` cho OpenRouter) rồi `doctor --ping`.
Có thể ghi đè không cần sửa file: `RADAR_MODELS_WRITER="google/x openrouter/vendor/y:free"`.

## Hành vi khi model lỗi

Lỗi 5xx: thử lại cùng model (tối đa 3 lần, chờ 2 s, 4 s). Lỗi 429 (giới hạn theo phút): chờ theo `Retry-After` của server, tối thiểu 20 s, 40 s (tối đa 90 s), vì cửa sổ giới hạn là cả phút; rồi mới sang model kế tiếp. Lỗi 4xx (sai key...) không thử lại.
Thiếu key của một model thì bỏ qua model đó. Nếu **mọi** model đều lỗi, lượt chạy dừng sớm (không đốt quota cho các repo
còn lại), không ghi nhớ repo nào, và job báo đỏ. Hạn mức free (OpenRouter khoảng 50 lượt/ngày nếu chưa nạp credit) là giới hạn thật:
mỗi repo tốn 2-3 lượt cho mỗi ngôn ngữ.

## Quyền riêng tư

Dữ liệu gửi đi là README và cấu trúc thư mục của **repo công khai**, nên rủi ro huấn luyện trên dữ liệu thấp. Đừng thêm
nguồn riêng tư (README nội bộ) vào pipeline này mà không đổi sang endpoint không huấn luyện (xem báo cáo nghiên cứu trong repo template).
README của repo quét được là **dữ liệu không tin cậy**: prompt coi nó là dữ liệu, model không có công cụ nào, và đầu ra
phải qua các cổng kiểm tra trước khi được dùng.

## Giới hạn theo tài khoản (đo ngày 12/10/2026)

`mistral-small-2603`: 20.000 token/phút, 1 request/giây. Mỗi lượt soát tốn vài nghìn token, nên `pace_seconds: 45` giữ nhịp khoảng 1-2 lượt soát/phút. Xem số thật của bạn ở console Mistral, mục *Limites*; nếu cao hơn, giảm `pace_seconds` để chạy nhanh hơn.
