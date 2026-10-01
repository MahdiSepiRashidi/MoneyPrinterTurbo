# Graph Report - MoneyPrinterTurbo  (2026-10-01)

## Corpus Check
- 158 files · ~293,859 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 23 file(s) not represented in the graph (top: (none) 6, .ttf 5, .ttc 4)

## Summary
- 4655 nodes · 8929 edges · 376 communities (116 shown, 260 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 390 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4c04e339`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- config/__init__.py
- _search_videos_with_cache
- services/video.py
- patch
- pathlib
- TestCli
- TestTaskService
- test_webui_voice_preview.py
- MemoryState
- material.py
- InMemoryTaskManager
- cli.py
- TestVoiceService
- controllers/base.py
- _request_bgm
- TestWaveSpeedProvider
- test_metaso_minimax.py
- TestClaudeCodeProvider
- TestMaterialSearchCache
- TestSoniloService
- TestRedisTaskManager
- MaterialInfo
- muapi.py
- TestSubtitleService
- TestVideoService
- _render_background_music_settings
- asgi.py
- VideoParams
- TestLoomLoomVideoBackend
- Main.py
- voice.py
- TestWebuiBackgroundMusic
- test_voxcpm.py
- TestElevenLabsMusicService
- _run_pipeline
- test_completed_task_renders_subject_named_video_download
- TestWebuiI18n
- TestOFoxService
- _render_loomloom_video_settings
- LLMProviderSpec
- ofox.py
- TestScriptPromptOptions
- SubMaker
- TestVolcEngineSeedanceService
- test_webui_settings_transfer.py
- TestASGICORS
- schema.py
- TestBackgroundMusicService
- _render_settings_dialog
- LoomLoomQuote
- TestLiteLLMProvider
- LoomLoomAPIError
- task_dir
- sonilo.py
- volcengine_seedance.py
- TestMptAgentSkill
- _render_generation_controls
- test_webui_tts_settings.py
- _single_tts
- TestMaterialUploadService
- v1/video.py
- TestMaterialTlsVerification
- TestLoomLoomSettings
- subtitle.py
- RedisTaskManager
- _flush_pending_config_locked
- TestSocialMetadata
- TestControllerAuthentication
- test_webui_task_history.py
- v1/llm.py
- loomloom.py
- _render_subtitle_settings
- ._call_with_capture
- TestElevenLabsVoice
- task.py
- _run_generation
- UploadPostService
- test_kokoro.py
- Path
- ._request
- concat_video_clips_with_ffmpeg
- _render_key_backup_settings
- storage_dir
- cache_manager.py
- MoneyPrinterTurbo Project
- _Response
- TestCoverrProvider
- test_video_effects.py
- ._capture_source_ranges_for_clip_speed
- _generate_response
- video_effects.py
- create_subtitle
- TestVideoCacheManager
- _image_response
- _png_bytes
- _render_audio_settings
- material_upload.py
- mpt_agent.py
- _FakeVideoDownloadResponse
- .test_download_videos_openai_image_skips_rejected_segment
- _FakeMoviePyClip
- _render_video_settings
- azure_tts_v1
- .test_script_order_does_not_skip_unattempted_candidates
- TestAsyncUpdateChecker
- .test_combine_videos_cleans_failed_encoded_clip_and_reader
- _GroupedSelectHarness
- test_webui_local_material_upload.py
- twelvelabs.py
- missing_config
- TestAPIAuthenticationHTTP
- TestSubtitleBackgroundSettings
- TestTwelveLabsService
- test_webui_custom_audio_upload.py
- test_batch_material_allocation.py
- _render_application
- Spec: Farsi Instagram Reel Generation Agent (MoneyPrinterTurbo)
- TestOFoxMaterialIntegration
- test_webui_generation_defaults.py
- services/llm.py
- RedisState
- TestConfigPersistence
- TestOpenAIImageProvider
- TestVersionChecker
- .test_pause_leading_and_trailing
- test_webui_llm_settings.py
- _schedule_cross_post
- Workflow
- TestTaskStaticFiles
- TestFishAudioVoiceHelpers
- TestTaskArtifacts
- _render_script_settings
- AsyncUpdateChecker
- Docker API Service
- TestVideoControllerDeleteHTTP
- _download_response
- TestRedisState
- test_webui_kokoro.py
- test_webui_upload_post_settings.py
- BaseState
- _SynchronizedConfig
- Plan: Farsi Instagram Reel Agent (from intent.md 2026-09-29)
- Test Material Image 1
- TestCliUiDefaults
- .test_nonblocking_update_is_applied_after_runtime_task_finishes
- ._use_litellm_provider
- .test_concat_video_clips_does_not_disable_codec_when_fallback_also_fails
- .test_minimax_tts_reuses_cn_llm_key_and_endpoint
- .test_tts_with_pauses_decode_timeout_returns_failure
- config.py
- validate_pexels_config
- Farsi Instagram Reel Agent Intent
- .test_save_video_streams_chunks_without_materializing_response_content
- test_webui_metaso_minimax.py
- patch_script_data
- _build_redis_url
- test_fluxionai_http_errors_are_not_successful_text
- TestRuntimeEnvironmentDetection
- TestLLMConnection
- redirect_servers
- redirect_servers
- _FakeRedis
- _FakeRedisPipeline
- TestTwelveLabsLive
- _apply_subtitle_spring_animation
- .test_generate_subtitle_uses_whisper_word_timing_without_correction
- TestCheckFfmpegReady
- TestMaterialResolutionTolerance
- .test_gemini_tts_uses_google_genai_and_compatible_submaker_fields
- VideoFitMode
- generate_script
- _download_videos_openai_image_on_demand
- get_llm_provider
- azure_tts_v2
- CI Python Tests Job
- TestVideoControllerCreateHTTP
- TestFishAudioTaskRestore
- TestFishAudioAPIKey
- TestLiteLLMLiveIntegration
- TestRetryWarningBoundary
- FakeHttpResponse
- webui.sh
- trello
- build_claude_code_env
- test_youtube_audience.py
- test_queued_audience_survives_config_change
- TestFishAudioDispatch
- recover_interrupted_cross_posts
- .test_cross_post_state_update_retries_transient_backend_failure
- .test_generate_audio_falls_back_to_sub_maker_when_file_duration_is_zero
- .test_real_multi_segment_concatenation_no_drift
- WebUI Screenshot (Chinese)
- .test_save_video_cleans_partial_stream_when_download_fails
- subtitle_font_supports_text
- TestProjectVersionMetadata
- AGENTS.md
- subtitle_colors_are_indistinguishable
- wrap_text
- parse_script_with_pauses
- APIMart Sponsor Logo
- AstraFlow Sponsor Logo
- BytePlus Sponsor Logo
- CCSub Sponsor Logo
- Fluxion AI Sponsor Logo
- Infistar.cc Sponsor Logo
- Metaso Sponsor Logo
- OfoxAI Sponsor Logo
- Picwish Sponsor Logo
- RecCloud Sponsor Logo
- Shengsuan Cloud Sponsor Logo
- Volcengine Sponsor Logo
- moneyprinterturbo
- moviepy (Video Editing)

## God Nodes (most connected - your core abstractions)
1. `VideoParams` - 155 edges
2. `TestCli` - 80 edges
3. `TestTaskService` - 76 edges
4. `MaterialInfo` - 64 edges
5. `TestVideoService` - 64 edges
6. `VideoAspect` - 62 edges
7. `MemoryState` - 58 edges
8. `TestLiteLLMProvider` - 58 edges
9. `TestVoiceService` - 52 edges
10. `_render_audio_settings()` - 47 edges

## Surprising Connections (you probably didn't know these)
- `3. Data Model` --references--> `VideoParams`  [INFERRED]
  intent/2026-09-29-ig-reel-agent/spec.md → app/models/schema.py
- `Epic C — Media` --references--> `VideoParams`  [INFERRED]
  plan/2026-09-29-ig-reel-agent/plan.md → app/models/schema.py
- `Epic C — Media` --references--> `uploaded_bgm_dir()`  [INFERRED]
  plan/2026-09-29-ig-reel-agent/plan.md → app/services/bgm.py
- `Epic C — Media` --references--> `resolve_bgm_file()`  [INFERRED]
  plan/2026-09-29-ig-reel-agent/plan.md → app/services/bgm.py
- `Epic A — Foundation` --references--> `_generate_response()`  [INFERRED]
  plan/2026-09-29-ig-reel-agent/plan.md → app/services/llm.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **CI/CD Pipeline** — github_workflows_ci_tests, github_workflows_ci_windows_smoke, github_workflows_docker_ghcr, test_readme_pytest [EXTRACTED 1.00]
- **Docker Deployment Variants** — docker_compose_webui, docker_compose_api, docker_compose_release, docker_compose_gpu, docker_compose_claude [EXTRACTED 1.00]
- **Farsi Reel Generation Pipeline** — intent_2026_09_29_ig_reel_agent_intent, skills_meta_safe_farsi_reel_script_skill, intent_2026_09_29_ig_reel_agent_intent_2026_09_29_ig_reel_agent_meta_graph_api, intent_2026_09_29_ig_reel_agent_intent_2026_09_29_ig_reel_agent_idea_cards [EXTRACTED 1.00]

## Communities (376 total, 260 thin omitted)

### Community 0 - "config/__init__.py"
Cohesion: 0.06
Nodes (23): __init_logger(), configure_terminal_logger(), live_config(), _selectbox(), test_catalan_language_switch_preserves_script_and_script_language(), _button_by_key_prefix(), headless_task_app(), test_headless_open_folder_shows_host_mapped_path() (+15 more)

### Community 1 - "_search_videos_with_cache"
Cohesion: 0.10
Nodes (13): _cache_dir(), _cache_key(), _cache_path(), _cached_source_info(), cleanup_expired_material_search_cache(), get_material_search_cache_lock(), load_material_search_cache(), _remove_invalid_cache() (+5 more)

### Community 2 - "services/video.py"
Cohesion: 0.10
Nodes (18): close_clip(), combine_videos(), process_one_clip(), delete_files(), _get_clip_processing_concurrency(), get_ffmpeg_binary(), _get_required_video_duration(), _hex_to_rgb() (+10 more)

### Community 3 - "patch"
Cohesion: 0.16
Nodes (5): _get_all(), _has_key(), _mock_response(), TestUploadPostService, TestUploadPostYouTubePayload

### Community 7 - "test_webui_voice_preview.py"
Cohesion: 0.08
Nodes (21): _button_by_key(), _FakeAudioUpload, _load_duration_estimator(), _load_provider_signature(), _load_voxcpm_state_helpers(), _session_audio(), test_duration_estimator_is_local_and_respects_voice_rate(), test_full_preview_reports_when_tts_returns_no_audio() (+13 more)

### Community 9 - "material.py"
Cohesion: 0.06
Nodes (29): _download_materials_in_parallel(), _download_videos_by_script_order(), _download_videos_ofox_on_demand(), _download_videos_seedance_on_demand(), _download_videos_wavespeed_on_demand(), generate_videos_wavespeed(), _get_material_concurrency(), _get_tls_verify() (+21 more)

### Community 10 - "InMemoryTaskManager"
Cohesion: 0.05
Nodes (4): _coerce_task_limit(), TaskManager, InMemoryTaskManager, TestInMemoryTaskManager

### Community 11 - "cli.py"
Cohesion: 0.07
Nodes (37): get_uuid(), _bgm_type(), _build_batch_tasks(), build_video_params(), _CliHelpFormatter, _clip_speed(), _force_utf8_console(), _hex_color() (+29 more)

### Community 13 - "controllers/base.py"
Cohesion: 0.15
Nodes (7): get_api_key(), get_api_key_values(), get_task_id(), normalize_task_id(), verify_token(), new_router(), FileNotFoundException

### Community 14 - "_request_bgm"
Cohesion: 0.09
Nodes (15): _base_url(), _create_video_proxy(), ElevenLabsAuthenticationError, ElevenLabsMusicError, ElevenLabsPaidPlanRequiredError, generate_bgm(), get_api_key(), _model_id() (+7 more)

### Community 16 - "test_metaso_minimax.py"
Cohesion: 0.07
Nodes (31): _base_url(), _bounded_float(), generate_videos(), get_api_key(), is_enabled(), _is_retryable_error(), MetasoMiniMaxDownloadError, MetasoMiniMaxError (+23 more)

### Community 18 - "TestMaterialSearchCache"
Cohesion: 0.06
Nodes (3): TestMaterialSearchCache, remote_search(), run_search()

### Community 19 - "TestSoniloService"
Cohesion: 0.05
Nodes (4): _event(), _StreamingResponse, TestSoniloService, create_proxy()

### Community 20 - "TestRedisTaskManager"
Cohesion: 0.07
Nodes (3): _queued_payload(), TestRedisTaskManager, _video_params()

### Community 21 - "MaterialInfo"
Cohesion: 0.10
Nodes (25): MaterialInfo, VideoAspect, _creator_info(), download_videos(), _download_videos_metaso_minimax_on_demand(), _download_videos_muapi_on_demand(), search_videos(), _filter_materials_by_aspect() (+17 more)

### Community 22 - "muapi.py"
Cohesion: 0.09
Nodes (33): _base_url(), _bounded_float(), _config_bool(), _duration_bounds(), _endpoint(), generate_videos(), get_api_key(), is_enabled() (+25 more)

### Community 25 - "_render_background_music_settings"
Cohesion: 0.09
Nodes (16): is_enabled(), _cache_minimax_voices(), _credential_signature(), _detect_audio_mime(), _get_cached_minimax_voices(), _parse_chatterbox_voices(), _render_background_music_settings(), _render_minimax_tts_settings() (+8 more)

### Community 26 - "asgi.py"
Cohesion: 0.08
Nodes (13): application_lifespan(), configure_browser_access(), reject_untrusted_browser_origin(), configure_cors(), exception_handler(), get_application(), is_browser_origin_allowed(), _normalize_allowed_origin() (+5 more)

### Community 27 - "VideoParams"
Cohesion: 0.07
Nodes (4): VideoParams, TestClipSpeed, TestVideoParams, TestVolcEngineSeedanceMaterialIntegration

### Community 28 - "TestLoomLoomVideoBackend"
Cohesion: 0.09
Nodes (4): LoomLoomSettings, _DownloadResponse, TestLoomLoomVideoBackend, _video_capability_payload()

### Community 29 - "Main.py"
Cohesion: 0.10
Nodes (20): is_task_busy(), _create_loomloom_script_backend(), _delete_task(), _dismiss_settings_dialog(), _format_task_subject(), _format_task_time(), _handle_loomloom_poll_error(), _is_headless_server() (+12 more)

### Community 30 - "voice.py"
Cohesion: 0.06
Nodes (18): get_all_azure_voices(), _get_audio_duration_from_file(), get_chatterbox_voices(), get_elevenlabs_api_key(), get_elevenlabs_voices(), get_fish_audio_api_key(), get_fish_audio_voices(), get_gemini_voices() (+10 more)

### Community 32 - "test_voxcpm.py"
Cohesion: 0.08
Nodes (25): _encode_voxcpm_audio_data_uri(), _iter_voxcpm_sse_events(), prepare_voxcpm_reference_audio(), voxcpm_tts(), parse_extension(), _FakeSegment, _sse_event(), _sse_lines() (+17 more)

### Community 33 - "TestElevenLabsMusicService"
Cohesion: 0.06
Nodes (3): _StreamingResponse, TestElevenLabsMusicService, __init__()

### Community 34 - "_run_pipeline"
Cohesion: 0.10
Nodes (16): VideoConcatMode, should_use_bgm(), is_openai_image_enabled(), generate_final_videos(), generate_script(), get_video_materials(), _get_video_music_prompt(), _mark_task_failed() (+8 more)

### Community 35 - "test_completed_task_renders_subject_named_video_download"
Cohesion: 0.10
Nodes (5): FakeClip, run(), test_generated_video_sources_do_not_receive_batch_allocation(), test_completed_task_renders_subject_named_video_download(), video()

### Community 36 - "TestWebuiI18n"
Cohesion: 0.08
Nodes (7): _duplicate_translation_keys(), _format_placeholders(), _load_translation(), _markdown_urls(), _required_translation_keys(), TestWebuiI18n, _TrKeyVisitor

### Community 38 - "_render_loomloom_video_settings"
Cohesion: 0.08
Nodes (17): snapshot_config_with_pending(), _create_loomloom_video_backend(), _current_loomloom_video_quote_context(), _effective_loomloom_api_token(), _effective_script_generation_backend(), _format_loomloom_video_model_option(), _format_numeric_range(), _load_loomloom_video_capability() (+9 more)

### Community 40 - "ofox.py"
Cohesion: 0.12
Nodes (19): _base_url(), _bounded_float(), _config_bool(), _duration_bounds(), generate_videos(), get_api_key(), is_enabled(), _is_retryable_error() (+11 more)

### Community 42 - "SubMaker"
Cohesion: 0.09
Nodes (21): chatterbox_tts(), _concat_audio_files(), _configure_pydub_ffmpeg(), elevenlabs_tts(), ensure_file_path_exists(), ensure_legacy_submaker_fields(), fish_audio_tts(), gemini_tts() (+13 more)

### Community 44 - "test_webui_settings_transfer.py"
Cohesion: 0.10
Nodes (20): _encode(), _FakeStreamlit, _load_settings_transfer_helpers(), _record_runtime_config(), _sample_config_sections(), test_credential_widget_state_keys_cover_shared_input_aliases(), test_key_backup_carries_llm_provider_extra_fields_with_the_key(), test_key_backup_collects_credentials_and_their_companion_settings() (+12 more)

### Community 46 - "schema.py"
Cohesion: 0.10
Nodes (27): AudioRequest, BaseResponse, BgmRetrieveData, BgmRetrieveResponse, BgmUploadData, BgmUploadResponse, FileData, _get_valid_ui_choice() (+19 more)

### Community 47 - "TestBackgroundMusicService"
Cohesion: 0.07
Nodes (4): _FakeRequest, TestBackgroundMusicService, _TextUpload, _UnseekableUpload

### Community 48 - "_render_settings_dialog"
Cohesion: 0.10
Nodes (13): normalize_provider_override(), _format_file_size(), format_llm_connection_error(), get_groq_model_ids(), get_llm_provider_label(), get_llm_provider_tips(), _get_material_api_keys(), _get_video_cache_stats() (+5 more)

### Community 49 - "LoomLoomQuote"
Cohesion: 0.09
Nodes (25): LoomLoomExecution, LoomLoomQuote, LoomLoomVideoCapability, LoomLoomVideoModel, helpers(), quote_page(), test_batch_candidate_autofill_once_preserves_manual_count(), test_batch_script_and_video_use_settings_key_without_local_llm() (+17 more)

### Community 51 - "LoomLoomAPIError"
Cohesion: 0.17
Nodes (6): LoomLoomAPIError, LoomLoomScriptBackend, LoomLoomScriptBatch, LoomLoomVideoBackend, LoomLoomVideoBatch, test_missing_key_clears_error_and_never_retries()

### Community 52 - "task_dir"
Cohesion: 0.13
Nodes (16): generate_audio(), resolve_custom_audio_file(), _resolve_reusable_voice_preview(), task_dir(), test_non_default_volume_regenerates_audio_without_double_gain(), test_task_regenerates_audio_when_preview_parameters_changed(), test_task_reuses_matching_full_preview_without_calling_tts(), _collect_task_summaries() (+8 more)

### Community 53 - "sonilo.py"
Cohesion: 0.07
Nodes (23): BgmServiceError, BgmUploadError, _remove_staged_file(), sanitize_upload_filename(), save_bgm_upload(), _stage_bgm_upload(), _validate_audio(), validate_audio_file() (+15 more)

### Community 54 - "volcengine_seedance.py"
Cohesion: 0.14
Nodes (19): _base_url(), _bounded_float(), _config_bool(), _duration_bounds(), generate_videos(), get_api_key(), is_enabled(), _is_retryable_error() (+11 more)

### Community 56 - "_render_generation_controls"
Cohesion: 0.14
Nodes (14): _active_generation_tasks(), _add_active_generation_task(), _build_uploaded_file_path(), _build_video_download_name(), _get_unmet_restore_upload_requirements(), _normalize_task_state(), _prepare_generation_task(), _remove_active_generation_task() (+6 more)

### Community 57 - "test_webui_tts_settings.py"
Cohesion: 0.11
Nodes (13): _load_translation(), test_all_tts_api_key_labels_include_an_official_configuration_link(), test_elevenlabs_environment_key_is_used_without_persisting_it(), test_elevenlabs_reconnect_restores_saved_key_before_loading_voices(), test_minimax_reconnect_restores_saved_tts_key(), test_minimax_shared_llm_key_is_not_duplicated_in_tts_config(), test_minimax_voice_selector_accepts_a_custom_voice_id(), test_minimax_voices_load_only_on_demand_and_sync_the_selected_voice() (+5 more)

### Community 58 - "_single_tts"
Cohesion: 0.17
Nodes (19): get_voxcpm_voices(), is_azure_v1_voice(), is_azure_v2_voice(), is_chatterbox_voice(), is_elevenlabs_voice(), is_fish_audio_voice(), is_gemini_voice(), is_kokoro_voice() (+11 more)

### Community 59 - "TestMaterialUploadService"
Cohesion: 0.09
Nodes (4): _image_bytes(), TestMaterialUploadService, _TextUpload, _UnseekableUpload

### Community 60 - "v1/video.py"
Cohesion: 0.13
Nodes (25): create_audio(), create_subtitle(), create_task(), create_video(), delete_video(), download_video(), get_all_tasks(), get_bgm_list() (+17 more)

### Community 62 - "TestLoomLoomSettings"
Cohesion: 0.16
Nodes (4): _coerce_seconds_setting(), resolve_api_token(), video_settings_from_mapping(), TestLoomLoomSettings

### Community 63 - "subtitle.py"
Cohesion: 0.18
Nodes (9): correct(), create(), _ensure_model_loaded(), file_to_subtitles(), levenshtein_distance(), similarity(), transcribe_audio_bytes(), generate_subtitle() (+1 more)

### Community 65 - "_flush_pending_config_locked"
Cohesion: 0.11
Nodes (11): _apply_pending_config_updates_locked(), delete_config_nonblocking(), _flush_pending_config_locked(), _pending_update_key(), _run_deferred_config_flush(), runtime_config_lock(), save_config(), _schedule_deferred_config_flush() (+3 more)

### Community 68 - "test_webui_task_history.py"
Cohesion: 0.10
Nodes (7): _load_task_history_helpers(), test_build_video_download_name_does_not_overmatch_similar_names(), test_find_final_task_video_ignores_intermediate_files(), test_find_final_task_video_returns_first_numbered_output(), test_history_scan_skips_non_object_script_payload(), test_restore_requirements_allow_replacing_upload_with_other_voice_modes(), test_restore_requirements_require_file_in_upload_voice_mode()

### Community 69 - "v1/llm.py"
Cohesion: 0.14
Nodes (10): generate_video_script(), generate_video_social_metadata(), generate_video_terms(), VideoScriptParams, VideoScriptRequest, VideoSocialMetadataParams, VideoSocialMetadataRequest, VideoTermsParams (+2 more)

### Community 70 - "loomloom.py"
Cohesion: 0.19
Nodes (6): LoomLoomCandidateError, LoomLoomConfigurationError, LoomLoomError, LoomLoomRunError, LoomLoomScriptBatchResult, LoomLoomScriptCandidate

### Community 71 - "_render_subtitle_settings"
Cohesion: 0.18
Nodes (8): font_dir(), resolve_ui_language(), get_all_fonts(), _initialize_session_state(), _render_subtitle_settings(), _saved_ui_bool(), _saved_ui_color(), _saved_ui_number()

### Community 72 - "._call_with_capture"
Cohesion: 0.05
Nodes (7): _FakeClip, _FakeResponse, TestFishAudioErrorHandling, validate(), TestFishAudioTTSRequest, _fake_post(), _fake_post()

### Community 74 - "task.py"
Cohesion: 0.07
Nodes (17): format_log_record(), _project_relative_path(), run_in_background(), text_to_srt(), time_convert_seconds_to_hmsm(), TestVideoControllerListHTTP, _attribute_name(), _log_record() (+9 more)

### Community 75 - "_run_generation"
Cohesion: 0.06
Nodes (17): file_iterator(), LoomLoomConfirmedVideoRequest, start(), _append_task_log(), get_task_logs(), _run_generation(), submit_generation(), test_task_preflight_rejects_missing_key_before_script_generation() (+9 more)

### Community 76 - "UploadPostService"
Cohesion: 0.11
Nodes (3): UploadPostService, TestUploadPostServiceDynamicConfig, test_other_platforms_ignore_youtube_audience()

### Community 77 - "test_kokoro.py"
Cohesion: 0.13
Nodes (13): get_kokoro_voices(), kokoro_tts(), _normalize_kokoro_voices(), test_live_voice_discovery(), kokoro_config(), test_failed_audio_never_overwrites_output(), test_pinned_voices_do_not_request_server(), test_transient_error_retries_successfully() (+5 more)

### Community 78 - "Path"
Cohesion: 0.16
Nodes (8): apply_environment_config(), ensure_config(), ensure_project(), generate_video(), log(), run_checked(), _safe_extract(), SkillError

### Community 79 - "._request"
Cohesion: 0.06
Nodes (4): TaskQueueFullError, TaskVideoRequest, TestVideoControllerFiles, TestVideoControllerTasks

### Community 80 - "concat_video_clips_with_ffmpeg"
Cohesion: 0.10
Nodes (14): concat_video_clips_with_ffmpeg(), build_command(), run_concat(), _describe_concat_output_progress(), _disable_runtime_video_codec(), _escape_ffmpeg_concat_path(), _fallback_write_videofile(), _ffmpeg_encoder_exists() (+6 more)

### Community 81 - "_render_key_backup_settings"
Cohesion: 0.09
Nodes (15): resolve_builtin_bgm_file(), _apply_key_backup(), _build_key_backup_payload(), _build_settings_preset_payload(), _collect_key_backup(), _count_backup_keys(), _credential_widget_state_keys(), _is_backup_config_key() (+7 more)

### Community 82 - "storage_dir"
Cohesion: 0.12
Nodes (14): list_bgm_files(), _list_bgm_files(), list_builtin_bgm_files(), resolve_bgm_file(), uploaded_bgm_dir(), get_bgm_file(), public_dir(), resource_dir() (+6 more)

### Community 83 - "cache_manager.py"
Cohesion: 0.19
Nodes (9): clean_video_cache(), get_video_cache_stats(), _is_cleanup_candidate(), _iter_video_cache_entries(), _validate_max_age_days(), video_cache_dir(), VideoCacheCleanupResult, _VideoCacheEntry (+1 more)

### Community 84 - "MoneyPrinterTurbo Project"
Cohesion: 0.12
Nodes (18): Edge TTS Voice List, Bug Report Issue Template, Issue Template Config, Feature Request Issue Template, Vulnerability Reporting Process, API Service, CLI Mode, Docker Deployment (+10 more)

### Community 85 - "_Response"
Cohesion: 0.16
Nodes (3): LoomLoomRun, _Response, TestLoomLoomScriptBackend

### Community 87 - "test_video_effects.py"
Cohesion: 0.12
Nodes (4): _detail_frame(), _gradient_clip(), TestFadeAndSlideTransitions, TestZoomTransitions

### Community 89 - "_generate_response"
Cohesion: 0.13
Nodes (10): coerce_claude_code_timeout(), _extract_chat_completion_text(), _extract_qwen_generation_text(), _generate_response(), _get_response_field(), _normalize_text_response(), _resolve_provider_field_value(), _sanitize_error_message() (+2 more)

### Community 90 - "video_effects.py"
Cohesion: 0.18
Nodes (10): fadein_transition(), fadeout_transition(), slidein_transition(), position(), slideout_transition(), _zoom_frame(), zoomin_transition(), scale_effect() (+2 more)

### Community 91 - "create_subtitle"
Cohesion: 0.08
Nodes (19): generate_terms(), _build_subtitle_formatter(), formatter(), _build_subtitle_items_from_edge_cues(), _build_subtitle_items_from_edge_cues_words(), _build_subtitle_items_from_legacy_submaker(), _build_subtitle_items_from_legacy_submaker_words(), create_subtitle() (+11 more)

### Community 95 - "_render_audio_settings"
Cohesion: 0.08
Nodes (28): _clear_voxcpm_prompt_state(), _clear_voxcpm_prompt_transcript(), _clear_voxcpm_separate_prompt_audio(), _get_kokoro_voice_options(), _get_reusable_full_voice_preview(), get_tts_provider_tips(), _get_voice_preview_provider_signature(), _get_voice_preview_sample() (+20 more)

### Community 96 - "material_upload.py"
Cohesion: 0.21
Nodes (10): _material_kind(), MaterialServiceError, MaterialUploadError, _remove_staged_file(), sanitize_material_filename(), save_material_upload(), _stage_material_upload(), uploaded_material_dir() (+2 more)

### Community 97 - "mpt_agent.py"
Cohesion: 0.17
Nodes (6): main(), parse_args(), report_invalid_pexels_config(), report_missing_config(), result_manifest_path(), write_result_manifest()

### Community 101 - "_render_video_settings"
Cohesion: 0.09
Nodes (16): normalize_clip_speed(), _delete_runtime_config(), _effective_voice_rate_before_audio_panel(), _estimate_voiceover_duration_range(), grouped_selectbox(), localized_widget_key(), _loomloom_video_coverage_plan(), _matching_full_voice_preview_duration() (+8 more)

### Community 102 - "azure_tts_v1"
Cohesion: 0.13
Nodes (7): azure_tts_v1(), convert_rate_to_percent(), create_edge_tts_communicate(), get_edge_tts_timeout_seconds(), parse_voice_name(), stream_edge_tts_chunks(), _stream_edge_tts_sync_with_timeout()

### Community 104 - "TestAsyncUpdateChecker"
Cohesion: 0.21
Nodes (3): TestAsyncUpdateChecker, check(), slow_check()

### Community 106 - "_GroupedSelectHarness"
Cohesion: 0.16
Nodes (6): _GroupedSelectHarness, _running_app(), test_grouped_video_source_applies_first_change_and_allows_switching_back(), test_grouped_video_source_ignores_unknown_event_and_repairs_saved_value(), test_grouped_video_source_keeps_groups_and_accessible_label_binding(), test_stock_concurrency_only_appears_for_stock_sources()

### Community 107 - "test_webui_local_material_upload.py"
Cohesion: 0.23
Nodes (9): _FakeStreamlit, _image_bytes(), _run_webui_upload_block(), _StoppedUpload, test_webui_enforces_image_size_limit(), test_webui_persists_valid_image_and_session_materials(), test_webui_rejects_invalid_image_before_starting_task(), test_webui_rolls_back_earlier_files_when_later_upload_is_invalid() (+1 more)

### Community 108 - "twelvelabs.py"
Cohesion: 0.26
Nodes (7): analyze_clip(), _client(), _cosine(), embed_text(), _embed_text_cached(), is_enabled(), rerank_terms_by_subject()

### Community 109 - "missing_config"
Cohesion: 0.16
Nodes (7): has_cli_option(), _has_configured_value(), missing_config(), _plain_config_value(), _provider_is_ready(), reuse_existing_llm_provider(), selected_video_source()

### Community 113 - "test_webui_custom_audio_upload.py"
Cohesion: 0.21
Nodes (8): _FakeStreamlit, _run_webui_audio_block(), _StoppedUpload, test_webui_enforces_custom_audio_size_limit(), test_webui_keeps_valid_voiceover_in_the_current_task_directory(), test_webui_rejects_corrupt_custom_audio_before_task_start(), _upload(), _wav_bytes()

### Community 114 - "test_batch_material_allocation.py"
Cohesion: 0.23
Nodes (11): _get_material_source_groups(), render_batch(), test_allocation_tracks_actual_duration_and_speed(), test_failed_clip_does_not_count_as_used(), test_matched_batch_rotates_candidates_in_keyword_order(), test_missing_manifest_falls_back_to_ungrouped_allocation(), test_random_batch_uses_new_sources_before_reuse(), test_safety_margin_does_not_consume_trimmed_source() (+3 more)

### Community 115 - "_render_application"
Cohesion: 0.12
Nodes (12): poll_available_update(), _apply_pending_settings_preset(), _apply_pending_task_restore(), _apply_restored_params(), _build_restore_upload_requirements(), _render_application(), _render_brand(), _render_pending_version_check() (+4 more)

### Community 116 - "Spec: Farsi Instagram Reel Generation Agent (MoneyPrinterTurbo)"
Cohesion: 0.14
Nodes (13): 10. Out of Scope, 1. Problem Summary, 2.1 Functional, 2.2 Non-Functional, 2. Requirements, 3. Data Model, 4. API Contracts, 5. UX / UI Design (+5 more)

### Community 118 - "test_webui_generation_defaults.py"
Cohesion: 0.31
Nodes (8): _new_app(), test_invalid_saved_generation_settings_fall_back_without_breaking_webui(), test_loomloom_tuning_survives_restart_without_persisting_payment_state(), test_ofox_source_shows_unchecked_paid_task_confirmation(), test_reusable_generation_settings_survive_a_new_webui_session(), test_script_order_constraint_does_not_replace_saved_concat_preference(), test_seedance_source_shows_unchecked_paid_task_confirmation(), _widget_by_key()

### Community 119 - "services/llm.py"
Cohesion: 0.21
Nodes (12): build_social_metadata_prompt(), _clamp_text(), _fallback_social_metadata(), generate_social_metadata(), generate_terms(), _limit_social_text(), _normalize_hashtags(), _normalize_social_language() (+4 more)

### Community 125 - ".test_pause_leading_and_trailing"
Cohesion: 0.24
Nodes (6): fake_silence(), fake_single_tts(), fake_silence(), fake_silence(), fake_single_tts(), _write_test_wav()

### Community 126 - "test_webui_llm_settings.py"
Cohesion: 0.23
Nodes (6): test_ai_video_settings_prioritize_sponsors_and_own_shengsuan_key(), test_configure_llm_link_opens_settings_on_llm_tab(), test_fluxionai_settings_defaults_and_connection_button(), test_kimi_platform_selection_keeps_endpoint_configuration_consistent(), test_material_settings_target_uses_localized_tab_state_and_is_consumed(), _widget_by_key()

### Community 127 - "_schedule_cross_post"
Cohesion: 0.13
Nodes (11): _ensure_cross_post_terminal_state(), _finalize_cross_post_future(), _patch_cross_post_state(), _record_cross_post_failure(), _register_cross_post_future(), _run_cross_post(), record_background_request(), _run_cross_post_with_slot() (+3 more)

### Community 128 - "Workflow"
Cohesion: 0.15
Nodes (12): 1. Ask the user, 2. Create the board, 3. Create lists, 4. Create cards, 5. Ordering within lists, 6. Verify, Backlog, Card count heuristic (+4 more)

### Community 134 - "_render_script_settings"
Cohesion: 0.12
Nodes (8): try_runtime_config_lock(), _open_material_settings_dialog(), _open_settings_dialog(), _render_local_script_generation(), render_script_prompt_preview(), _render_script_settings(), reset_script_system_prompt(), _run_llm_read_operation()

### Community 135 - "AsyncUpdateChecker"
Cohesion: 0.20
Nodes (3): AsyncUpdateChecker, UpdateCheckSnapshot, catalan_app()

### Community 136 - "Docker API Service"
Cohesion: 0.27
Nodes (10): Docker API Service, Docker Claude Subscription Variant, Docker GPU Override, Docker Release Compose (Prebuilt Image), Docker WebUI Service, MPT AI Agent Video Skill, Docker GHCR Publish Workflow, AI Agent Workflow (+2 more)

### Community 141 - "test_webui_kokoro.py"
Cohesion: 0.27
Nodes (5): selected_voice(), test_endpoint_or_credential_change_invalidates_cache(), test_first_open_offline_preserves_saved_voice(), test_manual_voices_and_clearing_them(), test_online_offline_recovery_retains_selection()

### Community 142 - "test_webui_upload_post_settings.py"
Cohesion: 0.27
Nodes (5): test_webui_upload_post_checkboxes_stay_decoupled(), test_webui_upload_post_youtube_privacy_fallback_to_public(), test_youtube_audience_hidden_for_other_platforms(), test_youtube_audience_selection_persists_on_first_change(), _widget_by_key()

### Community 145 - "Plan: Farsi Instagram Reel Agent (from intent.md 2026-09-29)"
Cohesion: 0.17
Nodes (11): Config key contract (defines everything below; add to `config.example.toml`, expose in `app/config/config.py`), Data model (store: `supervisor/store.py`, JSON files under `storage/`, created with `mkdir -p` at startup; atomic write = temp+rename; file lock per store), Epic A — Foundation, Epic B — Content, Epic D — Post, operator surface, ship, Features, Order of work, Plan: Farsi Instagram Reel Agent (from intent.md 2026-09-29) (+3 more)

### Community 146 - "Test Material Image 1"
Cohesion: 0.22
Nodes (9): Test Material Image 1, Test Material Image 2, Test Material Image 3, Test Material Image 4, Test Material Image 5, Test Material Image 6, Test Material Image 7, Test Material Image 8 (+1 more)

### Community 154 - "config.py"
Cohesion: 0.11
Nodes (8): _can_resolve_hostname(), _decode_linux_route_gateway(), get_container_default_gateway_ip(), get_default_ollama_base_url(), is_running_in_container(), load_config(), _load_toml_config(), test_main_starts_uvicorn_with_runtime_config()

### Community 155 - "validate_pexels_config"
Cohesion: 0.25
Nodes (4): _parse_string_list(), _replace_config_value(), validate_pexels_config(), _validate_pexels_key()

### Community 156 - "Farsi Instagram Reel Agent Intent"
Cohesion: 0.32
Nodes (6): Farsi Instagram Reel Agent Intent, Idea Card Store, Maktab Jazheh Brand, Meta Graph API Posting Integration, Social Media Publishing, Meta-Safe Farsi Reel Script Skill

### Community 159 - "test_webui_metaso_minimax.py"
Cohesion: 0.32
Nodes (4): test_invalid_metaso_resolution_requires_an_explicit_replacement(), test_metaso_source_requires_confirmation_and_never_enters_task_params(), test_metaso_upload_voiceover_uses_actual_audio_billing_copy(), _widget_by_key()

### Community 160 - "patch_script_data"
Cohesion: 0.25
Nodes (5): patch_script_data(), _script_file(), _write_json_atomic(), write_script_data(), save_script_data()

### Community 162 - "test_fluxionai_http_errors_are_not_successful_text"
Cohesion: 0.33
Nodes (3): test_fluxionai_defaults_and_group_overrides(), respond(), test_fluxionai_http_errors_are_not_successful_text()

### Community 165 - "redirect_servers"
Cohesion: 0.38
Nodes (5): redirect_servers(), do_GET(), do_POST(), _redirect(), test_music_provider_rejects_redirect_without_replaying_credentials_or_video()

### Community 166 - "redirect_servers"
Cohesion: 0.38
Nodes (5): redirect_servers(), do_GET(), do_POST(), _redirect(), test_paid_video_provider_rejects_redirect_without_replaying_request()

### Community 172 - "_apply_subtitle_spring_animation"
Cohesion: 0.25
Nodes (4): _apply_subtitle_spring_animation(), transform_frame(), _get_subtitle_spring_scale(), _scale_subtitle_frame_on_canvas()

### Community 183 - "VideoFitMode"
Cohesion: 0.33
Nodes (3): VideoFitMode, VideoTransitionMode, _fit_clip_to_canvas()

### Community 184 - "generate_script"
Cohesion: 0.60
Nodes (4): build_script_prompt(), generate_script(), _limit_script_text(), _normalize_script_paragraph_number()

### Community 185 - "_download_videos_openai_image_on_demand"
Cohesion: 0.12
Nodes (8): _download_videos_openai_image_on_demand(), generate_images_openai(), _openai_image_endpoint(), _openai_image_prompt(), _openai_image_size(), _OpenAIImageDecodeError, _render_openai_image_video(), _save_openai_image_file()

### Community 186 - "get_llm_provider"
Cohesion: 0.13
Nodes (5): get_llm_provider(), LLMProviderField, get_available_update(), _parse_version(), test_fluxionai_registry_metadata()

### Community 187 - "azure_tts_v2"
Cohesion: 0.50
Nodes (4): azure_tts_v2(), _format_duration_to_offset(), speech_synthesizer_word_boundary_cb(), _build_azure_v2_ssml()

### Community 188 - "CI Python Tests Job"
Cohesion: 0.50
Nodes (5): CI Python Tests Job, CI Windows Smoke Tests, redis (Queue/State), Test Directory Documentation, Pytest Test Runner

### Community 196 - "webui.sh"
Cohesion: 0.60
Nodes (4): find_available_port(), find_port(), PYTHONPATH, webui.sh script

### Community 197 - "trello"
Cohesion: 0.25
Nodes (7): mcp, trello, plugin, $schema, enabled, type, url

### Community 200 - "test_queued_audience_survives_config_change"
Cohesion: 0.18
Nodes (4): test_audience_payload_and_snapshot_override(), test_invalid_audience_never_uploads(), test_queued_audience_survives_config_change(), test_real_http_multipart_audience()

### Community 203 - "recover_interrupted_cross_posts"
Cohesion: 0.33
Nodes (4): _is_cross_post_active_in_process(), _is_cross_post_owner_alive(), _is_windows_process_alive(), recover_interrupted_cross_posts()

### Community 209 - "WebUI Screenshot (Chinese)"
Cohesion: 0.67
Nodes (3): API Demo Screenshot, WebUI Screenshot (English), WebUI Screenshot (Chinese)

### Community 286 - "wrap_text"
Cohesion: 1.00
Nodes (3): wrap_text(), get_text_size(), split_long_token()

## Knowledge Gaps
- **76 isolated node(s):** `$schema`, `plugin`, `type`, `url`, `enabled` (+71 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2140 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **260 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `VideoParams` connect `VideoParams` to `services/video.py`, `pathlib`, `TestTaskArtifacts`, `TestTaskService`, `test_webui_voice_preview.py`, `MemoryState`, `cli.py`, `test_metaso_minimax.py`, `TestRedisTaskManager`, `MaterialInfo`, `muapi.py`, `subtitle_colors_are_indistinguishable`, `Main.py`, `.test_start_returns_before_cross_post_worker_runs`, `_run_pipeline`, `test_completed_task_renders_subject_named_video_download`, `test_webui_settings_transfer.py`, `schema.py`, `.test_generate_subtitle_uses_whisper_word_timing_without_correction`, `task_dir`, `RedisTaskManager`, `test_youtube_audience.py`, `test_queued_audience_survives_config_change`, `task.py`, `_run_generation`, `.test_generate_audio_falls_back_to_sub_maker_when_file_duration_is_zero`, `._request`, `_render_key_backup_settings`, `test_webui_local_material_upload.py`, `TestSubtitleBackgroundSettings`, `test_webui_custom_audio_upload.py`, `test_batch_material_allocation.py`, `_render_application`, `Spec: Farsi Instagram Reel Generation Agent (MoneyPrinterTurbo)`, `TestOFoxMaterialIntegration`, `_schedule_cross_post`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `TestLiteLLMProvider` connect `TestLiteLLMProvider` to `._assert_ollama_base_url`, `pathlib`, `._patch_dashscope_generation`, `._use_litellm_provider`, `.test_current_default_model_names`, `.test_provider_defaults_are_not_persisted_as_user_overrides`, `.test_provider_registry_preserves_product_group_order`, `.test_registry_replaces_deprecated_provider_models`, `.test_required_api_key_providers_have_clickable_entry_points`, `.test_service_endpoint_registry_references_valid_stable_ids`, `.test_kimi_endpoint_selection_does_not_depend_on_marketing_url`, `.test_cloudflare_requires_account_id_before_request`, `.test_aimlapi_provider_uses_openai_compatible_client`, `.test_gemini_uses_google_genai_client`, `.test_openai_provider_error_redacts_embedded_base_url_credentials`, `.test_apimart_provider_uses_unwrapped_openai_compatible_endpoint`, `.test_aihubmix_provider_uses_openai_compatible_client`, `.test_evolink_provider_uses_openai_compatible_client`, `.test_openrouter_provider_uses_openai_compatible_client`, `.test_api_route_provider_uses_openai_compatible_client`, `.test_volcengine_provider_uses_openai_compatible_client`, `.test_mimo_provider_uses_openai_compatible_client`, `.test_azure_provider_uses_azure_client_directly`, `.test_pollinations_uses_unified_openai_compatible_api`, `.test_anthropic_uses_openai_compatible_chat_completions`, `.test_cloudflare_uses_ai_gateway_openai_endpoint`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `TestVoiceService` connect `TestVoiceService` to `pathlib`, `.test_minimax_tts_reuses_cn_llm_key_and_endpoint`, `.test_tts_with_pauses_decode_timeout_returns_failure`, `.test_minimax_tts_does_not_leave_invalid_audio_output`, `skipUnless`, `.test_azure_tts_v1_supports_legacy_edge_tts_without_boundary`, `.test_azure_tts_v1_rejects_boundary_only_stream`, `.test_azure_tts_v1_times_out_hanging_stream_sync`, `.test_gemini_tts_uses_google_genai_and_compatible_submaker_fields`, `.test_mimo_tts_uses_openai_compatible_audio_response`, `.test_match_script_line_normalizes_arabic_letter_forms`, `._call_with_capture`, `.test_no_voice_tts_generates_silent_audio_and_subtitle_timeline`, `.test_create_subtitle_ignores_markdown_separator_lines`, `.test_create_subtitle_word_level_preserves_edge_cue_timing`, `.test_get_audio_duration_accepts_non_mp3_files`, `.test_get_audio_duration_missing_file_returns_zero`, `.test_get_minimax_voice_catalog_exposes_provider_error`, `.test_generate_silent_audio_rejects_missing_output_file`, `.test_empty_voice_name_does_not_enable_no_voice_mode`, `.test_get_minimax_voice_catalog_normalizes_all_voice_types`, `.test_no_voice_alias_none_is_supported_temporarily`, `.test_chatterbox_voice_helpers`, `.test_chatterbox_tts_requires_base_url`, `.test_tts_forwards_rate_to_azure_v2`, `.test_tts_strips_gemini_style_metadata_before_dispatch`, `._make_broken_clip_class`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `VideoParams` (e.g. with `RedisTaskManager` and `_get_video_music_prompt()`) actually correct?**
  _`VideoParams` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `TestCli` (e.g. with `MaterialInfo` and `VideoTransitionMode`) actually correct?**
  _`TestCli` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `TestTaskService` (e.g. with `MaterialInfo` and `VideoParams`) actually correct?**
  _`TestTaskService` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `MaterialInfo` (e.g. with `_cached_source_info()` and `save_material_search_cache()`) actually correct?**
  _`MaterialInfo` has 20 INFERRED edges - model-reasoned connections that need verification._