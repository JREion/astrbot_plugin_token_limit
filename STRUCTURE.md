# STRUCTURE

鏈枃妗ｈ褰?v0.6.4 鐗堟湰鐨勬彃浠剁粨鏋勩€佸唴閮?API銆侀〉闈㈠厓绱犳槧灏勫拰涓昏鍑芥暟鑱岃矗銆?
## 鏂囦欢缁撴瀯

```text
astrbot_plugin_token_limit/
鈹溾攢鈹€ main.py
鈹溾攢鈹€ metadata.yaml
鈹溾攢鈹€ _conf_schema.json
鈹溾攢鈹€ README.md
鈹溾攢鈹€ DEVELOP.md
鈹溾攢鈹€ STRUCTURE.md
鈹溾攢鈹€ LICENSE
鈹溾攢鈹€ backend/
鈹?  鈹溾攢鈹€ __init__.py
鈹?  鈹溾攢鈹€ history_stats.py
鈹?  鈹溾攢鈹€ user_limits.py
鈹?  鈹斺攢鈹€ user_stats.py
鈹斺攢鈹€ pages/
    鈹斺攢鈹€ dashboard/
        鈹斺攢鈹€ index.html
```

杩愯鏃跺湪 AstrBot 鎻掍欢鏁版嵁鐩綍涓嬬敓鎴愶細

```text
<AstrBot plugin data>/astrbot_plugin_token_limit/
鈹溾攢鈹€ group_remarks.json
鈹溾攢鈹€ group_limits.json
鈹溾攢鈹€ history_usage.json
鈹斺攢鈹€ user_usage_48h.json
```

- `group_remarks.json`锛氫繚瀛?QQ 缇ゅ彿鍒板娉ㄥ悕鐨勬槧灏勶紝涓嶈窡闅?`limited_groups` 鍒犻櫎鑰屽垹闄ゃ€?- `group_limits.json`锛氫繚瀛?QQ 缇ゅ彿鍒颁釜鎬у寲姣忔棩 token 涓婇檺鐨勬槧灏勶紱涓€鏃︿繚瀛樺嵆瑕嗙洊鍏ㄥ眬 `daily_token_limit`锛屼笉闅忓悗缁叏灞€涓婇檺鍙樺寲銆?- `history_usage.json`锛氫繚瀛樺巻鍙?token 鐢ㄩ噺锛屽寘鍚瘡涓杩借釜缇ょ殑 `tracked_since`銆乣last_synced_at`銆乣total_tokens` 鍜岄潪闆跺皬鏃舵《 `hours`銆?- `user_usage_48h.json`锛氫繚瀛樿繎 48 灏忔椂鐨勭兢鍐呯敤鎴?token 鐢ㄩ噺灏忔椂妗跺拰灏介噺缂撳瓨鍒扮殑 QQ 鏄电О锛岃秴杩?48 灏忔椂鐨勬暟鎹細鍦ㄥ悓姝ユ椂涓㈠純銆?
## 鍏冩暟鎹笌閰嶇疆

### metadata.yaml

- `name`锛氭彃浠跺悕绉帮紝褰撳墠涓?`astrbot_plugin_token_limit`銆?- `version`锛氬綋鍓嶇増鏈?`0.6.4`銆?- `repo`锛氭彃浠朵粨搴撳湴鍧€銆?- `support_platforms`锛氶粯璁ゆ敮鎸?`aiocqhttp`銆乣qq_official`銆乣qq_official_webhook`銆?- `pages`锛氬０鏄?`dashboard` Plugin Page锛岄〉闈㈡枃浠朵负 `pages/dashboard/index.html`銆?
### _conf_schema.json

鍘熺敓 WebUI 閰嶇疆椤癸細

| 閰嶇疆椤?| 鍔熻兘 |
| --- | --- |
| `enabled` | 鎻掍欢鎬诲紑鍏炽€?|
| `limited_groups` | 闇€瑕侀檺娴佺殑 QQ 缇ゅ彿鍒楄〃锛涙柊缇ゅ彿浼氫粠鍔犲叆鏃跺埢寮€濮嬪巻鍙茬粺璁°€?|
| `daily_token_limit` | 鍗曠兢褰撳墠缁熻绐楀彛鍐呭熀纭€ token 涓婇檺銆?|
| `user_daily_token_limit` | 鍗曚釜缇よ亰鍐呭崟涓敤鎴峰綋鍓嶇粺璁＄獥鍙?token 涓婇檺锛沗-1` 琛ㄧず涓嶅惎鐢ㄣ€?|
| `over_limit_policy.action` | 瓒呴檺绛栫暐锛歚stop_llm` 鎴?`fallback_provider`銆?|
| `over_limit_policy.fallback_provider_id` | 鍥為€€妯″瀷渚涘簲鍟?ID銆?|
| `over_limit_policy.fallback_token_limit` | 鍥為€€妯″瀷棰濆 token 涓婇檺锛涚‖涓婇檺涓?`daily_token_limit + fallback_token_limit`銆?|
| `over_limit_policy.block_wake_words_after_limit` | 瓒呰繃缇よ亰鍩虹姣忔棩涓婇檺鍚庢槸鍚﹂樆鏂敜閱掕瘝瑙﹀彂锛沗@bot` 浠嶅彲缁х画杩涘叆鍥為€€鎴栧仠姝㈠搷搴旂瓥鐣ャ€?|
| `refresh_time` | 褰撳墠绐楀彛鍒锋柊鏃堕棿锛屾寜 AstrBot 鏈哄櫒鏈湴鏃跺尯璁＄畻銆?|
| `qq_platform_names` | QQ 骞冲彴閫傞厤鍣ㄥ悕绉扮櫧鍚嶅崟銆?|
| `match_unique_session` | 鏄惁鍏煎 `unique_session` 褰㈠紡鐨?`umo`銆?|
| `block_message` | 杈惧埌鍋滄璋冪敤鏉′欢鏃跺彂閫佺殑鎻愮ず銆?|
| `send_block_message` | 鏄惁鍙戦€佹彁绀恒€?|

`main.py` 鐨?`CONFIG_SCHEMA` 涓?`_conf_schema.json` 淇濇寔瀛楁涓€鑷淬€侾lugin Page 閫氳繃 `GET config` 鑾峰彇杩愯鏃?schema锛屽苟鍔ㄦ€佹敞鍏ュ洖閫€渚涘簲鍟嗕笅鎷夐€夐」銆?
## main.py

### 甯搁噺涓庢暟鎹粨鏋?
- `PLUGIN_NAME`锛氭彃浠跺悕绉板拰 Web API 鍓嶇紑銆?- `GROUP_REMARKS_FILE`锛氬娉ㄦ枃浠跺悕銆?- `GROUP_LIMITS_FILE`锛氱兢鑱婁釜鎬у寲姣忔棩涓婇檺鏂囦欢鍚嶃€?- `MAX_GROUP_REMARK_LENGTH`锛氬娉ㄦ渶澶ч暱搴︼紝褰撳墠 64銆?- `OVER_LIMIT_STOP` / `OVER_LIMIT_FALLBACK`锛氳秴闄愮瓥鐣ユ灇涓惧€笺€?- `TOKEN_FIELDS_SUM`锛欰strBot `ProviderStat` 涓緭鍏ャ€佺紦瀛樿緭鍏ュ拰杈撳嚭 token 瀛楁姹傚拰琛ㄨ揪寮忋€?- `CONFIG_SCHEMA`锛氬悗绔厤缃?schema銆?- `UsageWindow`锛氬綋鍓嶉檺娴佺獥鍙ｏ紝鍖呭惈鏈湴鍜?UTC 璧锋鏃堕棿銆?
### 妯″潡绾у伐鍏峰嚱鏁?
- `_ok()` / `_error()`锛氱敓鎴愮粺涓€ API 鍝嶅簲銆?- `_split_group_values()`锛氬吋瀹?list銆佹暟瀛椼€侀€楀彿銆佺┖鏍笺€佸垎鍙枫€佷腑鏂囨爣鐐瑰拰鎹㈣銆?- `_normalize_group_id()`锛氭爣鍑嗗寲缇ゅ彿锛屽吋瀹?`123.0`銆?- `_escape_like()`锛氳浆涔?SQL `LIKE` 閫氶厤绗︺€?- `_format_tokens()`锛氭牸寮忓寲 token 鏁颁负 `K` / `M`銆?- `_parse_refresh_time()`锛氳В鏋?`HH:MM`銆?- `_local_timezone()`锛氳幏鍙栬繍琛屾満鍣ㄦ湰鍦版椂鍖恒€?- `_build_usage_window()`锛氭牴鎹?`refresh_time` 鐢熸垚褰撳墠 24 灏忔椂闄愭祦缁熻绐楀彛銆?
### Main 鍒濆鍖?
`class Main(UserLimitMixin, UserStatsMixin, HistoryStatsMixin, Star)` 缁勫悎鍗曠敤鎴烽檺娴併€佷粖鏃ョ敤鎴风粺璁°€佸巻鍙茬粺璁?mixin 鍜?AstrBot `Star`銆?
`__init__(context, config)`锛?
- 淇濆瓨 `Context` 鍜岄厤缃璞°€?- 瑙ｆ瀽 `group_remarks.json`銆乣history_usage.json` 涓?`user_usage_48h.json` 璺緞銆?- 瑙ｆ瀽 `group_limits.json` 璺緞銆?- 鍒濆鍖?`_history_sync_lock` 涓?`_user_sync_lock`锛岄伩鍏嶅涓姹傚苟鍙戝悓姝ュ悓涓€鎸佷箙鍖栫粺璁℃枃浠躲€?- 璋冪敤 `_ensure_history_tracking_for_current_groups()`锛岃褰撳墠閰嶇疆涓殑缇ゅ彿鍦ㄦ彃浠跺惎鍔ㄦ椂寮€濮嬪巻鍙茶拷韪€?- 璋冪敤 `_ensure_user_tracking_for_current_groups()`锛岃褰撳墠閰嶇疆涓殑缇ゅ彿鍦ㄦ彃浠跺惎鍔ㄦ椂寤虹珛浠婃棩鐢ㄦ埛缁熻缁撴瀯銆?- 娉ㄥ唽 Web API锛?  - `GET /astrbot_plugin_token_limit/config`
  - `POST /astrbot_plugin_token_limit/config`
  - `GET /astrbot_plugin_token_limit/usage`
  - `GET /astrbot_plugin_token_limit/history`
  - `GET /astrbot_plugin_token_limit/user-usage`
  - `GET /astrbot_plugin_token_limit/providers`
  - `GET /astrbot_plugin_token_limit/remarks`
  - `POST /astrbot_plugin_token_limit/remarks`
  - `GET /astrbot_plugin_token_limit/group-settings`
  - `POST /astrbot_plugin_token_limit/group-settings`

