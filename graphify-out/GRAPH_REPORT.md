# Graph Report - MoneyPrinterTurbo  (2026-09-30)

## Corpus Check
- 217 files · ~286,334 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 23 file(s) not represented in the graph (top: (none) 6, .ttf 5, .ttc 4)

## Summary
- 4600 nodes · 8869 edges · 365 communities (106 shown, 259 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 379 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Config & Upload Pipeline
- LLM Provider Schema
- Video Combine & Subtitles
- Upload & Ping Controllers
- BGM & Service Imports
- CLI Batch Tests
- Task Test Rationales
- Task Artifacts
- Memory State Manager
- Material Download Service
- Task Manager (Base)
- CLI & Utils
- Voice Test Rationales
- Base Controller
- BGM Service Errors
- Material Test Rationales
- Metaso Minimax Service
- LLM Test Rationales
- Material Cache Tests
- Sonilo Event Tests
- Redis Task Manager
- Material Info & Download
- MUAPI Video Service
- Subtitle Test Rationales
- Video Test Rationales
- WebUI Settings & Dialogs
- ASGI App & CORS
- Video Params & Clip Speed
- LoomLoom Video & Tests
- Task Status & WebUI
- Voice Catalog
- WebUI BGM Tests
- VoxCPM Voice
- ElevenLabs Music Tests
- Video Concat & BGM
- Material Source Groups
- WebUI i18n Tests
- Ofox Service Tests
- LoomLoom WebUI Config
- LLM Provider Spec
- Ofox Video Service
- LLM Test Rationales
- TTS Voice Functions
- Volcengine Seedance Tests
- WebUI Settings Transfer
- ASGI CORS Tests
- Schema Models
- BGM Tests
- LLM Provider & WebUI
- LoomLoom Quote & Capability
- LLM Test Rationales
- LoomLoom Script Backend
- Version Check & WebUI Tasks
- Sonilo BGM Service
- Volcengine Seedance
- MPT Agent Skill Tests
- WebUI Task & Sonilo
- WebUI TTS Settings Tests
- Voice Provider Detection
- Material Upload Tests
- V1 Video Controller
- Material Test Rationales
- LoomLoom Settings
- Subtitle Generation
- Video Controller Tests
- Config Pending Updates
- Social Metadata Schema
- Controller Base Tests
- WebUI Task History Tests
- LLM Controller
- LoomLoom Errors
- Subtitle Font Support
- Fish Audio Tests
- ElevenLabs Voice Tests
- Logging & Cache
- Video Stream & WebUI Task
- LoomLoom Regression Tests
- Kokoro Voice Tests
- MPT Agent Skill
- Video Controller Tests
- Video Controller File Tests
- WebUI Key Backup
- Schema & Task Request
- Video Cache Manager
- Docs & Issue Templates
- Fish Audio Tests
- Material Test Rationales
- Video Effects Tests
- Video Clip Speed Tests
- LLM Response Parsing
- Video Effects Transitions
- Subtitle Formatter
- Cache Manager Tests
- OpenAI Image Tests
- OpenAI Image Tests
- WebUI Voice Preview
- Material Upload Errors
- MPT Agent CLI
- Material Download Fake
- OpenAI Image On-Demand
- Video Fake MoviePy Clip
- WebUI Voice Duration
- Azure TTS V1
- Material Parallel Download
- Version Checker Tests
- Video Combine Cleanup
- WebUI Grouped Select
- WebUI Local Material Upload
- TwelveLabs Service
- MPT Agent Config
- API Authentication Tests
- Subtitle Background Tests
- TwelveLabs Tests
- WebUI Custom Audio Upload
- FFmpeg & Audio Concat
- WebUI Restore & Clip Speed
- Video Codec Fallback Tests
- Ofox Material Tests
- WebUI Generation Defaults
- LLM Social Metadata
- Redis State
- Config Persistence Tests
- OpenAI Image Provider Tests
- Version Checker Tests
- Pause TTS Tests
- WebUI LLM Settings
- Cross-Post State
- WebUI Task Submit
- ASGI Static File Tests
- Fish Audio Voice Tests
- Task Artifacts Tests
- WebUI Local Script Gen
- Async Update Checker
- Docker & CI Workflows
- Video Delete Tests
- OpenAI Image Download
- Redis State Tests
- WebUI Kokoro Tests
- WebUI Upload Post Settings
- Base State ABC
- Synchronized Config
- Cross-Post Futures
- Test Image Resources
- CLI UI Defaults Tests
- Config Non-Blocking Tests
- LiteLLM Tests
- Video Concat Fallback Tests
- Minimax TTS Tests
- Pause Timeout Tests
- Container & Gateway Detection
- MPT Agent Pexels
- IG Reel & Farsi Skill
- Material Stream Download
- WebUI Metaso Minimax
- WebUI Minimax Voice Cache
- Redis URL Builder
- FluxionAI LLM Tests
- Runtime Environment Detection
- LLM Connection Tests
- Music Redirect Tests
- Paid Video Redirect Tests
- Fake Redis Test
- Fake Redis Pipeline Test
- TwelveLabs Live Tests
- Material Search Cache
- Whisper Subtitle Tests
- FFmpeg Check Tests
- Material Resolution Tolerance
- Gemini TTS Tests
- Video Fit Mode Schema
- LLM Script Generation
- OpenAI Image Save
- Version Checker Service
- Azure TTS V2
- CI & Test Config
- Font Path Traversal Tests
- Fish Audio Task Restore
- Fish Audio API Key
- LiteLLM Live Integration
- Retry Warning Tests
- MPT Agent Fake HTTP
- WebUI Entry Point
- Video Aspect Resolution
- Claude Code Env
- WaveSpeed Error Tests
- Cross-Post Schedule Tests
- Fish Audio Dispatch
- Cross-Post Retry Tests
- Audio Duration Fallback Tests
- ElevenLabs Multi-Segment Tests
- Docs UI Screenshots
- Metaso Minimax Fixtures
- Version Metadata Tests
- ApiMart Sponsor
- AstraFlow Sponsor
- BytePlus Sponsor
- CCSub Sponsor
- FluxionAI Sponsor
- Infistar Sponsor
- Metaso Sponsor
- Ofox Sponsor
- PicWish Sponsor
- RecCloud Sponsor
- ShengsuanYun Sponsor
- Volcengine Sponsor
- Package Entry
- MoviePy Requirement

## God Nodes (most connected - your core abstractions)
1. `VideoParams` - 153 edges
2. `TestCli` - 80 edges
3. `TestTaskService` - 76 edges
4. `TestVideoService` - 64 edges
5. `MaterialInfo` - 63 edges
6. `VideoAspect` - 62 edges
7. `MemoryState` - 58 edges
8. `TestLiteLLMProvider` - 58 edges
9. `TestVoiceService` - 52 edges
10. `_render_audio_settings()` - 47 edges

## Surprising Connections (you probably didn't know these)
- `MoneyPrinterTurbo Project` --semantically_similar_to--> `MoneyPrinterTurbo Project (Japanese)`  [INFERRED] [semantically similar]
  README-en.md → README-ja.md
- `MoneyPrinterTurbo Project` --semantically_similar_to--> `MoneyPrinterTurbo Project (Chinese)`  [INFERRED] [semantically similar]
  README-en.md → README.md
- `Meta Graph API Posting Integration` --semantically_similar_to--> `Social Media Publishing`  [INFERRED] [semantically similar]
  intent/2026-09-29-ig-reel-agent/intent.md → README-en.md
- `TestVideoControllerTasks` --uses--> `TaskQueueFullError`  [INFERRED]
  test/services/test_controller_video.py → app/controllers/manager/base_manager.py
- `TestInMemoryTaskManager` --uses--> `TaskQueueFullError`  [INFERRED]
  test/services/test_task_manager.py → app/controllers/manager/base_manager.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Docker Deployment Variants** — docker_compose_webui, docker_compose_api, docker_compose_release, docker_compose_gpu, docker_compose_claude [EXTRACTED 1.00]
- **CI/CD Pipeline** — github_workflows_ci_tests, github_workflows_ci_windows_smoke, github_workflows_docker_ghcr, test_readme_pytest [EXTRACTED 1.00]
- **Farsi Reel Generation Pipeline** — intent_2026_09_29_ig_reel_agent_intent, skills_meta_safe_farsi_reel_script_skill, intent_2026_09_29_ig_reel_agent_intent_2026_09_29_ig_reel_agent_meta_graph_api, intent_2026_09_29_ig_reel_agent_intent_2026_09_29_ig_reel_agent_idea_cards [EXTRACTED 1.00]

## Communities (365 total, 259 thin omitted)

### Community 0 - "Config & Upload Pipeline"
Cohesion: 0.04
Nodes (25): load_config(), _load_toml_config(), live_config(), _selectbox(), test_catalan_language_switch_preserves_script_and_script_language(), _button_by_key_prefix(), headless_task_app(), test_headless_open_folder_shows_host_mapped_path() (+17 more)

### Community 1 - "LLM Provider Schema"
Cohesion: 0.04
Nodes (33): get_video_materials_list(), LLMProviderField, list_bgm_files(), _list_bgm_files(), list_builtin_bgm_files(), resolve_bgm_file(), resolve_builtin_bgm_file(), uploaded_bgm_dir() (+25 more)

### Community 2 - "Video Combine & Subtitles"
Cohesion: 0.05
Nodes (45): _apply_subtitle_spring_animation(), transform_frame(), close_clip(), combine_videos(), process_one_clip(), concat_video_clips_with_ffmpeg(), build_command(), run_concat() (+37 more)

### Community 3 - "Upload & Ping Controllers"
Cohesion: 0.06
Nodes (13): ping(), UploadPostService, _get(), _get_all(), _has_key(), _mock_response(), TestUploadPostService, TestUploadPostServiceDynamicConfig (+5 more)

### Community 7 - "Task Artifacts"
Cohesion: 0.05
Nodes (32): patch_script_data(), _script_file(), _write_json_atomic(), write_script_data(), generate_audio(), resolve_custom_audio_file(), _resolve_reusable_voice_preview(), task_dir() (+24 more)

### Community 9 - "Material Download Service"
Cohesion: 0.07
Nodes (29): _creator_info(), _download_materials_in_parallel(), generate_videos_wavespeed(), get_api_key(), _get_material_concurrency(), _get_tls_verify(), _is_cloudflare_challenge(), _is_wavespeed_retryable_error() (+21 more)

### Community 10 - "Task Manager (Base)"
Cohesion: 0.05
Nodes (4): _coerce_task_limit(), TaskManager, InMemoryTaskManager, TestInMemoryTaskManager

### Community 11 - "CLI & Utils"
Cohesion: 0.07
Nodes (37): get_uuid(), _bgm_type(), _build_batch_tasks(), build_video_params(), _CliHelpFormatter, _clip_speed(), _force_utf8_console(), _hex_color() (+29 more)

### Community 13 - "Base Controller"
Cohesion: 0.07
Nodes (18): get_api_key(), get_api_key_values(), get_task_id(), normalize_task_id(), verify_token(), TaskQueueFullError, new_router(), delete_video() (+10 more)

### Community 14 - "BGM Service Errors"
Cohesion: 0.06
Nodes (25): BgmServiceError, BgmUploadError, _remove_staged_file(), sanitize_upload_filename(), save_bgm_upload(), _stage_bgm_upload(), _validate_audio(), validate_audio_file() (+17 more)

### Community 16 - "Metaso Minimax Service"
Cohesion: 0.08
Nodes (30): _base_url(), _bounded_float(), generate_videos(), get_api_key(), is_enabled(), _is_retryable_error(), MetasoMiniMaxDownloadError, MetasoMiniMaxError (+22 more)

### Community 18 - "Material Cache Tests"
Cohesion: 0.06
Nodes (3): TestMaterialSearchCache, remote_search(), run_search()

### Community 19 - "Sonilo Event Tests"
Cohesion: 0.05
Nodes (4): _event(), _StreamingResponse, TestSoniloService, create_proxy()

### Community 20 - "Redis Task Manager"
Cohesion: 0.06
Nodes (4): RedisTaskManager, _queued_payload(), TestRedisTaskManager, _video_params()

### Community 21 - "Material Info & Download"
Cohesion: 0.09
Nodes (27): MaterialInfo, VideoAspect, download_videos(), _download_videos_by_script_order(), _download_videos_metaso_minimax_on_demand(), _download_videos_muapi_on_demand(), _download_videos_ofox_on_demand(), _download_videos_openai_image_on_demand() (+19 more)

### Community 22 - "MUAPI Video Service"
Cohesion: 0.08
Nodes (32): _base_url(), _bounded_float(), _config_bool(), _duration_bounds(), _endpoint(), generate_videos(), get_api_key(), _is_retryable_error() (+24 more)

### Community 25 - "WebUI Settings & Dialogs"
Cohesion: 0.08
Nodes (25): _delete_runtime_config(), get_tts_provider_tips(), grouped_selectbox(), localized_widget_key(), _open_material_settings_dialog(), _open_settings_dialog(), _parse_chatterbox_voices(), _render_audio_settings() (+17 more)

### Community 26 - "ASGI App & CORS"
Cohesion: 0.07
Nodes (12): application_lifespan(), configure_browser_access(), reject_untrusted_browser_origin(), configure_cors(), exception_handler(), get_application(), is_browser_origin_allowed(), _normalize_allowed_origin() (+4 more)

### Community 27 - "Video Params & Clip Speed"
Cohesion: 0.06
Nodes (4): VideoParams, subtitle_colors_are_indistinguishable(), TestClipSpeed, TestVolcEngineSeedanceMaterialIntegration

### Community 28 - "LoomLoom Video & Tests"
Cohesion: 0.08
Nodes (6): LoomLoomRun, _DownloadResponse, _Response, TestLoomLoomScriptBackend, TestLoomLoomVideoBackend, _video_capability_payload()

### Community 29 - "Task Status & WebUI"
Cohesion: 0.08
Nodes (26): is_task_busy(), _build_settings_preset_payload(), _clear_voxcpm_prompt_state(), _clear_voxcpm_prompt_transcript(), _clear_voxcpm_separate_prompt_audio(), _delete_task(), _dismiss_settings_dialog(), _format_task_subject() (+18 more)

### Community 30 - "Voice Catalog"
Cohesion: 0.06
Nodes (18): get_all_azure_voices(), _get_audio_duration_from_file(), get_chatterbox_voices(), get_elevenlabs_api_key(), get_elevenlabs_voices(), get_fish_audio_api_key(), get_fish_audio_voices(), get_gemini_voices() (+10 more)

### Community 32 - "VoxCPM Voice"
Cohesion: 0.08
Nodes (25): _encode_voxcpm_audio_data_uri(), _iter_voxcpm_sse_events(), prepare_voxcpm_reference_audio(), voxcpm_tts(), parse_extension(), _FakeSegment, _sse_event(), _sse_lines() (+17 more)

### Community 33 - "ElevenLabs Music Tests"
Cohesion: 0.06
Nodes (3): _StreamingResponse, TestElevenLabsMusicService, __init__()

### Community 34 - "Video Concat & BGM"
Cohesion: 0.09
Nodes (22): VideoConcatMode, should_use_bgm(), is_openai_image_enabled(), is_enabled(), generate_final_videos(), generate_script(), generate_terms(), get_video_materials() (+14 more)

### Community 35 - "Material Source Groups"
Cohesion: 0.08
Nodes (16): _get_material_source_groups(), FakeClip, render_batch(), run(), test_allocation_tracks_actual_duration_and_speed(), test_failed_clip_does_not_count_as_used(), test_generated_video_sources_do_not_receive_batch_allocation(), test_matched_batch_rotates_candidates_in_keyword_order() (+8 more)

### Community 36 - "WebUI i18n Tests"
Cohesion: 0.08
Nodes (7): _duplicate_translation_keys(), _format_placeholders(), _load_translation(), _markdown_urls(), _required_translation_keys(), TestWebuiI18n, _TrKeyVisitor

### Community 38 - "LoomLoom WebUI Config"
Cohesion: 0.08
Nodes (17): snapshot_config_with_pending(), _create_loomloom_video_backend(), _current_loomloom_video_quote_context(), _effective_loomloom_api_token(), _effective_script_generation_backend(), _format_loomloom_video_model_option(), _format_numeric_range(), _load_loomloom_video_capability() (+9 more)

### Community 40 - "Ofox Video Service"
Cohesion: 0.12
Nodes (19): _base_url(), _bounded_float(), _config_bool(), _duration_bounds(), generate_videos(), get_api_key(), is_enabled(), _is_retryable_error() (+11 more)

### Community 42 - "TTS Voice Functions"
Cohesion: 0.12
Nodes (17): chatterbox_tts(), _configure_pydub_ffmpeg(), elevenlabs_tts(), ensure_file_path_exists(), ensure_legacy_submaker_fields(), fish_audio_tts(), gemini_tts(), get_audio_duration() (+9 more)

### Community 44 - "WebUI Settings Transfer"
Cohesion: 0.10
Nodes (20): _encode(), _FakeStreamlit, _load_settings_transfer_helpers(), _record_runtime_config(), _sample_config_sections(), test_credential_widget_state_keys_cover_shared_input_aliases(), test_key_backup_carries_llm_provider_extra_fields_with_the_key(), test_key_backup_collects_credentials_and_their_companion_settings() (+12 more)

### Community 46 - "Schema Models"
Cohesion: 0.12
Nodes (24): BaseResponse, BgmRetrieveData, BgmRetrieveResponse, BgmUploadData, BgmUploadResponse, FileData, _get_valid_ui_choice(), TaskListData (+16 more)

### Community 47 - "BGM Tests"
Cohesion: 0.07
Nodes (4): _FakeRequest, TestBackgroundMusicService, _TextUpload, _UnseekableUpload

### Community 48 - "LLM Provider & WebUI"
Cohesion: 0.08
Nodes (17): get_llm_provider(), normalize_provider_override(), test_fluxionai_registry_metadata(), _format_file_size(), format_llm_connection_error(), get_all_songs(), get_groq_model_ids(), get_llm_provider_label() (+9 more)

### Community 49 - "LoomLoom Quote & Capability"
Cohesion: 0.12
Nodes (19): LoomLoomQuote, LoomLoomVideoCapability, LoomLoomVideoModel, _function(), quote_page(), test_batch_script_and_video_use_settings_key_without_local_llm(), test_generated_long_script_autofills_video_count_once_and_shows_shortfall(), test_loomloom_execution_requires_confirmation_and_quoted_version() (+11 more)

### Community 51 - "LoomLoom Script Backend"
Cohesion: 0.17
Nodes (4): LoomLoomScriptBackend, LoomLoomScriptBatch, LoomLoomVideoBackend, LoomLoomVideoBatch

### Community 52 - "Version Check & WebUI Tasks"
Cohesion: 0.11
Nodes (21): poll_available_update(), _collect_task_summaries(), _count_processing_tasks(), _create_loomloom_script_backend(), _find_final_task_video(), _handle_loomloom_poll_error(), _loomloom_script_signature(), _friendly() (+13 more)

### Community 53 - "Sonilo BGM Service"
Cohesion: 0.11
Nodes (13): _base_url(), _create_video_proxy(), generate_bgm(), get_api_key(), _normalize_service_id(), _parse_event(), _remove_file(), _request_bgm() (+5 more)

### Community 54 - "Volcengine Seedance"
Cohesion: 0.12
Nodes (17): _base_url(), _bounded_float(), _config_bool(), _duration_bounds(), generate_videos(), _is_retryable_error(), _model_id(), _redact_secret() (+9 more)

### Community 56 - "WebUI Task & Sonilo"
Cohesion: 0.10
Nodes (18): is_enabled(), _active_generation_tasks(), _add_active_generation_task(), _build_uploaded_file_path(), _build_video_download_name(), _get_unmet_restore_upload_requirements(), _normalize_task_state(), open_task_folder() (+10 more)

### Community 57 - "WebUI TTS Settings Tests"
Cohesion: 0.11
Nodes (13): _load_translation(), test_all_tts_api_key_labels_include_an_official_configuration_link(), test_elevenlabs_environment_key_is_used_without_persisting_it(), test_elevenlabs_reconnect_restores_saved_key_before_loading_voices(), test_minimax_reconnect_restores_saved_tts_key(), test_minimax_shared_llm_key_is_not_duplicated_in_tts_config(), test_minimax_voice_selector_accepts_a_custom_voice_id(), test_minimax_voices_load_only_on_demand_and_sync_the_selected_voice() (+5 more)

### Community 58 - "Voice Provider Detection"
Cohesion: 0.17
Nodes (19): get_voxcpm_voices(), is_azure_v1_voice(), is_azure_v2_voice(), is_chatterbox_voice(), is_elevenlabs_voice(), is_fish_audio_voice(), is_gemini_voice(), is_kokoro_voice() (+11 more)

### Community 59 - "Material Upload Tests"
Cohesion: 0.09
Nodes (4): _image_bytes(), TestMaterialUploadService, _TextUpload, _UnseekableUpload

### Community 60 - "V1 Video Controller"
Cohesion: 0.15
Nodes (15): create_audio(), create_subtitle(), create_task(), create_video(), download_video(), get_all_tasks(), get_bgm_list(), get_task() (+7 more)

### Community 62 - "LoomLoom Settings"
Cohesion: 0.14
Nodes (4): LoomLoomSettings, resolve_api_token(), video_settings_from_mapping(), TestLoomLoomSettings

### Community 63 - "Subtitle Generation"
Cohesion: 0.12
Nodes (14): correct(), file_to_subtitles(), levenshtein_distance(), similarity(), generate_subtitle(), create_subtitle(), _do(), estimate_no_voice_duration() (+6 more)

### Community 65 - "Config Pending Updates"
Cohesion: 0.11
Nodes (11): _apply_pending_config_updates_locked(), delete_config_nonblocking(), _flush_pending_config_locked(), _pending_update_key(), _run_deferred_config_flush(), runtime_config_lock(), save_config(), _schedule_deferred_config_flush() (+3 more)

### Community 66 - "Social Metadata Schema"
Cohesion: 0.10
Nodes (3): VideoSocialMetadataParams, VideoSocialMetadataRequest, TestSocialMetadata

### Community 68 - "WebUI Task History Tests"
Cohesion: 0.10
Nodes (7): _load_task_history_helpers(), test_build_video_download_name_does_not_overmatch_similar_names(), test_find_final_task_video_ignores_intermediate_files(), test_find_final_task_video_returns_first_numbered_output(), test_history_scan_skips_non_object_script_payload(), test_restore_requirements_allow_replacing_upload_with_other_voice_modes(), test_restore_requirements_require_file_in_upload_voice_mode()

### Community 69 - "LLM Controller"
Cohesion: 0.17
Nodes (8): generate_video_script(), generate_video_social_metadata(), generate_video_terms(), VideoScriptParams, VideoScriptRequest, VideoTermsParams, VideoTermsRequest, TestLlmController

### Community 70 - "LoomLoom Errors"
Cohesion: 0.13
Nodes (9): _coerce_seconds_setting(), LoomLoomCandidateError, LoomLoomConfigurationError, LoomLoomConfirmedVideoRequest, LoomLoomError, LoomLoomExecution, LoomLoomRunError, LoomLoomScriptBatchResult (+1 more)

### Community 71 - "Subtitle Font Support"
Cohesion: 0.12
Nodes (11): _subtitle_font_supports_sample(), subtitle_font_supports_text(), font_dir(), resolve_ui_language(), get_all_fonts(), _initialize_session_state(), _render_subtitle_settings(), _saved_ui_bool() (+3 more)

### Community 72 - "Fish Audio Tests"
Cohesion: 0.14
Nodes (4): _FakeResponse, TestFishAudioErrorHandling, validate(), _fake_post()

### Community 74 - "Logging & Cache"
Cohesion: 0.12
Nodes (10): __init_logger(), configure_terminal_logger(), format_log_record(), _project_relative_path(), _log_record(), test_log_paths_on_another_mount_do_not_discard_the_record(), test_log_paths_outside_the_project_keep_the_absolute_path(), test_log_paths_stay_posix_style_on_every_platform() (+2 more)

### Community 75 - "Video Stream & WebUI Task"
Cohesion: 0.11
Nodes (11): file_iterator(), start(), _append_task_log(), get_task_logs(), _run_generation(), test_task_preflight_rejects_missing_key_before_script_generation(), test_task_preflight_rejects_missing_key_before_script_generation(), test_webui_worker_forwards_reference_audio_to_pipeline() (+3 more)

### Community 76 - "LoomLoom Regression Tests"
Cohesion: 0.20
Nodes (12): LoomLoomAPIError, helpers(), test_batch_candidate_autofill_once_preserves_manual_count(), test_capability_cache_isolated_by_endpoint_and_key_and_recovers(), test_changed_billable_inputs_allow_one_new_quote_attempt(), test_failed_quote_pauses_until_manual_retry_and_recovers(), test_incomplete_input_clears_failed_quote_without_network(), test_missing_key_clears_error_and_never_retries() (+4 more)

### Community 77 - "Kokoro Voice Tests"
Cohesion: 0.15
Nodes (12): get_kokoro_voices(), _normalize_kokoro_voices(), test_live_voice_discovery(), kokoro_config(), test_failed_audio_never_overwrites_output(), test_pinned_voices_do_not_request_server(), test_transient_error_retries_successfully(), test_transport_closes_audio_and_preserves_contract() (+4 more)

### Community 78 - "MPT Agent Skill"
Cohesion: 0.16
Nodes (8): apply_environment_config(), ensure_config(), ensure_project(), generate_video(), log(), run_checked(), _safe_extract(), SkillError

### Community 81 - "WebUI Key Backup"
Cohesion: 0.12
Nodes (11): _apply_key_backup(), _build_key_backup_payload(), _collect_key_backup(), _count_backup_keys(), _credential_widget_state_keys(), _is_backup_config_key(), _is_credential_config_key(), _normalize_backup_value() (+3 more)

### Community 82 - "Schema & Task Request"
Cohesion: 0.16
Nodes (3): SubtitleRequest, TaskVideoRequest, TestVideoParams

### Community 83 - "Video Cache Manager"
Cohesion: 0.19
Nodes (9): clean_video_cache(), get_video_cache_stats(), _is_cleanup_candidate(), _iter_video_cache_entries(), _validate_max_age_days(), video_cache_dir(), VideoCacheCleanupResult, _VideoCacheEntry (+1 more)

### Community 84 - "Docs & Issue Templates"
Cohesion: 0.12
Nodes (18): Edge TTS Voice List, Bug Report Issue Template, Issue Template Config, Feature Request Issue Template, Vulnerability Reporting Process, API Service, CLI Mode, Docker Deployment (+10 more)

### Community 87 - "Video Effects Tests"
Cohesion: 0.13
Nodes (4): _detail_frame(), _gradient_clip(), TestFadeAndSlideTransitions, TestZoomTransitions

### Community 89 - "LLM Response Parsing"
Cohesion: 0.13
Nodes (10): coerce_claude_code_timeout(), _extract_chat_completion_text(), _extract_qwen_generation_text(), _generate_response(), _get_response_field(), _normalize_text_response(), _resolve_provider_field_value(), _sanitize_error_message() (+2 more)

### Community 90 - "Video Effects Transitions"
Cohesion: 0.18
Nodes (10): fadein_transition(), fadeout_transition(), slidein_transition(), position(), slideout_transition(), _zoom_frame(), zoomin_transition(), scale_effect() (+2 more)

### Community 91 - "Subtitle Formatter"
Cohesion: 0.15
Nodes (9): _build_subtitle_formatter(), formatter(), _build_subtitle_items_from_edge_cues(), _build_subtitle_items_from_edge_cues_words(), _build_subtitle_items_from_legacy_submaker(), _build_subtitle_items_from_legacy_submaker_words(), _match_script_line(), mktimestamp() (+1 more)

### Community 95 - "WebUI Voice Preview"
Cohesion: 0.15
Nodes (11): _get_reusable_full_voice_preview(), _get_voice_preview_provider_signature(), _get_voice_preview_sample(), _get_voxcpm_effective_prompt_audio(), _get_voxcpm_preview_validation_error(), _get_voxcpm_prompt_audio(), _get_voxcpm_prompt_text(), _get_voxcpm_prompt_validation_error() (+3 more)

### Community 96 - "Material Upload Errors"
Cohesion: 0.20
Nodes (9): _material_kind(), MaterialServiceError, MaterialUploadError, _remove_staged_file(), sanitize_material_filename(), save_material_upload(), _stage_material_upload(), _validate_image() (+1 more)

### Community 97 - "MPT Agent CLI"
Cohesion: 0.17
Nodes (6): main(), parse_args(), report_invalid_pexels_config(), report_missing_config(), result_manifest_path(), write_result_manifest()

### Community 101 - "WebUI Voice Duration"
Cohesion: 0.12
Nodes (8): _effective_voice_rate_before_audio_panel(), _estimate_voiceover_duration_range(), _loomloom_video_coverage_plan(), _matching_full_voice_preview_duration(), _render_muapi_video_settings(), _render_ofox_video_settings(), _render_seedance_video_settings(), _render_wavespeed_video_settings()

### Community 102 - "Azure TTS V1"
Cohesion: 0.13
Nodes (7): azure_tts_v1(), convert_rate_to_percent(), create_edge_tts_communicate(), get_edge_tts_timeout_seconds(), parse_voice_name(), stream_edge_tts_chunks(), _stream_edge_tts_sync_with_timeout()

### Community 104 - "Version Checker Tests"
Cohesion: 0.21
Nodes (3): TestAsyncUpdateChecker, check(), slow_check()

### Community 106 - "WebUI Grouped Select"
Cohesion: 0.16
Nodes (6): _GroupedSelectHarness, _running_app(), test_grouped_video_source_applies_first_change_and_allows_switching_back(), test_grouped_video_source_ignores_unknown_event_and_repairs_saved_value(), test_grouped_video_source_keeps_groups_and_accessible_label_binding(), test_stock_concurrency_only_appears_for_stock_sources()

### Community 107 - "WebUI Local Material Upload"
Cohesion: 0.18
Nodes (9): _FakeStreamlit, _image_bytes(), _run_webui_upload_block(), _StoppedUpload, test_webui_enforces_image_size_limit(), test_webui_persists_valid_image_and_session_materials(), test_webui_rejects_invalid_image_before_starting_task(), test_webui_rolls_back_earlier_files_when_later_upload_is_invalid() (+1 more)

### Community 108 - "TwelveLabs Service"
Cohesion: 0.23
Nodes (7): analyze_clip(), _client(), _cosine(), embed_text(), _embed_text_cached(), is_enabled(), rerank_terms_by_subject()

### Community 109 - "MPT Agent Config"
Cohesion: 0.16
Nodes (7): has_cli_option(), _has_configured_value(), missing_config(), _plain_config_value(), _provider_is_ready(), reuse_existing_llm_provider(), selected_video_source()

### Community 113 - "WebUI Custom Audio Upload"
Cohesion: 0.18
Nodes (8): _FakeStreamlit, _run_webui_audio_block(), _StoppedUpload, test_webui_enforces_custom_audio_size_limit(), test_webui_keeps_valid_voiceover_in_the_current_task_directory(), test_webui_rejects_corrupt_custom_audio_before_task_start(), _upload(), _wav_bytes()

### Community 114 - "FFmpeg & Audio Concat"
Cohesion: 0.18
Nodes (6): get_ffmpeg_binary(), _concat_audio_files(), generate_silent_audio(), _publish_tts_ffmpeg_output(), _run_tts_ffmpeg(), get_ffmpeg_binary()

### Community 115 - "WebUI Restore & Clip Speed"
Cohesion: 0.17
Nodes (8): normalize_clip_speed(), _apply_pending_settings_preset(), _apply_pending_task_restore(), _apply_restored_params(), _build_restore_upload_requirements(), _render_application(), reset_subtitle_settings(), _set_stable_widget_value()

### Community 118 - "WebUI Generation Defaults"
Cohesion: 0.31
Nodes (8): _new_app(), test_invalid_saved_generation_settings_fall_back_without_breaking_webui(), test_loomloom_tuning_survives_restart_without_persisting_payment_state(), test_ofox_source_shows_unchecked_paid_task_confirmation(), test_reusable_generation_settings_survive_a_new_webui_session(), test_script_order_constraint_does_not_replace_saved_concat_preference(), test_seedance_source_shows_unchecked_paid_task_confirmation(), _widget_by_key()

### Community 119 - "LLM Social Metadata"
Cohesion: 0.27
Nodes (10): build_social_metadata_prompt(), _clamp_text(), _fallback_social_metadata(), generate_social_metadata(), _limit_social_text(), _normalize_hashtags(), _normalize_social_language(), _parse_social_metadata() (+2 more)

### Community 125 - "Pause TTS Tests"
Cohesion: 0.24
Nodes (6): fake_silence(), fake_single_tts(), fake_silence(), fake_silence(), fake_single_tts(), _write_test_wav()

### Community 126 - "WebUI LLM Settings"
Cohesion: 0.23
Nodes (6): test_ai_video_settings_prioritize_sponsors_and_own_shengsuan_key(), test_configure_llm_link_opens_settings_on_llm_tab(), test_fluxionai_settings_defaults_and_connection_button(), test_kimi_platform_selection_keeps_endpoint_configuration_consistent(), test_material_settings_target_uses_localized_tab_state_and_is_consumed(), _widget_by_key()

### Community 127 - "Cross-Post State"
Cohesion: 0.24
Nodes (6): _patch_cross_post_state(), _record_cross_post_failure(), _run_cross_post(), record_background_request(), _run_cross_post_with_slot(), cross_post_video()

### Community 128 - "WebUI Task Submit"
Cohesion: 0.18
Nodes (5): submit_generation(), test_scheduling_failure_is_saved_as_terminal_task_state(), test_submit_generation_copies_params_before_starting_worker(), test_submit_generation_keeps_voxcpm_reference_audio_out_of_params(), test_submit_generation_returns_while_pipeline_is_still_running()

### Community 134 - "WebUI Local Script Gen"
Cohesion: 0.20
Nodes (5): try_runtime_config_lock(), _detect_audio_mime(), _render_local_script_generation(), _run_llm_read_operation(), _synthesize_voice_preview()

### Community 135 - "Async Update Checker"
Cohesion: 0.20
Nodes (3): AsyncUpdateChecker, UpdateCheckSnapshot, catalan_app()

### Community 136 - "Docker & CI Workflows"
Cohesion: 0.27
Nodes (10): Docker API Service, Docker Claude Subscription Variant, Docker GPU Override, Docker Release Compose (Prebuilt Image), Docker WebUI Service, MPT AI Agent Video Skill, Docker GHCR Publish Workflow, AI Agent Workflow (+2 more)

### Community 141 - "WebUI Kokoro Tests"
Cohesion: 0.27
Nodes (5): selected_voice(), test_endpoint_or_credential_change_invalidates_cache(), test_first_open_offline_preserves_saved_voice(), test_manual_voices_and_clearing_them(), test_online_offline_recovery_retains_selection()

### Community 142 - "WebUI Upload Post Settings"
Cohesion: 0.27
Nodes (5): test_webui_upload_post_checkboxes_stay_decoupled(), test_webui_upload_post_youtube_privacy_fallback_to_public(), test_youtube_audience_hidden_for_other_platforms(), test_youtube_audience_selection_persists_on_first_change(), _widget_by_key()

### Community 145 - "Cross-Post Futures"
Cohesion: 0.25
Nodes (4): _ensure_cross_post_terminal_state(), _finalize_cross_post_future(), _register_cross_post_future(), _unregister_cross_post_future()

### Community 146 - "Test Image Resources"
Cohesion: 0.22
Nodes (9): Test Material Image 1, Test Material Image 2, Test Material Image 3, Test Material Image 4, Test Material Image 5, Test Material Image 6, Test Material Image 7, Test Material Image 8 (+1 more)

### Community 154 - "Container & Gateway Detection"
Cohesion: 0.25
Nodes (5): _can_resolve_hostname(), _decode_linux_route_gateway(), get_container_default_gateway_ip(), get_default_ollama_base_url(), is_running_in_container()

### Community 155 - "MPT Agent Pexels"
Cohesion: 0.25
Nodes (4): _parse_string_list(), _replace_config_value(), validate_pexels_config(), _validate_pexels_key()

### Community 156 - "IG Reel & Farsi Skill"
Cohesion: 0.32
Nodes (6): Farsi Instagram Reel Agent Intent, Idea Card Store, Maktab Jazheh Brand, Meta Graph API Posting Integration, Social Media Publishing, Meta-Safe Farsi Reel Script Skill

### Community 159 - "WebUI Metaso Minimax"
Cohesion: 0.32
Nodes (4): test_invalid_metaso_resolution_requires_an_explicit_replacement(), test_metaso_source_requires_confirmation_and_never_enters_task_params(), test_metaso_upload_voiceover_uses_actual_audio_billing_copy(), _widget_by_key()

### Community 160 - "WebUI Minimax Voice Cache"
Cohesion: 0.25
Nodes (4): _cache_minimax_voices(), _credential_signature(), _get_cached_minimax_voices(), _get_kokoro_voice_options()

### Community 162 - "FluxionAI LLM Tests"
Cohesion: 0.33
Nodes (3): test_fluxionai_defaults_and_group_overrides(), respond(), test_fluxionai_http_errors_are_not_successful_text()

### Community 165 - "Music Redirect Tests"
Cohesion: 0.38
Nodes (5): redirect_servers(), do_GET(), do_POST(), _redirect(), test_music_provider_rejects_redirect_without_replaying_credentials_or_video()

### Community 166 - "Paid Video Redirect Tests"
Cohesion: 0.38
Nodes (5): redirect_servers(), do_GET(), do_POST(), _redirect(), test_paid_video_provider_rejects_redirect_without_replaying_request()

### Community 172 - "Material Search Cache"
Cohesion: 0.40
Nodes (4): _filter_materials_by_aspect(), _search_videos_with_cache(), load_cache_safely(), load_matching_cache()

### Community 184 - "LLM Script Generation"
Cohesion: 0.60
Nodes (4): build_script_prompt(), generate_script(), _limit_script_text(), _normalize_script_paragraph_number()

### Community 187 - "Azure TTS V2"
Cohesion: 0.50
Nodes (4): azure_tts_v2(), _format_duration_to_offset(), speech_synthesizer_word_boundary_cb(), _build_azure_v2_ssml()

### Community 188 - "CI & Test Config"
Cohesion: 0.50
Nodes (5): CI Python Tests Job, CI Windows Smoke Tests, redis (Queue/State), Test Directory Documentation, Pytest Test Runner

### Community 196 - "WebUI Entry Point"
Cohesion: 0.60
Nodes (4): find_available_port(), find_port(), PYTHONPATH, webui.sh script

### Community 209 - "Docs UI Screenshots"
Cohesion: 0.67
Nodes (3): API Demo Screenshot, WebUI Screenshot (English), WebUI Screenshot (Chinese)

## Knowledge Gaps
- **42 isolated node(s):** `moneyprinterturbo`, `PYTHONPATH`, `WebUI Component`, `API Service`, `CLI Mode` (+37 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2100 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **259 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `VideoParams` connect `Video Params & Clip Speed` to `Config & Upload Pipeline`, `WebUI Task Submit`, `Video Combine & Subtitles`, `LLM Provider Schema`, `BGM & Service Imports`, `Task Artifacts Tests`, `Task Test Rationales`, `Task Artifacts`, `Memory State Manager`, `CLI & Utils`, `Base Controller`, `Metaso Minimax Service`, `Redis Task Manager`, `MUAPI Video Service`, `Task Status & WebUI`, `Video Concat & BGM`, `Material Source Groups`, `WebUI Settings Transfer`, `Schema Models`, `Whisper Subtitle Tests`, `Task ElevenLabs Key Tests`, `Cross-Post Schedule Tests`, `Video Stream & WebUI Task`, `Audio Duration Fallback Tests`, `Schema & Task Request`, `WebUI Local Material Upload`, `Subtitle Background Tests`, `WebUI Custom Audio Upload`, `WebUI Restore & Clip Speed`, `Ofox Material Tests`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Why does `TestLiteLLMProvider` connect `LLM Test Rationales` to `Ollama LLM Tests`, `BGM & Service Imports`, `Qwen LLM Tests`, `LiteLLM Tests`, `LLM Default Model Tests`, `LLM Provider Override Tests`, `LLM Registry Order Tests`, `LLM Deprecated Model Tests`, `LLM API Key Entry Points`, `LLM Endpoint Registry Tests`, `LLM Kimi Endpoint Tests`, `Cloudflare Account Tests`, `AI ML API LLM Tests`, `Gemini LLM Tests`, `OpenAI URL Redaction Tests`, `Apimart LLM Tests`, `AIHubMix LLM Tests`, `EvoLink LLM Tests`, `OpenRouter LLM Tests`, `APIRoute LLM Tests`, `Volcengine LLM Tests`, `Mimo LLM Tests`, `Azure LLM Tests`, `Pollinations LLM Tests`, `Anthropic LLM Tests`, `Cloudflare LLM Tests`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `TestVideoService` connect `Video Test Rationales` to `BGM & Service Imports`, `Material Info & Download`, `Video Concat Fallback Tests`, `Image Zoom Clip Tests`, `Failed Zoom Clip Tests`, `Video Unreadable Source Tests`, `Video Unique Clip Tests`, `Video Sequential Order Tests`, `Video Combine Audio Tests`, `Video Long Primary Tests`, `Video Wrap Text Tests`, `Video Subtitle Margin Tests`, `Video Multi-Lingual Subtitle Tests`, `Video BGM Path Tests`, `Video FFmpeg Env Path Tests`, `Video FFmpeg ImageIO Tests`, `Video Encoder Fallback Tests`, `Video Clip Concurrency Tests`, `Video Font Reject Tests`, `Video Line Metric Tests`, `Video None Transition Tests`, `Video Clip Speed Tests`, `Video Fake MoviePy Clip`, `FFmpeg Heartbeat Tests`, `Video Combine Cleanup`, `Concat Timeout Tests`, `Failed Encode Tests`, `Final Encode Tests`, `Video Codec Fallback Tests`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Are the 28 inferred relationships involving `VideoParams` (e.g. with `RedisTaskManager` and `_get_video_music_prompt()`) actually correct?**
  _`VideoParams` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `TestCli` (e.g. with `MaterialInfo` and `VideoTransitionMode`) actually correct?**
  _`TestCli` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `TestTaskService` (e.g. with `MaterialInfo` and `VideoParams`) actually correct?**
  _`TestTaskService` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `moneyprinterturbo`, `PYTHONPATH`, `WebUI Component` to the rest of the system?**
  _42 weakly-connected nodes found - possible documentation gaps or missing edges._