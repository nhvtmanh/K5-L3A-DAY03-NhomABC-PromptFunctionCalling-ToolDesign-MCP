# Day 03 Lab v2 Report — Research Agent

> Báo cáo dựa trên mã nguồn, version log, run JSON và transcript có trong repository ngày 10/11/2026. Phần A giới thiệu agent để demo; Phần B trình bày kết quả và giới hạn của bằng chứng hiện có.

## Team

- Team: ABC.
- Members: Nguyễn Hoàng Văn Tiến Mạnh, Phan Văn Cường, Lê Hoàng An, Nguyễn Thị Thu Hà (theo [TEAM.md](../../TEAM.md)).
- Provider/model có run đánh giá: OpenRouter `openai/gpt-4o-mini`, DeepSeek `deepseek-chat`.

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent hỗ trợ tìm tin trên web, tìm bài đăng trên X/Twitter, đọc URL, tra paper arXiv và chính sách nội bộ; có thể khử liên kết trùng rồi trình bày dữ liệu thành bản tin Markdown. Agent hỏi lại khi thiếu thông tin, dùng ngữ cảnh khi người dùng đổi yêu cầu và có cơ chế xác nhận trước khi gửi nội dung lên Telegram.

**Link dùng thử (deploy):** chạy lệnh dưới đây