`initialize()`锛?
- 鎻掍欢鍚敤鍚庡惎鍔ㄥ巻鍙茬粺璁′笌浠婃棩鐢ㄦ埛缁熻鍚庡彴鍚屾浠诲姟銆?
`terminate()`锛?
- 鎻掍欢绂佺敤鎴栭噸杞芥椂鍙栨秷鍘嗗彶缁熻涓庝粖鏃ョ敤鎴风粺璁″悗鍙板悓姝ヤ换鍔°€?
### 閰嶇疆涓庡娉ㄥ嚱鏁?
- `_resolve_group_remarks_path()`锛氫紭鍏堜娇鐢?`StarTools.get_data_dir()`锛屽け璐ユ椂鍥為€€鎻掍欢鐩綍銆?- `_load_group_remarks()` / `_save_group_remarks()`锛氳鍐欏娉?JSON銆?- `_sanitize_group_remark()`锛氳鍓娉ㄣ€?- `_resolve_group_limits_path()`锛氫笌澶囨敞鏂囦欢鍚岀洰褰曞瓨鏀剧兢鑱婁釜鎬у寲涓婇檺鏂囦欢銆?- `_load_group_limits()` / `_save_group_limits()`锛氳鍐?`group_limits.json`锛屾寜缇ゅ彿淇濆瓨闈炶礋鏁存暟 token 涓婇檺銆?- `_config_value()`锛氳鍙栭厤缃紝缂虹渷鏃朵娇鐢?schema 榛樿鍊笺€?- `_serialize_config()`锛氳緭鍑哄畬鏁撮厤缃揩鐓с€?- `_sanitize_config()`锛氭牎楠屽苟鏍囧噯鍖栨墍鏈夐厤缃」锛沗user_daily_token_limit` 鏈€灏忓€间负 `-1`锛宍-1` 琛ㄧず鍏抽棴鍗曠敤鎴烽檺娴併€?- `_sanitize_over_limit_policy()`锛氭牎楠岃秴闄愮瓥鐣ワ紝鍥為€€绛栫暐蹇呴』濉啓涓旇兘鎵惧埌渚涘簲鍟嗭紝骞朵繚瀛樷€滆秴闄愬悗涓嶅啀鍝嶅簲鍞ら啋璇嶁€濆紑鍏炽€?- `_normalize_config_list()`锛氭爣鍑嗗寲鍒楄〃鍨嬮厤缃€?
### 闄愭祦鐩爣璇嗗埆

- `_limited_groups()`锛氳鍙栧苟鍘婚噸闄愭祦 QQ 缇ゅ彿銆?- `_qq_platform_names()`锛氳鍙?QQ 骞冲彴閫傞厤鍣ㄥ悕绉伴泦鍚堛€?- `_qq_platform_ids()`锛氫粠 AstrBot platform manager 瑙ｆ瀽骞冲彴瀹炰緥 ID锛涙棤娉曡В鏋愭椂鍥為€€骞冲彴鍚嶇О銆?- `_is_enabled()`锛氬垽鏂彃浠舵槸鍚﹀惎鐢ㄣ€?- `_is_qq_group_event(event)`锛氬垽鏂槸鍚︿负鐩爣 QQ 骞冲彴缇よ亰娑堟伅銆?- `_event_get_extra(event, key)`锛氬吋瀹硅鍙?AstrBot 浜嬩欢 `extra` 鏁版嵁锛屽け璐ユ椂杩斿洖绌恒€?- `_event_truthy_attr(event, name)`锛氬吋瀹硅鍙栦簨浠跺竷灏斿睘鎬ф垨鏃犲弬鏂规硶銆?- `_event_has_at_bot(event)`锛氬敖閲忛€氳繃浜嬩欢灞炴€с€佹秷鎭摼 At 缁勪欢鍜屽師濮嬫秷鎭垽鏂槸鍚︾敱 `@bot` 瑙﹀彂锛涜瘑鍒负 `@bot` 鏃朵笉浼氳鍞ら啋璇嶅紑鍏抽樆鏂€?- `_is_wake_word_invocation(event)`锛氬湪闈?`@bot` 瑙﹀彂鍓嶆彁涓嬶紝璇嗗埆鍞ら啋璇嶈Е鍙戜簨浠躲€?- `_should_block_wake_word_invocation(event, limit_context)`锛氬綋寮€鍏冲惎鐢ㄤ笖缇よ亰鐢ㄩ噺杈惧埌鏈夋晥鍩虹涓婇檺鏃讹紝鍒ゆ柇鏈鍞ら啋璇嶈Е鍙戞槸鍚﹂渶瑕侀樆鏂€?- `_umo_candidates_for_group(group_id)`锛氱敓鎴愭爣鍑?`umo` 鍊欓€夊€笺€?- `_unique_session_like_patterns(group_id)`锛氱敓鎴愬吋瀹逛細璇濋殧绂荤殑 `LIKE` 鍖归厤瑙勫垯銆?
### 鐢ㄩ噺銆佸洖閫€鍜岀‖涓婇檺

