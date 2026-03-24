--
-- PostgreSQL database dump
--

\restrict h0Dbt4MQHY4GOngjk3sNSlhGhR24b30dc7MdDYlULry4Dtk2oz7Ps2vCZP8I4Y1

-- Dumped from database version 14.19 (Ubuntu 14.19-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.19 (Ubuntu 14.19-0ubuntu0.22.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: channel_posts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.channel_posts (
    id integer NOT NULL,
    user_id bigint,
    audio_url text,
    comment text,
    posted_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    message_id integer
);


ALTER TABLE public.channel_posts OWNER TO postgres;

--
-- Name: channel_posts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.channel_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.channel_posts_id_seq OWNER TO postgres;

--
-- Name: channel_posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.channel_posts_id_seq OWNED BY public.channel_posts.id;


--
-- Name: generations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.generations (
    id integer NOT NULL,
    user_id bigint,
    task_id text,
    prompt text,
    audio_url text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_free boolean DEFAULT false,
    custom_mode boolean DEFAULT false,
    status text DEFAULT 'pending'::text,
    notified boolean DEFAULT false,
    completed_at timestamp without time zone
);


ALTER TABLE public.generations OWNER TO postgres;

--
-- Name: generations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.generations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.generations_id_seq OWNER TO postgres;

--
-- Name: generations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.generations_id_seq OWNED BY public.generations.id;


--
-- Name: payments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.payments (
    id integer NOT NULL,
    user_id bigint,
    amount real,
    status text,
    payment_id text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.payments OWNER TO postgres;

--
-- Name: payments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.payments_id_seq OWNER TO postgres;

--
-- Name: payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.payments_id_seq OWNED BY public.payments.id;


--
-- Name: referrals; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.referrals (
    id integer NOT NULL,
    referrer_id bigint,
    referred_id bigint,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    bonus_applied boolean DEFAULT false
);


ALTER TABLE public.referrals OWNER TO postgres;

--
-- Name: referrals_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.referrals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.referrals_id_seq OWNER TO postgres;

--
-- Name: referrals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.referrals_id_seq OWNED BY public.referrals.id;


--
-- Name: user_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_tokens (
    user_id bigint NOT NULL,
    access_token text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_tokens OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id bigint NOT NULL,
    username text,
    first_name text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    free_generation_used boolean DEFAULT false,
    invited_by bigint,
    balance integer DEFAULT 0
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: channel_posts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.channel_posts ALTER COLUMN id SET DEFAULT nextval('public.channel_posts_id_seq'::regclass);


--
-- Name: generations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.generations ALTER COLUMN id SET DEFAULT nextval('public.generations_id_seq'::regclass);


--
-- Name: payments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments ALTER COLUMN id SET DEFAULT nextval('public.payments_id_seq'::regclass);


--
-- Name: referrals id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.referrals ALTER COLUMN id SET DEFAULT nextval('public.referrals_id_seq'::regclass);


--
-- Data for Name: channel_posts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.channel_posts (id, user_id, audio_url, comment, posted_at, message_id) FROM stdin;
\.


--
-- Data for Name: generations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.generations (id, user_id, task_id, prompt, audio_url, created_at, is_free, custom_mode, status, notified, completed_at) FROM stdin;
1	338544009	test_monitor_final_002	Текст песни: Финальный тест работающего мониторинга	https://example.com/test-success.mp3	2025-11-22 21:24:25.088268	f	f	completed	t	\N
2	338544009	test_auto_monitor_001	Текст песни: Тест автоматического мониторинга	https://example.com/auto-test.mp3	2025-11-23 08:37:15.778663	f	f	completed	t	\N
3	338544009	final_test_main_loop	Текст песни: Финальный тест работающего мониторинга в основном event loop	https://example.com/final-success.mp3	2025-11-23 08:42:42.911495	f	f	completed	t	\N
4	338544009	test_new_task	Тестовая задача	https://example.com/test-new.mp3	2025-11-23 15:51:17.824272	f	f	completed	t	\N
5	338544009	b1669574-f774-43d8-b736-651cc9f2822b	Тестовая генерация	https://musicfile.api.box/YjdiMDJlMWEtZGJkYy00NmIyLWJjZTMtYzQ0MGQ0NzE4MjVj.mp3	2025-11-23 16:02:08.577195	f	f	completed	t	\N
6	338544009	last_celery_task	Последняя генерация	https://musicfile.api.box/latest_generation.mp3	2025-11-24 17:53:30.189639	f	f	completed	t	\N
7	338544009	1ec56c46-9a66-43fc-a845-4cce0ee16eea	Тест с явной очередью generation	\N	2025-11-24 22:19:34.73923	f	f	processing	f	\N
8	338544009	1ec56c46-9a66-43fc-a845-4cce0ee16eea	Тест с явной очередью generation	\N	2025-11-24 22:19:36.745056	f	f	completed	f	\N
9	338544009	f5cf3a58-9f8b-4e7f-9f55-24bebf5018ae	Стиль: Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.		2025-11-24 23:28:39.602698	f	f	pending	f	\N
10	338544009	3a32c299-f06c-4b09-b78b-d556ecee88bf	Стиль: Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.		2025-11-24 23:31:01.569823	f	f	pending	f	\N
11	338544009	83bfb8b6-b8ee-4d29-a05d-c58f0e5deee6	Тест с prefork pool и psycopg2	\N	2025-11-24 23:32:50.411108	f	f	processing	f	\N
12	338544009	f9ae873a-fbca-4ebd-94b9-97747ced91b1	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:32:50.412841	f	f	processing	f	\N
13	338544009	7c67a5ac-a540-4041-9b73-dfcae65c2b6b	Тест с работающим пулом БД	\N	2025-11-24 23:32:50.411924	f	f	processing	f	\N
14	338544009	9659c7ed-d53b-4885-b8ba-9b3e79ce4fbc	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала	\N	2025-11-24 23:32:50.413649	f	f	processing	f	\N
15	338544009	f9ae873a-fbca-4ebd-94b9-97747ced91b1	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:32:52.417219	f	f	completed	f	\N
16	338544009	83bfb8b6-b8ee-4d29-a05d-c58f0e5deee6	Тест с prefork pool и psycopg2	\N	2025-11-24 23:32:52.417195	f	f	completed	f	\N
17	338544009	9659c7ed-d53b-4885-b8ba-9b3e79ce4fbc	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала	\N	2025-11-24 23:32:52.417904	f	f	completed	f	\N
18	338544009	7c67a5ac-a540-4041-9b73-dfcae65c2b6b	Тест с работающим пулом БД	\N	2025-11-24 23:32:52.417839	f	f	completed	f	\N
19	338544009	f5cf3a58-9f8b-4e7f-9f55-24bebf5018ae	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:32:52.423701	f	f	processing	f	\N
20	338544009	3a32c299-f06c-4b09-b78b-d556ecee88bf	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:32:52.423797	f	f	processing	f	\N
21	338544009	3a32c299-f06c-4b09-b78b-d556ecee88bf	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:32:54.426075	f	f	completed	f	\N
22	338544009	f5cf3a58-9f8b-4e7f-9f55-24bebf5018ae	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:32:54.427628	f	f	completed	f	\N
23	338544009	c8c35695-0d20-4f85-b9dd-dc5628cb0b62	Стиль: Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.		2025-11-24 23:33:51.731974	f	f	pending	f	\N
24	338544009	c8c35695-0d20-4f85-b9dd-dc5628cb0b62	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:33:51.733839	f	f	processing	f	\N
25	338544009	c8c35695-0d20-4f85-b9dd-dc5628cb0b62	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:33:53.73705	f	f	completed	f	\N
26	338544009	7dd2e5c5-fa9d-4a7b-be80-63b2fa64bc10	Стиль: Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.		2025-11-24 23:37:29.427192	f	f	pending	f	\N
27	338544009	7dd2e5c5-fa9d-4a7b-be80-63b2fa64bc10	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:37:29.428136	f	f	processing	f	\N
28	338544009	7dd2e5c5-fa9d-4a7b-be80-63b2fa64bc10	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:37:31.431758	f	f	completed	f	\N
29	338544009	79c921e1-d4af-4b70-a966-4adf2d9872ba	Стиль: Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.		2025-11-24 23:48:25.683105	f	f	pending	f	\N
30	338544009	79c921e1-d4af-4b70-a966-4adf2d9872ba	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:48:25.68431	f	f	processing	f	\N
31	338544009	79c921e1-d4af-4b70-a966-4adf2d9872ba	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:48:27.689888	f	f	completed	f	\N
32	338544009	79c921e1-d4af-4b70-a966-4adf2d9872ba	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	https://musicfile.api.box/music_79c921e1.mp3	2025-11-24 23:48:27.691539	f	f	completed	f	\N
33	338544009	0fc7b1b5-6a2c-47e3-99e8-046375d3904c	Стиль: Жеткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.		2025-11-25 12:09:54.843972	f	f	pending	f	\N
67	338544009	ba0c6e22-572a-4f09-b412-6f8be9f7b6ca	/start	https://musicfile.api.box/MDZjMzQxZjgtYTUwZi00MDJjLWEwZDctNWU3ZTM1MjYxNmNk.mp3	2025-11-26 17:55:37.76695	f	f	completed	f	\N
34	338544009	0fc7b1b5-6a2c-47e3-99e8-046375d3904c	Жеткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-25 12:09:54.846355	f	f	processing	f	\N
35	338544009	0fc7b1b5-6a2c-47e3-99e8-046375d3904c	Жеткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-25 12:09:56.851573	f	f	completed	f	\N
36	338544009	0fc7b1b5-6a2c-47e3-99e8-046375d3904c	Жеткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	https://musicfile.api.box/music_0fc7b1b5.mp3	2025-11-25 12:09:56.853198	f	f	completed	f	\N
37	338544009	92fd8881-df87-4442-8094-ff0343af9aa9	Жесткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-25 12:11:58.138423	f	f	processing	f	\N
39	338544009	92fd8881-df87-4442-8094-ff0343af9aa9	Жесткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-25 12:12:00.142893	f	f	completed	f	\N
40	338544009	92fd8881-df87-4442-8094-ff0343af9aa9	Жесткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	https://musicfile.api.box/music_92fd8881.mp3	2025-11-25 12:12:00.144209	f	f	completed	f	\N
42	338544009	b6aba2c8-dd94-4c54-9ed3-4f90d65d6e87	Жесткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-25 12:13:49.738582	f	f	processing	f	\N
43	338544009	b6aba2c8-dd94-4c54-9ed3-4f90d65d6e87	Жесткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-25 12:13:51.741839	f	f	completed	f	\N
44	338544009	b6aba2c8-dd94-4c54-9ed3-4f90d65d6e87	Жесткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	https://musicfile.api.box/music_b6aba2c8.mp3	2025-11-25 12:13:51.743312	f	f	completed	f	\N
38	338544009	92fd8881-df87-4442-8094-ff0343af9aa9	Стиль: Жесткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.		2025-11-25 12:11:58.138751	f	f	pending	f	\N
41	338544009	b6aba2c8-dd94-4c54-9ed3-4f90d65d6e87	Стиль: Жесткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.		2025-11-25 12:13:49.737957	f	f	pending	f	\N
45	338544009	b0e8e6df-2e66-4254-af91-2b95c2763b4e	Стиль: Жесткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.		2025-11-25 12:15:09.994833	f	f	pending	f	\N
46	338544009	102c31e4-0ef9-4931-bd01-379db4cd7e99	Стиль: Жесткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.		2025-11-25 12:16:08.210566	f	f	pending	f	\N
47	338544009	7bb827ac-75f4-4252-8b56-e66cfd2ece37	Стиль: Жесткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.		2025-11-25 15:56:43.09223	f	f	pending	f	\N
48	338544009	fd0876cf-eb68-41a3-96d4-cdfa7e063f27	Тестовая генерация с инициализацией БД	\N	2025-11-25 23:27:04.329963	f	f	processing	t	\N
49	338544009	fd0876cf-eb68-41a3-96d4-cdfa7e063f27	Тестовая генерация с инициализацией БД	https://musicfile.api.box/NzQ2Y2MyZWMtNGYwYi00OWNlLTg0ZDYtODdlMWY4YWMxZWVm.mp3	2025-11-25 23:29:54.723968	f	f	completed	t	\N
50	338544009	59b42888-c27a-4b5d-9811-951a1c477a12	Стиль: Сначала соло гитара, потом бас гитара, потом ритм гитара, потом пауза, ударные барабаны, потом все инструменты вместе. Энергия, драйв.		2025-11-26 08:01:00.393496	f	f	pending	t	\N
51	338544009	59b42888-c27a-4b5d-9811-951a1c477a12	Сначала соло гитара, потом бас гитара, потом ритм гитара, потом пауза, ударные барабаны, потом все инструменты вместе. Энергия, драйв.	\N	2025-11-26 11:50:19.820669	f	f	processing	t	\N
52	338544009	59b42888-c27a-4b5d-9811-951a1c477a12	Сначала соло гитара, потом бас гитара, потом ритм гитара, потом пауза, ударные барабаны, потом все инструменты вместе. Энергия, драйв.	https://musicfile.api.box/Njg4ZDhhMTAtM2NjNS00OTc1LWE1NGUtOThiYWUzZjgwN2I3.mp3	2025-11-26 11:52:18.300111	f	f	completed	t	\N
53	338544009	a1182695-e5f4-47b0-a26c-f016198ab295	Стиль: Рок гитара + барабаны + фортепиано. Очень врывная музыка с затиханием и снова взрывом. Для тренажерного зала.		2025-11-26 13:04:28.151673	f	f	pending	f	\N
54	338544009	a1182695-e5f4-47b0-a26c-f016198ab295	Рок гитара + барабаны + фортепиано. Очень врывная музыка с затиханием и снова взрывом. Для тренажерного зала.	\N	2025-11-26 13:04:28.153434	f	f	processing	f	\N
55	338544009	a1182695-e5f4-47b0-a26c-f016198ab295	Рок гитара + барабаны + фортепиано. Очень врывная музыка с затиханием и снова взрывом. Для тренажерного зала.	https://musicfile.api.box/ZGFmMGRlYzUtMDEzMi00MTZkLWJlYmYtZTliNzhkZmI5YThj.mp3	2025-11-26 13:06:14.604649	f	f	completed	f	\N
56	338544009	594f8ce5-7106-44e8-a13c-f4285363d1d2	Стиль: Рок гитара + барабаны + фортепиано. Очень врывная музыка с затиханием и снова взрывом. Для тренажерного зала.		2025-11-26 13:11:35.309611	f	f	pending	f	\N
57	338544009	594f8ce5-7106-44e8-a13c-f4285363d1d2	Рок гитара + барабаны + фортепиано. Очень врывная музыка с затиханием и снова взрывом. Для тренажерного зала.	\N	2025-11-26 13:11:35.310529	f	f	processing	f	\N
58	338544009	594f8ce5-7106-44e8-a13c-f4285363d1d2	Рок гитара + барабаны + фортепиано. Очень врывная музыка с затиханием и снова взрывом. Для тренажерного зала.	https://musicfile.api.box/NzNiOGMyODgtY2M4ZS00ZGExLWFjMmUtMWI1MmJlZjBiNGM0.mp3	2025-11-26 13:13:19.831455	f	f	completed	f	\N
59	338544009	b0810144-6949-4607-96a7-d6967d29dd72	Стиль: романс. Текст: Ты, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!		2025-11-26 13:56:39.937626	f	f	pending	f	\N
60	338544009	b0810144-6949-4607-96a7-d6967d29dd72	Стиль: Ты, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!. Текст песни: романс	\N	2025-11-26 13:56:39.938578	f	f	processing	f	\N
61	338544009	b0810144-6949-4607-96a7-d6967d29dd72	Стиль: Ты, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!. Текст песни: романс	https://musicfile.api.box/YmFiODhmYWQtZTgyMy00ZDhmLWFjNjktNjU2YjA3NDc1Nzc1.mp3	2025-11-26 13:58:47.411715	f	f	completed	f	\N
62	338544009	00473238-984e-4bca-a48f-3c0364350d02	Стиль: Рок исполнение. Текст: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!		2025-11-26 15:41:55.025231	f	f	pending	f	\N
63	338544009	00473238-984e-4bca-a48f-3c0364350d02	Стиль: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!. Текст песни: Рок исполнение	\N	2025-11-26 15:41:55.028192	f	f	processing	f	\N
64	338544009	00473238-984e-4bca-a48f-3c0364350d02	Стиль: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!. Текст песни: Рок исполнение	https://musicfile.api.box/N2Q4ZjI5ZTUtYTZkYS00MTg5LWI4MTQtY2Q5M2UxYTI0ZjM2.mp3	2025-11-26 15:44:54.837636	f	f	completed	f	\N
65	338544009	ba0c6e22-572a-4f09-b412-6f8be9f7b6ca	/start	\N	2025-11-26 17:53:51.903618	f	f	processing	f	\N
66	338544009	ba0c6e22-572a-4f09-b412-6f8be9f7b6ca	Стиль: /start		2025-11-26 17:53:51.903755	f	f	pending	f	\N
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.payments (id, user_id, amount, status, payment_id, created_at) FROM stdin;
\.


--
-- Data for Name: referrals; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.referrals (id, referrer_id, referred_id, created_at, bonus_applied) FROM stdin;
\.


--
-- Data for Name: user_tokens; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_tokens (user_id, access_token, created_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (user_id, username, first_name, created_at, free_generation_used, invited_by, balance) FROM stdin;
7108317408	aaandrey23	Андрей	2025-11-19 07:33:33	f	\N	0
8341832184	\N	Ирина	2025-11-16 10:49:17	f	\N	0
338544009	Igor_Bibin	Игорь	2025-11-16 08:17:43	f	\N	3
\.


--
-- Name: channel_posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.channel_posts_id_seq', 1, false);


--
-- Name: generations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.generations_id_seq', 67, true);


--
-- Name: payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.payments_id_seq', 1, false);


--
-- Name: referrals_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.referrals_id_seq', 1, false);


--
-- Name: channel_posts channel_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.channel_posts
    ADD CONSTRAINT channel_posts_pkey PRIMARY KEY (id);


--
-- Name: generations generations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.generations
    ADD CONSTRAINT generations_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: referrals referrals_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.referrals
    ADD CONSTRAINT referrals_pkey PRIMARY KEY (id);


--
-- Name: user_tokens user_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_tokens
    ADD CONSTRAINT user_tokens_pkey PRIMARY KEY (user_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: idx_generations_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_generations_created_at ON public.generations USING btree (created_at);


--
-- Name: idx_generations_notified; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_generations_notified ON public.generations USING btree (notified);


--
-- Name: idx_generations_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_generations_status ON public.generations USING btree (status);


--
-- Name: idx_generations_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_generations_user_id ON public.generations USING btree (user_id);


--
-- Name: idx_payments_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payments_status ON public.payments USING btree (status);


--
-- Name: idx_payments_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payments_user_id ON public.payments USING btree (user_id);


--
-- Name: idx_referrals_referred_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_referrals_referred_id ON public.referrals USING btree (referred_id);


--
-- Name: idx_referrals_referrer_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_referrals_referrer_id ON public.referrals USING btree (referrer_id);


--
-- Name: channel_posts channel_posts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.channel_posts
    ADD CONSTRAINT channel_posts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: generations generations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.generations
    ADD CONSTRAINT generations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: payments payments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: referrals referrals_referred_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.referrals
    ADD CONSTRAINT referrals_referred_id_fkey FOREIGN KEY (referred_id) REFERENCES public.users(user_id);


--
-- Name: referrals referrals_referrer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.referrals
    ADD CONSTRAINT referrals_referrer_id_fkey FOREIGN KEY (referrer_id) REFERENCES public.users(user_id);


--
-- Name: user_tokens user_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_tokens
    ADD CONSTRAINT user_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

GRANT USAGE ON SCHEMA public TO albimusic_user;


--
-- Name: TABLE channel_posts; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.channel_posts TO albimusic_user;


--
-- Name: SEQUENCE channel_posts_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.channel_posts_id_seq TO albimusic_user;


--
-- Name: TABLE generations; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.generations TO albimusic_user;


--
-- Name: SEQUENCE generations_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.generations_id_seq TO albimusic_user;


--
-- Name: TABLE payments; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.payments TO albimusic_user;


--
-- Name: SEQUENCE payments_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.payments_id_seq TO albimusic_user;


--
-- Name: TABLE referrals; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.referrals TO albimusic_user;


--
-- Name: SEQUENCE referrals_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.referrals_id_seq TO albimusic_user;


--
-- Name: TABLE user_tokens; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.user_tokens TO albimusic_user;


--
-- Name: TABLE users; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.users TO albimusic_user;


--
-- PostgreSQL database dump complete
--

\unrestrict h0Dbt4MQHY4GOngjk3sNSlhGhR24b30dc7MdDYlULry4Dtk2oz7Ps2vCZP8I4Y1