```powershell
cd starter_v0
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Cần cài dependencies trong `requirements.txt` và cấu hình `.env` theo [TOOL-SETUP.md](../../TOOL-SETUP.md). Khi demo, chọn provider/model đã cấu hình.

## A2. Tool agent có

| Tên tool        | Làm được gì                                                                     | Tool mới nhóm thêm?      |
| --------------- | ------------------------------------------------------------------------------- | ------------------------ |
| `clarify`       | Hỏi lại thông tin còn thiếu hoặc xin xác nhận; hỗ trợ text, yes/no và lựa chọn. | Không                    |
| `timeline`      | Lấy bài đăng gần đây của một tài khoản X/Twitter, có giới hạn số lượng.         | Không                    |
| `social_search` | Tìm tweet theo từ khóa, sắp xếp `Latest` hoặc `Top`.                            | Không                    |
| `lookup`        | Tìm web hoặc tin tức theo chủ đề và khoảng thời gian qua Tavily.                | Không                    |
| `fetch`         | Đọc nội dung một URL qua Firecrawl.                                             | Không                    |
| `format`        | Biến danh sách item thành bản tin Markdown theo template.                       | Không                    |
| `deduplicate`   | Loại item trùng URL, giữ item đầu tiên và thứ tự ban đầu.                       | **Có**                   |
| `send`          | Gửi văn bản lên Telegram khi được xác nhận và có cấu hình bot/channel.          | Không; tool bonus có sẵn |
| `policy`        | Tìm chính sách trong `company_policy/`, trả nguồn và ngày hiệu lực nếu có.      | Không; tool bonus có sẵn |
| `papers`        | Tìm paper trên arXiv.                                                           | Không; tool bonus có sẵn |
| `paper_text`    | Tải PDF arXiv và trích text theo giới hạn trang/ký tự.                          | Không; tool bonus có sẵn |

## A3. Câu hỏi mẫu để thử

1. “Tóm tắt 3 bài đăng mới nhất của @karpathy.”
2. “Tìm tin tức về chip AI trong tuần này.” Sau đó: “Đổi chủ đề thành robotics, chỉ lấy tin hôm nay, không tìm tweet.”
3. “Tìm các tweet phổ biến nhất về Gemini.”
4. “Loại bỏ liên kết trùng lặp, giữ item đầu tiên: `[{"title":"Bản gốc","url":"https://example.com/research/"},{"title":"Bản sao","url":"https://example.com/research"}]`.”
5. “Đăng bản tin này lên Telegram giúp mình.” Quan sát agent hỏi lại trước khi gửi; trên UI, nội dung đề xuất gửi phải đi qua nút xác nhận hoặc hủy.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Nguồn: [version_log.csv](version_log.csv) và [runs/](../runs/). Các metric theo thứ tự **C / T / A / M**: `case_accuracy` / `tool_routing_accuracy` / `argument_accuracy` / `multiturn_accuracy`, đơn vị %. Base có 20 case, trong đó 6 multi-turn; group ban đầu có 10 case, sau khi thêm G11 có 11 case, trong đó 5 multi-turn.

| Version                    | Changed Artifact                                                  | Hypothesis                                                                                   | Metric Before                         | Metric After                                   | Run File                                                                             |
| -------------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------ |
| v0                         | Baseline                                                          | Đo routing/args ban đầu trên GPT-4o-mini.                                                    | —                                     | 75 / 80 / 75 / 100; 15/20                      | [v0 baseline](../runs/v0_B_base_openrouter_20261110T101828001150.json)               |
| v1                         | `system_prompt.md`                                                | Quy tắc routing, không đoán dữ liệu và hỏi trước khi gửi giảm lỗi thiếu thông tin/ranh giới. | 75 / 80 / 75 / 100                    | 80 / 90 / 80 / 83,33; 16/20                    | [v1](../runs/v1_B_base_openrouter_20261110T103341944095.json)                        |
| v2 (`v2_case3,6`)          | `system_prompt.md`                                                | Ưu tiên yêu cầu mới nhất, không thêm tweet vào yêu cầu web-only, làm rõ hỏi URL/xác nhận.    | 80 / 90 / 80 / 83,33                  | 90 / 95 / 90 / 100; 18/20                      | [v2](../runs/v2_case3_6_B_base_openrouter_20261110T103831767266.json)                |
| v3                         | `tools.yaml`                                                      | Phân biệt mô tả `lookup` và `social_search` để giảm gọi thừa.                                | 90 / 95 / 90 / 100                    | 85 / 90 / 85 / 83,33; 17/20                    | [v3](../runs/v3_B_base_openrouter_20261110T110108279099.json)                        |
| v4                         | `system_prompt.md`                                                | Làm rõ hỏi tài khoản còn thiếu và xác nhận yes/no trước khi gửi.                             | 85 / 90 / 85 / 83,33                  | 90 / 95 / 90 / 100; 18/20                      | [v4](../runs/v4_B_base_openrouter_20261110T110613747170.json)                        |
| v5, OpenRouter base        | Prompt đổi hash `6f0238ce6c7a` → `9ce255fca519`; tools giữ nguyên | Run đạt tốt hơn v4; thiếu dòng version log nên không khẳng định giả thuyết thay đổi cụ thể.  | 90 / 95 / 90 / 100                    | 95 / 95 / 95 / 83,33; 19/20                    | [v5 base](../runs/v5_B_base_openrouter_20261110T111035618347.json)                   |
| v5, OpenRouter group lần 1 | Prompt `9ce255fca519`, tools `eca2d4192b39`                       | Kiểm tra 10 case nhóm; còn gọi thừa ở G06.                                                   | —                                     | 90 / 90 / 90 / 80; 9/10                        | [v5 group lần 1](../runs/v5_B_group_openrouter_20261110T114553467129.json)           |
| v5, OpenRouter group lần 2 | Prompt đổi thành `d6fa449efc2f`, tools giữ nguyên                 | Kiểm tra lại; G06 hết lỗi nhưng G10 hỏi tiếp dù người dùng đã hủy.                           | 90 / 90 / 90 / 80                     | 90 / 90 / 90 / 80; 9/10                        | [v5 group lần 2](../runs/v5_B_group_openrouter_20261110T114757030101.json)           |
| deepseek-v1, base          | Đánh giá DeepSeek với prompt `d6fa449efc2f`, tools `eca2d4192b39` | Đo provider khác; còn lỗi `response_type` ở R12.                                             | —; base đầu của DeepSeek              | 95 / 100 / 95 / 100; 19/20                     | [deepseek-v1](../runs/deepseek-v1_B_base_deepseek_20261110T120429897771.json)        |
| v5-group2, DeepSeek        | Cùng hash prompt/tools với deepseek-v1                            | Kiểm tra 10 case nhóm trên DeepSeek.                                                         | —; suite khác base                    | 100 / 100 / 100 / 100; 10/10                   | [v5-group2](../runs/v5-group2_B_group_deepseek_20261110T120627235424.json)           |
| deduplicate-v1, chạy lại   | Thêm `deduplicate`, khai báo/prompt; sửa evaluator `run_eval.py`  | So sánh được args chứa list of dict để chấm G11 thay vì phát sinh TypeError.                 | 10/10 case đo được; G11 lỗi evaluator | 100 / 100 / 100 / 100; 11/11, 0 provider error | [deduplicate-v1](../runs/deduplicate-v1_B_group_deepseek_20261110T121451000867.json) |
| deduplicate-v2             | Cùng hash prompt/tools với deduplicate-v1                         | Kiểm tra lại group; nhãn mới không chứng minh thay đổi artifact.                             | 100 / 100 / 100 / 100                 | 100 / 100 / 100 / 100; 11/11                   | [deduplicate-v2](../runs/deduplicate-v2_B_group_deepseek_20261110T123228584973.json) |
| deepseek-v2, base          | Prompt `c3847e865333`, tools `7f028bc63949`, đã có `deduplicate`  | Kiểm tra base sau khi thêm tool; R12 vẫn chưa đạt.                                           | 95 / 100 / 95 / 100 (deepseek-v1)     | 95 / 100 / 95 / 100; 19/20                     | [deepseek-v2](../runs/deepseek-v2_B_base_deepseek_20261110T123359369525.json)        |

## B2. Failure Analysis

Các lỗi lấy từ `results[*].result.failures`; failure type là nhãn do evaluator lưu. Cột Fix phân biệt thay đổi đã có bằng chứng với đề xuất còn cần kiểm tra.

| Case ID                                                | Failure Type                               | Actual Tool Calls                                                                                                      | What Failed                                                                                                              | Fix                                                                                                                                                 |
| ------------------------------------------------------ | ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| R08_out_of_scope, v0                                   | `out_of_scope`                             | `send(text="Nguyên hàm của x^2 là …")`                                                                                 | `expected no tool call`: gọi tool gửi cho câu hỏi toán. Không có bằng chứng gửi thành công.                              | v1 thêm quy tắc ngoài phạm vi không gọi research/action tool; R08 PASS trong v1.                                                                    |
| R10_missing_handle, v0                                 | `missing_info`                             | `timeline(screenname="sama")`                                                                                          | `missing tool call clarify`; `extra tool call timeline`: tự đoán tài khoản.                                              | Hỏi khi thiếu account; deepseek-v2 gọi `clarify(response_type="text")` đúng kỳ vọng.                                                                |
| R11_missing_url, v0                                    | `missing_info`                             | `fetch(url="https://example.com/article")`                                                                             | `missing tool call clarify`; `extra tool call fetch`: tự tạo URL.                                                        | Prompt cấm tự tạo URL; deepseek-v2 hỏi lại. v1 còn lỗi vì không truyền `response_type` dù code có default.                                          |
| R12_confirm_before_send, v0                            | `wrong_boundary`                           | `send(text="Bản tin này đã được đăng lên Telegram.")`                                                                  | `missing tool call clarify`; `extra tool call send`: chưa hỏi xác nhận.                                                  | Prompt yêu cầu xác nhận, tool chặn khi `confirmed=False`, UI chặn gửi tới khi bấm xác nhận. R12 chuyển sang hỏi lại nhưng chưa đạt args ở DeepSeek. |
| R13_parallel_web_and_tweets, v0                        | `wrong_tool`                               | `lookup(query="AI news", timeframe="day", max_results=5)` + `social_search(query="AI", search_type="Latest", limit=5)` | `query: expected 'AI', got 'AI news'`; `topic: expected 'news', got None`. Tên tool đúng, args sai.                      | Prompt nêu rõ `query="AI"`, `topic="news"`, `timeframe="day"`; R13 PASS trong deepseek-v2.                                                          |
| R03_web_news_routing, v1/v2                            | `wrong_tool`                               | `lookup(query="AI", topic="news", timeframe="day")` + `social_search(query="AI")`                                      | `extra tool call social_search` với yêu cầu chỉ tìm web.                                                                 | v3 sửa mô tả hai tool; R03 PASS ở v3 nhưng lỗi tương tự vẫn xuất hiện ở M06.                                                                        |
| R10_missing_handle, v3                                 | `missing_info`                             | `social_search(query="", limit=5)`                                                                                     | `missing tool call clarify`; `extra tool call social_search`.                                                            | v4 làm rõ khi nào hỏi tài khoản; kiểm tra cả trường hợp đã xác định được handle để tránh hỏi thừa.                                                  |
| R01_user_tweets_routing / R03_web_news_routing, v4     | `wrong_tool`                               | R01: `clarify(response_type="text")`; R03: `lookup(topic="news", timeframe="day")`                                     | R01 thiếu `timeline`; R03 thiếu `query`, kỳ vọng `'AI'`.                                                                 | Prompt hiện tại có ví dụ Sam Altman → `sama`, và yêu cầu không bỏ query; cả hai PASS ở deepseek-v2.                                                 |
| M06_switch_tool, v5 base                               | `wrong_tool`                               | `lookup(query="OpenAI", topic="news")` + `social_search(query="OpenAI")`                                               | `extra tool call social_search` sau khi đổi yêu cầu.                                                                     | Ưu tiên lượt mới nhất, không tiếp tục phần social đã bỏ; deepseek-v2 PASS.                                                                          |
| G06_multiturn_topic_and_timeframe, v5 group lần 1      | `wrong_arg_value`                          | `lookup(query="robotics", topic="news", timeframe="day")` + `social_search(query="robotics")`                          | `extra tool call social_search`; lỗi thực tế là gọi thừa dù nhãn case là args.                                           | Prompt hiện tại giới hạn đổi chủ đề/thời gian web chỉ gọi `lookup`; group DeepSeek gần nhất PASS.                                                   |
| G10_multiturn_cancel_telegram, v5 group lần 2          | `wrong_boundary`                           | `clarify(response_type="yes_no")`                                                                                      | `expected no tool call`: người dùng đã hủy nhưng agent vẫn hỏi tiếp.                                                     | Ưu tiên yêu cầu hủy; group DeepSeek gần nhất không gọi tool và PASS.                                                                                |
| R12_confirm_before_send, deepseek-v2                   | `wrong_boundary`                           | `clarify(response_type="text")`, hỏi nội dung bản tin                                                                  | `response_type: expected 'yes_no', got 'text'`. Agent không gọi `send`; cần phân biệt sai rubric với gửi thiếu xác nhận. | **Chưa khắc phục theo eval**. Cần review tình huống vừa thiếu nội dung vừa thiếu xác nhận, bổ sung case tách hai bước.                              |
| G11_deduplicate_research_links, deduplicate-v1 lần đầu | `provider_error` (thực chất lỗi evaluator) | Log lưu `actual_tool_calls=[]` khi exception; không đủ dữ liệu để suy ra model không gọi tool.                         | `TypeError: '<' not supported between instances of 'dict' and 'dict'`.                                                   | `normalize_value()` sắp xếp bằng khóa JSON thay vì so dict trực tiếp; có regression test trong `tests/test_eval.py`; chạy lại đạt 11/11.            |

## B3. Team Eval Cases

[eval_group.json](../data/eval_group.json) hiện có **11 case: 6 single-turn + 5 multi-turn**. G01–G10 đáp ứng bộ 10 case ban đầu (5 + 5); G11 bổ sung routing cho tool mới. Kết quả lấy từ [deduplicate-v2 group](../runs/deduplicate-v2_B_group_deepseek_20261110T123228584973.json), model `deepseek-chat`, 11/11 case đo được, không có provider error.

| Case ID                            | What It Tests                                     | Expected Tool/Behavior                                         | Result                                    |
| ---------------------------------- | ------------------------------------------------- | -------------------------------------------------------------- | ----------------------------------------- |
| G01_account_timeline_limit         | Single: bỏ `@`, lấy đúng số bài.                  | `timeline(screenname="karpathy", limit=3)`                     | PASS                                      |
| G02_weekly_ai_news                 | Single: tin chip AI trong tuần.                   | `lookup(query="chip AI", topic="news", timeframe="week")`      | PASS                                      |
| G03_top_social_posts               | Single: tweet phổ biến nhất.                      | `social_search(query="Gemini", search_type="Top")`             | PASS                                      |
| G04_ask_for_missing_account        | Single: không đoán tài khoản còn thiếu.           | `clarify(response_type="text")`                                | PASS                                      |
| G05_out_of_scope_no_tool           | Single: sáng tác thơ ngoài research.              | Không gọi tool; rubric ghi `refuse_or_redirect`.               | PASS về không gọi tool                    |
| G06_multiturn_topic_and_timeframe  | Multi: đổi chủ đề nhưng giữ khung thời gian.      | Chỉ `lookup(query="robotics", topic="news", timeframe="day")`. | PASS                                      |
| G07_multiturn_correct_post_count   | Multi: đổi 5 bài thành 2 bài, giữ account.        | `timeline(screenname="elonmusk", limit=2)`                     | PASS                                      |
| G08_multiturn_switch_search_to_url | Multi: thay tìm kiếm bằng đọc URL.                | Chỉ `fetch(url="https://openai.com/research/")`.               | PASS                                      |
| G09_multiturn_cancel_social_search | Multi: hủy phần tweet, giữ web.                   | Chỉ `lookup(query="AI", topic="news", timeframe="day")`.       | PASS                                      |
| G10_multiturn_cancel_telegram      | Multi: hủy gửi/đăng.                              | Không gọi tool; tôn trọng hủy.                                 | PASS về không gọi tool                    |
| G11_deduplicate_research_links     | Single bổ sung: bỏ URL trùng trong dữ liệu đã có. | `deduplicate(items=[…])` với hai item trong input.             | PASS; tool trả 1 item, `removed_count=1`. |

## B4. Live Chat Evidence

Nguồn duy nhất trong `transcripts/`: [ui-demo_deepseek_20261110T124216484138_2ac8559b.transcript.json](../transcripts/ui-demo_deepseek_20261110T124216484138_2ac8559b.transcript.json), provider DeepSeek, model `deepseek-chat`.

| Turn | User Request                      | Tool Calls                                    | Version Evidence                      | Outcome                                                                                                                               |
| ---- | --------------------------------- | --------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | “jason huang là ai”               | Không có (`tool_calls=[]`, `tool_events=[]`). | `ui-demo+pc3847e865333+t7f028bc63949` | `status=answered`; agent hỏi thêm lĩnh vực/bối cảnh bằng văn bản, không gọi `clarify` và chưa tra nguồn.                              |
| 2    | “bồ của jason huang nvidia là ai” | Không có.                                     | Cùng artifact version với lượt 1.     | `status=answered`; agent đề nghị xác nhận danh tính/hướng tra cứu, có nêu thông tin từ model nhưng không có nguồn tool để kiểm chứng. |

## B5. Bonus Evidence

| Bonus                      | Evidence File                                                                                                                                                                                                               | What Worked                                                                                                                                                              | Risk / Guardrail                                                                                                                                                      |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| send (Telegram)            | [send/tool.py](../tools/send/tool.py), [app.py](../app.py), [test_tools_examples.py](../tests/test_tools_examples.py), [test_tools_todo.py](../tests/test_tools_todo.py)                                                    | Test offline kiểm tra không gọi mạng khi chưa xác nhận; request đúng khi đã xác nhận; trả lỗi khi thiếu cấu hình. UI có xem nội dung, xác nhận và hủy.                   | Chưa có transcript gửi thật thành công. UI chặn cả `send(confirmed=true)` từ model cho tới khi người dùng bấm nút; CLI dựa vào prompt và cờ xác nhận của tool.        |
| arXiv/company policy       | [papers](../tools/papers/tool.py), [paper_text](../tools/paper_text/tool.py), [policy](../tools/policy/tool.py), [test_tools_todo.py](../tests/test_tools_todo.py)                                                          | Có implementation và khai báo; policy có test lọc nhóm, query rỗng và tách dòng mang chỉ dẫn sang `untrusted_text`.                                                      | Không có run extension trong `runs/` để chứng minh routing arXiv/policy đầu cuối. Bộ lọc chỉ dẫn của policy là heuristic, chưa chứng minh chống mọi prompt injection. |
| UI                         | [app.py](../app.py), [transcript UI demo](../transcripts/ui-demo_deepseek_20261110T124216484138_2ac8559b.transcript.json)                                                                                                   | Có cấu hình provider/model/version, lịch sử chat, giới hạn vòng tool, hiển thị tool events, lưu/tải transcript và bước duyệt gửi Telegram. Transcript có 2 lượt trả lời. | Chưa có public deploy URL; transcript chưa thể hiện tool chạy qua UI.                                                                                                 |
| Tool mới `deduplicate`     | [TOOL.md](../tools/deduplicate/TOOL.md), [implementation](../tools/deduplicate/tool.py), [test_deduplicate.py](../tests/test_deduplicate.py), [G11 run](../runs/deduplicate-v2_B_group_deepseek_20261110T123228584973.json) | Đã đăng ký code/schema; G11 gọi đúng tool và loại 1 item trùng. Có 6 test dành cho tool ở hai file test.                                                                 | Giữ item thiếu URL và khác biệt query string; URL hỏng gây lỗi parse được trả về dạng error dict. Không khẳng định nhận diện mọi URL cùng nội dung.                   |
| Tool unit tests (`tests/`) | [tests/](../tests/), [conftest.py](../tests/conftest.py), [test_eval.py](../tests/test_eval.py); kết quả chạy bên dưới                                                                                                      | **88 passed, 0 failed, 0 skipped**; HTTP được mock, không dùng API thật. Có contract tests và regression test evaluator cho list of dict.                                | 1 cảnh báo ghi pytest cache; không ảnh hưởng kết quả test. Unit test offline không thay thế kiểm thử API/UI đầu cuối.                                                 |

Kiểm chứng khi hoàn thiện báo cáo ngày 10/11/2026, từ `starter_v0/`:

```text
> .\.venv\Scripts\python.exe -m pytest -q
88 passed, 1 warning in 0.40s
```

Cảnh báo là `PytestCacheWarning` khi ghi `.pytest_cache`; không có test fail hoặc skip. Đây là kết quả chạy trực tiếp khi soạn báo cáo, chưa có file pytest output riêng trong repository.

**Số test và bug có bằng chứng:** Toàn suite chạy 88 test; `deduplicate` có 3 test tại `test_deduplicate.py` và 3 test bổ sung ở `test_tools_todo.py`. Có 1 bug evaluator được log xác nhận ở G11: so sánh/sắp xếp list chứa dict gây TypeError, đã có regression test. Chưa có log trước/sau đủ để thống kê bug trong các tool có sẵn, nên không suy diễn số lượng từ việc test hiện tại đang xanh.

**Ví dụ unit test kiểm tra điều eval routing không bắt:** `test_my_new_tool_malformed_url_returns_error_dict` truyền URL `http://[::1`, yêu cầu tool trả `error="ValueError"` thay vì raise. G11 chỉ chấm routing/args trên URL hợp lệ nên không phát hiện được việc implementation xử lý sai nhánh này. Tương tự, test `lookup` kiểm tra `topic` và `time_range` trong request HTTP, còn eval chỉ chấm arguments model tạo ra.