- `_daily_limit()`锛氳鍙栧熀纭€ token 涓婇檺銆?- `_daily_limit_for_group(group_id, group_limits=None)`锛氳鍙栨煇涓兢鑱婄殑鏈夋晥鍩虹涓婇檺锛涘瓨鍦ㄤ釜鎬у寲涓婇檺鏃朵紭鍏堜娇鐢?`group_limits.json`锛屽惁鍒欏洖閫€鍏ㄥ眬 `daily_token_limit`銆?- `_over_limit_policy()`锛氬悎骞跺苟娓呮礂瓒呴檺绛栫暐锛屽寘鎷洖閫€閰嶇疆鍜屽敜閱掕瘝闃绘柇寮€鍏炽€?- `_fallback_provider_id()` / `_fallback_token_limit()`锛氳鍙栧洖閫€渚涘簲鍟嗗拰鍥為€€棰濆害銆?- `_fallback_provider_exists(provider_id)`锛氭鏌ヤ緵搴斿晢瀛樺湪涓旀敮鎸?`text_chat`銆?- `_provider_options()`锛氫粠 `Context.get_all_providers()` 鐢熸垚鍥為€€渚涘簲鍟嗛€夐」銆?- `_config_schema_for_page()`锛氬悜椤甸潰 schema 娉ㄥ叆 `fallback_provider_id.options`銆?- `_query_usage_for_group(group_id, window, provider_id=None, exclude_provider_id=None)`锛?  - 鏌ヨ AstrBot 鍘熺敓 `ProviderStat`銆?  - 鎸夊綋鍓?`umo` 鍖归厤鍙ｅ緞缁熻 token銆?  - 杩斿洖绐楀彛鎬婚噺鍜屽皬鏃舵《銆?- `_query_split_usage_for_group()`锛?  - 閰嶇疆鍥為€€渚涘簲鍟嗘椂锛屾媶鍒嗗師濮嬩緵搴斿晢鐢ㄩ噺鍜屽洖閫€渚涘簲鍟嗙敤閲忋€?  - 鏈厤缃洖閫€渚涘簲鍟嗘椂锛屾墍鏈夌敤閲忓綊鍏?`primary_used`銆?- `_build_limit_state()`锛?  - `stop_llm`锛歚used < limit` 涓?`normal`锛宍used >= limit` 涓?`stopped`銆?  - `fallback_provider` 涓斿洖閫€棰濆害澶т簬 0锛歚used < limit` 涓?`normal`锛宍limit <= used < limit + fallback_token_limit` 涓?`fallback`锛宍used >= hard_limit` 涓?`stopped`銆?  - 鍥為€€渚涘簲鍟嗘槸鍚﹀彲鐢ㄤ笉鏀瑰彉纭笂闄愶紝鍙奖鍝嶆槸鍚﹁兘寮哄埗閫夋嫨璇ヤ緵搴斿晢銆?- `_build_event_limit_context(event)`锛氫负绛夊緟 LLM 鍜?LLM 璇锋眰閽╁瓙鏋勯€犵粺涓€闄愭祦涓婁笅鏂囥€?- `_build_usage_payload()`锛氱敓鎴?Plugin Page 褰撳墠绐楀彛鐢ㄩ噺鏁版嵁锛屽寘鎷娉ㄣ€佺兢鑱婃湁鏁堜笂闄愩€佹槸鍚︿娇鐢ㄤ釜鎬у寲涓婇檺銆佺姸鎬併€佺‖涓婇檺銆佸洖閫€鏍囩鎵€闇€瀛楁鍜屽皬鏃舵《銆?
### Web API 鍑芥暟

| 鍑芥暟 | endpoint | 浣滅敤 |
| --- | --- | --- |
| `api_get_config()` | `GET config` | 杩斿洖 `{config, schema}`銆?|
| `api_save_config()` | `POST config` | 淇濆瓨閰嶇疆骞跺己鍒跺悓姝ヤ竴娆″巻鍙茬粺璁°€?|
| `api_get_usage()` | `GET usage` | 鑺傛祦鍚屾鍘嗗彶缁熻鍜屼粖鏃ョ敤鎴风粺璁★紝骞惰繑鍥炲綋鍓嶇獥鍙ｇ敤閲忋€?|
| `api_get_history()` | `GET history` | 鐢?`HistoryStatsMixin` 鎻愪緵锛岃繑鍥炲巻鍙蹭笅鎷夎彍鍗曞拰鏌辩姸鍥炬暟鎹€?|
| `api_get_user_usage()` | `GET user-usage` | 鐢?`UserStatsMixin` 鎻愪緵锛岃繑鍥炲綋鍓嶅埛鏂板懆鏈熷唴鏌愮兢 Top N 鐢ㄦ埛 token 鐢ㄩ噺鎺掕銆?|
| `api_get_providers()` | `GET providers` | 杩斿洖鍙敤鍥為€€渚涘簲鍟嗗垪琛ㄣ€?|
| `api_get_remarks()` | `GET remarks` | 杩斿洖澶囨敞鏄犲皠銆?|
| `api_save_remark()` | `POST remarks` | 淇濆瓨鎴栧垹闄ゅ娉ㄣ€?|
| `api_get_group_settings()` | `GET group-settings` | 杩斿洖鏌愪釜缇よ亰鐨勬湁鏁堟瘡鏃ヤ笂闄愩€佸叏灞€涓婇檺鍜屾槸鍚﹀凡璁剧疆涓€у寲涓婇檺銆?|
| `api_save_group_settings()` | `POST group-settings` | 淇濆瓨鏌愪釜缇よ亰鐨勪釜鎬у寲姣忔棩涓婇檺鍒?`group_limits.json`銆?|

缁熶竴鍝嶅簲缁撴瀯锛?
```json
{
  "status": "ok",
  "message": null,
  "data": {}
}
```

### LLM 璇锋眰閽╁瓙

- `on_waiting_llm_request(event)`锛?  - 鍏堣皟鐢?`_remember_user_usage_event()` 灏介噺缂撳瓨缇ゅ唴鐢ㄦ埛 QQ 鏄电О銆?  - 璋冪敤 `_block_user_daily_limit_if_needed()`锛涘惎鐢ㄥ崟鐢ㄦ埛涓婇檺涓旇鐢ㄦ埛鍦ㄨ缇ゅ綋鍓嶇獥鍙ｇ敤閲忚揪鍒颁笂闄愭椂锛岄潤榛?`event.stop_event()`锛屼笉杩涘叆鍥為€€妯″瀷锛屼篃涓嶅彂閫佺兢鑱婃彁绀恒€?  - 鍏堣皟鐢?`_maybe_sync_history_stats()`锛屾寜 5 鍒嗛挓鑺傛祦琛ラ綈鍘嗗彶缁熻銆?  - 璋冪敤 `_maybe_sync_user_stats()`锛屾寜 2 鍒嗛挓鑺傛祦琛ラ綈杩?48 灏忔椂鐢ㄦ埛缁熻銆?  - 鍦?AstrBot 閫夋嫨 provider 涔嬪墠璁＄畻闄愭祦鐘舵€併€?  - 鑻?`block_wake_words_after_limit` 鍚敤锛屼笖缇よ亰鐢ㄩ噺宸茬粡杈惧埌璇ョ兢鏈夋晥鍩虹涓婇檺锛屽垯闃绘柇鍞ら啋璇嶈Е鍙戜簨浠讹紱`@bot` 瑙﹀彂缁х画杩涘叆鍚庣画鍥為€€鎴栧仠姝㈠搷搴旂瓥鐣ャ€?  - 鍥為€€鍖洪棿涓斿洖閫€渚涘簲鍟嗘湁鏁堟椂鍐欏叆 `event.set_extra("selected_provider", fallback_provider_id)`銆?  - 鍥為€€渚涘簲鍟嗗け鏁堟椂涓嶅啓鍏ワ紝浜ょ粰 AstrBot 褰撳墠鍙敤渚涘簲鍟嗐€?- `on_llm_request(event, req)`锛?  - 鍏堣ˉ鍏呭甫 `conversation_id` 鐨勭敤鎴疯姹傚綊鍥犲揩鐓э紝骞跺啀娆℃墽琛屽崟鐢ㄦ埛涓婇檺鍏滃簳闈欓粯闃绘柇銆?  - 澶嶇敤 `_build_event_limit_context()` 鍋氬厹搴曘€?  - 鍐嶆鎵ц鍞ら啋璇嶉樆鏂垽鏂紝閬垮厤绛夊緟 LLM 閽╁瓙鏈敓鏁堟椂婕忔嫤銆?  - `normal` 鍜?`fallback` 鏀捐銆?  - `stopped` 鏃舵寜閰嶇疆鍙戦€?`block_message` 骞?`event.stop_event()`銆?
## backend/user_limits.py

`UserLimitMixin` 鐙珛鎵胯浇鈥滃崟涓敤鎴锋瘡鏃ョ敤閲忎笂闄愨€濈殑鍒ゅ畾閫昏緫銆傝 mixin 鍙湪 `user_daily_token_limit >= 0` 鏃跺伐浣滐紱榛樿 `-1` 涓嶅悓姝ャ€佷笉鏌ヨ銆佷笉鎷︽埅锛屼互鑺傜害璧勬簮銆?
### Mixin 鍑芥暟

- `_user_daily_limit()`锛氳鍙?`user_daily_token_limit`锛岄潪娉曞€兼寜 `-1` 澶勭悊銆?- `_user_daily_limit_enabled()`锛氬垽鏂崟鐢ㄦ埛闄愭祦鏄惁鍚敤銆?- `_user_usage_total_for_event(event)`锛?  - 浠呭鐞嗗凡鍚敤鎻掍欢銆佺洰鏍?QQ 缇よ亰銆佺兢鍙峰湪 `limited_groups` 鍐呬笖鍙幏鍙栧彂閫佽€?ID 鐨?LLM 浜嬩欢銆?  - 寮哄埗鍚屾璇ョ兢浠婃棩鐢ㄦ埛缁熻銆?  - 鍚堝苟 ProviderStat 瀹炴椂鑱氬悎缁撴灉鍜?`user_usage_48h.json` 涓凡褰掑洜灏忔椂妗讹紝寰楀埌璇ョ敤鎴峰湪璇ョ兢褰撳墠鍒锋柊鍛ㄦ湡鍐呯殑 token 鎬婚噺銆?- `_should_block_user_daily_limit(event)`锛氬綋鐢ㄦ埛褰撳墠绐楀彛鐢ㄩ噺杈惧埌鎴栬秴杩囦笂闄愭椂杩斿洖闃绘柇涓婁笅鏂囥€?- `_block_user_daily_limit_if_needed(event, stage)`锛氶潤榛橀樆鏂鐢ㄦ埛鏈 LLM 璇锋眰锛屼粎鍐?AstrBot 鏃ュ織锛屼笉鍙戦€?`block_message`锛屼笉鍒囨崲鍥為€€渚涘簲鍟嗐€?
## backend/history_stats.py

`HistoryStatsMixin` 鐙珛缁存姢鍘嗗彶缁熻閫昏緫锛岄伩鍏?`main.py` 缁х画鑶ㄨ儉銆?
### 甯搁噺

- `HISTORY_STATS_FILE`锛氭寔涔呭寲鏂囦欢鍚?`history_usage.json`銆?- `HISTORY_STATS_VERSION`锛氬巻鍙叉枃浠剁粨鏋勭増鏈€?- `HISTORY_SYNC_OVERLAP`锛氬悓姝ュ洖鐪嬬獥鍙ｏ紝褰撳墠 2 灏忔椂锛岀敤浜庝慨姝?AstrBot 寤惰繜鍐欏叆銆?- `HISTORY_SYNC_MIN_INTERVAL`锛氶潪寮哄埗鍚屾鏈€鐭棿闅旓紝褰撳墠 5 鍒嗛挓銆?- `HISTORY_BACKGROUND_SYNC_INTERVAL`锛氬悗鍙板悓姝ラ棿闅旓紝褰撳墠 3600 绉掋€?- `HISTORY_DEFAULT_TOP_LIMIT`锛氭湭閫夋嫨缇よ亰鏃跺睍绀?Top N锛屽綋鍓?10銆?- `HISTORY_RANGE_KEYS`锛歚24h`銆乣7d`銆乣30d`銆乣all`銆?
### 鏁版嵁缁撴瀯

- `HistoryUsageWindow`锛氬巻鍙叉煡璇㈢獥鍙ｏ紝瀛楁涓?`UsageWindow` 鍚屽悕锛屽彲澶嶇敤 `Main._query_usage_for_group()`銆?
### 妯″潡绾у伐鍏峰嚱鏁?
- `_history_ok()` / `_history_error()`锛氬巻鍙?API 鍝嶅簲銆?- `_normalize_history_group_id()`锛氭爣鍑嗗寲缇ゅ彿銆?- `_format_history_tokens()`锛氭牸寮忓寲 token锛屾敮鎸佹寚瀹?`K` / `M` 灏忔暟浣嶆暟銆?- `_local_timezone()` / `_now_utc()`锛氭椂闂村伐鍏枫€?- `_parse_datetime()` / `_iso_utc()` / `_hour_start()`锛歎TC 灏忔椂妗惰鑼冨寲銆?- `_month_key()` / `_hour_label()` / `_hour_range_label()` / `_day_range_label()`锛氬浘琛ㄦ爣绛炬牸寮忓寲銆?
### Mixin 鍑芥暟

- `_resolve_history_stats_path()`锛氫笌澶囨敞鏂囦欢鍚岀洰褰曞瓨鏀惧巻鍙叉枃浠躲€?- `_load_history_stats()` / `_save_history_stats()`锛氳鍐欏巻鍙?JSON銆?- `_empty_history_stats()`锛氱敓鎴愮┖缁撴瀯銆?- `_sanitize_history_stats()`锛氭竻娲楀巻鍙叉枃浠讹紝绉婚櫎闈炴硶妗讹紝閲嶇畻 `total_tokens`銆?- `_ensure_history_tracking_for_current_groups(data=None)`锛?  - 鎵弿褰撳墠 `limited_groups`銆?  - 鏂扮兢鍙峰啓鍏?`tracked_since=now`銆?  - 涓嶅垹闄ゆ棫缇ゅ彿锛屽洜姝よ绉婚櫎鐨勭兢浠嶄細缁х画杩借釜銆?- `_history_background_sync_loop()`锛氭彃浠跺惎鐢ㄥ悗姣忓皬鏃跺己鍒跺悓姝ヤ竴娆″巻鍙茬粺璁°€?- `_start_history_background_sync()`锛氬湪 `initialize()` 涓垱寤哄悗鍙板悓姝ヤ换鍔°€?- `_stop_history_background_sync()`锛氬湪 `terminate()` 涓彇娑堝悗鍙板悓姝ヤ换鍔°€?- `_maybe_sync_history_stats(force=False)`锛?  - 浣跨敤 `_history_sync_lock` 涓茶鍖栧巻鍙插悓姝ャ€?  - 闈炲己鍒惰皟鐢ㄥ彈 5 鍒嗛挓鑺傛祦淇濇姢锛涜妭娴佹湡鍐呬笖缇ゅ垪琛ㄦ湭鍙樺寲鏃惰繑鍥炲唴瀛樼紦瀛橈紝閬垮厤閲嶅璇诲啓鏂囦欢銆?  - 寮哄埗璋冪敤鐢ㄤ簬鎵撳紑鍘嗗彶寮圭獥鍜屼繚瀛橀厤缃€?  - 閬嶅巻鎵€鏈夊凡杩借釜缇わ紝璋冪敤 `_sync_history_group()`銆?- `_sync_history_stats_locked(force)`锛氭寔鏈夐攣鍚庣殑瀹為檯鍚屾娴佺▼銆?- `_sync_history_group(group_id, group_data, now)`锛?  - 鏌ヨ鑼冨洿涓?`last_synced_at - 2h` 鍒板綋鍓嶆椂鍒伙紱棣栨鍚屾浠?`tracked_since` 寮€濮嬨€?  - 鏌ヨ璧风偣鎸夊皬鏃跺榻愶紝棣栦釜杩借釜灏忔椂淇濈暀浠庡姞鍏ユ椂鍒诲紑濮嬬殑閮ㄥ垎灏忔椂銆?  - 鍒犻櫎琚煡璇㈢獥鍙ｅ唴鏃ф《锛屽啀鍐欏叆 AstrBot `ProviderStat` 璁＄畻鍑虹殑鏂版《銆?  - 浣跨敤鈥滃皬鏃剁粷瀵瑰€艰鐩栤€濊€屼笉鏄閲忕疮鍔狅紝閬垮厤椤甸潰鍒锋柊銆侀厤缃彉鏇存垨 `refresh_time` 淇敼瀵艰嚧閲嶅缁熻銆?- `api_get_history()`锛?  - 鏌ヨ鍙傛暟锛歚group_id`銆乣range`銆乣limit`銆?  - 寮哄埗鍚屾鍘嗗彶缁熻銆?  - 璋冪敤 `_build_usage_payload()` 鑾峰彇褰撳墠闄愭祦缇や笅鎷夎彍鍗曘€佹瘡鏃ョ敤閲忓拰鐘舵€佸渾鐐广€?  - 鏈€夋嫨缇よ亰鏃惰繑鍥炲巻鍙叉€婚噺 Top N銆?  - 閫夋嫨缇よ亰鏃舵寜鏃堕棿鑼冨洿杩斿洖瓒嬪娍鏌辩姸鍥俱€?  - 閫夋嫨缇よ亰鏃堕澶栬繑鍥?`range_total_tokens` 鍜?`range_total_display`锛岀敤浜庢樉绀哄綋鍓嶆椂闂磋法搴﹀唴璇ョ兢 token 鐢ㄩ噺鎬诲拰銆?- `_history_dropdown_groups()`锛氱敓鎴愬綋鍓?`limited_groups` 涓嬫媺鑿滃崟鏁版嵁锛岀姸鎬佷负 `normal`銆乣fallback`銆乣stopped`銆?- `_history_top_bars()`锛氭寜 `total_tokens` 闄嶅簭杩斿洖 Top N銆?- `_history_group_bars()`锛氭寜 `24h`銆乣7d`銆乣30d`銆乣all` 鍒嗘淳妗惰仛鍚堛€?- `_history_recent_hour_bars()`锛氳繎 24 灏忔椂鎸夊皬鏃惰繑鍥炲師濮嬫《锛涢〉闈㈡牴鎹搴﹀姩鎬佽仛鍚堜负 2銆? 鎴?4 灏忔椂妗躲€?- `_history_recent_day_bars()`锛氳繎 7 澶╂寜鏃ュ睍绀猴紱杩戜竴涓湀鎸?3 澶╄仛鍚堬紝骞朵娇鐢ㄨ嫳鏂囨湀浠界缉鍐欐爣绛俱€?- `_history_all_bars()`锛氬巻鍙叉€诲拰鐭法搴︽寜鏃ュ睍绀猴紝瓒呰繃 31 澶╂寜鏈堝睍绀恒€?- `_history_hour_values()` / `_history_iter_hours()`锛氶亶鍘嗚鑼冨寲灏忔椂妗躲€?- `_history_bar()`锛氱粺涓€鏌辩姸鍥炬暟鎹粨鏋勶紝鍙负杩?24 灏忔椂鍜岃繎涓€涓湀鏌遍《鏁板€兼寚瀹?1 浣嶅皬鏁版樉绀恒€?
## backend/user_stats.py

`UserStatsMixin` 鐙珛缁存姢杩?48 灏忔椂缇ゅ唴鐢ㄦ埛 token 鐢ㄩ噺缁熻锛岀敤浜?Plugin Page 鐨勨€滀粖鏃ョ敤鎴?token 鐢ㄩ噺缁熻鈥濆脊绐椼€?
### 甯搁噺涓庢暟鎹粨鏋?
- `USER_USAGE_STATS_FILE`锛氭寔涔呭寲鏂囦欢鍚?`user_usage_48h.json`銆?- `USER_USAGE_RETENTION`锛氱敤鎴峰皬鏃舵《淇濈暀鏃堕棿锛屽綋鍓?48 灏忔椂銆?- `USER_USAGE_REQUEST_RETENTION`锛氱敤鎴疯姹傚綊鍥犲揩鐓т繚鐣欐椂闂达紝褰撳墠 48 灏忔椂銆?- `USER_USAGE_REQUEST_LOOKBACK`锛氭妸 ProviderStat 璁板綍鍥為厤鍒版渶杩戜竴娆＄敤鎴疯姹傜殑鏈€澶у洖鐪嬫椂闂达紝褰撳墠 10 鍒嗛挓銆?- `USER_USAGE_REQUEST_FUTURE_TOLERANCE`锛氬厑璁镐簨浠惰褰曟椂闂寸暐鏅氫簬 provider `start_time` 鐨勫宸紝褰撳墠 5 绉掋€?- `USER_USAGE_SYNC_OVERLAP`锛氬悓姝ュ洖鐪嬬獥鍙ｏ紝褰撳墠 2 灏忔椂锛岀敤浜庝慨姝?AstrBot 寤惰繜鍐欏叆銆?- `USER_USAGE_SYNC_MIN_INTERVAL`锛氶潪寮哄埗鍚屾鏈€鐭棿闅旓紝褰撳墠 2 鍒嗛挓銆?- `USER_USAGE_BACKGROUND_SYNC_INTERVAL`锛氬悗鍙板悓姝ラ棿闅旓紝褰撳墠 3600 绉掋€?- `USER_USAGE_DEFAULT_TOP_LIMIT`锛氶粯璁ゅ睍绀?Top N锛屽綋鍓?10銆?- `UserUsageWindow`锛氫粖鏃ョ敤鎴风粺璁℃煡璇㈢獥鍙ｏ紝鎸?`refresh_time` 鐢熸垚褰撳墠 24 灏忔椂缁熻鍛ㄦ湡銆?
### 妯″潡绾у伐鍏峰嚱鏁?
- `_normalize_user_group_id()` / `_sanitize_user_id()`锛氭爣鍑嗗寲缇ゅ彿鍜岀敤鎴峰彿銆?- `_sanitize_user_name()`锛氭竻娲?QQ 鏄电О鎴栫兢鍚嶇墖銆?- `_format_user_tokens()`锛氭牸寮忓寲 token 鏁颁负 `K` / `M`銆?- `_build_user_usage_window()`锛氭寜 `refresh_time` 鐢熸垚褰撳墠鍒锋柊鍛ㄦ湡绐楀彛銆?- `_extract_user_id_from_umo(umo, group_id)`锛氫粠 AstrBot `ProviderStat.umo` 涓В鏋愮兢鍐呯敤鎴?ID锛涙敮鎸佸父瑙?`鐢ㄦ埛ID_缇ゅ彿`銆乣缇ゅ彿_鐢ㄦ埛ID` 浠ュ強甯﹀啋鍙风殑骞冲彴浼氳瘽鏍煎紡銆?- `_timestamp_to_utc()`锛氬皢 AstrBot provider 缁熻涓殑 Unix 绉掔骇 `start_time` 杞负 UTC 鏃堕棿锛岀敤浜庤姹傚綊鍥犮€?
### Mixin 鍑芥暟

