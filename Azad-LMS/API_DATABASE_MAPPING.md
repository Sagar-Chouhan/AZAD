# Azad LMS - Database Dependency & Schema Mapping

This document maps every endpoint to its database dependencies, tables, columns, operations, and schema relationships.

## 1. Database Architecture Overview

- **Engine Dialect**: PostgreSQL (`postgresql+psycopg2`)
- **Active Tables Registered in Base.metadata**: 51 tables
- **Total Tables in SQL Dump (`azadlms_dev_db.sql`)**: 80 tables (including 29 legacy Laravel framework tables)
- **ORM Pattern**: SQLAlchemy Declarative Models with Session dependency injection (`get_db`)

## 2. Table-to-Endpoint Dependency Catalog

| Table Name | Primary Key | Foreign Keys | Endpoints Accessing | Operations |
|---|---|---|---|---|
| `assessment_mapping` | `assessment_mapping_id` | None | 30 | DELETE, INSERT, SELECT, UPDATE |
| `assessment_master` | `assessment_id` | None | 23 | DELETE, INSERT, SELECT, UPDATE |
| `batch_masters` | `batch_id` | centre_id -> centre_masters.centre_id | 11 | SELECT |
| `batch_participant` | `batch_participant_id` | batch_id -> batch_masters.batch_id, participant_id -> participantmasters.participant_id | 11 | SELECT |
| `block_master` | `block_lgd_code` | None | 13 | DELETE, INSERT, SELECT, UPDATE |
| `centre_masters` | `centre_id` | None | 20 | DELETE, INSERT, SELECT, UPDATE |
| `course_masters` | `course_id` | None | 6 | SELECT, UPDATE |
| `didyouknow` | `didyouknow_id` | None | 0 | None direct |
| `district_master` | `district_lgd_code` | state_lgd_code -> state_master.state_lgd_code | 20 | DELETE, INSERT, SELECT, UPDATE |
| `document_categories` | `doc_category_id` | None | 7 | DELETE, INSERT, SELECT, UPDATE |
| `document_masters` | `doc_id` | None | 33 | DELETE, INSERT, SELECT, UPDATE |
| `drop_bucket_items` | `drop_bucket_item_id` | bucket_id -> drop_buckets.bucket_id | 7 | SELECT |
| `drop_bucket_masters` | `drop_bucket_id` | None | 29 | DELETE, INSERT, SELECT, UPDATE |
| `drop_buckets` | `bucket_id` | drop_bucket_id -> drop_bucket_masters.drop_bucket_id | 10 | DELETE, SELECT, UPDATE |
| `entity_audit_logs` | `id` | user_id -> users.id | 0 | None direct |
| `language_master` | `language_id` | None | 53 | DELETE, INSERT, SELECT, UPDATE |
| `login_logs` | `id` | None | 1 | SELECT |
| `match_correct_answers` | `match_correct_answers_id` | match_right_id -> match_right_items.match_right_id, match_left_id -> match_left_items.match_left_id, match_making_id -> match_making_masters.match_making_id | 10 | DELETE, SELECT, UPDATE |
| `match_left_items` | `match_left_id` | match_making_id -> match_making_masters.match_making_id | 7 | SELECT |
| `match_making_masters` | `match_making_id` | None | 29 | DELETE, INSERT, SELECT, UPDATE |
| `match_right_items` | `match_right_id` | match_making_id -> match_making_masters.match_making_id | 7 | SELECT |
| `mcq_master` | `mcq_id` | None | 29 | DELETE, INSERT, SELECT, UPDATE |
| `mcq_question_options` | `mcq_option_id` | mcq_id -> mcq_master.mcq_id | 7 | SELECT |
| `module_masters` | `module_id` | None | 51 | DELETE, INSERT, SELECT, UPDATE |
| `module_type` | `module_type_id` | None | 37 | DELETE, INSERT, SELECT, UPDATE |
| `mood_questions_master` | `question_id` | None | 0 | None direct |
| `participant_dbs` | `participant_db_id` | None | 8 | SELECT |
| `participant_feedback` | `feedback_id` | None | 1 | SELECT |
| `participant_mcqs` | `participant_mcq_id` | None | 8 | SELECT |
| `participant_mm` | `participant_mm_id` | None | 8 | SELECT |
| `participant_module` | `participant_module_id` | None | 15 | SELECT, UPDATE |
| `participant_mood_answers` | `answer_id` | question_id -> mood_questions_master.question_id, selected_option_id -> question_options.option_id | 0 | None direct |
| `participant_scs` | `participant_sc_id` | None | 8 | SELECT |
| `participant_time_spent_log` | `id` | None | 0 | None direct |
| `participantmasters` | `participant_id` | None | 12 | INSERT, SELECT |
| `pdf_masters` | `pdf_id` | None | 13 | DELETE, INSERT, SELECT, UPDATE |
| `post_session_assessment` | `post_session_assessment_id` | None | 30 | DELETE, INSERT, SELECT, UPDATE |
| `post_video_question_score` | `id` | None | 0 | None direct |
| `ppt_masters` | `ppt_id` | None | 13 | DELETE, INSERT, SELECT, UPDATE |
| `pre_session_assessment` | `pre_session_assessment_id` | None | 23 | DELETE, INSERT, SELECT, UPDATE |
| `question_options` | `option_id` | question_id -> mood_questions_master.question_id | 0 | None direct |
| `scq_master` | `scq_id` | None | 29 | DELETE, INSERT, SELECT, UPDATE |
| `scq_question_options` | `scq_option_id` | scq_id -> scq_master.scq_id | 7 | SELECT |
| `self_paced_learning` | `self_paced_learning_id` | None | 30 | DELETE, INSERT, SELECT, UPDATE |
| `state_master` | `state_lgd_code` | None | 17 | DELETE, INSERT, SELECT, UPDATE |
| `time_spent_module_log` | `id` | None | 7 | SELECT |
| `topic_mapping` | `topic_mapping_id` | None | 30 | DELETE, INSERT, SELECT, UPDATE |
| `topic_master` | `topic_id` | None | 36 | DELETE, INSERT, SELECT, UPDATE |
| `users` | `id` | None | 65 | DELETE, INSERT, SELECT, UPDATE |
| `video_masters` | `video_id` | None | 13 | DELETE, INSERT, SELECT, UPDATE |
| `video_questions` | `video_question_id` | None | 0 | None direct |