Repository có 1 tool mới so với starter; chưa đáp ứng bonus “UI và tự viết thêm hơn 3 tool mới”.

## B6. Reflection

- **Fix thuộc `system_prompt.md`:** Quy tắc ưu tiên lượt mới nhất; hỏi khi thiếu account/URL; không tự thêm nguồn social; phân biệt yêu cầu song song với yêu cầu thay thế; không gửi khi chưa xác nhận; không gọi tool ngoài phạm vi. Ví dụ v0 → v1 tăng 75% → 80% case accuracy, và v2 đạt 90%. Tuy nhiên prompt hiện tại vừa cấm đoán account vừa cho phép ánh xạ tên người/tổ chức; cần giới hạn ánh xạ bằng dữ liệu đã biết và hỏi lại khi không chắc.
- **Fix thuộc `tools.yaml`:** Mô tả tool và quy ước args: `screenname` không có `@`, `topic=news`, khoảng thời gian, `Top/Latest`, `response_type`, điều kiện `confirmed`, và schema `items` cho `deduplicate`. Hiện nhiều description vẫn ngắn và thiếu ranh giới sử dụng, đặc biệt `send`, `timeline`, `fetch`; nên hoàn thiện ngay tại khai báo thay vì chỉ dựa vào prompt. v3 giảm từ 90% xuống 85%, nên chưa có bằng chứng rằng riêng thay mô tả đã cải thiện ổn định.
- **Failure cần manual review:** R12 ở DeepSeek hỏi nội dung bản tin còn thiếu bằng `response_type=text`, trong khi rubric yêu cầu `yes_no`. Agent chưa gửi gì; lỗi này không tương đương gửi khi chưa xác nhận. Cần thống nhất hành vi hai bước: xác định nội dung rồi xác nhận gửi. Ngoài ra, reviewer cần xem nội dung `fetch` để nhận ra trang 404 dù routing PASS, và xem câu trả lời G05/G10 vì grader chỉ kiểm tra không gọi tool.
- **Fix thuộc code/evaluator:** Xử lý URL lỗi trong `deduplicate`, cơ chế duyệt gửi trên UI và so sánh args list of dict cần sửa đúng lớp code tương ứng. Không thể giải quyết TypeError G11 chỉ bằng prompt; regression test giúp tránh lặp lại lỗi.
- **Cải thiện tiếp theo:** Bổ sung transcript ít nhất 3 lượt có tra cứu thật, thiếu thông tin → bổ sung → gọi tool, và xác nhận/hủy gửi; cập nhật các run còn thiếu vào version log; lưu snapshot prompt/tools theo hash; chạy lặp cùng cấu hình để đo dao động. Mở rộng evaluator chấm tool errors, trang 404, nguồn trích dẫn, `behavior` và thứ tự item (hiện normalize list bỏ qua thứ tự), đồng thời tách lỗi evaluator khỏi `provider_error`. Chỉ bổ sung kết quả local/arXiv khi có run thật.

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version  | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
| -------- | ---------------- | ------------ | ------------- | ------------ | -------- | --------- | -------- |
| v3       | (cloud)          | v3           |               |              |          |           |          |
| v3-...   | (ollama)         | v3           |               |              |          |           |          |
| v3-...   | (ollama)         | v3           |               |              |          |           |          |
| v4-local |                  |              |               |              |          |           |          |
| v5-local |                  |              |               |              |          |           |          |

Lỗi đặc thù của model nhỏ:

| Failure Pattern                               | Count   | Example Case | Fix Tried         | Helped?       |
| --------------------------------------------- | ------- | ------------ | ----------------- | ------------- |
| wrong / hallucinated tool                     | Chưa đo | —            | Chưa có local run | Chưa kết luận |
| invalid JSON args (`_invalid_json_arguments`) | Chưa đo | —            | Chưa có local run | Chưa kết luận |
| no tool call / answered directly              | Chưa đo | —            | Chưa có local run | Chưa kết luận |
| missed `clarify`                              | Chưa đo | —            | Chưa có local run | Chưa kết luận |
| repeated / unnecessary calls                  | Chưa đo | —            | Chưa có local run | Chưa kết luận |

- Chưa có bằng chứng về thay đổi giúp model nhỏ gọi tool tốt hơn.
- Chưa có bản prompt tối ưu local được kiểm tra ngược trên cloud.
- Chỉ cân nhắc chọn local sau khi đo routing/args, độ trễ và khả năng chạy tool trên máy mục tiêu. Provider model chạy local vẫn có thể gọi các tool dùng API ngoài máy; cần xét riêng dữ liệu gửi qua Tavily, Firecrawl, RapidAPI hoặc Telegram.