- `_resolve_user_stats_path()`锛氫笌澶囨敞鏂囦欢鍚岀洰褰曞瓨鏀?`user_usage_48h.json`銆?- `_load_user_stats()` / `_save_user_stats()`锛氳鍐欒繎 48 灏忔椂鐢ㄦ埛缁熻 JSON銆?- `_sanitize_user_stats()`锛氭竻娲楀巻鍙叉枃浠讹紝涓㈠純瓒呰繃 48 灏忔椂鐨勫皬鏃舵《鍜岃姹傚綊鍥犲揩鐓с€?- `_ensure_user_tracking_for_current_groups(data=None)`锛氫负褰撳墠 `limited_groups` 寤虹珛鐢ㄦ埛缁熻缇ょ粨鏋勩€?- `_start_user_background_sync()` / `_stop_user_background_sync()`锛氬湪鎻掍欢鍚仠鏃剁鐞嗙敤鎴风粺璁″悗鍙颁换鍔°€?- `_maybe_sync_user_stats(force=False, group_id=None)`锛氬甫閿佸悓姝ョ敤鎴风粺璁★紱闈炲己鍒跺悓姝ユ寜 2 鍒嗛挓鑺傛祦锛屾墦寮€鐢ㄦ埛缁熻寮圭獥鏃跺彲鎸夌兢寮哄埗鍚屾銆?- `_sync_user_group(group_id, group_data, now)`锛氭煡璇?AstrBot `ProviderStat`锛岀粨鍚堣姹傚綊鍥犻槦鍒楄鐩栨渶杩戝悓姝ョ獥鍙ｅ唴鐨勭敤鎴峰皬鏃舵《銆?- `_assign_user_usage_records()` / `_match_user_usage_request()`锛氬皢 `umo` 鍙兘瀹氫綅鍒扮兢浼氳瘽鐨?ProviderStat 鏄庣粏鎸夊悓 `umo`銆佸悓浼氳瘽 ID锛堝鏈夛級鍜屾渶杩戣姹傛椂闂村洖閰嶅埌缇ゅ唴鐢ㄦ埛 LLM 璇锋眰锛涚兢鑱婂叡鐢?`conversation_id` 鏃朵笉浼氬彧鎸変細璇?ID 鍚堝苟銆?- `_merge_user_hours()`锛氬悎骞跺彲鐩存帴浠?`umo` 瑙ｆ瀽鍑虹殑灏忔椂妗跺拰璇锋眰褰掑洜寰楀埌鐨勫皬鏃舵《銆?- `_prune_user_group_data()`锛氬垹闄よ秴杩?48 灏忔椂鎴栧嵆灏嗚閲嶆柊鏌ヨ绐楀彛瑕嗙洊鐨勬棫妗躲€?- `_prune_user_usage_requests()`锛氭竻鐞嗚秴杩?48 灏忔椂鎴栭潪娉曠殑璇锋眰褰掑洜蹇収銆?- `_query_hourly_user_usage_for_group()`锛氭煡璇㈡煇缇ゅ湪鏃堕棿娈靛唴鐨?ProviderStat锛岃繑鍥炲彲鐩存帴鎸夌敤鎴疯仛鍚堢殑灏忔椂妗跺拰闇€瑕佸綊鍥犵殑璁板綍鏄庣粏銆?- `_query_user_totals_for_group()`锛氭煡璇㈠綋鍓嶅埛鏂板懆鏈熷唴鏌愮兢鎸夌敤鎴疯仛鍚堢殑 token 鎬婚噺銆?- `_stored_user_totals_for_group()` / `_combine_user_totals()`锛氬皢瀹炴椂 ProviderStat 鐩存帴鑱氬悎缁撴灉鍜屾寔涔呭寲褰掑洜灏忔椂妗跺悎骞朵负褰撳墠绐楀彛鎺掕鏁版嵁銆?- `_remember_user_usage_event(event, conversation_id=None)`锛氬湪 LLM 绛夊緟閽╁瓙鍜?LLM 璇锋眰閽╁瓙閲屽敖閲忎粠娑堟伅浜嬩欢缂撳瓨鐢ㄦ埛 QQ 鏄电О锛屽苟璁板綍璇锋眰褰掑洜蹇収锛汱LM 璇锋眰闃舵浼氳ˉ鍏?`conversation_id`銆?- `_event_user_id()` / `_event_user_name()`锛氬吋瀹逛笉鍚?AstrBot 浜嬩欢瀛楁璇诲彇鐢ㄦ埛鍙蜂笌鏄电О銆?- `api_get_user_usage()`锛氳繑鍥炵兢鑱婁笅鎷夎彍鍗曘€佸綋鍓嶇獥鍙ｃ€佸悓姝ユ椂闂达紝浠ュ強閫変腑缇ょ殑鐢ㄦ埛 Top N 妯悜鏌辩姸鍥炬暟鎹€?- `_user_usage_dropdown_groups()`锛氬鐢ㄥ綋鍓嶇敤閲忕姸鎬佺敓鎴愮敤鎴风粺璁″脊绐楃殑缇よ亰涓嬫媺鑿滃崟銆?- `_user_usage_rows()`锛氬皢鐢ㄦ埛 token 鎬婚噺杞负鍓嶇鎺掕琛岋紝杩囨护 0 鐢ㄩ噺鐢ㄦ埛锛屾樀绉扮己澶辨椂鏄剧ず QQ 鍙凤紱鍚敤鍗曠敤鎴蜂笂闄愭椂闄勫甫 `over_user_limit` 渚涢〉闈㈡爣绾€?
## pages/dashboard/index.html