---

## 3. Detailed Endpoint-to-Database Mapping

| Method | Endpoint Path | Module | Tables Accessed | Operations | Filter / Join Columns |
|---|---|---|---|---|---|
| `GET` | `/users/creatable-roles` | Users | `users` | SELECT | `users.role` |
| `POST` | `/users` | Users | `users` | INSERT | `users.status` |
| `GET` | `/users` | Users | `users` | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/users/{user_id}` | Users | `users` | SELECT | `users.id` |
| `PUT` | `/users/{user_id}` | Users | `users` | UPDATE | `users.id` |
| `DELETE` | `/users/{user_id}` | Users | `users` | DELETE | `users.id` |
| `GET` | `/participants/states` | Participants | `assessment_mapping`<br>`batch_masters`<br>`batch_participant`<br>`block_master`<br>`centre_masters`<br>`district_master`<br>`drop_bucket_items`<br>`drop_bucket_masters`<br>`drop_buckets`<br>`match_correct_answers`<br>`match_left_items`<br>`match_making_masters`<br>`match_right_items`<br>`mcq_master`<br>`mcq_question_options`<br>`module_masters`<br>`module_type`<br>`participant_dbs`<br>`participant_mcqs`<br>`participant_mm`<br>`participant_module`<br>`participant_scs`<br>`participantmasters`<br>`post_session_assessment`<br>`scq_master`<br>`scq_question_options`<br>`state_master`<br>`time_spent_module_log`<br>`users` | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/participants/districts/{state_lgd_code}` | Participants | `assessment_mapping`<br>`batch_masters`<br>`batch_participant`<br>`block_master`<br>`centre_masters`<br>`district_master`<br>`drop_bucket_items`<br>`drop_bucket_masters`<br>`drop_buckets`<br>`match_correct_answers`<br>`match_left_items`<br>`match_making_masters`<br>`match_right_items`<br>`mcq_master`<br>`mcq_question_options`<br>`module_masters`<br>`module_type`<br>`participant_dbs`<br>`participant_mcqs`<br>`participant_mm`<br>`participant_module`<br>`participant_scs`<br>`participantmasters`<br>`post_session_assessment`<br>`scq_master`<br>`scq_question_options`<br>`state_master`<br>`time_spent_module_log`<br>`users` | SELECT | `district_master.state_lgd_code`<br>`state_master.state_lgd_code`<br>`users.state_lgd_code` |
| `GET` | `/participants/blocks/{district_lgd_code}` | Participants | `assessment_mapping`<br>`batch_masters`<br>`batch_participant`<br>`block_master`<br>`centre_masters`<br>`district_master`<br>`drop_bucket_items`<br>`drop_bucket_masters`<br>`drop_buckets`<br>`match_correct_answers`<br>`match_left_items`<br>`match_making_masters`<br>`match_right_items`<br>`mcq_master`<br>`mcq_question_options`<br>`module_masters`<br>`module_type`<br>`participant_dbs`<br>`participant_mcqs`<br>`participant_mm`<br>`participant_module`<br>`participant_scs`<br>`participantmasters`<br>`post_session_assessment`<br>`scq_master`<br>`scq_question_options`<br>`state_master`<br>`time_spent_module_log`<br>`users` | SELECT | `block_master.district_lgd_code`<br>`district_master.district_lgd_code`<br>`users.district_lgd_code` |
| `GET` | `/participants/centres/{block_id}` | Participants | `assessment_mapping`<br>`batch_masters`<br>`batch_participant`<br>`block_master`<br>`centre_masters`<br>`district_master`<br>`drop_bucket_items`<br>`drop_bucket_masters`<br>`drop_buckets`<br>`match_correct_answers`<br>`match_left_items`<br>`match_making_masters`<br>`match_right_items`<br>`mcq_master`<br>`mcq_question_options`<br>`module_masters`<br>`module_type`<br>`participant_dbs`<br>`participant_mcqs`<br>`participant_mm`<br>`participant_module`<br>`participant_scs`<br>`participantmasters`<br>`post_session_assessment`<br>`scq_master`<br>`scq_question_options`<br>`state_master`<br>`time_spent_module_log`<br>`users` | SELECT | `centre_masters.block_id`<br>`participantmasters.block_id`<br>`time_spent_module_log.id`<br>`users.id` |
| `GET` | `/participants/participants/all-centres` | Participants | `assessment_mapping`<br>`batch_masters`<br>`batch_participant`<br>`block_master`<br>`centre_masters`<br>`district_master`<br>`drop_bucket_items`<br>`drop_bucket_masters`<br>`drop_buckets`<br>`match_correct_answers`<br>`match_left_items`<br>`match_making_masters`<br>`match_right_items`<br>`mcq_master`<br>`mcq_question_options`<br>`module_masters`<br>`module_type`<br>`participant_dbs`<br>`participant_mcqs`<br>`participant_mm`<br>`participant_module`<br>`participant_scs`<br>`participantmasters`<br>`post_session_assessment`<br>`scq_master`<br>`scq_question_options`<br>`state_master`<br>`time_spent_module_log`<br>`users` | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/participants/participants/batches` | Participants | `assessment_mapping`<br>`batch_masters`<br>`batch_participant`<br>`block_master`<br>`centre_masters`<br>`district_master`<br>`drop_bucket_items`<br>`drop_bucket_masters`<br>`drop_buckets`<br>`match_correct_answers`<br>`match_left_items`<br>`match_making_masters`<br>`match_right_items`<br>`mcq_master`<br>`mcq_question_options`<br>`module_masters`<br>`module_type`<br>`participant_dbs`<br>`participant_mcqs`<br>`participant_mm`<br>`participant_module`<br>`participant_scs`<br>`participantmasters`<br>`post_session_assessment`<br>`scq_master`<br>`scq_question_options`<br>`state_master`<br>`time_spent_module_log`<br>`users` | SELECT | `batch_masters.centre_id`<br>`centre_masters.centre_id`<br>`time_spent_module_log.id`<br>`users.centre_id`<br>`users.id` |
| `GET` | `/participants/enrollment/{batch_id}` | Participants | `assessment_mapping`<br>`batch_masters`<br>`batch_participant`<br>`block_master`<br>`centre_masters`<br>`district_master`<br>`drop_bucket_items`<br>`drop_bucket_masters`<br>`drop_buckets`<br>`match_correct_answers`<br>`match_left_items`<br>`match_making_masters`<br>`match_right_items`<br>`mcq_master`<br>`mcq_question_options`<br>`module_masters`<br>`module_type`<br>`participant_dbs`<br>`participant_mcqs`<br>`participant_mm`<br>`participant_module`<br>`participant_scs`<br>`participantmasters`<br>`post_session_assessment`<br>`scq_master`<br>`scq_question_options`<br>`state_master`<br>`time_spent_module_log`<br>`users` | SELECT | `batch_masters.batch_id`<br>`batch_participant.batch_id`<br>`time_spent_module_log.id`<br>`users.id` |
| `POST` | `/participants/` | Participants | `users` | INSERT | `users.block_lgd_code`<br>`users.centre_id`<br>`users.district_lgd_code`<br>`users.email`<br>`users.id`<br>`users.name` |
| `GET` | `/participants` | Participants | `users` | SELECT | `users.centre_id`<br>`users.id`<br>`users.role` |
| `GET` | `/participants/{participant_id}/report` | Participants | `users` | SELECT | `users.id` |
| `GET` | `/participants/{participant_id}/modules` | Participants | `users` | SELECT | `users.id` |
| `POST` | `/participants/assign` | Participants | `users` | INSERT | `users.id`<br>`users.status` |
| `POST` | `/participants/unassign` | Participants | `users` | INSERT | `users.id`<br>`users.status` |
| `GET` | `/participants/{participant_id}/key-details` | Participants | `users` | SELECT | `users.id` |
| `PUT` | `/participants/{participant_id}/change-password` | Participants | `users` | UPDATE | `users.id`<br>`users.password` |
| `GET` | `/participants/{participant_id}/time-spent` | Participants | `users` | SELECT | `users.id` |
| `GET` | `/participants/{participant_id}/edit` | Participants | `users` | SELECT | `users.id` |
| `PUT` | `/participants/{participant_id}` | Participants | `users` | UPDATE | `users.block_lgd_code`<br>`users.centre_id`<br>`users.district_lgd_code`<br>`users.email`<br>`users.id`<br>`users.name` |
| `GET` | `/auth/captcha` | Authentication | `users` | SELECT | Primary Keys / Foreign Keys |
| `POST` | `/auth/login` | Authentication | `users` | INSERT | Primary Keys / Foreign Keys |
| `POST` | `/auth/refresh` | Authentication | `users` | INSERT | Primary Keys / Foreign Keys |
| `POST` | `/auth/logout` | Authentication | `users` | INSERT | Primary Keys / Foreign Keys |
| `POST` | `/auth/forgot-password` | Authentication | `users` | INSERT | `users.password` |
| `POST` | `/auth/reset-password` | Authentication | `users` | INSERT | `users.id`<br>`users.password` |
| `POST` | `/integrations/www/trainee` | WWW Integration | None | INSERT | Primary Keys / Foreign Keys |
| `GET` | `/centres/states` | Centres | `centre_masters`<br>`district_master` | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/centres/districts/{state_id}` | Centres | `centre_masters`<br>`district_master` | SELECT | `centre_masters.state_id` |
| `GET` | `/centres/blocks/{district_id}` | Centres | `centre_masters`<br>`district_master` | SELECT | `centre_masters.district_id` |
| `GET` | `/centres` | Centres | `block_master`<br>`centre_masters`<br>`district_master`<br>`state_master` | SELECT | `centre_masters.district_id`<br>`centre_masters.state_id` |
| `POST` | `/centres` | Centres | `block_master`<br>`centre_masters`<br>`district_master`<br>`state_master` | INSERT | `block_master.status`<br>`centre_masters.status`<br>`district_master.status`<br>`state_master.status` |
| `GET` | `/centres/{centre_id}` | Centres | `block_master`<br>`centre_masters`<br>`district_master`<br>`state_master` | SELECT | `centre_masters.centre_id` |
| `PUT` | `/centres/{centre_id}` | Centres | `block_master`<br>`centre_masters`<br>`district_master`<br>`state_master` | UPDATE | `centre_masters.centre_id` |
| `PATCH` | `/centres/{centre_id}/status` | Centres | `block_master`<br>`centre_masters`<br>`district_master`<br>`state_master` | UPDATE | `block_master.status`<br>`centre_masters.centre_id`<br>`centre_masters.status`<br>`district_master.status`<br>`state_master.status` |
| `DELETE` | `/centres/{centre_id}` | Centres | `block_master`<br>`centre_masters`<br>`district_master`<br>`state_master` | DELETE | `block_master.status`<br>`centre_masters.centre_id`<br>`centre_masters.status`<br>`district_master.status`<br>`state_master.status` |
| `GET` | `/states` | State Masters | `users` | SELECT | `users.name`<br>`users.status` |
| `POST` | `/states` | State Masters | `users` | INSERT | `users.role`<br>`users.status` |
| `GET` | `/states/{state_lgd_code}` | State Masters | `users` | SELECT | `users.state_lgd_code` |
| `PUT` | `/states/{state_lgd_code}` | State Masters | `users` | UPDATE | `users.role`<br>`users.state_lgd_code` |
| `DELETE` | `/states/{state_lgd_code}` | State Masters | `users` | DELETE | `users.role`<br>`users.state_lgd_code` |
| `GET` | `/districts` | District Masters | `users` | SELECT | `users.name`<br>`users.state_lgd_code`<br>`users.status` |
| `POST` | `/districts` | District Masters | `users` | INSERT | `users.role`<br>`users.status` |
| `GET` | `/districts/{district_lgd_code}` | District Masters | `users` | SELECT | `users.district_lgd_code`<br>`users.status` |
| `PUT` | `/districts/{district_lgd_code}` | District Masters | `users` | UPDATE | `users.district_lgd_code`<br>`users.role`<br>`users.status` |
| `DELETE` | `/districts/{district_lgd_code}` | District Masters | `users` | DELETE | `users.district_lgd_code`<br>`users.role`<br>`users.status` |
| `GET` | `/documents/categories` | Document Management | None | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/documents/languages` | Document Management | None | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/documents` | Document Management | `document_categories`<br>`document_masters`<br>`language_master`<br>`module_masters`<br>`module_type`<br>`pdf_masters`<br>`ppt_masters`<br>`topic_master`<br>`video_masters` | SELECT | `document_categories.language_id`<br>`document_masters.doc_type`<br>`document_masters.language_id`<br>`language_master.language_id`<br>`module_masters.language_id`<br>`pdf_masters.language_id` |
| `GET` | `/documents/export/csv` | Document Management | `document_masters` | SELECT | `document_masters.doc_category_id`<br>`document_masters.doc_ref_id`<br>`document_masters.doc_type`<br>`document_masters.language_id`<br>`document_masters.status` |
| `GET` | `/documents/{doc_id}` | Document Management | `document_categories`<br>`document_masters`<br>`language_master`<br>`module_masters`<br>`module_type`<br>`pdf_masters`<br>`ppt_masters`<br>`topic_master`<br>`video_masters` | SELECT | `document_masters.doc_id` |
| `POST` | `/documents` | Document Management | `document_categories`<br>`document_masters`<br>`language_master`<br>`module_masters`<br>`module_type`<br>`pdf_masters`<br>`ppt_masters`<br>`topic_master`<br>`video_masters` | INSERT | `document_categories.status`<br>`document_masters.status`<br>`module_masters.status`<br>`module_type.status`<br>`pdf_masters.status`<br>`ppt_masters.status` |
| `PUT` | `/documents/{doc_id}` | Document Management | `document_categories`<br>`document_masters`<br>`language_master`<br>`module_masters`<br>`module_type`<br>`pdf_masters`<br>`ppt_masters`<br>`topic_master`<br>`video_masters` | UPDATE | `document_categories.status`<br>`document_masters.doc_id`<br>`document_masters.status`<br>`module_masters.status`<br>`module_type.status`<br>`pdf_masters.status` |
| `DELETE` | `/documents/{doc_id}` | Document Management | `document_categories`<br>`document_masters`<br>`language_master`<br>`module_masters`<br>`module_type`<br>`pdf_masters`<br>`ppt_masters`<br>`topic_master`<br>`video_masters` | DELETE | `document_categories.status`<br>`document_masters.doc_id`<br>`document_masters.status`<br>`module_masters.status`<br>`module_type.status`<br>`pdf_masters.status` |
| `GET` | `/documents/{document_id}/translation/form` | Document Management | `document_masters` | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/documents/{document_id}/translation/{language_id}` | Document Management | `document_categories`<br>`document_masters`<br>`language_master`<br>`module_masters`<br>`module_type`<br>`pdf_masters`<br>`ppt_masters`<br>`topic_master`<br>`video_masters` | SELECT | `document_categories.language_id`<br>`document_masters.language_id`<br>`language_master.language_id`<br>`module_masters.language_id`<br>`pdf_masters.language_id`<br>`ppt_masters.language_id` |
| `POST` | `/documents/{document_id}/translation/save` | Document Management | `document_masters` | INSERT | `document_masters.language_id`<br>`document_masters.status` |
| `GET` | `/reference/states` | Reference Data | `users` | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/reference/districts` | Reference Data | `users` | SELECT | `users.id` |
| `GET` | `/reference/centres` | Reference Data | `users` | SELECT | `users.id` |
| `GET` | `/courses` | Courses | `course_masters`<br>`language_master`<br>`module_masters`<br>`participant_module` | SELECT | `course_masters.language_id`<br>`language_master.language_id`<br>`module_masters.language_id` |
| `GET` | `/courses/{course_id}/translation` | Courses | `course_masters`<br>`language_master`<br>`module_masters`<br>`participant_module` | SELECT | `course_masters.course_id`<br>`course_masters.language_id`<br>`language_master.language_id`<br>`module_masters.language_id`<br>`participant_module.course_id` |
| `GET` | `/courses/{course_id}/edit` | Courses | `course_masters`<br>`language_master`<br>`module_masters`<br>`participant_module` | SELECT | `course_masters.course_id`<br>`course_masters.language_id`<br>`language_master.language_id`<br>`module_masters.language_id`<br>`participant_module.course_id` |
| `PUT` | `/courses/{course_id}` | Courses | `course_masters`<br>`language_master`<br>`module_masters`<br>`participant_module` | UPDATE | `course_masters.course_description`<br>`course_masters.course_id`<br>`course_masters.course_image`<br>`course_masters.course_name`<br>`course_masters.language_id`<br>`course_masters.status` |
| `GET` | `/courses/export` | Courses | `course_masters`<br>`language_master`<br>`module_masters`<br>`participant_module` | SELECT | `course_masters.course_name`<br>`course_masters.language_id`<br>`course_masters.status`<br>`language_master.language_id`<br>`language_master.language_name`<br>`module_masters.language_id` |
| `GET` | `/batches` | Batch Master | `batch_masters`<br>`batch_participant`<br>`centre_masters`<br>`district_master`<br>`participantmasters`<br>`state_master`<br>`users` | SELECT | `batch_masters.status`<br>`centre_masters.district_id`<br>`centre_masters.state_id`<br>`centre_masters.status`<br>`district_master.status`<br>`participantmasters.district_id` |
| `POST` | `/batches` | Batch Master | `users` | INSERT | `users.id`<br>`users.role`<br>`users.status` |
| `GET` | `/batches/{batch_id}` | Batch Master | `batch_masters`<br>`batch_participant`<br>`centre_masters`<br>`district_master`<br>`participantmasters`<br>`state_master`<br>`users` | SELECT | `batch_masters.batch_id`<br>`batch_participant.batch_id`<br>`users.id` |
| `PUT` | `/batches/{batch_id}` | Batch Master | `users` | UPDATE | `users.id`<br>`users.role` |
| `PATCH` | `/batches/{batch_id}/status` | Batch Master | `users` | UPDATE | `users.id`<br>`users.role`<br>`users.status` |
| `DELETE` | `/batches/{batch_id}` | Batch Master | `users` | DELETE | `users.id`<br>`users.role`<br>`users.status` |
| `GET` | `/batches/{batch_id}/participants` | Batch Master | `batch_masters`<br>`batch_participant`<br>`centre_masters`<br>`district_master`<br>`participantmasters`<br>`state_master`<br>`users` | SELECT | `batch_masters.batch_id`<br>`batch_participant.batch_id`<br>`users.id` |
| `GET` | `/topics` | Topic Master | `module_masters`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | SELECT | `module_masters.language_id`<br>`topic_master.language_id` |
| `GET` | `/topics/{topic_id}` | Topic Master | `module_masters`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | SELECT | `self_paced_learning.topic_id`<br>`topic_mapping.topic_id`<br>`topic_master.topic_id` |
| `DELETE` | `/topics/{topic_id}` | Topic Master | `module_masters`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | DELETE | `self_paced_learning.topic_id`<br>`topic_mapping.topic_id`<br>`topic_master.topic_id` |
| `POST` | `/topics` | Topic Master | `module_masters`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | INSERT | Primary Keys / Foreign Keys |
| `POST` | `/topics/{topic_id}/translation` | Topic Master | `module_masters`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | INSERT | `self_paced_learning.topic_id`<br>`topic_mapping.topic_id`<br>`topic_master.topic_id` |
| `PUT` | `/topics/{topic_id}` | Topic Master | `module_masters`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | UPDATE | `self_paced_learning.topic_id`<br>`topic_mapping.topic_id`<br>`topic_master.topic_id` |
| `GET` | `/topics/{topic_id}/translation/{language_id}` | Topic Master | `module_masters`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | SELECT | `module_masters.language_id`<br>`self_paced_learning.topic_id`<br>`topic_mapping.topic_id`<br>`topic_master.language_id`<br>`topic_master.topic_id` |
| `GET` | `/modules` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | SELECT | `document_masters.language_id`<br>`drop_bucket_masters.language_id`<br>`language_master.language_id`<br>`match_making_masters.language_id`<br>`mcq_master.language_id`<br>`module_masters.language_id` |
| `GET` | `/modules/export` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | SELECT | `document_masters.language_id`<br>`drop_bucket_masters.language_id`<br>`language_master.language_id`<br>`match_making_masters.language_id`<br>`mcq_master.language_id`<br>`module_masters.language_id` |
| `POST` | `/modules` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | INSERT | `document_masters.language_id`<br>`document_masters.status`<br>`drop_bucket_masters.language_id`<br>`drop_bucket_masters.status`<br>`language_master.language_id`<br>`match_making_masters.language_id` |
| `GET` | `/modules/{module_id}` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | SELECT | `assessment_master.module_id`<br>`document_masters.module_id`<br>`module_masters.module_id`<br>`post_session_assessment.module_id`<br>`pre_session_assessment.module_id`<br>`self_paced_learning.module_id` |
| `PUT` | `/modules/{module_id}` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | UPDATE | `assessment_master.module_id`<br>`document_masters.module_id`<br>`document_masters.status`<br>`drop_bucket_masters.status`<br>`match_making_masters.status`<br>`mcq_master.status` |
| `DELETE` | `/modules/{module_id}` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | DELETE | `assessment_master.module_id`<br>`document_masters.module_id`<br>`module_masters.module_id`<br>`post_session_assessment.module_id`<br>`pre_session_assessment.module_id`<br>`self_paced_learning.module_id` |
| `POST` | `/modules/{module_id}/translation` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | INSERT | `assessment_master.module_id`<br>`document_masters.module_id`<br>`module_masters.module_id`<br>`post_session_assessment.module_id`<br>`pre_session_assessment.module_id`<br>`self_paced_learning.module_id` |
| `GET` | `/modules/{module_id}/translation` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | SELECT | `assessment_master.module_id`<br>`document_masters.language_id`<br>`document_masters.module_id`<br>`drop_bucket_masters.language_id`<br>`language_master.language_id`<br>`match_making_masters.language_id` |
| `GET` | `/modules/modules/{module_id}/post-assessments` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | SELECT | `assessment_master.module_id`<br>`document_masters.module_id`<br>`module_masters.module_id`<br>`post_session_assessment.module_id`<br>`pre_session_assessment.module_id`<br>`self_paced_learning.module_id` |
| `GET` | `/modules/modules/{module_id}/pre-assessments` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | SELECT | `assessment_master.module_id`<br>`document_masters.module_id`<br>`module_masters.module_id`<br>`post_session_assessment.module_id`<br>`pre_session_assessment.module_id`<br>`self_paced_learning.module_id` |
| `GET` | `/modules/assessments/{assessment_id}/scqs` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | SELECT | `assessment_mapping.assessment_id`<br>`assessment_master.assessment_id`<br>`document_masters.language_id`<br>`drop_bucket_masters.language_id`<br>`language_master.language_id`<br>`match_making_masters.language_id` |
| `GET` | `/modules/assessments/{assessment_id}/mcqs` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | SELECT | `assessment_mapping.assessment_id`<br>`assessment_master.assessment_id`<br>`document_masters.language_id`<br>`drop_bucket_masters.language_id`<br>`language_master.language_id`<br>`match_making_masters.language_id` |
| `GET` | `/modules/assessments/{assessment_id}/match-makings` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | SELECT | `assessment_mapping.assessment_id`<br>`assessment_master.assessment_id`<br>`document_masters.language_id`<br>`drop_bucket_masters.language_id`<br>`language_master.language_id`<br>`match_making_masters.language_id` |
| `GET` | `/modules/assessments/{assessment_id}/drop-buckets` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | SELECT | `assessment_mapping.assessment_id`<br>`assessment_master.assessment_id`<br>`document_masters.language_id`<br>`drop_bucket_masters.language_id`<br>`language_master.language_id`<br>`match_making_masters.language_id` |
| `POST` | `/modules/assessment-mapping` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | INSERT | Primary Keys / Foreign Keys |
| `GET` | `/modules/main-content/topics/{module_id}` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | SELECT | `assessment_master.module_id`<br>`document_masters.module_id`<br>`module_masters.module_id`<br>`post_session_assessment.module_id`<br>`pre_session_assessment.module_id`<br>`self_paced_learning.module_id` |
| `GET` | `/modules/main-content/documents` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | SELECT | Primary Keys / Foreign Keys |
| `POST` | `/modules/main-content` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | INSERT | Primary Keys / Foreign Keys |
| `GET` | `/modules/main-content/{module_id}` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | SELECT | `assessment_master.module_id`<br>`document_masters.language_id`<br>`document_masters.module_id`<br>`drop_bucket_masters.language_id`<br>`language_master.language_id`<br>`match_making_masters.language_id` |
| `POST` | `/modules/self-paced` | Module Master | None | INSERT | Primary Keys / Foreign Keys |
| `GET` | `/modules/self-paced/{module_id}` | Module Master | None | SELECT | Primary Keys / Foreign Keys |
| `PATCH` | `/modules/main-content/{self_paced_learning_id}/deactivate` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | UPDATE | `document_masters.self_paced_learning`<br>`module_masters.self_paced_learning`<br>`self_paced_learning.self_paced_learning_id` |
| `PATCH` | `/modules/main-content/{self_paced_learning_id}/activate` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | UPDATE | `document_masters.self_paced_learning`<br>`module_masters.self_paced_learning`<br>`self_paced_learning.self_paced_learning_id` |
| `PATCH` | `/modules/assessment-mapping/deactivate` | Module Master | `assessment_mapping`<br>`assessment_master`<br>`document_masters`<br>`drop_bucket_masters`<br>`language_master`<br>`match_making_masters`<br>`mcq_master`<br>`module_masters`<br>`module_type`<br>`post_session_assessment`<br>`pre_session_assessment`<br>`scq_master`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master` | UPDATE | Primary Keys / Foreign Keys |
| `GET` | `/pdf-masters` | PDF Master | `language_master`<br>`pdf_masters` | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/pdf-masters/export/csv` | PDF Master | None | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/pdf-masters/{pdf_id}/archived-versions` | PDF Master | `language_master`<br>`pdf_masters` | SELECT | `pdf_masters.pdf_id` |
| `GET` | `/pdf-masters/{pdf_id}` | PDF Master | `language_master`<br>`pdf_masters` | SELECT | `pdf_masters.pdf_id` |
| `POST` | `/pdf-masters` | PDF Master | `language_master`<br>`pdf_masters` | INSERT | `language_master.language_id`<br>`pdf_masters.cloud_url`<br>`pdf_masters.language_id`<br>`pdf_masters.pdf_description`<br>`pdf_masters.pdf_name`<br>`pdf_masters.status` |
| `PUT` | `/pdf-masters/{pdf_id}` | PDF Master | `language_master`<br>`pdf_masters` | UPDATE | `language_master.language_id`<br>`pdf_masters.cloud_url`<br>`pdf_masters.language_id`<br>`pdf_masters.pdf_description`<br>`pdf_masters.pdf_id`<br>`pdf_masters.pdf_name` |
| `DELETE` | `/pdf-masters/{pdf_id}` | PDF Master | `language_master`<br>`pdf_masters` | DELETE | `pdf_masters.pdf_id` |
| `GET` | `/ppt-masters` | PPT Master | `language_master`<br>`ppt_masters` | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/ppt-masters/export/csv` | PPT Master | None | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/ppt-masters/{ppt_id}/archived-versions` | PPT Master | `language_master`<br>`ppt_masters` | SELECT | `ppt_masters.ppt_id` |
| `GET` | `/ppt-masters/{ppt_id}` | PPT Master | `language_master`<br>`ppt_masters` | SELECT | `ppt_masters.ppt_id` |
| `POST` | `/ppt-masters` | PPT Master | `language_master`<br>`ppt_masters` | INSERT | `language_master.language_id`<br>`ppt_masters.cloud_url`<br>`ppt_masters.language_id`<br>`ppt_masters.ppt_description`<br>`ppt_masters.ppt_name`<br>`ppt_masters.status` |
| `PUT` | `/ppt-masters/{ppt_id}` | PPT Master | `language_master`<br>`ppt_masters` | UPDATE | `language_master.language_id`<br>`ppt_masters.cloud_url`<br>`ppt_masters.language_id`<br>`ppt_masters.ppt_description`<br>`ppt_masters.ppt_id`<br>`ppt_masters.ppt_name` |
| `DELETE` | `/ppt-masters/{ppt_id}` | PPT Master | `language_master`<br>`ppt_masters` | DELETE | `ppt_masters.ppt_id` |
| `GET` | `/video-masters` | VIDEO Master | `language_master`<br>`video_masters` | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/video-masters/export/csv` | VIDEO Master | None | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/video-masters/{video_id}/archived-versions` | VIDEO Master | `language_master`<br>`video_masters` | SELECT | `video_masters.video_id` |
| `GET` | `/video-masters/{video_id}` | VIDEO Master | `language_master`<br>`video_masters` | SELECT | `video_masters.video_id` |
| `POST` | `/video-masters` | VIDEO Master | `language_master`<br>`video_masters` | INSERT | `language_master.language_id`<br>`video_masters.language_id`<br>`video_masters.status`<br>`video_masters.video_description`<br>`video_masters.video_name`<br>`video_masters.youtube_url` |
| `PUT` | `/video-masters/{video_id}` | VIDEO Master | `language_master`<br>`video_masters` | UPDATE | `language_master.language_id`<br>`video_masters.language_id`<br>`video_masters.status`<br>`video_masters.video_description`<br>`video_masters.video_id`<br>`video_masters.video_name` |
| `DELETE` | `/video-masters/{video_id}` | VIDEO Master | `language_master`<br>`video_masters` | DELETE | `video_masters.video_id` |
| `GET` | `/dashboard` | Dashboard | `users` | SELECT | `users.centre_id`<br>`users.id` |
| `GET` | `/dashboard/trainee-status/details` | Dashboard | `users` | SELECT | `users.centre_id`<br>`users.id`<br>`users.status` |
| `GET` | `/dashboard/state-wise-trainee-status` | Dashboard | `users` | SELECT | `users.centre_id`<br>`users.id`<br>`users.status` |
| `GET` | `/dashboard/state-wise-participants` | Dashboard | `users` | SELECT | `users.centre_id`<br>`users.id` |
| `GET` | `/dashboard/district-wise-participants` | Dashboard | `users` | SELECT | `users.centre_id`<br>`users.id` |
| `GET` | `/dashboard/gender-distribution` | Dashboard | `users` | SELECT | `users.centre_id`<br>`users.id` |
| `GET` | `/dashboard/age-group-distribution` | Dashboard | `users` | SELECT | `users.centre_id`<br>`users.id` |
| `GET` | `/dashboard/state-wise-centres` | Dashboard | `users` | SELECT | `users.centre_id`<br>`users.id` |
| `GET` | `/dashboard/module-wise-performance` | Dashboard | `users` | SELECT | `users.centre_id`<br>`users.id` |
| `GET` | `/dashboard/document-type-distribution` | Dashboard | `assessment_master`<br>`batch_masters`<br>`batch_participant`<br>`centre_masters`<br>`course_masters`<br>`district_master`<br>`document_categories`<br>`document_masters`<br>`login_logs`<br>`module_masters`<br>`participant_dbs`<br>`participant_mcqs`<br>`participant_mm`<br>`participant_module`<br>`participant_scs`<br>`participantmasters`<br>`post_session_assessment`<br>`state_master`<br>`users` | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/dashboard/monthly-trending-modules` | Dashboard | `users` | SELECT | `users.centre_id`<br>`users.id`<br>`users.status` |
| `GET` | `/dashboard/module-assignment-usage` | Dashboard | `users` | SELECT | `users.centre_id`<br>`users.id` |
| `GET` | `/dashboard/monthly-logins/details` | Dashboard | `users` | SELECT | `users.centre_id`<br>`users.id` |
| `GET` | `/dashboard/centre-wise-trainees` | Dashboard | `users` | SELECT | `users.centre_id`<br>`users.id`<br>`users.status` |
| `GET` | `/dashboard/state-wise-trainees` | Dashboard | `users` | SELECT | `users.centre_id`<br>`users.id`<br>`users.status` |
| `GET` | `/mcqs/` | Assessment - MCQ | None | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/mcqs/export` | Assessment - MCQ | None | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/mcqs/{parent_id}` | Assessment - MCQ | None | SELECT | Primary Keys / Foreign Keys |
| `PUT` | `/mcqs/{parent_id}/translation` | Assessment - MCQ | None | UPDATE | Primary Keys / Foreign Keys |
| `POST` | `/mcqs/` | Assessment - MCQ | None | INSERT | Primary Keys / Foreign Keys |
| `PUT` | `/mcqs/{mcq_id}` | Assessment - MCQ | None | UPDATE | Primary Keys / Foreign Keys |
| `DELETE` | `/mcqs/{mcq_id}` | Assessment - MCQ | None | DELETE | Primary Keys / Foreign Keys |
| `GET` | `/scqs/export` | Assessment - SCQ | None | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/scqs/` | Assessment - SCQ | None | SELECT | Primary Keys / Foreign Keys |
| `PUT` | `/scqs/{parent_id}/translation` | Assessment - SCQ | None | UPDATE | Primary Keys / Foreign Keys |
| `GET` | `/scqs/{parent_id}` | Assessment - SCQ | None | SELECT | Primary Keys / Foreign Keys |
| `POST` | `/scqs/` | Assessment - SCQ | None | INSERT | Primary Keys / Foreign Keys |
| `PUT` | `/scqs/{scq_id}` | Assessment - SCQ | None | UPDATE | Primary Keys / Foreign Keys |
| `DELETE` | `/scqs/{scq_id}` | Assessment - SCQ | None | DELETE | Primary Keys / Foreign Keys |
| `GET` | `/drop-buckets/` | Assessment - Drop Bucket | None | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/drop-buckets/{parent_id}/all` | Assessment - Drop Bucket | None | SELECT | Primary Keys / Foreign Keys |
| `PUT` | `/drop-buckets/{parent_id}/all` | Assessment - Drop Bucket | None | UPDATE | Primary Keys / Foreign Keys |
| `GET` | `/drop-buckets/{drop_bucket_id}/items` | Assessment - Drop Bucket | `drop_buckets` | SELECT | `drop_buckets.bucket_id`<br>`drop_buckets.drop_bucket_id`<br>`drop_buckets.language_id` |
| `GET` | `/drop-buckets/{parent_id}` | Assessment - Drop Bucket | None | SELECT | Primary Keys / Foreign Keys |
| `POST` | `/drop-buckets/` | Assessment - Drop Bucket | None | INSERT | Primary Keys / Foreign Keys |
| `PUT` | `/drop-buckets/{drop_bucket_id}` | Assessment - Drop Bucket | `drop_buckets` | UPDATE | `drop_buckets.bucket_id`<br>`drop_buckets.drop_bucket_id` |
| `DELETE` | `/drop-buckets/{drop_bucket_id}` | Assessment - Drop Bucket | `drop_buckets` | DELETE | `drop_buckets.bucket_id`<br>`drop_buckets.drop_bucket_id` |
| `GET` | `/drop-buckets/buckets/{bucket_id}/items` | Assessment - Drop Bucket | None | SELECT | Primary Keys / Foreign Keys |
| `PUT` | `/drop-buckets/buckets/{bucket_id}/items` | Assessment - Drop Bucket | None | UPDATE | Primary Keys / Foreign Keys |
| `PUT` | `/drop-buckets/{parent_id}/translation` | Assessment - Drop Bucket | None | UPDATE | Primary Keys / Foreign Keys |
| `GET` | `/match-making/` | Match Making | None | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/match-making/{parent_id}` | Match Making | None | SELECT | Primary Keys / Foreign Keys |
| `POST` | `/match-making/` | Match Making | None | INSERT | Primary Keys / Foreign Keys |
| `PUT` | `/match-making/{match_making_id}` | Match Making | None | UPDATE | Primary Keys / Foreign Keys |
| `DELETE` | `/match-making/{match_making_id}` | Match Making | None | DELETE | Primary Keys / Foreign Keys |
| `GET` | `/match-making/{match_making_id}/left-items` | Match Making | None | SELECT | Primary Keys / Foreign Keys |
| `POST` | `/match-making/{match_making_id}/left-items` | Match Making | None | INSERT | Primary Keys / Foreign Keys |
| `GET` | `/match-making/left-items/{match_left_id}` | Match Making | None | SELECT | Primary Keys / Foreign Keys |
| `PUT` | `/match-making/left-items/{match_left_id}` | Match Making | None | UPDATE | Primary Keys / Foreign Keys |
| `DELETE` | `/match-making/left-items/{match_left_id}` | Match Making | None | DELETE | Primary Keys / Foreign Keys |
| `GET` | `/match-making/{match_making_id}/right-items` | Match Making | None | SELECT | Primary Keys / Foreign Keys |
| `POST` | `/match-making/{match_making_id}/right-items` | Match Making | None | INSERT | Primary Keys / Foreign Keys |
| `GET` | `/match-making/right-items/{match_right_id}` | Match Making | None | SELECT | Primary Keys / Foreign Keys |
| `PUT` | `/match-making/right-items/{match_right_id}` | Match Making | None | UPDATE | Primary Keys / Foreign Keys |
| `DELETE` | `/match-making/right-items/{match_right_id}` | Match Making | None | DELETE | Primary Keys / Foreign Keys |
| `GET` | `/match-making/{match_making_id}/correct-answers` | Match Making | None | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/match-making/correct-answers/{match_correct_answers_id}` | Match Making | `match_correct_answers` | SELECT | `match_correct_answers.match_correct_answers_id` |
| `POST` | `/match-making/{match_making_id}/correct-answers` | Match Making | None | INSERT | Primary Keys / Foreign Keys |
| `PUT` | `/match-making/correct-answers/{match_correct_answers_id}` | Match Making | `match_correct_answers` | UPDATE | `match_correct_answers.match_correct_answers_id` |
| `DELETE` | `/match-making/correct-answers/{match_correct_answers_id}` | Match Making | `match_correct_answers` | DELETE | `match_correct_answers.match_correct_answers_id` |
| `POST` | `/assessment/upload-image` | Assessment - Uploads | None | INSERT | Primary Keys / Foreign Keys |
| `POST` | `/mobile/auth/login` | Mobile Authentication | `participantmasters` | INSERT | Primary Keys / Foreign Keys |
| `POST` | `/mobile/auth/refresh` | Mobile Authentication | None | INSERT | Primary Keys / Foreign Keys |
| `POST` | `/mobile/auth/logout` | Mobile Authentication | None | INSERT | Primary Keys / Foreign Keys |
| `GET` | `/mobile/auth/me` | Mobile Authentication | None | SELECT | Primary Keys / Foreign Keys |
| `POST` | `/mobile/auth/forgot-password` | Mobile Authentication | None | INSERT | Primary Keys / Foreign Keys |
| `POST` | `/mobile/auth/reset-password` | Mobile Authentication | None | INSERT | Primary Keys / Foreign Keys |
| `POST` | `/mobile/auth/change-password` | Mobile Authentication | None | INSERT | Primary Keys / Foreign Keys |
| `GET` | `/mobile/dashboard/stats` | Mobile Dashboard | None | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/mobile/dashboard/tips` | Mobile Dashboard | None | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/media/pptx/info` | Mobile Media | None | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/media/pptx/slide/{number}` | Mobile Media | None | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/media/{file_path:path}` | Mobile Media | None | SELECT | Primary Keys / Foreign Keys |
| `POST` | `/profile/photo` | Mobile Profile | None | INSERT | Primary Keys / Foreign Keys |
| `GET` | `/assessment/{module_id}` | Mobile Assessment | None | SELECT | Primary Keys / Foreign Keys |
| `POST` | `/assessment/{module_id}/submit` | Mobile Assessment | None | INSERT | Primary Keys / Foreign Keys |
| `POST` | `/activity/time-spent` | Mobile Activity | None | INSERT | Primary Keys / Foreign Keys |
| `POST` | `/activity/module-time` | Mobile Activity | None | INSERT | Primary Keys / Foreign Keys |
| `GET` | `/activity/video-questions/{video_id}` | Mobile Activity | None | SELECT | Primary Keys / Foreign Keys |
| `POST` | `/activity/video-question` | Mobile Activity | None | INSERT | Primary Keys / Foreign Keys |
| `GET` | `/mobile/module/list` | Mobile Module | None | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/mobile/module/types` | Mobile Module | `language_master`<br>`module_masters`<br>`module_type`<br>`participant_module` | SELECT | `module_masters.module_type`<br>`module_type.module_type` |
| `GET` | `/mobile/module/languages` | Mobile Module | `language_master`<br>`module_masters`<br>`module_type`<br>`participant_module` | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/mobile/module/{module_id}/topics` | Mobile Module | `assessment_mapping`<br>`document_masters`<br>`module_masters`<br>`pdf_masters`<br>`ppt_masters`<br>`pre_session_assessment`<br>`self_paced_learning`<br>`topic_mapping`<br>`topic_master`<br>`video_masters` | SELECT | `document_masters.language_id`<br>`document_masters.module_id`<br>`module_masters.language_id`<br>`module_masters.module_id`<br>`pdf_masters.language_id`<br>`ppt_masters.language_id` |
| `POST` | `/mobile/feedback/submit` | Mobile Feedback | None | INSERT | Primary Keys / Foreign Keys |
| `GET` | `/mobile/feedback/form` | Mobile Feedback | `participant_feedback` | SELECT | Primary Keys / Foreign Keys |
| `GET` | `/mobile/feedback/questions` | Mobile Feedback | None | SELECT | Primary Keys / Foreign Keys |