### 椤甸潰缁撴瀯

- `.app` / `.layout`锛氶〉闈㈡牴瀹瑰櫒鍜屼袱鏍忓竷灞€銆?- 宸︿晶 `.panel`锛氱敤閲忕粺璁°€?  - `#windowText`锛氬綋鍓嶇獥鍙ｆ椂闂淬€?  - `#refreshBtn`锛氬埛鏂板綋鍓嶇獥鍙ｇ敤閲忋€?  - `#usageList`锛氱兢鐢ㄩ噺鍒楄〃銆?  - `.group-id`锛歈Q 缇ゅ彿銆?  - `.group-remark`锛氱伆鑹叉嫭鍙峰娉ㄣ€?  - `.icon-button`锛氱紪杈戝娉ㄩ搮绗旀寜閽€?  - 榻胯疆 `.icon-button`锛氭墦寮€鈥滅兢鑱婁釜鎬у寲閰嶇疆鈥濆脊绐楋紝涓哄崟涓兢鑱婁繚瀛樻瘡鏃ョ敤閲忎笂闄愩€?  - `.fallback-tag`锛氶粍鑹测€滃洖閫€妯″瀷鈥濇爣绛俱€?  - `.stop-tag`锛氱孩鑹测€滃仠姝㈠搷搴斺€濇爣绛俱€?  - `.usage-value.fallback` / `.usage-value.stopped`锛氶粍鑹?绾㈣壊鐢ㄩ噺鍊笺€?  - `.progress-fill.fallback` / `.progress-fill.stopped`锛氶粍鑹?绾㈣壊杩涘害鏉°€?- 鍙充晶 `.panel`锛氭彃浠跺姛鑳姐€?  - `#openConfigBtn`锛氭墦寮€鎻掍欢鍩虹閰嶇疆锛屼綅浜庡姛鑳芥寜閽尯鏈€涓婃柟銆?  - `#openStrategyBtn`锛氭墦寮€鈥滅敤閲忚秴闄愮瓥鐣ラ厤缃€濄€?  - `#openHistoryBtn`锛氭墦寮€鈥滃巻鍙?token 鐢ㄩ噺缁熻鈥濄€?  - `#openUserUsageBtn`锛氭墦寮€鈥滀粖鏃ョ敤鎴?token 鐢ㄩ噺缁熻鈥濄€?  - `#statusLine`锛氭彃浠跺惎鐢ㄧ姸鎬併€?
### 寮圭獥鍏冪礌

- `#overlay`锛氭彃浠跺熀纭€閰嶇疆寮圭獥銆?  - `#configForm`锛氬姩鎬侀厤缃〃鍗曪紝涓嶆覆鏌?`over_limit_policy`銆?  - `#saveBtn` / `#cancelBtn` / `#toast`锛氫繚瀛樸€佸彇娑堝拰鐘舵€併€?- `#strategyOverlay`锛氳秴闄愮瓥鐣ュ脊绐椼€?  - `#strategyForm`锛氭覆鏌?`over_limit_policy`銆?  - 濮嬬粓鏄剧ず鈥滆秴闄愬悗涓嶅啀鍝嶅簲鍞ら啋璇嶁€濆紑鍏炽€?  - 浠呭綋 `action=fallback_provider` 鏃舵樉绀哄洖閫€渚涘簲鍟嗗拰鍥為€€涓婇檺銆?- `#historyOverlay`锛氬巻鍙茬粺璁″脊绐椼€?  - `#groupSelect` / `#groupSelectTrigger` / `#groupSelectMenu`锛氳嚜缁樼兢鑱婁笅鎷夎彍鍗曘€?  - `#rangeSelect` / `#rangeSelectTrigger` / `#rangeSelectMenu`锛氳嚜缁樻椂闂磋法搴︿笅鎷夎彍鍗曘€?  - `#historyRangeTotal`锛氬彸渚ф€婚噺鍗犱綅锛涢€変腑缇よ亰鍚庢樉绀鸿缇ゅ綋鍓嶆椂闂磋法搴﹀唴 token 鐢ㄩ噺鎬诲拰銆?  - `#historyYAxis`锛氬姩鎬佺旱杞存爣绛俱€?  - `#historyChart`锛氭煴鐘跺浘瀹瑰櫒銆?  - `#historyXAxis`锛氬姩鎬佹í杞存爣绛俱€?  - `#historyFooter`锛氭渶鍚庡悓姝ユ椂闂淬€?- `#userUsageOverlay`锛氫粖鏃ョ敤鎴?token 鐢ㄩ噺缁熻寮圭獥銆?  - `#userGroupSelect` / `#userGroupSelectTrigger` / `#userGroupSelectMenu`锛氳嚜缁樼兢鑱婁笅鎷夎彍鍗曪紝琛屼负涓庡巻鍙茬粺璁＄兢鑱婁笅鎷変竴鑷淬€?  - `#refreshUserUsageBtn`锛氬埛鏂版寜閽紝淇濇寔褰撳墠缇よ亰閫夋嫨骞堕噸鏂拌姹備粖鏃ョ敤鎴?token 鐢ㄩ噺銆?  - `#userUsageWindow`锛氬綋鍓嶅埛鏂板懆鏈熺獥鍙ｆ枃鏈€?  - `#userUsageChart`锛氭í鍚戞煴鐘跺浘瀹瑰櫒锛屽睍绀洪€変腑缇よ亰鍐?Top N 鐢ㄦ埛 token 鐢ㄩ噺锛涜秴鍑?`user_daily_token_limit` 鐨勭敤鎴锋煴瀛愬拰鏁板€兼樉绀轰负绾㈣壊銆?  - `#userUsageFooter`锛氭渶鍚庡悓姝ユ椂闂淬€?- `#remarkOverlay`锛氬娉ㄧ紪杈戝脊绐椼€?  - `#remarkTarget`銆乣#remarkInput`銆乣#saveRemarkBtn`銆乣#cancelRemarkBtn`銆乣#remarkToast`銆?- `#groupSettingsOverlay`锛氱兢鑱婁釜鎬у寲閰嶇疆寮圭獥銆?  - `#groupSettingsTarget`锛氬綋鍓嶉厤缃洰鏍囩兢鍙枫€?  - `#groupLimitInput`锛氳缇よ亰姣忔棩 token 涓婇檺杈撳叆妗嗭紝榛樿鏄剧ず褰撳墠鏈夋晥涓婇檺銆?  - `#groupSettingsHint`锛氳鏄庡綋鍓嶅€兼潵鑷叏灞€涓婇檺杩樻槸涓€у寲涓婇檺銆?  - `#saveGroupSettingsBtn` / `#cancelGroupSettingsBtn` / `#groupSettingsToast`锛氫繚瀛樸€佸彇娑堝拰鐘舵€佹彁绀恒€?- `#historyTooltip`锛氬巻鍙叉煴鐘跺浘鐐瑰嚮鍚庢樉绀虹殑姘旀场 tag銆?  - `#historyTooltipLabel`锛氭煴瀛愭í鍧愭爣鍐呭銆?  - `#historyTooltipValue`锛氭煴瀛?token 鏁板€肩粺璁￠噺锛岀矖浣撴樉绀恒€?
### 鍓嶇鍑芥暟

- 閫氱敤锛歚setToast()`銆乣setStrategyToast()`銆乣setRemarkToast()`銆乣formatDate()`銆乣normalizeTextareaText()`銆乣normalizeListText()`銆乣parseListText()`銆?- 閰嶇疆娓叉煋锛歚renderConfigControl()`銆乣appendConfigRow()`銆乣renderConfigForm()`銆乣renderStrategyForm()`銆?- 褰撳墠鐢ㄩ噺锛歚renderUsage()`銆乣loadUsage()`銆?- 缇よ亰涓€у寲閰嶇疆锛歚openGroupSettings()`銆乣closeGroupSettings()`銆乣saveGroupSettings()`銆?- 鍘嗗彶缁熻锛?  - `historyRangeLabel()`锛氭椂闂磋法搴︽爣绛俱€?  - `closeCustomSelects()` / `toggleCustomSelect()`锛氳嚜缁樹笅鎷夎彍鍗曞紑鍚堛€?  - `statusDotClass()`锛氱豢/榛?绾㈢姸鎬佸渾鐐广€?  - `selectedHistoryGroup()`锛氬綋鍓嶉€変腑缇ゃ€?  - `reloadHistory()` / `loadHistory()`锛氳姹?`history` API銆?  - `renderHistoryControls()`锛氭覆鏌撲袱涓笅鎷夎彍鍗曘€?  - `renderHistoryTotal()`锛氭覆鏌撳巻鍙插脊绐楀彸渚х殑褰撳墠鏃堕棿璺ㄥ害鐢ㄩ噺鎬诲拰锛涙湭閫夌兢鑱婃椂淇濇寔涓虹┖銆?  - `formatHistoryTokenNumber()`锛氭寜鎸囧畾灏忔暟浣嶆牸寮忓寲鍘嗗彶鍥炬煴椤舵暟鍊笺€?  - `aggregateHistoryBars()`锛氬墠绔寜鎸囧畾灏忔椂鏁拌仛鍚堣繎 24 灏忔椂鍘熷灏忔椂妗躲€?  - `resolveHistoryBarsForViewport()`锛氭牴鎹浘琛ㄥ彲鐢ㄥ搴﹂€夋嫨 2銆? 鎴?4 灏忔椂鑱氬悎绮掑害銆?  - `handleHistoryResize()`锛氬巻鍙插脊绐楁墦寮€鏃堕殢绐楀彛瀹藉害鍙樺寲閲嶆柊璁＄畻 24 灏忔椂鑱氬悎绮掑害銆?  - `showHistoryTooltip()` / `hideHistoryTooltip()`锛氱偣鍑绘煴鐘跺浘鏌卞瓙鏃讹紝鍦ㄩ紶鏍囦綅缃樉绀?闅愯棌瀹屾暣鍐呭姘旀场銆?  - `renderHistoryChart()`锛氭覆鏌撳姩鎬佽酱銆佹暟鍊兼爣绛惧拰鏌辩姸鍥惧姩鐢汇€?  - `formatTokenNumber()`锛氬墠绔酱鏍囩鏍煎紡鍖栥€?- 浠婃棩鐢ㄦ埛缁熻锛?  - `selectedUserUsageGroup()`锛氳鍙栧綋鍓嶉€変腑鐨勭敤鎴风粺璁＄兢鑱娿€?  - `renderUserUsageControls()`锛氭覆鏌撶兢鑱婁笅鎷夎彍鍗曘€?  - `renderUserUsageWindow()`锛氭覆鏌撳綋鍓嶅埛鏂板懆鏈熸椂闂寸獥鍙ｃ€?  - `renderUserUsageChart()`锛氭覆鏌撴í鍚戞煴鐘跺浘锛涙湭閫夋嫨缇よ亰鏃舵樉绀烘搷浣滄彁绀恒€?  - `loadUserUsage()` / `reloadUserUsage()`锛氳姹?`user-usage` API銆?- 寮圭獥锛歚openConfig()`銆乣closeConfig()`銆乣openStrategy()`銆乣closeStrategy()`銆乣openHistory()`銆乣closeHistory()`銆乣openUserUsage()`銆乣closeUserUsage()`銆乣openRemark()`銆乣closeRemark()`銆乣openGroupSettings()`銆乣closeGroupSettings()`銆?- 淇濆瓨锛歚saveConfig()`銆乣saveStrategy()`銆乣saveRemark()`銆乣saveGroupSettings()`銆?- `init()`锛氱瓑寰?bridge ready 鍚庡姞杞介厤缃拰褰撳墠鐢ㄩ噺銆?
### 椤甸潰浜や簰瑙勫垯