---

## 4. Key Relationships and Foreign Key Constraints

The following core foreign key relationships are strictly enforced by the schema:

### Table `batch_masters`
- `centre_id` references `centre_masters.centre_id`

### Table `batch_participant`
- `batch_id` references `batch_masters.batch_id`
- `participant_id` references `participantmasters.participant_id`

### Table `district_master`
- `state_lgd_code` references `state_master.state_lgd_code`

### Table `drop_bucket_items`
- `bucket_id` references `drop_buckets.bucket_id`

### Table `drop_buckets`
- `drop_bucket_id` references `drop_bucket_masters.drop_bucket_id`

### Table `entity_audit_logs`
- `user_id` references `users.id`

### Table `match_correct_answers`
- `match_right_id` references `match_right_items.match_right_id`
- `match_left_id` references `match_left_items.match_left_id`
- `match_making_id` references `match_making_masters.match_making_id`

### Table `match_left_items`
- `match_making_id` references `match_making_masters.match_making_id`

### Table `match_right_items`
- `match_making_id` references `match_making_masters.match_making_id`

### Table `mcq_question_options`
- `mcq_id` references `mcq_master.mcq_id`

### Table `participant_mood_answers`
- `question_id` references `mood_questions_master.question_id`
- `selected_option_id` references `question_options.option_id`

### Table `question_options`
- `question_id` references `mood_questions_master.question_id`

### Table `scq_question_options`
- `scq_id` references `scq_master.scq_id`