- 鎵€鏈夋寜閽兘鏈?`:hover` 涓?`:active` 棰滆壊/浣嶇Щ鍙嶉銆?- 澶囨敞鏄剧ず鍦ㄧ兢鍙峰彸渚э紝鏍煎紡涓?`锛堝娉級`锛涢搮绗斿浘鏍囪窡鍦ㄧ兢鍙锋垨澶囨敞鍙充晶銆?- 鐢ㄩ噺缁熻姣忎釜缇よ亰鐨勯搮绗旀寜閽悗鏂规樉绀洪娇杞寜閽紱鐐瑰嚮鍚庡彲淇濆瓨璇ョ兢鑱婁釜鎬у寲姣忔棩鐢ㄩ噺涓婇檺銆?- 缇よ亰涓€у寲涓婇檺淇濆瓨鍚庣珛鍗冲奖鍝嶅綋鍓嶇敤閲忚繘搴︽潯銆佸洖閫€/鍋滄鐘舵€佸拰 LLM 璇锋眰闄愭祦鍒ゆ柇锛涘叾浠栫兢鑱婄户缁娇鐢ㄥ叏灞€涓婇檺銆?- 寮€鍚€滆秴闄愬悗涓嶅啀鍝嶅簲鍞ら啋璇嶁€濆悗锛岀兢鑱婄敤閲忚揪鍒拌缇ゆ湁鏁堝熀纭€姣忔棩涓婇檺鏃讹紝鍞ら啋璇嶈Е鍙戜笉鍐嶈繘鍏?LLM 娴佺▼锛沗@bot` 瑙﹀彂浠嶄細缁х画鎵ц鍥為€€妯″瀷鎴栧仠姝㈠搷搴旇鍒欍€?- 閰嶇疆 textarea 浼氭妸淇濆瓨鍊间腑鐨勬樉寮?`\n` 娓叉煋涓虹湡瀹炴崲琛屻€?- 鍘嗗彶缁熻缇よ亰涓嬫媺鑿滃崟涓紝鐘舵€佸渾鐐规斁鍦ㄦ瘡鏃?token 鐢ㄩ噺鏁板瓧鍓嶆柟锛氱豢鑹叉甯搞€侀粍鑹插洖閫€銆佺孩鑹插仠姝㈠搷搴斻€?- 鏈€夋嫨缇よ亰鏃讹紝鍘嗗彶鍥惧睍绀哄巻鍙叉€?token Top N 缇よ亰銆?- 閫夋嫨缇よ亰鍚庯紝鎸?`杩?24 灏忔椂`銆乣杩?7 澶ー銆乣杩戜竴涓湀`銆乣鍘嗗彶鎬诲拰` 灞曠ず瓒嬪娍銆?- 姣忔閲嶆柊鎵撳紑鍘嗗彶缁熻寮圭獥鏃讹紝缇よ亰涓嬫媺鑿滃崟鎭㈠涓衡€滈€夋嫨缇よ亰 ...鈥濓紝鏃堕棿璺ㄥ害鎭㈠涓衡€滆繎 24 灏忔椂鈥濓紝鍥捐〃鎭㈠鍘嗗彶鎬?token Top N銆?- 杩?24 灏忔椂鏌辩姸鍥剧敱椤甸潰鎸夊搴﹀姩鎬侀€夋嫨鑱氬悎绮掑害锛氫紭鍏?2 灏忔椂 12 鏍规煴锛涚┖闂翠笉瓒虫椂闄嶄负 3 灏忔椂 8 鏍规煴锛涗粛涓嶈冻鏃堕檷涓?4 灏忔椂 6 鏍规煴銆?- 杩戜竴涓湀鏌辩姸鍥炬寜 3 澶╄仛鍚堬紝妯潗鏍囨湀浠戒娇鐢ㄨ嫳鏂囩缉鍐欙紝渚嬪 `Jun 06-08`锛涜繎 24 灏忔椂鍜岃繎涓€涓湀鏌遍《鏁板€间繚鐣?1 浣嶅皬鏁帮紝鍏朵粬鍙ｅ緞淇濇寔鍘熸湁灏忔暟浣嶃€?- 閫変腑缇よ亰鍚庯紝涓や釜涓嬫媺鑿滃崟鍙充晶鏄剧ず鎵€閫夋椂闂磋法搴﹀唴璇ョ兢 token 鐢ㄩ噺鎬诲拰銆?- 鐐瑰嚮鍘嗗彶鏌辩姸鍥句腑鐨勪换涓€鏌卞瓙浼氭樉绀烘皵娉?tag锛岀涓€琛屼负妯潗鏍囷紝绗簩琛屼负 token 鐢ㄩ噺鍊硷紱鏂囨湰寮哄埗瀹屾暣鏄剧ず锛屽搴﹂殢鏈€闀挎枃鏈鑷€傚簲銆?- 鏌辩姸鍥惧垏鎹㈡暟鎹椂閫氳繃楂樺害杩囨浮鍔ㄧ敾骞虫粦鍙樺寲锛涙í绾靛潗鏍囧拰鏌遍《鏁板€肩敱鏁版嵁鍔ㄦ€佺敓鎴愩€?- 浠婃棩鐢ㄦ埛 token 鐢ㄩ噺缁熻寮圭獥榛樿鏄剧ず鈥滈€夋嫨缇よ亰 ...鈥濆拰鎿嶄綔鎻愮ず锛涢€変腑缇よ亰鍚庡睍绀哄綋鍓嶅埛鏂板懆鏈熷唴 token 娑堣€楁渶楂樼殑 Top N 鐢ㄦ埛銆?- 浠婃棩鐢ㄦ埛缁熻浣跨敤妯悜鏌辩姸鍥撅紝绾靛悜鏍囩涓?QQ 鏄电О锛涙棤娉曡幏鍙栨樀绉版椂鏄剧ず QQ 鍙凤紱娑堣€楅噺涓?0 鐨勭敤鎴蜂笉鏄剧ず銆傛煴瀛愭寜鏈€闀跨旱鍧愭爣鏂囧瓧缁熶竴纭畾宸︿晶璧风偣锛岀揣璐存爣绛惧彸渚у榻愩€傚惎鐢ㄥ崟鐢ㄦ埛涓婇檺涓旂敤鎴风敤閲忚揪鍒颁笂闄愭椂锛岃鐢ㄦ埛鏌卞瓙鍜?token 鏁板€间负绾㈣壊銆?- 浠婃棩鐢ㄦ埛缁熻寮圭獥姣忔鎵撳紑銆侀€夋嫨缇よ亰鎴栫偣鍑烩€滃埛鏂扳€濋兘浼氶噸鏂拌姹傚悗绔紱鍚庣浼氬己鍒跺悓姝ラ€変腑缇よ亰鐨?ProviderStat 鍜岃姹傚綊鍥犳暟鎹€?
## 閰嶇疆涓庣粺璁″悓姝ラ€昏緫

- 褰撳墠绐楀彛闄愭祦缁熻浣跨敤 `refresh_time` 鍒囧垎 24 灏忔椂绐楀彛銆?- 缇よ亰涓€у寲涓婇檺鍙鐩栧熀纭€ `daily_token_limit`锛涘洖閫€妯″瀷棰濆涓婇檺浠嶆潵鑷叏灞€ `over_limit_policy.fallback_token_limit`锛涘敜閱掕瘝闃绘柇闃堝€间娇鐢ㄨ缇ゆ渶缁堟湁鏁堝熀纭€涓婇檺銆?- 鍗曠敤鎴蜂笂闄?`user_daily_token_limit` 鍙寜鈥滄煇缇ゅ唴鏌愮敤鎴封€濈粺璁★紝涓嶈法缇ゅ悎骞讹紱杈惧埌涓婇檺鍚庨潤榛橀樆鏂鐢ㄦ埛鍙戣捣鐨?LLM 璇锋眰锛屼笉浣跨敤鍥為€€妯″瀷锛屼篃涓嶅彂閫佺兢鑱婃彁绀恒€?- 鍘嗗彶缁熻涓嶄緷璧?`refresh_time`锛涘畠浠ョ兢鍙烽娆″姞鍏?`limited_groups` 鐨勬椂闂翠负璧风偣锛屾寜灏忔椂妗舵寔涔呭寲銆?- 鍘嗗彶鍚屾鍩轰簬 AstrBot 鍘熺敓 `ProviderStat`锛屼繚瀛樼殑鏄瘡灏忔椂缁濆妗跺€硷紝涓嶆槸绱姞 delta銆?- 浠婃棩鐢ㄦ埛缁熻涔熷熀浜?AstrBot 鍘熺敓 `ProviderStat`锛涙寔涔呭寲鏂囦欢淇濈暀杩?48 灏忔椂缇ゅ唴鐢ㄦ埛灏忔椂妗躲€佽姹傚綊鍥犲揩鐓у拰鏄电О缂撳瓨锛屼笉璺ㄧ兢鍚堝苟鍚屼竴涓敤鎴枫€?- 閰嶇疆淇濆瓨浼氬己鍒跺悓姝ヤ竴娆″巻鍙茬粺璁★紱椤甸潰 `usage` 鍜?LLM 绛夊緟閽╁瓙浼氳妭娴佸悓姝ャ€?- 閰嶇疆淇濆瓨浼氬己鍒跺悓姝ヤ竴娆′粖鏃ョ敤鎴风粺璁★紱椤甸潰 `usage` 鍜?LLM 绛夊緟閽╁瓙浼氳妭娴佸悓姝ワ紝鎵撳紑鐢ㄦ埛缁熻寮圭獥鏃朵細鎸夐€変腑缇ゅ己鍒跺悓姝ャ€?- 鏃х兢鍙蜂笉浼氬洜涓轰粠 `limited_groups` 绉婚櫎鑰屼粠 `history_usage.json` 鍒犻櫎锛屽洜姝ゅ啀娆″姞鍏ユ椂鍘嗗彶鎬婚噺鍜岃秼鍔垮彲浠ョ户缁樉绀恒€?

## v0.6.2 补充结构说明

- `metadata.yaml` 在该版本更新为 `0.6.2`。
- `group_limits.json` 在 v0.6.2 起保存“群聊个性化配置”结构，兼容旧格式：
  - 旧格式：`{"123456": 1000000}`，表示该群覆盖全局 `daily_token_limit`。
  - 新格式：`{"123456": {"daily_token_limit": 1000000, "only_at_bot_llm": true}}`。
  - `daily_token_limit` 缺省时表示该群继续使用全局每日上限。
  - `only_at_bot_llm=true` 表示该群无论是否超限，都只允许 `@bot` 触发 LLM 回复；唤醒词触发会被静默阻断。
- `main.py` 新增常量：
  - `GROUP_SETTING_DAILY_LIMIT = "daily_token_limit"`。
  - `GROUP_SETTING_ONLY_AT_BOT = "only_at_bot_llm"`。
- `main.py` 新增或扩展函数：
  - `_load_group_settings()` / `_save_group_settings()`：读写新结构，并兼容旧的群号到整数上限映射。
  - `_load_group_limits()` / `_save_group_limits()`：保留兼容接口，只暴露群号到每日上限的映射；保存上限时保留已有 `only_at_bot_llm`。
  - `_group_only_at_bot_llm(group_id, group_settings=None)`：读取某群是否启用“仅通过 @bot 触发 LLM 回复”。
  - `_should_block_group_only_at_bot_invocation(event)`：当插件启用、事件来自受限 QQ 群、该群启用 `only_at_bot_llm`、且本次为非 `@bot` 的唤醒词触发时返回群号。
  - `_block_group_only_at_bot_invocation_if_needed(event, stage)`：执行静默 `event.stop_event()` 并写 AstrBot 日志。
- `on_waiting_llm_request()` 和 `on_llm_request()` 的处理顺序：
  - 首先执行 `_block_group_only_at_bot_invocation_if_needed()`。
  - 然后执行单用户每日上限、历史/用户统计同步、群聊回退模型或停止响应规则。
  - `_is_wake_word_invocation()` 内部会先调用 `_event_has_at_bot()`，因此同一句消息包含 `@bot` 和唤醒词时不会被 `only_at_bot_llm` 阻断。
- `GET /astrbot_plugin_token_limit/group-settings` 返回字段增加：
  - `only_at_bot_llm`：当前群是否启用“仅通过 @bot 触发 LLM 回复”。
- `POST /astrbot_plugin_token_limit/group-settings` 支持字段增加：
  - `only_at_bot_llm`：布尔值，保存当前群的 token 节约策略。
  - `reset=true` 只重置 `daily_token_limit`，不会清除 `only_at_bot_llm`。
- `GET /astrbot_plugin_token_limit/usage` 的每个群聊项增加：
  - `only_at_bot_llm`：用于 Plugin Page 打开“群聊个性化配置”弹窗时先渲染缓存状态。
  - 顶层 `group_settings`：完整群聊个性化配置快照。
- `pages/dashboard/index.html` 新增页面元素：
  - `.group-settings-section`：群聊个性化配置弹窗内的分组栏目。
  - `.group-settings-section-title`：栏目标题“本群 token 节约策略”。
  - `.group-settings-checkbox`：复选框布局。
  - `#groupOnlyAtBotInput`：复选框“仅通过 @bot 触发 LLM 回复”。
- `pages/dashboard/index.html` 相关前端逻辑：
  - `state.currentSettingsInitialOnlyAtBot` 保存弹窗打开时的初始开关值。
  - `openGroupSettings()` 从 `usage` 缓存和 `group-settings` API 读取 `only_at_bot_llm`。
  - `saveGroupSettings()` 同时保存 `daily_token_limit` 与 `only_at_bot_llm`；任一字段变化都会提交。
  - `resetGroupSettings()` 仍只提交 `reset=true`，仅重置本群每日上限为全局值。

## v0.6.4 补充结构说明

- `metadata.yaml` 当前版本为 `0.6.4`。
- `group_limits.json` 的单群配置结构继续兼容旧格式，并新增可选字段：
  - `context_limit_05`：布尔值，`true` 表示该群启用“最大上下文窗口设置为额度的 0.5%”。
  - 示例：`{"123456": {"daily_token_limit": 6000000, "only_at_bot_llm": true, "context_limit_05": true}}`。
  - `daily_token_limit` 缺省时，该群上下文限制值随全局 `daily_token_limit` 实时变化；存在个性化上限时，按该群个性化上限计算。
- `main.py` 新增常量：
  - `GROUP_SETTING_CONTEXT_LIMIT_05 = "context_limit_05"`。
  - `TOKEN_LIMIT_CONTEXT_RATIO = 0.005`。
  - `TOKEN_LIMIT_CONTEXT_TRIM_RATIO = 0.8`。
  - `TOKEN_LIMIT_CONTEXT_COMPRESS_THRESHOLD = 0.82`。
  - `TOKEN_LIMIT_CONTEXT_FALLBACK_TURNS = 3`。
  - `TOKEN_LIMIT_TEMP_PROVIDER_PREFIX = "__token_limit_context__"`。
- `main.py` 新增或扩展内部 API：
  - `_group_context_limit_05(group_id, group_settings=None)`：读取某群是否启用 0.5% 上下文窗口策略。
  - `_group_context_limit_tokens(group_id, group_settings=None, group_limits=None)`：返回某群有效每日上限的 0.5%，未启用时返回 `0`。
  - `_format_context_limit_tokens(value)`：将上下文窗口限制值格式化为无空格 K/M 文本，小于 1000 token 时显示为 `1K`。
  - `_provider_id_for_context_limit(event, limit_context)`：优先尊重事件上已有的 `selected_provider`；正常区间选择 AstrBot 当前 provider，回退区间且回退 provider 有效时选择回退 provider。
  - `_apply_context_limit_provider_if_needed(event, limit_context)`：为当前请求创建 provider 浅拷贝，复制 `provider_config` 并写入临时 `max_context_tokens`，再通过 `selected_provider` 指向临时 provider。
  - `_set_temp_context_provider_limit(event, context_tokens)`：仅修改本次临时 provider 副本的 `max_context_tokens`，用于必需输入过大时避免 AstrBot 无意义压缩。
  - `_context_limit_trim_budget(tokens)`：返回上下文预裁剪预算，当前为限制值的 80%。
  - `_context_limit_compress_threshold(tokens)` / `_context_limit_for_tokens(tokens)`：按 AstrBot 默认 0.82 压缩阈值计算触发线和可容纳当前估算消息的临时窗口。
  - `_estimate_text_tokens(value)` / `_estimate_content_tokens(content)`：用轻量规则估算文本、多模态消息片段和附件描述 token 数，避免为预裁剪引入额外模型调用。
  - `_estimate_request_messages_tokens(req, history_messages)`：轻量估算系统提示、历史上下文、当前输入和附件描述的 token 数。
  - `_drop_oldest_context_turn(messages)`：按最旧历史轮次裁剪，尽量保留最近对话。
  - `_keep_recent_context_turns(messages, turns)`：兜底阶段保留最近 N 轮历史，当前用于仍超过压缩阈值时至少保留最近 3 轮。
  - `_clear_request_conversation_token_usage(req)`：将本次请求绑定会话的 `token_usage` 缓存清零，避免旧缓存继续触发 AstrBot 压缩判断。
  - `_trim_provider_request_context_if_needed(event, req, limit_context)`：仅裁剪当前 `ProviderRequest.contexts` 中的旧历史轮次，不写回持久化会话历史；先尽量裁到 80% 预算内，若仍超过 AstrBot 压缩阈值则保留最近 3 轮并只抬高本次临时窗口；日志以单行输出。
  - `_cleanup_temp_context_provider(event)`：从 `provider_manager.inst_map` 与 `provider_insts` 中移除临时 provider，并把 `selected_provider` 恢复为原始 provider ID。
  - `_cleanup_temp_context_provider_later(event, temp_provider_id)`：异常路径兜底清理临时 provider，避免请求未进入 LLM 钩子时残留注册项。
- LLM 请求处理顺序：
  - `on_waiting_llm_request()` 在 AstrBot 构建主 agent 之前执行，因此负责为启用策略的群聊预先选择临时 provider。
  - 群聊状态为 `normal` 时，临时 provider 基于当前 AstrBot 默认 provider 创建。
  - 群聊状态为 `fallback` 且回退 provider 有效时，临时 provider 基于回退 provider 创建。
  - 群聊状态为 `stopped` 时不创建临时 provider。
  - `on_llm_request()` 在 `normal` / `fallback` 放行前执行历史上下文预裁剪；必要时先抬高本次临时 provider 窗口，再清理 provider 注册表临时项，使后续 `reset_coro` 组装 messages 时使用较短历史并尽量避开 `ContextManager` 压缩。
- `GET /astrbot_plugin_token_limit/usage` 的每个群聊项增加：
  - `context_limit_05`：当前群是否启用上下文窗口 0.5% 策略。
  - `context_limit_tokens`：当前策略启用时的实际上下文 token 数；未启用时为 `0`。
  - `context_limit_display`：用于页面显示的 0.5% 限制值，按无空格 K/M 格式化。
- `GET /astrbot_plugin_token_limit/group-settings` 返回字段增加：
  - `context_limit_05`、`context_limit_tokens`、`context_limit_display`。
- `POST /astrbot_plugin_token_limit/group-settings` 支持字段增加：
  - `context_limit_05`：布尔值，只保存上下文窗口节约策略，不会自动改写 `daily_token_limit`。
  - `reset=true` 只重置 `daily_token_limit`，不会清除 `only_at_bot_llm` 或 `context_limit_05`。
- `pages/dashboard/index.html` 新增页面元素：
  - `#groupContextLimitInput`：复选框“最大上下文窗口设置为额度的 0.5%”。
  - `#groupContextLimitValue`：显示限制后的 K/M 数值，例如 `(30K)`。
  - `.group-settings-inline-note`：浅色小字号说明样式。
  - `.toast.warning`：黄色警告提示样式，复用 `#groupSettingsToast`。
- `pages/dashboard/index.html` 新增或扩展前端函数：
  - `groupContextLimitDisplay(limitTokens)`：按当前输入的群聊每日上限计算 0.5% 并格式化为 K/M。
  - `updateGroupContextLimitValue()`：在打开弹窗、API 回填和输入框变化时刷新括号数值。
  - `groupContextLimitWarningMessage()` / `updateGroupContextLimitWarning()`：根据勾选状态和限制值显示短上下文或长上下文黄色警告。
  - `openGroupSettings()`：从 usage 缓存和 `group-settings` API 读取 `context_limit_05`，并渲染当前限制值。
  - `saveGroupSettings()`：独立比较并提交 `context_limit_05`，避免只改节约策略时误把每日上限变成个性化配置。
- 页面交互规则：
  - 未勾选“最大上下文窗口设置为额度的 0.5%”时，该群继续使用 AstrBot provider 默认 `max_context_tokens`。
  - 勾选后，括号中的限制值随“单独配置本群每日用量上限”输入框即时更新；保存后后端按最终有效上限实时计算。
  - 勾选后，限制值 `< 15K` 时提示回复延迟风险，限制值 `>= 200K` 时提示 token 用量风险；保存中、重置中和错误提示优先于黄色警告。
  - 如果该群未设置个性化每日上限，后续修改全局 `daily_token_limit` 会同步改变该群上下文限制值。
  - 如果该群已设置个性化每日上限，后续修改全局 `daily_token_limit` 不影响该群上下文限制值。

## v0.6.3 补充结构说明

- `metadata.yaml` 当前版本为 `0.6.3`。
- `user_usage_48h.json` 在 v0.6.3 起使用缩进 JSON 保存，便于管理员直接阅读。
- `user_usage_48h.json` 的 `groups.{group_id}.users.{user_id}` 结构新增 `dialogs`：
  - `stat_id`：AstrBot `ProviderStat.id`，用于去重。
  - `created_at`：本次有效 LLM 请求计入 token 的 UTC 时间。
  - `prompt`：本次请求中用户输入的前 20 个字，过滤常见 @ 标记，不包含 `ProviderRequest.system_prompt`。
  - `tokens`：本次请求计入该用户的 token 用量。
- `groups.{group_id}.requests[]` 请求归因快照新增 `prompt` 字段；`on_llm_request()` 从 `ProviderRequest.prompt` 补齐，供后续 ProviderStat 写入后回配到具体用户。
- `backend/user_stats.py` 新增/扩展内部 API：
  - `_sanitize_dialog_prompt(value)`：压缩空白、过滤常见 CQ/HTML at 标记，并截取前 20 个字。
  - `_sanitize_user_dialog(raw_dialog, cutoff=None)`：清洗持久化对话明细并执行 48 小时裁剪。
  - `_merge_user_dialogs(base, extra)`：合并用户维度的对话明细。
  - `_store_user_dialogs(users, dialogs, replace_start, replace_end)`：按同步覆盖窗口替换旧明细，并按 `stat_id` 去重。
  - `_user_dialog_key(dialog)`：生成对话去重键，优先使用 `ProviderStat.id`。
  - `_user_dialog_from_record(record, tokens, request_item=None)`：把 ProviderStat 明细与请求快照转换为前端可用对话记录。
  - `_find_prompt_for_usage_record(candidates, record)`：为可直接解析用户的 ProviderStat 记录补充请求 prompt。
  - `_query_user_usage_details_for_group(group_id, window, group_data=None)`：返回当前刷新窗口内的用户 token 总量和对话明细；`api_get_user_usage()` 使用它渲染页面。
  - `_stored_user_dialogs_for_group(stats, group_id, window)`：从持久化 JSON 取当前窗口内的对话明细作为兜底数据。
  - `_combine_user_dialogs(realtime_dialogs, stored_dialogs)`：合并实时明细与持久化明细并去重。
  - `_user_usage_dialog_rows(dialogs)`：将对话明细格式化为 API 字段：`prompt`、`tokens`、`display`、`time`、`created_at`。
- `api_get_user_usage()` 的 `users[]` 每项新增 `dialogs[]`：
  - `prompt`：表格“对话”列。
  - `display` / `tokens`：表格“用量”列与排序数值。
  - `time` / `created_at`：表格“时间”列与排序数值。
- `pages/dashboard/index.html` 新增页面元素：
  - `#userDialogOverlay`：点击今日用户柱状图后打开的“对话数据”悬浮窗口。
  - `#closeUserDialogBtn`：右上角 `x` 关闭按钮，关闭后回到今日用户统计窗口。
  - `#userDialogTarget`：显示当前用户昵称/QQ 号。
  - `#userDialogTableBody`：渲染对话明细表格主体。
  - `#sortUserDialogTokensBtn` / `#sortUserDialogTimeBtn`：按用量或时间切换正序/倒序排序。
  - `#sortUserDialogTokensIcon` / `#sortUserDialogTimeIcon`：显示当前排序方向。
- `pages/dashboard/index.html` 新增/扩展前端函数：
  - `openUserDialog(user)`：打开对话表格并默认按时间倒序。
  - `closeUserDialog()`：关闭对话表格并清理当前用户状态。
  - `sortUserDialog(key)`：切换“用量”或“时间”排序方向。
  - `sortedUserDialogs()`：根据当前排序状态返回对话明细副本。
  - `renderUserDialog()`：渲染“对话 / 用量 / 时间”三列表格。
  - `renderUserUsageChart()`：用户横向柱状图新增点击打开对话数据弹窗，并补充 hover/active 效果。
