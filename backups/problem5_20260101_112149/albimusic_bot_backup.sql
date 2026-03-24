--
-- PostgreSQL database dump
--

\restrict k1FcP5ZbjV3Ed2dx4bjWlAjiJJte8G10rxbVhaxbZJ5kNUf6xr1Os1IpdmfeYg0

-- Dumped from database version 14.20 (Ubuntu 14.20-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.20 (Ubuntu 14.20-0ubuntu0.22.04.1)

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
142	338544009	563f693c-1335-4c57-b715-1e1806b7d665	Текст песни: Мужской хор\nСтиль: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!	\N	2025-11-28 10:57:32.181305	f	f	failed	f	\N
443	338544009	ad37c94f-de53-4ca8-9cda-b63f1e99b3f1	Мужской хор	https://musicfile.api.box/ZWJmYjFmY2UtMjhiNS00YWQ1LWJkZDYtNzdiMWQ2NzIxNmM2.mp3	2025-12-03 08:50:26.62079	f	f	completed	f	\N
2	338544009	test_auto_monitor_001	Текст песни: Тест автоматического мониторинга	https://example.com/auto-test.mp3	2025-11-23 08:37:15.778663	f	f	completed	t	\N
3	338544009	final_test_main_loop	Текст песни: Финальный тест работающего мониторинга в основном event loop	https://example.com/final-success.mp3	2025-11-23 08:42:42.911495	f	f	completed	t	\N
175	338544009	d2b2f5ae-3c31-487f-bd2e-e19ce76965e0	Мужской хор	https://musicfile.api.box/YzUzZjIzMGEtODMzYS00NTY1LWE3ZGMtNWU2YzU4NDg1YmFk.mp3	2025-11-28 15:07:01.874961	f	f	completed	f	\N
4	338544009	test_new_task	Тестовая задача	https://example.com/test-new.mp3	2025-11-23 15:51:17.824272	f	f	completed	t	\N
789	338544009	553f7f06-5cbd-490e-80b8-96d97b0c6a97	vocal, female, jazz, saxophone. Тестовая песня после оптимизации системы и очистки очереди. Эта песня должна сгенерироваться быстро и корректно.	https://musicfile.api.box/ZWM1NzQ2NjMtMjg1YS00YmE5LWI4YjEtZTgzNDA3ZTRhMjZl.mp3	2025-12-07 20:07:18.384564	f	f	completed	f	\N
5	338544009	b1669574-f774-43d8-b736-651cc9f2822b	Тестовая генерация	https://musicfile.api.box/YjdiMDJlMWEtZGJkYy00NmIyLWJjZTMtYzQ0MGQ0NzE4MjVj.mp3	2025-11-23 16:02:08.577195	f	f	completed	t	\N
6	338544009	last_celery_task	Последняя генерация	https://musicfile.api.box/latest_generation.mp3	2025-11-24 17:53:30.189639	f	f	completed	t	\N
8	338544009	1ec56c46-9a66-43fc-a845-4cce0ee16eea	Тест с явной очередью generation	\N	2025-11-24 22:19:36.745056	f	f	completed	f	\N
263	338544009	dc3e64d0-5f01-442d-a3a2-e6e86fcf8ce5	1 Часть: ТОЛЬКО МУЖСКОЙ ГОЛОС. Наша дочка Алёнка. Умная и заботливая. Красивая и умная. Любит играть на гитаре и поет. 2 часть: (ТОЛЬКО женский голос): нежная и ласковая, очень внимательная. Помогает маме. С днем рождения дочь - тебе 18! 3 часть (ТОЛЬКО РЭП): с собакой гуляет, дом прибирает, в институт готовится, будет заниматься фотографией, умеет готовить лазанью. 4 часть (рок гитара):  красивый припев про ее песни под гитару, что их слушает весь мир в интернете. Что она стала популярной!	https://musicfile.api.box/MjU3ZjQxZWEtNTVkOC00M2Y0LTljMTQtMzJhNThjZTRlZTk2.mp3	2025-11-30 13:09:08.150777	f	f	completed	f	\N
15	338544009	f9ae873a-fbca-4ebd-94b9-97747ced91b1	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:32:52.417219	f	f	completed	f	\N
16	338544009	83bfb8b6-b8ee-4d29-a05d-c58f0e5deee6	Тест с prefork pool и psycopg2	\N	2025-11-24 23:32:52.417195	f	f	completed	f	\N
17	338544009	9659c7ed-d53b-4885-b8ba-9b3e79ce4fbc	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала	\N	2025-11-24 23:32:52.417904	f	f	completed	f	\N
18	338544009	7c67a5ac-a540-4041-9b73-dfcae65c2b6b	Тест с работающим пулом БД	\N	2025-11-24 23:32:52.417839	f	f	completed	f	\N
21	338544009	3a32c299-f06c-4b09-b78b-d556ecee88bf	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:32:54.426075	f	f	completed	f	\N
22	338544009	f5cf3a58-9f8b-4e7f-9f55-24bebf5018ae	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:32:54.427628	f	f	completed	f	\N
25	338544009	c8c35695-0d20-4f85-b9dd-dc5628cb0b62	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:33:53.73705	f	f	completed	f	\N
28	338544009	7dd2e5c5-fa9d-4a7b-be80-63b2fa64bc10	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	\N	2025-11-24 23:37:31.431758	f	f	completed	f	\N
32	338544009	79c921e1-d4af-4b70-a966-4adf2d9872ba	Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	https://musicfile.api.box/music_79c921e1.mp3	2025-11-24 23:48:27.691539	f	f	completed	f	\N
67	338544009	ba0c6e22-572a-4f09-b412-6f8be9f7b6ca	/start	https://musicfile.api.box/MDZjMzQxZjgtYTUwZi00MDJjLWEwZDctNWU3ZTM1MjYxNmNk.mp3	2025-11-26 17:55:37.76695	f	f	completed	f	\N
791	338544009	e2c14f5e-66cb-4454-b74e-4b4e047a7b02	Луна светит ярко, звезды горят, музыка льется рекой чистого звука. Мелодия касается сердца и души, пробуждая чувства светлые.	https://musicfile.api.box/ZjdkNTlkYzAtYzVjNC00NWQ1LWIxMzMtZWNjZGZmNmUwYjlm.mp3	2025-12-07 20:12:11.971706	f	f	completed	f	\N
36	338544009	0fc7b1b5-6a2c-47e3-99e8-046375d3904c	Жеткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	https://musicfile.api.box/music_0fc7b1b5.mp3	2025-11-25 12:09:56.853198	f	f	completed	f	\N
144	338544009	00ebe5a8-f09b-478e-ae72-df39b42bcc76	Стиль: Мужской хор. Текст: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!		2025-11-28 10:59:32.355843	f	f	failed	f	\N
40	338544009	92fd8881-df87-4442-8094-ff0343af9aa9	Жесткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	https://musicfile.api.box/music_92fd8881.mp3	2025-11-25 12:12:00.144209	f	f	completed	f	\N
794	338544009	bf97fe24-e047-459d-a7dc-b3ea3d3872f5	Что-то очень спокойное, для медитации, для сна.	https://musicfile.api.box/ZjA4MWQwNmEtZDg4ZS00ZDA5LTgwYmMtZGZmYWJjMDk1MDBj.mp3	2025-12-07 21:59:18.337169	f	f	completed	f	\N
146	338544009	c29216fa-146b-48e4-a56f-21ee3aa7630d	Стиль: Мужской хор. Текст: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!		2025-11-28 12:29:08.884207	f	f	failed	f	\N
44	338544009	b6aba2c8-dd94-4c54-9ed3-4f90d65d6e87	Жесткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.	https://musicfile.api.box/music_b6aba2c8.mp3	2025-11-25 12:13:51.743312	f	f	completed	f	\N
797	338544009	2e4717e4-7a89-415f-9758-4f019b1e4772	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/MGJjNmY1YjMtNzkxNS00NTUyLWI2NmYtYzY4NzRiY2JkMWVh.mp3	2025-12-08 06:16:31.489655	f	f	completed	f	\N
800	338544009	77916268-fab1-4824-b2c6-771b22bc3bc4	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу	https://musicfile.api.box/MGI2MDUyMTgtYmE2OS00ZTQxLWExNDctMDNlMWIyZTRlMTRk.mp3	2025-12-08 08:09:41.479983	f	f	completed	f	\N
803	1307197823	02ac850d-5af8-4606-bd39-71910e7af910	Have Fun With Russian - это Русский с улыбкой. Учись с удовольствием, любя Россию.	https://musicfile.api.box/NWYxM2MwY2MtNTRlOS00ZDk4LThlZjMtYTc5Mzg2ZGRmNTYx.mp3	2025-12-09 19:37:21.115476	f	f	completed	f	\N
243	338544009	efd4fb59-0de6-447a-a024-9db259b1be2e	Мелодичная, красивая музыка класических инструментов, завораживающая, мощная, глубокая, красивая, переливающаяся. Смена инструментов.	https://musicfile.api.box/MWY4NTk2MjUtMzIwOS00NzY0LTgzMWUtNDcyYmRjMzE3OWQw.mp3	2025-11-29 23:35:21.868367	f	f	completed	f	\N
180	338544009	f61501c3-b59c-4620-ab06-e090f2267e82	Стиль: 💰 Баланс		2025-11-28 15:26:41.285825	f	f	failed	f	\N
184	338544009	697e48d0-7802-43ce-8cd5-806e5338ec6c	Стиль: 🎵 Создать песню		2025-11-28 15:26:41.371276	f	f	failed	f	\N
806	807201256	5d8962cc-ad85-49ca-bfef-f383503422f1	🎵 Создать песню	https://musicfile.api.box/MjVkN2I2YjMtZjJiNS00MzgzLWI1NjAtMDZjNjE1NzM2N2U5.mp3	2025-12-10 12:29:25.225414	f	f	completed	f	\N
917	817684210	a3169959-2784-4082-8583-023d558ced8c	Такая спокойная типо блюза и андеграунда с пением	https://musicfile.api.box/MjE2ODc1M2QtNWFjOC00OWE3LWE4MzMtN2E3YjRjMDhmMGNh.mp3	2025-12-13 14:32:05.99979	f	f	completed	f	\N
49	338544009	fd0876cf-eb68-41a3-96d4-cdfa7e063f27	Тестовая генерация с инициализацией БД	https://musicfile.api.box/NzQ2Y2MyZWMtNGYwYi00OWNlLTg0ZDYtODdlMWY4YWMxZWVm.mp3	2025-11-25 23:29:54.723968	f	f	completed	t	\N
215	338544009	11ff79d4-81e3-4ae1-be9e-c78609777574	Тяжелый рок в исполнении духового оркестра	https://musicfile.api.box/ZDdmZThmNTEtNzJkZC00MWQ2LWJjYTUtN2Y2OTkwN2I1Y2Iw.mp3	2025-11-28 18:26:17.816741	f	f	completed	f	\N
45	338544009	b0e8e6df-2e66-4254-af91-2b95c2763b4e	Стиль: Жесткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.		2025-11-25 12:15:09.994833	f	f	failed	f	\N
46	338544009	102c31e4-0ef9-4931-bd01-379db4cd7e99	Стиль: Жесткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.		2025-11-25 12:16:08.210566	f	f	failed	f	\N
52	338544009	59b42888-c27a-4b5d-9811-951a1c477a12	Сначала соло гитара, потом бас гитара, потом ритм гитара, потом пауза, ударные барабаны, потом все инструменты вместе. Энергия, драйв.	https://musicfile.api.box/Njg4ZDhhMTAtM2NjNS00OTc1LWE1NGUtOThiYWUzZjgwN2I3.mp3	2025-11-26 11:52:18.300111	f	f	completed	t	\N
47	338544009	7bb827ac-75f4-4252-8b56-e66cfd2ece37	Стиль: Жесткая Рок гитара, и ударники. На 2 минуты. Жестко и энергично. Для тренажерного зала.		2025-11-25 15:56:43.09223	f	f	failed	f	\N
55	338544009	a1182695-e5f4-47b0-a26c-f016198ab295	Рок гитара + барабаны + фортепиано. Очень врывная музыка с затиханием и снова взрывом. Для тренажерного зала.	https://musicfile.api.box/ZGFmMGRlYzUtMDEzMi00MTZkLWJlYmYtZTliNzhkZmI5YThj.mp3	2025-11-26 13:06:14.604649	f	f	completed	f	\N
266	338544009	684375b6-e58b-4be5-b2fc-9d8d3676f797	1 Часть: ТОЛЬКО МУЖСКОЙ ГОЛОС. Наша дочка Алёнка. Умная и заботливая. Красивая и умная. Любит играть на гитаре и поет. 2 часть: (ТОЛЬКО женский голос): нежная и ласковая, очень внимательная. Помогает маме. С днем рождения дочь - тебе 18! 3 часть (ТОЛЬКО РЭП): с собакой гуляет, дом прибирает, в институт готовится, будет заниматься фотографией, умеет готовить лазАнью. 4 часть (рок гитара):  красивый припев про ее песни под гитару, что их слушает весь мир в интернете. Что она стала популярной!	https://musicfile.api.box/YWU4N2FmOTQtODQ0OS00NzAzLWFmZTMtMzk3NDk0MjNiNTBh.mp3	2025-11-30 13:27:57.668507	f	f	completed	f	\N
58	338544009	594f8ce5-7106-44e8-a13c-f4285363d1d2	Рок гитара + барабаны + фортепиано. Очень врывная музыка с затиханием и снова взрывом. Для тренажерного зала.	https://musicfile.api.box/NzNiOGMyODgtY2M4ZS00ZGExLWFjMmUtMWI1MmJlZjBiNGM0.mp3	2025-11-26 13:13:19.831455	f	f	completed	f	\N
269	338544009	1acbf4d3-15de-4569-aeb3-5fe10783511e	Взрывная и мощная. Энергичная для двидений. Заводнач, под которую не возможно стоять на месте. Любые инструменты. Можно применить - затухание и резкое возобновление и мощь.	https://musicfile.api.box/YmRlYjViNWQtMGQ5Mi00OGRkLWEyYTEtN2I2YjVmZGE0Y2Rl.mp3	2025-11-30 14:31:47.170305	f	f	completed	f	\N
61	338544009	b0810144-6949-4607-96a7-d6967d29dd72	Стиль: Ты, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!. Текст песни: романс	https://musicfile.api.box/YmFiODhmYWQtZTgyMy00ZDhmLWFjNjktNjU2YjA3NDc1Nzc1.mp3	2025-11-26 13:58:47.411715	f	f	completed	f	\N
272	338544009	972779a8-6ab2-4824-bc63-d97f2066d2ec	[Инструментал] Energetic Eurodance, hard pumping bassline, powerful synthesizer hooks, aggressive electronic drums, distorted male vocal shouting short phrases, 140 BPM	https://musicfile.api.box/OWYwZDY1OTUtNTA1OS00NTAzLWExYTYtNjNmYzUzMGE3NTEy.mp3	2025-11-30 14:40:28.879357	f	f	completed	f	\N
64	338544009	00473238-984e-4bca-a48f-3c0364350d02	Стиль: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!. Текст песни: Рок исполнение	https://musicfile.api.box/N2Q4ZjI5ZTUtYTZkYS00MTg5LWI4MTQtY2Q5M2UxYTI0ZjM2.mp3	2025-11-26 15:44:54.837636	f	f	completed	f	\N
245	338544009	ce6af2ab-813b-42ff-bc3c-c154f536698d	Рэп	\N	2025-11-30 10:15:28.817491	f	f	error	f	\N
446	338544009	5b3ac42d-3da6-42b8-9bca-a452ecb5d168	И любви твоей яркие вспышки,\nИ эмоций когда через край!\nЯ люблю тебя разную, слышишь?\nПусть останется так, продолжай!	https://musicfile.api.box/ZWQzNzY2NzQtNmNmNC00ZDRkLTg5ZGMtYmJjMDRkOGQ3MzFj.mp3	2025-12-03 08:52:01.813356	f	f	completed	f	\N
148	338544009	96695e94-d0f2-4d55-b3e6-41bb4a33291d	Стиль: Мужской хор. Текст: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!		2025-11-28 12:38:49.81143	f	f	failed	f	\N
150	338544009	74d08c7e-a485-49d9-8675-c690fcf01303	Стиль: Мужской хор. Текст: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!		2025-11-28 12:47:57.98435	f	f	failed	f	\N
452	338544009	db64deb4-5b99-43a7-b901-3328eb568cc3	Тестовая песня для проверки русского языка	https://musicfile.api.box/MmVhMGI4ZWItZjQwYi00NGI4LTk1YTctOTllNDc0YmMwNTYw.mp3	2025-12-03 11:13:34.376137	f	f	completed	f	\N
152	338544009	43fa8ba5-6e9d-473c-884c-0e49c9302d91	Стиль: Мужской хор. Текст: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!		2025-11-28 12:57:53.286996	f	f	failed	f	\N
455	338544009	0736a61f-a671-472a-bb96-0b4c740acc7f	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!	https://musicfile.api.box/ZWEzNmQyNjAtZThiZS00NGM2LWJiOTAtYTc3YWFhYmQxMjRj.mp3	2025-12-03 11:17:42.146126	f	f	completed	f	\N
156	338544009	aa7f2ede-5717-45a6-97bb-1fcdc902858b	Стиль: Мужской хор. Текст: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!		2025-11-28 13:04:28.86801	f	f	failed	f	\N
458	338544009	6e81368d-1ddd-403b-8ceb-31a991d046d1	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!	https://musicfile.api.box/MGFkNjU2NzEtMTFhYS00ZTU5LWI3NWEtYjAxZDkwMTY1Mzdl.mp3	2025-12-03 11:25:46.334861	f	f	completed	f	\N
158	338544009	c3fcca97-7ef4-4908-bbf0-6a615bb7d1f3	Стиль: Мужской хор. Текст: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!		2025-11-28 13:06:20.505522	f	f	failed	f	\N
160	338544009	055bf4de-3701-485c-83f2-4b13dbb09dc6	Стиль: Мужской хор. Текст: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!	https://musicfile.api.box/NDNhYzI5NTAtYmZlYy00ODM1LTgxZWUtNGNkZjZiYmE0ZjFh.mp3	2025-11-28 13:07:47.158782	f	f	completed	f	\N
162	338544009	1ba96e91-d7bf-40ab-bf76-3d5c2de0b0a7	Стиль: Несколько видов гитар друг за другом. Общий ритм высокий и энергичный. Для тренировок.	https://musicfile.api.box/NjBlYzc1OGUtMmY3OS00ZjBiLWE0NTMtMjY4YmJhYzU5YjVi.mp3	2025-11-28 14:20:37.662109	f	f	completed	f	\N
186	338544009	8fba13c7-7add-439d-8d0f-a7769adf4618	/start	https://musicfile.api.box/MWRkODBhZjItOTYxOC00N2RkLWJhMDgtZjYwMzQ2N2NiYTJh.mp3	2025-11-28 15:29:17.572666	f	f	completed	f	\N
218	338544009	4aa0ec3e-ac37-4c3a-8128-c06f7d209d82	Жесткий рог на инструменте орган	https://musicfile.api.box/MmRhZGU1ZmEtOGRkMy00NjI1LTkyNTktMzhkNGJkOTdhYjYy.mp3	2025-11-28 21:53:07.051754	f	f	completed	f	\N
275	338544009	53926b97-1543-40bf-99f2-843b2fd667d6	Клубный синт-поп хит: Upbeat synth-pop anthem, catchy and playful lead synthesizer melody, four-on-the-floor kick drum, funky bassline, robotic filtered vocals, euphoric chorus, 1990s dance vibe	https://musicfile.api.box/MGZkMDQ1Y2QtNzExOS00YjFlLTgwYzAtMWZlN2JjMDJhOWVh.mp3	2025-11-30 14:46:43.057482	f	f	completed	f	\N
278	338544009	a531aa9d-cda8-4f9a-8d88-32c054c5ce3d	Иконический синтезаторный грув: Iconic 80s electro funk instrumental, memorable bouncing synthesizer bassline, crisp electronic drums, jazzy synth leads, futuristic sound effects, no vocals	https://musicfile.api.box/MzFlNTM4NTYtYjNhMy00MDVhLTg1ZWItYWNhZjc0YzU5OGJl.mp3	2025-11-30 14:52:20.81815	f	f	completed	f	\N
281	338544009	dc04c6a1-bcc0-42f7-a926-38077ed5b349	Призыв к движению: Upbeat tribal house music, infectious carnival-style rhythm, call-and-response male vocal group chants, driving bass, energetic percussion breakdown, feel-good summer anthem	https://musicfile.api.box/M2IwNmIyYzktMTc1OC00Nzc4LWFhYWYtZThlMDE0NGE1NzY2.mp3	2025-11-30 15:04:13.595393	f	f	completed	f	\N
284	338544009	90dafdc7-9f74-4595-af7b-5f5f64f2cea4	Мощный трэш-метал рифф: Aggressive thrash metal, fast palm-muted guitar riffs, pounding double bass drums, raw angry vocal screaming about inner strength, blistering guitar solo, headbanging rhythm	https://musicfile.api.box/MWIyZDY0OTEtOWJkNy00ZWNjLWIxMzUtN2RlNmUxZjk5NGJj.mp3	2025-11-30 15:11:50.890901	f	f	completed	f	\N
287	338544009	6fd9426c-dec8-4a5b-b64e-1f8f96deb720	Народный танцевальный припев: Folk dance rock, anthemic group shouting "Hey!" in the chorus, driving acoustic guitar strumming, stomping clap beat, accordion melody, rowdy tavern atmosphere	https://musicfile.api.box/Y2U5NDhkYWUtZjAzZS00MTgyLTkxNTQtYmIwNWEyNzY3NjEx.mp3	2025-11-30 15:21:09.502918	f	f	completed	f	\N
449	338544009	620b175b-63fa-4aba-86cd-ff727d0b8842	Стиль: группа мужчин поет вместе. Текст: И любви твоей яркие вспышки,\nИ эмоций когда через край!\nЯ люблю тебя разную, слышишь?\nПусть останется так, продолжай!		2025-12-03 08:55:11.64687	f	f	error	f	\N
72	338544009	b0722095-a00e-42f8-a814-5b2fa857f549	Стиль: Я люблю и грозу и ненастье,\nИногда и в дождях утопаю,\nВот такое вот - ты мое счастье!\nТы умеешь быть разной, я знаю!. Текст песни: Рок и рэп	https://musicfile.api.box/OTc1MWRmM2ItOTNkYy00YmMzLTk5NzItMzQwNmI3Yjc2OGIw.mp3	2025-11-27 15:24:33.127664	f	f	completed	f	\N
496	338544009	c22958a7-a57e-4709-a419-3014ad563ad8	ТЕКСТ_ДЛЯ_ПРОВЕРКИ_12345: Солнце светит, птицы поют, трава зеленая	https://musicfile.api.box/ODdmMjQ1YTUtNDAzZi00OGFkLTkxMmQtYWJiYjFjMzQxOTdi.mp3	2025-12-03 17:57:50.030629	f	f	completed	f	\N
75	338544009	db586999-15b5-4d46-9ec5-610443910397	Стиль: И любви твоей яркие вспышки,\nИ эмоций когда через край!\nЯ люблю тебя разную, слышишь?\nПусть останется так, продолжай!\n\nТы прости меня милая в мыслях!\nВ сердце добром своем ты прости,\nЗа обиды которые были,\nЗа ошибки, что ждут впереди!. Текст песни: Рок и рэп. Мужской и женсский голоса.	https://musicfile.api.box/NjNmZTczM2ItYmQ3My00YzlkLTlkYWQtYmQxYjU3MDU4YmNm.mp3	2025-11-27 15:35:27.271697	f	f	completed	f	\N
536	338544009	fe2111e7-13e3-4de0-957a-f2d24fb4ff63	в стиле Мужской русский хор: Ты прости меня милая в мыслях!\nВ сердце добром своем ты прости,\nЗа обиды которые были,\nЗа ошибки, что ждут впереди!	https://musicfile.api.box/MWNiZDcxMjItMTdkYy00NGQ4LWFiNjAtMjViMDE0NWQyZmMy.mp3	2025-12-04 09:05:43.674164	f	f	completed	f	\N
78	338544009	aaeffe8e-77eb-4799-afa0-3cfa478827db	Стиль: Ты прости меня милая в мыслях!\nВ сердце добром своем ты прости,\nЗа обиды которые были,\nЗа ошибки, что ждут впереди!. Текст песни: Оперетта	https://musicfile.api.box/YjUzZTM3ZjMtY2E0OC00ODU0LTgxODctNDExYjc3ZGVhZGZk.mp3	2025-11-27 15:43:18.63223	f	f	completed	f	\N
154	338544009	d8823be7-1a41-4347-81d6-a8ace919ad5c	Текст песни: Мужской хор\nСтиль: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!	\N	2025-11-28 13:00:42.584964	f	f	failed	f	\N
81	338544009	9da3cf08-aea1-40cf-8b4a-990fb6da25e0	Стиль: Я хочу, чтобы счастье и радость\nПоселились на веки с тобой! \nЧтоб не сделал тебе никто гадость,\nОт невзгод я укрою собой!. Текст песни: Хором на распев	https://musicfile.api.box/ZmIxZTUzMmUtY2YzOC00YTdkLWFkZDEtZjQxYzg0ZmYyMTVj.mp3	2025-11-27 15:55:24.56624	f	f	completed	f	\N
248	338544009	fe886cfc-8fa5-447c-9733-ba6ebe9c14dc	Наша любимая дочурка Аленка. Ей исполнилось 18 лет. Мы ее очень любим. Она творческий ребенок. Поет и играет на гитаре. Поступает в институт культуры. С днем рождения!	https://musicfile.api.box/NDhlMGYyYmYtM2ViMC00M2VkLTkzZTUtZjY1YzYzYTgzOWEy.mp3	2025-11-30 10:21:10.520974	f	f	completed	f	\N
251	338544009	7ec56704-b62b-40ce-ba52-0fd22387a467	1 партия мужсской голос. 2 партия женский голос. Под гитару оычная песня. 3 партия мужской голос ОБЯЗАТЕЛЬНО РЭП. 4 партия  жесткий рок под рок гитару.	https://musicfile.api.box/NWYwNWI0ODgtOGU0NC00ZDcyLTgzNmUtYmQxNTIzMDMxZjBk.mp3	2025-11-30 10:33:12.494456	f	f	completed	f	\N
290	338544009	b790e80d-9b34-49a2-b2af-4e955ffac3c2	Гимн решимости: Anthemic stadium rock, powerful clean electric guitar chords, strong male vocals singing about seizing the day, huge sing-along chorus, epic drum fills, 2000s rock radio vibe	https://musicfile.api.box/YjRjMWM1NTYtNDMxOS00MmMwLWJkNWEtYmRmNGNjYjJjNjU0.mp3	2025-11-30 15:56:06.646676	f	f	completed	f	\N
293	338544009	1650a789-71d8-422d-ae3c-fce8ccf6c374	Хард-техно с вокальными сэмплами: Hard techno track, relentless pounding kick drum, distorted industrial synth stabs, repetitive vocal sample "Go!", chaotic energy, dark warehouse party vibe	https://musicfile.api.box/ZWNmZWE3YzAtNjI1ZS00YTRiLTg5OTYtOGQ3ZTdjMjZmOTll.mp3	2025-11-30 17:39:17.9012	f	f	completed	f	\N
980	338544009	c79b08bc-61b0-4b21-87d5-d85e0a8089e3	Instrumental folk song. Melancholic and lonely melody played by a wooden flute, accompanied by a gentle, rhythmic acoustic guitar with arpeggios. The mood is contemplative and nostalgic, like a shepherd alone in the mountains. The tempo is slow to medium, with a natural, flowing feel. The sound is warm and organic, with a slight echo on the flute.	https://musicfile.api.box/MjgzNTE1YjYtM2I3Yi00ZmJiLWI0YzUtZDhmNWE4NGNhMWNh.mp3	2025-12-25 08:40:44.837441	f	f	completed	f	\N
983	338544009	935d7978-cd94-4b2c-8bc5-cd32ef1f3e46	Instrumental folk song. Melancholic and lonely melody played by a wooden flute, accompanied by a gentle, rhythmic acoustic guitar with arpeggios. The mood is contemplative and nostalgic, like a shepherd alone in the mountains. The tempo is slow to medium, with a natural, flowing feel. The sound is warm and organic, with a slight echo on the flute.	https://musicfile.api.box/Mjc1ZDk1MzctYjVjOS00NTk4LWFiNTQtNGIyN2I4YWJhZDhj.mp3	2025-12-25 11:11:16.48287	f	f	completed	f	\N
986	338544009	b4214938-ea62-4863-bb36-b0911a8dcf06	A solitary shepherd's melody. The soulful sound of a Romanian flute (nai or pan flute) sings a heartfelt, improvisational tune over a bed of delicate acoustic guitar strumming. The rhythm is steady, like a slow walk across green hills. The feeling is one of vast open spaces, longing, and peaceful solitude. High-quality recording, intimate and atmospheric.	https://musicfile.api.box/OTJkOTI0M2MtNDUwMi00MGEzLTkxZjQtMWIyNGYyMzJmMTcz.mp3	2025-12-25 11:19:53.788625	f	f	completed	f	\N
84	338544009	1a23631a-d9f1-4404-a35d-09e8a9c0313a	Стиль: Я хочу, чтобы счастье и радость\nПоселились на веки с тобой! \nЧтоб не сделал тебе никто гадость,\nОт невзгод я укрою собой!. Текст песни: Под классическую акустическую гитару	https://musicfile.api.box/NmIyZDFmMDEtMzhmZC00YWU5LWI3MTAtYjI3ZjhhMjUzYTdi.mp3	2025-11-27 16:02:49.463433	f	f	completed	f	\N
87	338544009	8d057a77-3463-4f77-94a9-1a21b9aca96b	Стиль: /start. Текст песни: Русский народный хор	https://musicfile.api.box/Mzg0MzRkOGEtYTM5Zi00YTYyLTgyYjgtYWVjNmE2MmNiMTU5.mp3	2025-11-27 16:17:49.923682	f	f	completed	f	\N
90	338544009	01378155-54c6-4a6d-8479-3a44dc068692	Стиль: Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.. Текст песни: Русский хор. Но тема - про любовь!	https://musicfile.api.box/ZTRkMDRmNjktODFiMi00ZWZjLWI5ZmQtMWY5MzhlNDJmMTIw.mp3	2025-11-27 16:23:31.070317	f	f	completed	f	\N
193	338544009	51114c6e-5371-4c66-9851-99713c559e77	Рок гитара с ударниками. Очень энергично и взрывно	https://musicfile.api.box/Y2Y3MzIxMGMtYzJjMi00MjQ3LTkwMTQtMzQwMjU2YWVmYjVm.mp3	2025-11-28 15:35:05.626528	f	f	completed	f	\N
93	338544009	3c47b5a3-0ab9-410a-a188-383b7fa55afc	Стиль: Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!\n\nЯ люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!. Текст песни: Рок жесткий  и рэп жесткий	https://musicfile.api.box/ODc0MmQyN2MtNWI1Ni00ZjdlLTlkY2ItMDIzNDg1YWFkZTUy.mp3	2025-11-27 17:36:52.310129	f	f	completed	f	\N
462	338544009	e55155ae-be79-45d8-93fe-5b8d9f20885f	Стиль: Мужской хор. Текст: Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!		2025-12-03 11:32:11.918474	f	t	error	f	2025-12-03 11:32:53.737514
197	338544009	67d86560-d746-4222-b421-cb0576db717d	Песню Scorpions но симфоническим оркестром.	\N	2025-11-28 15:39:57.849431	f	f	error	f	\N
96	338544009	46c0525a-2087-4ed9-9217-3bb5ea4b8ea4	Стиль: Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!. Текст песни: Жесткий рок и рэп мужским голсом	https://musicfile.api.box/M2NkOWE3MDMtZDQ2Yy00ZDkzLWE3NTctYjVmZDU1NzU3ZGM1.mp3	2025-11-27 17:47:57.156637	f	f	completed	f	\N
202	338544009	cd27f89d-f482-4e02-aba5-4f942921ab4f	Похожую на песню popcorn только на гитаре	https://musicfile.api.box/YmM5ZmVkMWMtM2E1MC00MDNiLWI0OWYtMzhmZjc3ODk2MTQ4.mp3	2025-11-28 15:42:48.802195	f	f	completed	f	\N
222	338544009	c18228ff-e1cf-4e89-855c-9607edf74844	test music style	https://musicfile.api.box/OGYwMTBlZjQtOGY5Yi00OGEwLThlOTAtNzNiNTQ4YTUwMGM3.mp3	2025-11-28 22:01:35.52906	f	f	completed	f	\N
225	338544009	ce3f6124-23b0-4a99-8fb3-fc9923c09d62	Сильная мотивирующая музыка для спорта, для движения. Рок гитара, ударники, еще что-то грандиозное.	https://musicfile.api.box/MTU4YTVhNjUtMzUxNy00ZmQzLThjODktYzg1ZmM4ZjJmZjNi.mp3	2025-11-28 22:04:54.377621	f	f	completed	f	\N
466	338544009	f844a4ba-cb88-4cd0-9107-6ca87e94b5c2	Стиль: Мужской хор. Текст: Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.		2025-12-03 12:26:17.883461	f	t	error	f	2025-12-03 12:27:11.069193
254	338544009	2db7817b-0f60-4309-b96d-267b7f7ffa37	ГИТАРА: 1 партия мужской голос. 2 партия женский голос.  3 партия - РЭП: мужской голос ОБЯЗАТЕЛЬНО РЭП. 4 партия  жесткий рок под рок гитару.	https://musicfile.api.box/MjhiOTM4MjctNzYwZS00Yzc5LWFiNzgtYTVhNDEzZDdmNzRh.mp3	2025-11-30 12:33:27.317934	f	f	completed	f	\N
296	338544009	65104367-bba7-4f98-9464-7c4ab28e3579	Веселый электропоп: Bubblegum dance track, silly high-pitched synthesizer melody, simple upbeat lyrics about dancing, steady disco beat, cheesy 2000s europop style	https://musicfile.api.box/MTVhNGI2ODAtNDQzMy00NjIyLWJkZjAtNTQ4ZTE2NTcyMTE5.mp3	2025-11-30 17:59:19.659021	f	f	completed	f	\N
498	338544009	f33fa64f-7128-40d9-bae2-276e0e32f969	ТЕСТ_СТИЛЬ_2025: Хард-рок с гитарным соло. ТЕСТ_ТЕКСТ_2025: Солнце светит очень ярко	https://musicfile.api.box/MDRhZGVjNjAtOWM1ZS00NjU2LWFkNDMtZDQxZDcwZWU4ODc4.mp3	2025-12-03 18:09:58.455513	f	f	completed	f	\N
299	338544009	7980d99e-fecf-4bd7-904e-345db2988b83	Глэм-рок с саксофоном: 80s glam rock party anthem, catchy saxophone hook, crunchy guitar power chords, raspy charismatic male vocals, big snare drum sound, rebellious lyrics	https://musicfile.api.box/ZjljY2VkMjAtMWM0NS00NzRiLTkzMWYtY2EyZmM2ZTM0OGZh.mp3	2025-11-30 18:13:07.257105	f	f	completed	f	\N
346	5696467892	d24f695e-3c61-4f46-84e2-31694b9989c0	Красивая скрипка	https://musicfile.api.box/YmExNzI3NGItZmVlYy00ZmE4LWE5MzUtNDU4YzdlNTk1MzE1.mp3	2025-12-01 22:30:32.760066	f	f	completed	f	\N
99	338544009	f0b666cb-8c4c-4ec8-b4ab-3342f0c07bf7	Стиль: Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!. Текст песни: Рэп мужским голосом	https://musicfile.api.box/ZGM4MThiY2EtZmVkYS00YTQzLTgyODUtMTI2NmQyM2Q5NGM5.mp3	2025-11-27 17:55:23.356894	f	f	completed	f	\N
461	338544009	d8888710-0f7d-49f8-a44b-ef78ec690e2b	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!	https://musicfile.api.box/Y2I4NGFmYzItZTk1OS00ZDVmLWJjNTEtMTMyY2MxNTg0MDEy.mp3	2025-12-03 11:29:57.830751	f	f	completed	f	\N
102	338544009	7d9efa6b-7bf9-41bb-8523-50b47a16e33d	Стиль: Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!. Текст песни: Рок н рол. В два голоса мужской и женский	https://musicfile.api.box/MDZjNGFhMjYtZTg1ZC00OTYxLThmMWUtZWZmOGQ1NTgzMDVm.mp3	2025-11-27 18:15:23.091983	f	f	completed	f	\N
465	338544009	0936d1f3-0299-4336-9201-f2e8a4731464	Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/MjRlNzQ0ZWUtMTc2OS00NzY4LTk5NDktNTI5NDY2ZmYzNDRi.mp3	2025-12-03 12:24:46.490858	f	f	completed	f	\N
759	338544009	a0f0d596-b9ac-4fcd-97ef-4cd1e9bca32a	vocal, female, jazz, saxophone. Тест текст песни	\N	2025-12-07 18:29:45.738628	f	f	error	f	\N
105	338544009	2d1fba28-1c47-49b2-b7bf-f68469624274	Стиль: Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!. Текст песни: Акутичекая гитара. Поет мужчина	https://musicfile.api.box/YWI4NmE1ZGMtZjNiZi00MmI3LTkzNDgtY2M3ZDMzMWI5OGM1.mp3	2025-11-27 18:29:18.967604	f	f	completed	f	\N
500	338544009	c7f27824-77a0-4e65-b5ba-cef2147d5eec	СТИЛЬ МУЗЫКИ: Поп-рок с элементами электроники. ТЕКСТ ПЕСНИ: Солнце светит ярко, птицы поют весеннюю песню	https://musicfile.api.box/MjRmMDUxNmYtZTA5Zi00ZTNiLWFiNjgtOTMzOGI0ZWZjNDNj.mp3	2025-12-03 18:41:15.354136	f	f	completed	f	\N
194	338544009	b40663f0-9c3b-4448-8ad8-941da95dc626	Рок гитара с ударниками. Очень энергично и взрывно	https://musicfile.api.box/ODkwN2FjNjItNjBkMC00YmIzLWJlY2ItYjhkZjMzYWNkOTYz.mp3	2025-11-28 15:35:59.783281	f	f	completed	f	\N
108	338544009	ed1d2bb3-c704-4577-a3ac-be6260cbccc0	Стиль: Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!. Текст песни: Акусстичесская гитара. Поет мужчина	https://musicfile.api.box/Y2Q4MWU2MmQtYTk1Yi00MThmLTk3YjgtZGQ1OTdmZTA4YmY4.mp3	2025-11-27 18:37:34.359432	f	f	completed	f	\N
228	338544009	c805cb46-f6d4-4e78-b011-457bd9cd1b18	Основа это ударные! Вокруг ударных по очереди играют разные другие инструменты: то гитара, то виолончель, то скрипка, то труба, то саксофон. Мотивация, сила, энергия, драйв, взрыв, мощь, тишина и снова взрыв!	https://musicfile.api.box/MzUwNWUzM2UtMzk2ZS00OGY4LWIwZGMtNGZkN2QzYmI2OGQw.mp3	2025-11-29 07:34:15.294502	f	f	completed	f	\N
231	338544009	78bc1307-d2d4-4322-8828-6ebad7c6fa6f	Красивая мелодичная на виолончели и скрипе.	https://musicfile.api.box/MDc2MzgzNzQtMTdlNC00YjIxLWI1ZGUtNWJhMGRhN2ZjZTJj.mp3	2025-11-29 07:38:39.571826	f	f	completed	f	\N
257	338544009	0593ff3b-8699-429f-a7da-8d0af3cffefa	1 Часть: ТОЛЬКО МУЖСКОЙ ГОЛОС. Наша дочка Алёнка. Умная и заботливая. Красивая и умная. Любит играть на гитаре и поет. 2 часть: (ТОЛЬКО женский голос): нежная и ласковая, очень внимательная. Помогает маме. С днем рождения дочь - тебе 18! 3 часть (ТОЛЬКО РЭП): с собакой гуляет, дом прибирает, в институт готовится, будет заниматься фотографией, умеет готовить лазанью. 4 часть (рок гитара):  красивый припев про ее песни под гитару, что их слушает весь мир в интернете. Что она стала популярной!	https://musicfile.api.box/YmU0MDRjN2QtNzMyNC00Yjk0LTgyMjEtM2M5MTg0MjYzMTQy.mp3	2025-11-30 12:40:13.489754	f	f	completed	f	\N
302	338544009	d79c4e00-1f1d-4b51-8b63-74a246ab0c6f	Эпичный инструментальный билд-ап: Electronic instrumental build-up, starting with a simple synth arpeggio, adding layers of percussion and bass, rising intensity to a explosive drop with a powerful synth lead	https://musicfile.api.box/NDZiMjU3N2ItNzE4Yy00OGRhLWEwODYtNTQxOTg1MjdiNDU5.mp3	2025-11-30 18:19:12.664632	f	f	completed	f	\N
111	338544009	e571ec29-233d-427b-b0fb-8295f0976790	Стиль: Я иду по улице,\nСолнце светит ярко.. Текст песни: Акустическая гитара. Поет мужчина	https://musicfile.api.box/OGU4MDUyNTgtZmRhNy00ZGQwLWFiODQtNjJjZDlhNDAzMmI2.mp3	2025-11-27 18:43:48.419636	f	f	completed	f	\N
114	338544009	ed4770d5-714f-455c-a05c-0f641cf4d159	Стиль: Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!. Текст песни: акустическая гитара. Поет мужчина.	https://musicfile.api.box/MGQ1YWNmZDktYThhZC00YzZkLTkxN2QtYjk1ZjllZWJjYWE5.mp3	2025-11-27 18:55:53.992789	f	f	completed	f	\N
920	1460772542	599aabcc-0ed4-42b8-ab5f-6f1ecb095ed1	Стиль: Рэп андеграунд. Текст: Сет, бит, хит, фит, миг, \nСнял клип, хат, кик, \nБасс, клик, мат, крик, \nРэп щит, капюшон вшит, \nУ ще...	ERROR_NOTIFIED	2025-12-13 15:09:54.680189	f	f	error	f	\N
117	338544009	30a840a9-7fdb-4a76-b245-eb6b9e031829	Стиль: 1. Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.. Текст песни: Акустическая гитара. Поет мужчина	https://musicfile.api.box/NTVkNWVlODUtOTNkOS00OGI2LTg1NzYtOTE3ZmUxMGU0ODk3.mp3	2025-11-27 19:08:35.738255	f	f	completed	f	\N
923	896769788	a8e9f18a-932a-4be4-8f6d-bdf29f1d7548	Хип хоп 90х годов	https://musicfile.api.box/MmQxNjhlYjMtNjY3YS00ODRmLWI1YjAtNzc0YmFkMGJhMzVl.mp3	2025-12-13 16:54:41.231942	f	f	completed	f	\N
120	338544009	93b64b3e-c816-4a6f-9ff1-c6bf7e145378	Стиль: Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!. Текст песни: Акустическая гитара. Поет ТОЛЬКО мужской голос! ИССКЛЮЧИТЬ женский голос.	https://musicfile.api.box/ZWExZDI1ZjQtM2QzMy00MjhhLThmNmEtMTJlZjFmZTczNTE0.mp3	2025-11-27 19:19:50.827902	f	f	completed	f	\N
235	338544009	d848a804-f958-4cac-9851-39b7783e8d07	1 партия: спокойная мелодичная скрипка, 2 партия: рок гитара и ударники, 3 партия: виолончель и ударники, потом затишье и резко взрыв и мощь рок гитара и ударников.	https://musicfile.api.box/MmIxZWE1NzEtNzgxMS00YmM3LWJkNGEtNzY2Y2E4YmFmMjVl.mp3	2025-11-29 20:30:24.043002	f	f	completed	f	\N
237	338544009	80d63205-0873-435b-ab02-5a119801cad1	1 партия: спокойная мелодичная скрипка, 2 партия: рок гитара и ударники, 3 партия: виолончель и ударники, потом затишье и резко взрыв и мощь рок гитара и ударников.	https://musicfile.api.box/NDJiYjEwZjgtNDEyZS00ZTA5LTlkYWMtZjAwMDRkYzJhZmNm.mp3	2025-11-29 20:32:40.276027	f	f	completed	f	\N
203	338544009	775981a9-43d7-4251-834a-5840047239bb	Стиль: Тяжелый рок, инструментя Рок гитапра и орган.		2025-11-28 17:28:30.916507	f	f	failed	f	\N
305	338544009	dc419ad8-87fb-4d5a-8f3d-023bf310e119	Скоростной панк-рок: High-speed punk rock, distorted three-chord guitar progression, fast simple drumming, shouted rebellious vocals with a catchy melody, short and energetic track	https://musicfile.api.box/YzMzY2MyMWUtNjUzYy00ODU4LWE4NDctNjNlNjkzMTg5M2Vh.mp3	2025-11-30 18:40:40.140543	f	f	completed	f	\N
308	338544009	60e07dd0-3fea-412c-89ca-0fc823f99276	Фанковый брейкбит: Old-school breakbeat, funky wah-wah guitar sample, heavy syncopated drum loop, deep sub-bass, scratch effects, energetic and groovy	https://musicfile.api.box/NmZkOTYzMjAtZDhiYS00MzlmLWE0OWUtMDNjMjJiYzgyYTdi.mp3	2025-11-30 18:45:32.973084	f	f	completed	f	\N
311	338544009	ac2273e3-6fd9-4599-82d8-2b761a138dbf	Метал-баллада с мощным припевом: Heavy metal power ballad, clean arpeggiated guitar intro exploding into a heavy distorted chorus, emotional powerful vocals, epic guitar harmonies	https://musicfile.api.box/Mjg3ZTg1MzEtMGMxNS00ZGI0LWFlZjgtZjgwZWI5MTUzNjEz.mp3	2025-11-30 18:51:34.900101	f	f	completed	f	\N
317	338544009	5b6be963-0fcf-4688-9e42-904e79eed5cd	Стимпанк-марш: Steampunk industrial march, pounding anvil-like percussion, grinding brass synth melodies, deep male choir chants, mechanical and rhythmic	https://musicfile.api.box/ZWMzNzg5M2YtZWI3OC00ODdlLWI0OWItZjUzM2VjMDllZDMy.mp3	2025-11-30 19:02:43.949983	f	f	completed	f	\N
123	338544009	8b5272b7-6291-4e30-a93c-759eaaef7bf6	Стиль: Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!. Текст песни: Только акустическая гитара. ТОЛЬКО мужской голос!	https://musicfile.api.box/OTY2OTY0ZGItZTlkMS00NDg4LTgxYmQtODAwMDExOGYyYjQ0.mp3	2025-11-27 19:32:48.689747	f	f	completed	f	\N
126	338544009	206539cb-a020-4b68-902c-0f33775c52ad	Зажигательная, взрывающая мощь внутри тела, виртуозная гитара. Мощные ударники. + большой оркестр. Очень энергично. Применить затухание, замедление и потом резкий врзыв и ритмичность. Для тренажерного зала.	https://musicfile.api.box/ZDkxYjhmYWItMmQyOC00OTFjLTlhODQtMGEyYzZiYTVkZWY0.mp3	2025-11-27 20:49:20.12914	f	f	completed	f	\N
166	338544009	29e44021-c2fe-42cd-8bfa-941c238018b3	Мужской хор	\N	2025-11-28 14:58:11.53892	f	f	error	f	\N
129	338544009	93977f33-feb0-4813-a081-b11ae765f959	Класические инструменты, смычковые, духовые, плюс ударники. Знаменитая композиция группы Scorpions.	\N	2025-11-27 22:00:31.968723	f	f	error	f	\N
132	338544009	fbc70699-af11-4046-9ae0-dd8824039208	Класические инструменты, смычковые, духовые, плюс ударники. Знаменитая композиция группы Scorpions.	\N	2025-11-27 22:09:42.643648	f	f	error	f	\N
169	338544009	3b51e5ac-eaad-40a7-9fe9-c10f4fbf500d	Мужской хор	\N	2025-11-28 15:01:52.461767	f	f	error	f	\N
135	338544009	ae0193b8-62a0-43a7-a048-ad902f7a716d	Класические инструменты, смычковые, духовые, плюс ударники. Знаменитая композиция группы Scorpions.	\N	2025-11-28 08:42:53.427854	f	f	error	f	\N
314	338544009	684e911c-7ffc-4cfb-ab85-940a822ec9a2	Эйсид-хаус с кислотной басс-линией: Acid house track, pulsating 303 bassline, repetitive vocal chop samples, classic house piano chords, soaring string synth pads, trippy atmosphere	https://musicfile.api.box/MTI5MzRhZGUtYTlhMC00Zjg1LTljMTItODFmMGQxMDBlMzZi.mp3	2025-11-30 18:58:38.900187	f	f	completed	f	\N
474	5696467892	c5f2dced-dee3-4bff-ae1d-9fe6a4cfb68c	Красивая скрипка и виолончель	https://musicfile.api.box/MWQxYTQ5MzAtZDRmMC00ZGIxLThhYzEtZThjNjMyMjczZWYz.mp3	2025-12-03 17:03:01.953921	f	f	completed	f	\N
477	338544009	cbdc7bd5-5862-4aae-bc33-844d7a358512	ТЕСТОВЫЙ ТЕКСТ ПЕСНИ: Солнце светит ярко, небо голубое	https://musicfile.api.box/MmE2MmZkMTItMmYyNy00MDU2LWI1NDktOThjYjMyZTViM2Yw.mp3	2025-12-03 17:05:25.91196	f	f	completed	f	\N
137	338544009	c5375cb8-7a54-44ca-aa91-670594e66859	Текст песни: Хор мужской.\nСтиль: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!	\N	2025-11-28 10:31:22.83749	f	f	failed	f	\N
519	338544009	a0f078f0-5ba4-476d-ba1c-c1f4f1f77909	ТЕСТ СТИЛЬ. ЭКСТРЕННЫЙ ТЕСТ	https://musicfile.api.box/NDdhZDdiODYtYTNhMy00MThiLWFkZWMtMzc5OGI0NTQyNmRh.mp3	2025-12-03 22:14:55.604012	f	f	completed	t	\N
209	338544009	c977fae3-5c93-4372-b5ca-e3c7ef16fed9	Жесткий рок, но инструменты классические, смычковые и духовые	\N	2025-11-28 18:14:45.06196	f	f	error	f	\N
139	338544009	e378328c-7be0-4690-b7b8-6d089e5f9674	Текст песни: Мужской хор\nСтиль: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!	\N	2025-11-28 10:41:22.015763	f	f	failed	f	\N
504	338544009	5c69741f-25d7-4a17-9e6c-0fb8f5107aff	ДИАГНОСТИКА_ЦИКЛА: Хеви-метал. ДИАГНОСТИКА_ЦИКЛА: Текст для проверки полного цикла	https://musicfile.api.box/NjZiNjA1M2MtZDAwZC00ZTgxLWE3NzMtMTU3YzBhZmFhYzll.mp3	2025-12-03 21:20:21.888426	f	f	completed	t	\N
212	338544009	0fb0bc90-0d94-4cd4-835c-cdd537f47bff	Тяжелый рок в исполнении духового оркестра	\N	2025-11-28 18:19:09.274299	f	f	error	f	\N
141	338544009	e241f5b1-9d99-4f67-8029-67776e8d801f	Текст песни: Мужской хор\nСтиль: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!	https://example.com/generated_529.mp3	2025-11-28 10:45:41.068153	f	f	completed	f	\N
240	338544009	40212338-e9aa-4b32-9da1-da086555e9c5	Красивая мелодичная завораживающая классическая музыка с классическими инструментами. Мощная, глубокая.	https://musicfile.api.box/ZmI2NjE0OTAtMWZkOS00ZWRjLWJkYzAtYTIwMzE3Yzc1ZDFl.mp3	2025-11-29 22:45:19.536417	f	f	completed	f	\N
539	338544009	08089e81-3f05-440e-b843-f72c98f1e877	Ты прости меня милая в мыслях, в сердце добром своем ты прости, за обиды которые были, за ошибки что ждут впереди!	https://musicfile.api.box/Nzg0MThiOTUtYjYzZi00NTUyLTkzNDUtYzlmZjc0N2U3ZjNj.mp3	2025-12-04 15:58:00.894378	f	f	completed	f	\N
260	338544009	38e31fd8-1586-4790-8e63-d3575b051e90	1 Часть: ТОЛЬКО МУЖСКОЙ ГОЛОС. Наша дочка Алёнка. Умная и заботливая. Красивая и умная. Любит играть на гитаре и поет. 2 часть: (ТОЛЬКО женский голос): нежная и ласковая, очень внимательная. Помогает маме. С днем рождения дочь - тебе 18! 3 часть (ТОЛЬКО РЭП): с собакой гуляет, дом прибирает, в институт готовится, будет заниматься фотографией, умеет готовить лазанью. 4 часть (рок гитара):  красивый припев про ее песни под гитару, что их слушает весь мир в интернете. Что она стала популярной!	https://musicfile.api.box/OGVkYzhjYjEtZDk2Yy00ZDA3LWFhZjEtOWQyZDE3YmZjY2Vl.mp3	2025-11-30 12:55:15.76436	f	f	completed	f	\N
542	338544009	4fa5ace6-4e78-4d33-815f-e8d437cf05a8	Ты прости меня милая в мыслях, в сердце добром своем ты прости, за обиды которые были, за ошибки что ждут впереди!	https://musicfile.api.box/OTY3NGZkODgtNDM5Mi00NWJlLTkzYmItZGMzNDBkMmM1MjA3.mp3	2025-12-04 16:02:16.911259	f	f	completed	f	\N
545	338544009	422c0842-a454-4469-bf2c-2b2117c84d76	Мужской хор поет без слов, хоральная музыка	https://musicfile.api.box/ODVjNzE0OTItYmI3YS00ZDk4LThkNjUtMjhhMWY2MDJjNjQw.mp3	2025-12-04 16:12:53.455279	f	f	completed	f	\N
809	338544009	795f59bb-54ce-49b0-bb2b-b52d80def3ef	A deeply meditative and expansive ambient soundscape. Ethereal, slow-evolving pads, like a gentle fog over a mountain lake at dawn. Subtle, crystalline bells that appear and dissolve like thoughts. Very slow tempo, minimalist, immersive. Feels like weightless floating in space. The sound should evoke profound inner peace and vast, quiet emptiness. [стиль: ambient, drone, healing music]	https://musicfile.api.box/YmYyOWI5NDMtOWZiNC00N2JiLWEzMjktOWVlMDdlMGE5YmY5.mp3	2025-12-10 16:03:10.259736	f	f	completed	f	\N
812	338544009	0cc10d16-1026-43ab-96be-3541c544cd06	A beautiful and gentle relaxation music. A soft, memorable, and looping piano melody, simple and heart-touching, like a music box. In the background, a warm, slow pad synth creates an atmosphere, like a soft blanket. Very distant, delicate sounds of nature: a single bird, rustling leaves. The tempo is slow, like a calm heartbeat. The music should evoke a feeling of safety, warmth, and gentle sadness that brings peace. [стиль: neoclassical, ambient, calming music]	https://musicfile.api.box/ZTY4YjVjMGEtODdiZS00ODI2LTkwNGItYWM3NGQ2MWUzOGNi.mp3	2025-12-10 16:09:51.692178	f	f	completed	f	\N
706	338544009	46accb14-98d0-4724-a560-68d7b4eb8aaf	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/ZjAzMmZjNTQtZjc4MS00ZTE4LWEyMWQtY2QzMjViMjg4MWU2.mp3	2025-12-07 09:55:55.075235	f	f	completed	f	\N
815	338544009	5234d600-8b76-48f3-8ec3-81f2bd092ec7	Deeply relaxing and emotional string ensemble piece. A slow, soulful cello carries the main melody, full of feeling but without drama. A bed of warm, sustained violin and viola chords supports it. The development is very gradual, like a slow sunrise. No percussion. The music should feel like a compassionate embrace, soothing inner pain. [стиль: chamber music, minimalist, emotional]	https://musicfile.api.box/MGI2YTdjOGUtODVkMi00NTNhLTgwMTUtMzc4ZDAzNmNhYzZk.mp3	2025-12-10 16:23:54.140595	f	f	completed	f	\N
476	338544009	1df95675-b912-4016-a8ca-2657c81762dd	999999	https://musicfile.api.box/N2QxMGY0N2YtMjQwNi00ZTViLWIwNzAtN2ZmZjQ1ZmZkYjg0.mp3	2025-12-03 17:04:11.148452	f	f	completed	f	\N
818	338544009	7e23a85e-2562-4d4c-9a7b-213d780dd351	Dynamic, high-contrast photo of a silhouette of an athlete pushing against a wall of intense, abstract energy. Sweat and motion blur. The color palette is vibrant neon (electric blue, hot pink, lime green) against dark shadows. Style: cyberpunk motivational poster, high energy, gritty, cinematic, with a sense of explosive movement. Shot on 35mm. --ar 9:16 (vertical for Reels/Shorts)	https://musicfile.api.box/N2Y0MmFiNTQtZjg5OC00MDAzLTlhZDItMTIwMzE4OGYzMWU4.mp3	2025-12-10 16:31:57.361829	f	f	completed	f	\N
479	338544009	b52b1a27-283d-4d52-89c6-82b86bb55aa3	ТЕСТОВЫЙ ТЕКСТ ПЕСНИ: Солнце светит ярко, небо голубое	https://musicfile.api.box/ZTBiNDI1NjMtNjdkMi00MDlkLWI1YjgtNjJlMmJkZDZhM2Zi.mp3	2025-12-03 17:10:12.840374	f	f	completed	f	\N
521	338544009	9ecff95f-d320-4600-b653-fc5c45412d46	поп-рок стиль. ТЕСТ для проверки цикла	https://musicfile.api.box/MGQ1NWViNTAtN2NlMC00MTk3LWIyOTAtZjhmOTUwMjQzNGY4.mp3	2025-12-03 22:29:45.911425	f	f	completed	f	\N
548	338544009	6a537a8b-09ea-46fd-a2a0-e0363d6d67ce	male choir singing without words, choral music	https://musicfile.api.box/YTI4NzU5OWEtYWRkMS00MjAyLWFiMWUtOTRiNGVmMDE5MzI1.mp3	2025-12-04 16:19:05.496277	f	f	completed	f	\N
551	338544009	5690bca6-db63-4ef8-84cf-c5c85bc7d0e7	Хор грубых мужских голосов басом. Без музыки, только голоса.	https://musicfile.api.box/ZmVmN2E1YzMtNTBmYy00NTU3LWExODctZTgxZjRlZjM4Nzg4.mp3	2025-12-04 16:23:46.467489	f	f	completed	f	\N
554	338544009	07be4ed0-634f-4ce8-a57a-fb5a3d2558a2	Фортепианная мелодия, грустная, медленная	https://musicfile.api.box/YWNjNGZjYjgtYzkwNi00YmNlLTg2NTYtODE4NDAwYWFmMTkz.mp3	2025-12-04 16:29:45.008373	f	f	completed	f	\N
578	999999	6db0f5e0-6d40-475a-a20d-98608fabaf58	This is a full test song with English lyrics to check duration	https://musicfile.api.box/ZDEzNjNlOWYtMmU2MS00MWY4LThjMmItY2I2YzUxNjE3Mjc2.mp3	2025-12-04 19:17:12.377096	f	f	completed	f	\N
582	338544009	05663741-8305-455e-bf87-db778695545e	Testing style transfer in Suno API with custom mode	https://musicfile.api.box/NmZhY2ZiODAtMTljYS00NTA5LThkMDktNjk5YmMyNzU4Mzli.mp3	2025-12-04 19:36:07.055355	f	f	completed	f	\N
320	338544009	3d359b61-81e9-421e-b5b6-ee2effdff8e4	Поп-рок с фанковым басом: Commercial pop-rock with a funky bassline, shiny electric guitar riffs, handclaps, confident male vocals singing an anthem of self-belief, extremely catchy chorus	https://musicfile.api.box/MzhjYWQ5MDItYjA3Yi00MTM5LTg4NjctMTRhYzJkM2U0YmUx.mp3	2025-11-30 19:11:18.962101	f	f	completed	f	\N
481	338544009	fe6a0b1b-0c97-4e98-862d-998778fc8e5b	ФИНАЛЬНЫЙ ТЕСТ ТЕКСТА: Солнце светит ярко	https://musicfile.api.box/NzNhZThhMmQtNjA1MC00NjE4LTk5NTItYmQ5NGJmNTZjNzNk.mp3	2025-12-03 17:16:00.194443	f	f	completed	f	\N
323	338544009	913701fa-6889-4ecf-89e4-05c2008960a7	Нео-классический метал инструментал: Neo-classical metal instrumental, shredding electric guitar solos, complex arpeggios, symphonic keyboard backgrounds, blast beat drumming, technical and melodic	https://musicfile.api.box/YTlkNTcwNDEtYWJkMi00MjhhLTlmOTctYjQ4NjdhZWQ4YWE0.mp3	2025-11-30 19:16:56.977717	f	f	completed	f	\N
326	338544009	b6b150da-3892-4148-a497-1abddd41ef9a	Электро-свинг с современным дропом: Electro-swing track, vintage big band horn sample, swung rhythm, fused with a modern hard bass drop and electronic beats, unique and energetic	https://musicfile.api.box/YjhlNjA0MjEtYzcyZi00ODIyLWIzZWYtYmVhY2FkYjVhYzkw.mp3	2025-11-30 19:20:47.218382	f	f	completed	f	\N
329	338544009	a694148b-f6f4-4b42-a2fe-74238c9e3759	Стадионный хэви-метал: Arena heavy metal, thunderous drum intro, twin guitar harmonies, bass-heavy production, commanding vocalist with a wide range, lyrics about overcoming challenges, crowd noise samples	https://musicfile.api.box/YTgxMDkwNjgtY2I1OC00ZjA2LWI1ZWYtYmYxZDIwYTQyZDgx.mp3	2025-11-30 19:26:51.929955	f	f	completed	f	\N
332	338544009	6322625f-5d11-4eb5-bfbc-4afbd4db1878	[Instrumental] A funky breakbeat intro with a wah-wah guitar sample and a deep bassline, suddenly exploding into a powerful hard rock anthem with distorted electric guitar riffs, pounding drums, and an aggressive energetic rhythm. Dynamic contrast, perfect for gym motivation.	https://musicfile.api.box/YmM0ZWUyNWQtZDMzYS00YzliLWJjYmMtZDE5YmJhN2Y1YmY3.mp3	2025-11-30 19:30:12.687607	f	f	completed	f	\N
335	338544009	b9b06cd3-d661-4581-aa8e-d645bcef278d	[Instrumental] Starts as an old-school funk breakbeat with a slick wah-wah guitar lick, syncopated drums, and a thick bassline. After 30 seconds, the track builds up and dramatically shifts into high-energy stadium rock with heavy overdriven guitar power chords, crashing cymbals, and a driving, motivational tempo.	https://musicfile.api.box/ZGFmNTY1ZWMtMGVkZi00NDFiLWI2NzYtNjdkM2M2MzdjMmEz.mp3	2025-11-30 19:36:06.267386	f	f	completed	f	\N
523	338544009	762d9ead-e52b-4fa5-9433-a31178ec3acf	электронная поп-музыка. Финальный тест системы	https://musicfile.api.box/ZjY2ZWNkMzktYjQyMS00ZjYwLTg4NzktZTQ4MzM1MzFlNDhk.mp3	2025-12-03 22:37:14.563189	f	f	completed	f	\N
338	338544009	8885f34c-3666-4143-aa87-447f6cc5b575	[Instrumental] A groovy and rhythmic funk breakbeat sets the mood, then the music cuts out leaving only the drum loop for a moment before slamming in with a massive, aggressive hard rock drop. Raging distorted guitars, thunderous drums, and intense energy. Perfect for a workout pump-up.	https://musicfile.api.box/ZTY2YTI2MTctY2M0OC00ZDQ3LWJlMTgtZGYyNGMwZWQ1NTU4.mp3	2025-11-30 19:40:31.649367	f	f	completed	f	\N
557	338544009	53e17909-7810-4162-85ab-c1ed0002ddc4	Ты прости меня милая в мыслях!\nВ сердце добром своем ты прости,\nЗа обиды которые были,\nЗа ошибки, что ждут впереди!	https://musicfile.api.box/MDQxMzYzYmUtNmVlOC00ZTFmLWE1OTEtYWU5YzM5NGZlOTk5.mp3	2025-12-04 16:36:41.786072	f	f	completed	f	\N
341	338544009	e342f433-fcc5-46e9-8f5b-6c7107e40741	Стиль: Рэп. Текст: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!\n\nЯ люблю и грозу и ненастье,\nИногда и в дождях утопаю,\nВот такое вот - ты мое счастье!\nТы умеешь быть разной, я знаю!\n\nИ любви твоей яркие вспышки,\nИ эмоций когда через край!\nЯ люблю тебя разную, слышишь?\nПусть останется так, продолжай!	https://musicfile.api.box/MDA2ZWQ4YTUtZTQyMy00NWM0LTg5YjgtYjdhZWY3Yzc4YjBj.mp3	2025-12-01 21:28:27.90871	f	f	completed	f	\N
560	338544009	f085f402-d6dd-4cfd-b41c-df7360ebff18	Мужской хор поет песню: «Ты прости меня милая в мыслях, в сердце добром своем ты прости"	https://musicfile.api.box/YWU0YTA0ZjUtYzkzZS00NjVkLTljMjUtYjZjYmU0YTg1Mzhh.mp3	2025-12-04 16:44:36.879278	f	f	completed	f	\N
586	338544009	d76b146f-4034-4eea-914c-3fafa9e800ef	[Куплет 1]\nУтро начинается с первого луча,\nСолнце касается спящих полей.\nВ этом мире так много, что значит для нас,\nВсе наши мечты, все надежды, затей.\n\n[Припев]\nИ мы идем по дороге вперед,\nНе зная куда, но туда, где свет.\nВ каждом шаге есть капля удачи,\nВ каждом вздохе - частичка надежды.\n\n[Куплет 2]\nГород просыпается в шуме машин,\nЛюди спешат по своим же делам.\nНо среди суеты и бегущих картин,\nЕсть место для тех, кто мечтает и ждет.\n\n[Припев]\nИ мы идем по дороге вперед,\nНе зная куда, но туда, где свет.\nВ каждом шаге есть капля удачи,\nВ каждом вздохе - частичка надежды.\n\n[Бридж]\nВремя летит, как река вдалеке,\nУнося с собой все печали и грусть.\nНо остаются в душе человека,\nТе моменты, что хочется в сердце нести.\n\n[Финальный припев]\nИ мы идем по дороге вперед,\nНе зная куда, но туда, где свет.\nВ каждом шаге есть капля удачи,\nВ каждом вздохе - частичка надежды.\nВечная дорога, вечный полет. [Длина песни: 3 минуты]	https://musicfile.api.box/NGUzZTM4NDktMjIwYi00ZWJjLWJhNGYtOTQ1Y2ZjYmQ2MDgx.mp3	2025-12-04 19:42:49.426753	f	f	completed	f	\N
926	7866183841	0a7dd687-7a7a-42ec-b246-06696cb1de5d	Стиль: 1 хип хоп андерграунд\n2 пианино \n3 мужской \n4 темп средний , настроение мрачное. Текст: Когда в моих глазах уснет холодный город в прошлом я буду потрошить свою систему взглядом ревом \nМне...	https://musicfile.api.box/Yzc3MDRkYjYtOTVjZS00YjgxLThmYzItZDlhYmI3MTQ3ZGI3.mp3	2025-12-13 17:01:45.591221	f	f	completed	f	\N
929	1776435167	6fc6072a-a540-47a9-925f-ae76bf1f9a24	Стиль: Жанр ( рок \nГолос мужской\nНастроение грустное. Текст: простите мама ваш сын ужасно болен и не помогут доктора \nлишь только смерть ее еще зовут покоем помо...	https://musicfile.api.box/MjIwMTUwNGItNGZkMC00NTA2LTgzMDItNmQ5NjMwM2Y2ZGY4.mp3	2025-12-13 18:32:28.130838	f	f	completed	f	\N
932	1895249696	0efd051c-3713-4361-95dc-31268facca61	Стиль: Рок, хорроркор, экспериментальное техно,  женский голос, темп как в роке. Текст: Однажды, я стал поэтом.\nИсписано было рукой поэта, лучезарные легенды.\nВесь мир росколот на столетия...	https://musicfile.api.box/ZTI3N2E2OGQtNDVhOS00NTU0LTkxMGItYzg5YWYyYmJkMTk4.mp3	2025-12-13 19:06:39.358389	f	f	completed	f	\N
935	5429189658	c09974e6-0177-4e64-9a19-146e2e13c689	Стиль: Рок. Текст: Что есть время и жизнь человека?\nЛишь мгновение стёртое в пыль.\nИ всю жизнь он несёт это бремя,\nИ не...	https://musicfile.api.box/MGE5Y2U3MDYtMjBmNC00MjE1LTgxMjEtYWY2MTZlNWIxZTIy.mp3	2025-12-13 19:16:57.919959	f	f	completed	f	\N
349	5696467892	fc0cefae-86d1-4194-a6f5-584de6a5dc7c	Рэп	https://musicfile.api.box/YjYwMDM0ZDYtNGM4Yy00MjlhLWE3MDEtZTQ3MzA3NGI2NWFj.mp3	2025-12-01 22:34:58.54751	f	f	completed	f	\N
352	338544009	8952087e-82e4-4c08-b448-751478709ba9	[Instrumental] A funky breakbeat intro with a wah-wah guitar and a deep sub-bass, abruptly cutting to a lone drum loop before exploding into a fusion of aggressive hard rock and energetic eurodance. Raging distorted guitars meet a hard pumping bassline and powerful synthesizer hooks. 140 BPM, intense workout energy.	https://musicfile.api.box/YWFkNmQ4OTctNWU4MS00NWJiLWI5NTAtM2I2YzZiMWQ2MzFm.mp3	2025-12-02 07:15:06.334013	f	f	completed	f	\N
358	338544009	b50afda4-bc28-4176-b5b7-a5be140c4a63	[Instrumental] A funky breakbeat mixed with a vintage electro-swing horn sample and a swung rhythm. After a brief drum break, it violently drops into a massive hard rock finale with raging guitars and a modern hard bassline. Unique and powerfully energetic.	https://musicfile.api.box/NWQ4MTE3MTctMzlhYy00MjE0LTg3ODMtOTZmOGQwOTIzNjY1.mp3	2025-12-02 09:23:35.194725	f	f	completed	f	\N
525	999999	TEST_TASK_ID	Тестовый промпт	http://test.com	2025-12-04 07:11:24.534617	f	f	test	f	\N
364	338544009	714bd811-87fd-4564-b18f-35c6d509803e	Племенной Евродэнс\n[Instrumental] Upbeat tribal house music with infectious carnival rhythms and call-and-response chants, fused with the powerful synthesizer hooks and aggressive electronic drums of 140 BPM Eurodance. Energetic percussion breakdown.	https://musicfile.api.box/Njc0NTc0NTUtZGVhMC00MDNkLTk0NDctZjE4ZmE4ZTU5NTM2.mp3	2025-12-02 09:48:52.991738	f	f	completed	f	\N
821	338544009	61ac4f20-1dbd-41bf-b320-f4c5da955ac1	Upbeat, infectious Latin dance track. A fusion of reggaeton rhythms with modern pop-house. Bouncy dembow beat, sparkling tropical synths, and a funky, groovy bass guitar. Infectious, joyful melody that makes it impossible to stand still. Add a catchy, flirtatious female vocal line in Spanish about a summer night and dancing without worries. "Baila conmigo hasta que el sol salga..." [стиль: Latin pop, reggaeton, dance]	https://musicfile.api.box/MjMyOGIzN2EtNmExOC00Y2EwLWFiYjAtMzI3ZDIxZjFlY2U5.mp3	2025-12-10 16:47:22.820592	f	f	completed	f	\N
370	338544009	12bfe0b2-a15b-47a4-b9f8-b9b31bfddef7	Племенной Рок-Марш\n[Instrumental] Upbeat tribal house with infectious rhythms and group chants, evolving into a powerful steampunk industrial rock march with grinding brass synth melodies and distorted guitars. Driving and anthemic.	https://musicfile.api.box/YTUxYWI0MDUtZDI5Yy00OTIxLWI5NmUtYThkNzQyZTA5NTlj.mp3	2025-12-02 12:03:34.71801	f	f	completed	f	\N
563	338544009	b49c6563-193c-4ff2-a1bc-5568cef533ee	Ты прости меня милая в мыслях!\nВ сердце добром своем ты прости,\nЗа обиды которые были,\nЗа ошибки, что ждут впереди!	https://musicfile.api.box/MWUwOTFiODctODI4Ny00OWE2LTg3YTctNzBhN2I0NGYwN2Vi.mp3	2025-12-04 16:55:11.615924	f	f	completed	f	\N
376	338544009	5aa49bdc-d341-4b66-a0d0-1b3b06399cd6	Метал-Баллада с Электро-Свинг Хорами\n[Instrumental] A heavy metal power ballad structure: clean guitar intro exploding into a heavy distorted chorus, but with epic deep male choir chants in the style of a steampunk march. Dramatic and grand.	https://musicfile.api.box/MjQ2NDFlNWEtZWUwOS00N2U2LWFkMmMtNzIxMDdjMjhiODBk.mp3	2025-12-02 12:52:55.697851	f	f	completed	f	\N
603	338544009	248dd3b7-5cbd-48f4-91f0-655b99797c7e	[Instrumental] A dark, minor-key reinterpretation of the famous silly melody, played on a haunting synth over a slow, groovy funk breakbeat. Out of nowhere, it transforms into a triumphant, upbeat eurodance chorus with the original happy melody. Dramatic contrast.	https://musicfile.api.box/MmJlNzk3NWUtYWIzMy00YzM3LTg5ZTMtYTM2Y2NhMWFhNjA3.mp3	2025-12-04 20:22:21.726389	f	f	completed	f	\N
382	338544009	88606139-aa10-4df1-adbc-44f7f2d5b886	Стимпанк-Поп-Рок\n[Instrumental] A steampunk industrial march with pounding anvil-like percussion and grinding brass synths, fused with the catchy, confident vocals and shiny electric guitar riffs of commercial pop-rock. An anthem of self-belief.	https://musicfile.api.box/ODg3OTY5ZmYtZDJiMS00MTc4LTkyMGItOGE4ZmE0ZjkwMzli.mp3	2025-12-02 13:40:31.6973	f	f	completed	f	\N
609	338544009	c205245c-8d0e-425c-ace1-91af5c2d70ce	[Instrumental] 8-bit video game music meets gym anthem. A super catchy, repetitive chip-tune melody (like a Crazy Frog ringtone) is backed by a powerful combination of distorted rock guitar power chords and a hard-hitting four-on-the-floor techno kick drum. Pure pixelated energy.	https://musicfile.api.box/MTY0M2VkMGMtYWY4Yi00ZDYzLTkzZjYtYmQ1ZTlkZDVmMzlh.mp3	2025-12-04 20:37:38.323956	f	f	completed	f	\N
824	338544009	49522482-654f-448f-b9c9-c76dc19881be	An energetic and joyful salsa track with a modern twist. A driving, punchy rhythm section: crisp timbales, lively cowbell, and a fast, walking bass line. Bright, brassy trumpet riffs lead the melody, full of life. A charismatic male and female vocal duo sing call-and-response in passionate, flirtatious Spanish about dancing all night. The chorus is explosive and anthemic, impossible not to dance to. [style: salsa, latin pop, cuban music]	https://musicfile.api.box/ZGIyZTMyNzItYmM4Zi00NTQ0LWIzNWYtNWUyZDg0YTBhZGVm.mp3	2025-12-10 17:04:41.057564	f	f	completed	f	\N
355	338544009	195dbe73-d9a8-4a98-a79c-f84ddeaf6477	[Instrumental] Starts with a groovy breakbeat and tribal percussion, building with call-and-response male group chants. The track then slams into a powerful steampunk industrial march with grinding brass synths and thunderous, distorted guitar riffs. Mechanical and rhythmic.	https://musicfile.api.box/YzM4ZmRhYjItZmMzZS00ZmM2LWJmZWUtMDgyNTA3OWZkNWMx.mp3	2025-12-02 08:29:34.138578	f	f	completed	f	\N
827	338544009	3889bc4a-8c42-454c-b07e-865cebaf8fdb	A cinematic shot from inside a retro sports car driving on a wet, neon-lit highway at night. The view is through the windshield. Raindrops streak the glass, reflecting the glowing pink and cyan lights of the city and endless road. Style: retro synthwave, outrun aesthetic, dark teal and magenta color grading, cinematic, 4k. --ar 21:9 (ultra-widescreen)	https://musicfile.api.box/ZDlhNGJhM2YtODQ4ZC00ODBhLWFmMzMtYTlmYmVhY2JlYzkw.mp3	2025-12-10 17:09:17.325862	f	f	completed	f	\N
485	338544009	1f4cb6c7-ee6d-4eed-b30c-a0fac2ecd1ed	ТЕКСТ ИЗ БОТА: Солнце светит ярко, птицы поют	https://musicfile.api.box/ZmUxNTk5NGItMDVkMS00ZWIzLWE1NTUtZWMzOTIzYWRkNzZj.mp3	2025-12-03 17:26:37.104931	f	f	completed	f	\N
361	338544009	dafab014-a7c2-4c38-864e-7fbbd7fd1fa7	[Instrumental] Energetic Eurodance verses with a hard pumping bassline and distorted male vocal shouts, building into a explosive heavy metal chorus with epic guitar harmonies and pounding double bass drums. Aggressive and melodic.	https://musicfile.api.box/YWRiYjRhYWMtMWFjNC00ZWNjLTljZTUtM2Q4NmI3YTM1ZGM4.mp3	2025-12-02 09:38:36.371861	f	f	completed	f	\N
830	338544009	5ceeac97-575e-4505-8a80-07f8f79db60f	Dreamy synthwave driving music for a night highway. Retro 80s vibe with a modern edge. Pulsating analog bassline, echoing electric guitar riffs, and soaring, melancholy synthesizer melodies. Steady mid-tempo beat with crisp electronic drums. Evokes a feeling of nostalgia, freedom, and endless road ahead. [жанр: synthwave, retrowave, cinematic]	https://musicfile.api.box/ODliNjU4ZWEtZjhhMC00MGVmLTllZGQtOTQzNTVmNmI2YmY2.mp3	2025-12-10 17:28:58.770461	f	f	completed	f	\N
833	338544009	bedb840b-b4f5-4568-a82d-095fc3363e02	Epic orchestral trailer music with a dark ethnic twist. Massive, pounding taiko drums and thunderous brass sections. A haunting, powerful female vocal chant in a Slavic or Nordic style, singing of ancient legends. Swelling strings, choirs, and a relentless sense of impending grandeur. Blend of "Two Steps From Hell" and tribal folklore. [стиль: epic trailer, hybrid orchestral, world]	https://musicfile.api.box/M2NiYjZhOGEtYmE4Yi00YmE2LTlkYzAtMGYyNWNkZTdjMzVj.mp3	2025-12-10 17:47:02.846649	f	f	completed	f	\N
367	338544009	d383d046-fbee-4702-b738-c39aa1974ab7	Брейкбит Евродэнс\n[Instrumental] Old-school breakbeat with a funky wah-wah guitar sample and scratch effects, seamlessly merging into an energetic eurodance chorus with a hard pumping bassline and powerful synth hooks. Groovy and explosive.	https://musicfile.api.box/YjM2MWYzZTYtZGU3Ni00NjY2LWJjODMtZTY3NGMxNzIxMTI5.mp3	2025-12-02 10:04:25.033559	f	f	completed	f	\N
373	338544009	00e97ec8-9366-4744-8c2d-5aa49dc4d6cb	Метал-Баллада с Племенным Припевом\n[Instrumental] A heavy metal power ballad with a clean arpeggiated guitar intro, exploding into a chorus driven by upbeat tribal house rhythms, call-and-response chants and energetic percussion. Emotional yet primal.	https://musicfile.api.box/NWQ2ZDhiNWYtNWI0YS00ZWI0LTk4YTAtYWI5MmRmM2YyOTY1.mp3	2025-12-02 12:35:54.376572	f	f	completed	f	\N
526	999999	TEST_SYNC_TASK	Тест синхронного сохранения	http://test-audio.com/test.mp3	2025-12-04 07:11:24.596842	f	f	completed	f	\N
177	338544009	a0b05289-9791-4292-84ef-d231db87f1d5	Что-то на подобие Metalica только симфоническим оркестром	\N	2025-11-28 15:11:06.908567	f	f	error	f	\N
606	338544009	6649efb8-b2f5-448d-b16c-2f4a598f6071	[Instrumental] A straight-up, confident pop-rock track (funky bass, shiny guitars) where the iconic silly synth hook is used as the anthemic, shout-along chorus melody. Extremely catchy and motivational, without being childish.	https://musicfile.api.box/Y2Y1NjNmYTYtNmNiZC00M2RiLThlOWMtM2Y0MzIzM2JkNTI4.mp3	2025-12-04 20:29:43.589998	f	f	completed	f	\N
379	338544009	4db0f4a2-a987-41f2-8cb6-6e45ef286cd9	Фанковая Метал-Баллада\n[Instrumental] A heavy metal power ballad that starts with a clean funky breakbeat guitar riff and a deep sub-bass, before exploding into a heavy distorted chorus with raging guitars. Groovy and powerful.	https://musicfile.api.box/M2UzMTY3YmQtMzczZi00ODZmLTg4MDQtYmIwNjE1MjkzZmIy.mp3	2025-12-02 13:00:59.354482	f	f	completed	f	\N
836	338544009	f14872dc-2009-4d6c-9d88-df2ba5a80d9f	Authentic and emotional ethnic fusion. The soulful, raw sound of the Armenian duduk meets the rhythmic groove of the West African kora. A frame drum provides a hypnotic heartbeat. A melancholic, improvisational male voice sings in a made-up language that sounds ancient and full of longing. Feels like a caravan moving through vast deserts under a starry sky. [стиль: world fusion, folk, spiritual]	https://musicfile.api.box/YmVkNzkzNmMtODNmYi00M2QzLTk5ZDMtMmE2ZjQxZjk1M2U1.mp3	2025-12-10 17:57:14.923881	f	f	completed	f	\N
568	999999	030f9a8b-b442-4b6c-b3b6-829fb71c3b66	Поп музыка с синтезатором. Это другой текст	https://musicfile.api.box/MjU3YzViOGUtNTliZS00NzE1LTk0ZWYtNDhjODE1NGE1OWRl.mp3	2025-12-04 17:53:53.935002	f	f	completed	f	\N
962	338544009	00fd1cec-55b3-454e-b5cc-3bec40d9e053	Стиль: Рок гитара, мужской вокал. Текст: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой ил...	https://musicfile.api.box/Nzg1ODI0ZDItMTkwNy00YTg3LTg1MmItOGEzNGRmMmFjNDQ1.mp3	2025-12-17 18:58:42.25356	f	f	completed	f	\N
590	338544009	e5b7bf42-4b18-442a-83cb-f005331cb3cf	[Куплет 1]\nУтро начинается с первого луча,\nСолнце касается спящих полей.\nВ этом мире так много, что значит для нас,\nВсе наши мечты, все надежды, затей.\n\n[Припев]\nИ мы идем по дороге вперед,\nНе зная куда, но туда, где свет.\nВ каждом шаге есть капля удачи,\nВ каждом вздохе - частичка надежды.\n\n[Куплет 2]\nГород просыпается в шуме машин,\nЛюди спешат по своим же делам.\nНо среди суеты и бегущих картин,\nЕсть место для тех, кто мечтает и ждет.\n\n[Припев]\nИ мы идем по дороге вперед,\nНе зная куда, но туда, где свет.\nВ каждом шаге есть капля удачи,\nВ каждом вздохе - частичка надежды.\n\n[Бридж]\nВремя летит, как река вдалеке,\nУнося с собой все печали и грусть.\nНо остаются в душе человека,\nТе моменты, что хочется в сердце нести.\n\n[Финальный припев]\nИ мы идем по дороге вперед,\nНе зная куда, но туда, где свет.\nВ каждом шаге есть капля удачи,\nВ каждом вздохе - частичка надежды.\nВечная дорога, вечный полет. [Длина песни: 3 минуты]	https://musicfile.api.box/OWFjMGVkZDYtNTE0Yy00YThmLTk1YzItZDA2Y2I5ZTE5MTUy.mp3	2025-12-04 19:50:26.372395	f	f	completed	f	\N
839	338544009	4e848267-6e44-4705-9c5b-3c3325876a8c	A poignant and dramatic neo-classical piano piece. Starts with a simple, fragile melodic motif. Gradually builds in complexity and emotion, incorporating sweeping, minimalist string arrangements. Moments of quiet despair erupt into powerful, resonant chords. The composition feels deeply personal, like a musical diary of a heartbreak. Inspired by Ólafur Arnalds and Ludovico Einaudi. [стиль: neo-classical, contemporary classical, minimalist]	ERROR_NOTIFIED	2025-12-10 18:04:03.316988	f	f	error	f	\N
385	338544009	bdf86a2b-2ff6-4407-8e80-76e0262c8370	Евродэнс Стимпанк\n[Instrumental] A steampunk industrial march with mechanical rhythms and deep choir chats, but with the powerful synthesizer hooks and hard pumping bassline of 140 BPM Eurodance. Futuristic and energetic.	https://musicfile.api.box/OWRkZThjZDktNTBkYi00ZmE2LThmZGYtOWVmZTUxOTlkOWI4.mp3	2025-12-02 15:46:27.525442	f	f	completed	f	\N
388	338544009	f8b2046b-cf57-445e-a2f9-3531ccda561f	[Instrumental] A fusion of old-school breakbeat with a funky wah-wah guitar and electro-swing's vintage big band horn sample. Heavy syncopated drum loop, deep sub-bass, and a swung rhythm. Uniquely groovy.	https://musicfile.api.box/OThiZTkwN2QtODQ0MS00OWU0LWE4ZDUtYjJkMmYwODM2MTFk.mp3	2025-12-02 16:08:07.569786	f	f	completed	f	\N
391	338544009	0fcf1e3b-99dc-4bab-bbfd-d4c64a0f335b	[Instrumental] Electro-swing with a vintage big band horn sample and swung rhythm, fused with confident pop-rock vocals, a funky bassline, and an extremely catchy, guitar-driven chorus. Upbeat and anthemic.	https://musicfile.api.box/YWNmOTRiYjgtMzQzYS00OTQ0LWE2NGYtODZkODllYTIxNDNl.mp3	2025-12-02 16:12:13.558952	f	f	completed	f	\N
394	338544009	7d3c03c3-2005-41ec-811e-002d96902131	[Instrumental] Commercial pop-rock with a funky bassline and confident vocals, building up into a massive, energetic eurodance chorus with powerful synthesizer hooks and aggressive electronic drums. Extremely catchy and motivational.	https://musicfile.api.box/NzU3ZmUwNjEtY2IzOS00ODNhLTg1ZjUtYTA2OGFkN2VkYjI3.mp3	2025-12-02 16:16:40.324853	f	f	completed	f	\N
512	338544009	f476c3ec-74a9-42a3-9e2d-e2cd099f3fe6	ТЕСТ СТИЛЬ. РЕАЛЬНЫЙ ТЕСТ пользователя	https://musicfile.api.box/OGM2ZmNhMTEtMzM4MS00N2E0LWE0MzctMjMzNTEzOTA0MzEx.mp3	2025-12-03 21:54:46.984947	f	f	completed	t	\N
397	338544009	80f082d4-a165-4a9a-8c97-5e6b5c5a0584	Чистый Фанк-Метал Брейкбит\n[Instrumental] A heavy funk metal track. Starts with a groovy, syncopated breakbeat featuring a wah-wah guitar and slap bass, then slams into a massive drop with tight, distorted Red Hot Chili Peppers-style guitar riffs and pounding drums. Energetic, rhythmic, perfect for gym.	https://musicfile.api.box/YjU3NWMxYTktYjQ2Ny00ZGUyLTg5YmYtNGUxZjY5NjRiMDA3.mp3	2025-12-02 16:36:07.255691	f	f	completed	f	\N
400	5319854535	65f4e6ce-98b2-4b53-93eb-c2669a56203a	Поп. Женский голос.	https://musicfile.api.box/ZTEyZmQyM2EtZGViYy00ZTcwLWI2MTUtZDg5NThiNDI2ZDQy.mp3	2025-12-02 16:41:03.757869	f	f	completed	f	\N
567	999999	07da836b-ad24-47e9-a11a-39d02f448172	Это тестовый текст песни	https://musicfile.api.box/Yjc2N2U2YTAtNTJjNy00YmE5LWFkZTktMTRhMjI0YjI3Yzc0.mp3	2025-12-04 17:53:23.108477	f	f	completed	f	\N
572	338544009	be10d9ff-af49-4c6c-9e84-89d520f75246	Тестируем передачу стиля в Suno API	https://musicfile.api.box/ZWI2MGJhODQtNjQxYi00NjAwLThmMTEtMzg1YTAwNDRjMDIz.mp3	2025-12-04 17:57:16.744901	f	f	completed	f	\N
403	338544009	1dfaf08d-1dfb-4796-b16c-fa1967676e4b	[Instrumental] A powerful fusion. Begins with a funky breakbeat that incorporates a catchy electro-swing horn riff. After a drum break, it explodes not into pure rock, but into a heavy electronic drop with distorted synth-bass and aggressive drum and bass beats, keeping the swing rhythm. Unique and driving.	https://musicfile.api.box/OWNmZmQwZTQtZGEyNi00YWYzLTgzZWQtODMzMzNiODRhZjY0.mp3	2025-12-02 19:01:02.587626	f	f	completed	f	\N
409	338544009	6a142faf-ef5f-4450-adfd-214b18150e2b	[Instrumental] Dynamic and driving. A continuous track that alternates between verses with a funky breakbeat (wah-wah guitar, scratch effects) and explosive choruses with a hard-hitting 140 BPM Eurodance drop (pumping bassline, powerful synth hooks). Clear, motivating structure.	https://musicfile.api.box/ZGIxMTk1NDYtMDA1OC00Zjg4LTg5NTUtNDE4NWVlZGY2MTg2.mp3	2025-12-02 19:20:07.603954	f	f	completed	f	\N
490	338544009	4f5fa4d1-f4ff-44dc-9918-37faefdd75ce	ФИНАЛЬНЫЙ ТЕСТ: Текст песни для проверки	https://musicfile.api.box/ZjcyZmQ0ZWItYzBlZi00YmM2LTgzNDgtZWQ4MWViNzMyM2Y0.mp3	2025-12-03 17:35:16.111784	f	f	completed	f	\N
415	1024266028	eb65abc6-660b-4c5b-8e55-93fb8da7b2c7	Жанр: классика\nНастроение: праздничное	https://musicfile.api.box/ZDBhM2VmN2YtM2VjMC00M2FjLTkxNzMtMGNhMWYxODMwN2My.mp3	2025-12-02 22:57:14.103279	f	f	completed	f	\N
421	338544009	5749b0c2-2840-4b35-a86f-8194374f5306	Хор мужской	https://musicfile.api.box/Nzk1NWFlNzgtOGM5Ni00YTA3LTkxZWQtNzI1NzIyOThjNzBl.mp3	2025-12-03 07:30:28.123586	f	f	completed	f	\N
427	338544009	74a14ac9-751f-4554-99e8-b5c981de2ac7	Мужской хор	https://musicfile.api.box/ZjljMWRiOTQtOTJmZC00MTIzLWJiMDYtMDEwNzkyOWU0MjZh.mp3	2025-12-03 08:19:35.289622	f	f	completed	f	\N
514	338544009	f28026aa-a922-4c08-b07d-4f06395eae71	ТЕСТ. МГНОВЕННЫЙ ТЕСТ	https://musicfile.api.box/ZThhNGMxNzUtNmUxOS00N2NmLWIyMjYtNjE5MWIzMTAzZWEz.mp3	2025-12-03 21:57:45.829933	f	f	completed	t	\N
430	338544009	a2cffa8a-5f2e-4ba3-bfcb-b3273724de31	Мужской хор	https://musicfile.api.box/YzFmZDI3NmQtYTAwZS00NDNkLWE2Y2YtMWZhZmU2ODgwMDMy.mp3	2025-12-03 08:25:55.692591	f	f	completed	f	\N
436	338544009	acc28574-c2ce-42ae-956d-24bbcf41bfac	Мужской хор	https://musicfile.api.box/ZjM5YmFiZWMtOGJjOS00NjRlLWE5NGMtYWZmZTZjZWI1ZDI3.mp3	2025-12-03 08:35:58.754947	f	f	completed	f	\N
530	338544009	488d1f31-5a57-432b-886a-a22df045b8f6	синтвейв. Тест синхронной генерации\nКуплет: Работает без Celery	\N	2025-12-04 08:19:59.708183	f	f	error	f	\N
597	338544009	45ecdea1-7f0b-4bba-b8b8-ca6a4dc336e1	[Instrumental] Structure: A) Catchy, silly synth hook over a standard dance beat. 😎 Transition into a heavy, syncopated old-school breakbeat section with deep bass. C) The synth hook returns, but now mixed with aggressive electronic drums and noise sweeps. Cyclical and dynamic.	https://musicfile.api.box/MWZlY2E5MGYtYWRjYi00ODMxLWExNzAtMzlhM2IzYWQyZGNm.mp3	2025-12-04 20:09:29.636138	f	f	completed	f	\N
938	2044499510	cf1a1f44-e847-4e84-8293-94f111c26a51	Стиль: Поп. Текст: Маша с днем рождения...	https://musicfile.api.box/MTNkMDE3OTgtMWU1YS00ZGJhLThjYWEtNTJiMDRjYzRmZWM1.mp3	2025-12-13 19:30:31.662464	f	f	completed	f	\N
941	5226511367	1298861e-c75b-41d2-a950-00ec39b8229f	Стиль: Хип хоп. Текст: Зима фонарь опять второй этаж пьем пивас...	https://musicfile.api.box/MTAzNzM4ZjItMzkzNS00MWE0LWEyYWQtYjdhMzVlZmIwZGYw.mp3	2025-12-14 01:01:40.665193	f	f	completed	f	\N
492	338544009	5bb66a45-e591-44a1-a69e-4ae628a05e8a	ПРОБНАЯ ОТПРАВКА: Текст для проверки работы	\N	2025-12-03 17:37:28.730777	f	f	error	f	\N
947	5926679424	d4d8b87b-412c-4618-adef-24fa40cb56d5	Стиль: Поп\nПианино \nМужской голос\nНастроение. Текст: Мне снова не спится\nМоя душа не спокойная\n\nВ моих мыслях только она \nВедь она моя любовь\n\nМне снова ...	https://musicfile.api.box/ODVlMTBjYjEtOGMyYi00NzBkLWEwMmQtOTMwYTMzOGEyZjEz.mp3	2025-12-15 19:17:06.17452	f	f	completed	f	\N
944	684367352	39ae4f3a-2547-48ab-b894-230a84572db8	Стиль: Хип-хоп. Текст: прижмемся друг к другу\nЯувижу твои губы\nОни меня манили с первых минут\nИ до сих пор меня прут\nТвои г...	ERROR_NOTIFIED	2025-12-14 08:48:56.483949	f	f	error	f	\N
950	7596080666	ac07c8b7-30cf-4728-9ae1-8b19d982cc0d	1.жанр поп\n2.гитара\n3.ритм спокойный темп медленный \n4.настроение грустное,атмосфера летнего теплого вечера перед уездом	https://musicfile.api.box/MWYyMWZiOWUtZDM0Yi00MGVjLWE1YmMtMDFkYzhiMDE1ZmVl.mp3	2025-12-15 19:31:05.129897	f	f	completed	f	\N
406	338544009	3d7bdb83-9a51-4110-8a49-d05336483acd	[Instrumental] Upbeat and primal. Combines the infectious carnival-style rhythm and call-and-response chants of tribal house with the powerful synthesizer hooks and hard 140 BPM kick drum of Eurodance. Focus on constant energy, no ballads.	https://musicfile.api.box/YTA4Y2ExOTUtODExYi00YWEyLTk3ZDgtOThhYWUxNWRmOTk5.mp3	2025-12-02 19:13:32.585589	f	f	completed	f	\N
412	338544009	987dc146-9360-4ddb-9d18-ac8436734c20	Стимпанк Энерджи-Ритм\n[Instrumental] Industrial gym anthem. The mechanical, pounding percussion of a steampunk march is fused with the shiny, catchy guitar riffs and confident, shouted vocals of pop-rock. No ballads, pure driving rhythm and self-belief anthem vibe.	https://musicfile.api.box/NjA1NDM0MzgtMTIzYy00ZTJmLTgyODYtZTA5NGIwMDMyODUy.mp3	2025-12-02 19:25:57.503735	f	f	completed	f	\N
418	781459029	fc14d6d5-1a56-4b5a-9732-04036a07447d	Классика, флейта, женский голос, настроение весёлое	https://musicfile.api.box/MDI1NGRmMmEtOTdiMS00Mjg5LWFkNDMtMmFkNTYzZjY1NGEz.mp3	2025-12-02 23:00:09.881751	f	f	completed	f	\N
424	338544009	cb0e96d9-c4ca-4400-b433-8d173d1d4607	Стиль: Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!. Текст: Мужской и женский хор	https://musicfile.api.box/ZjE3M2I2NmQtM2NhMS00OWVhLWE1NWYtYTZhNGU0NjhjY2Rl.mp3	2025-12-03 07:41:54.530513	f	f	completed	f	\N
517	338544009	0fd4e3b4-3afd-490f-8fbf-f6a248809d83	ТЕСТ СТИЛЬ. НЕМЕДЛЕННЫЙ ТЕСТ	https://musicfile.api.box/MThjMjY3ZjQtMDZlNC00MzhjLTlmMzktMDgzOGE1MzI3OGVl.mp3	2025-12-03 22:13:11.391573	f	f	completed	t	\N
433	338544009	6ea2be09-6049-4c50-a648-a9042df760b9	Стиль: И любви твоей яркие вспышки,\nИ эмоций когда через край!\nЯ люблю тебя разную, слышишь?\nПусть останется так, продолжай!. Текст: мужской хор		2025-12-03 08:28:52.039529	f	f	error	f	\N
840	338544009	c328ad3e-1d08-4dd9-afd4-fb1efbdcfee4	Стиль: A poignant and dramatic neo-classical piano piece. Starts with a simple, fragile melodic motif. Gradually builds in complexity and emotion, incorporating sweeping, minimalist string arrangements. Moments of quiet despair erupt into powerful, resonant chords. The composition feels deeply personal, like a musical diary of a heartbreak. Inspired by Ólafur Arnalds and Ludovico Einaudi. [стиль: neo-classical, contemporary classical, minimalist]	ERROR_NOTIFIED	2025-12-11 07:19:10.327233	f	f	error	f	\N
440	338544009	71b4ac23-f251-49e9-b807-cd2fcdd366a4	Стиль: И любви твоей яркие вспышки,\nИ эмоций когда через край!\nЯ люблю тебя разную, слышишь?\nПусть останется так, продолжай!. Текст: Мужской хор		2025-12-03 08:40:07.138742	f	f	error	f	\N
1001	338544009	f7517b4e-0055-41c4-a04b-5510132f0162	Pan flute and acoustic guitar instrumental. Sad, lyrical folk melody, slow tempo, pastoral atmosphere. Similar to "The Lonely Shepherd".	https://musicfile.api.box/ZjhkOGU4ZjEtNmY3ZS00OTcyLThkNDAtMzMzNzlhMGE0M2E1.mp3	2025-12-26 23:02:37.362056	f	f	completed	f	\N
533	338544009	638bdca7-a5f0-4eef-bad6-61a76e3ab877	Мужской русский хор. Ты прости меня милая в мыслях!\nВ сердце добром своем ты прости,\nЗа обиды которые были,\nЗа ошибки, что ждут впереди!	https://musicfile.api.box/NGFmNDI1ODYtZGMxZS00YzAyLWE1NjMtODZjNGJjNjYxNGFl.mp3	2025-12-04 08:58:13.411867	f	f	completed	f	\N
575	999999	e6d1b351-ffdb-4802-afb9-8ac687b8a4b1	Testing style transfer in Suno API	https://musicfile.api.box/YjBkNzg0MGItZmQwNi00MDQ2LTgyNWItNmY5Yzg1ZDAwYThm.mp3	2025-12-04 19:04:25.475699	f	f	completed	f	\N
600	338544009	a350b85a-c569-4ead-8566-d89888e374c3	Instrumental] The classic "Popcorn" melody is swung and played by a vintage big band horn section over a lively electro-swing beat. Suddenly, it drops into a modern, heavy bassline section while keeping the horns. Irresistibly danceable.	https://musicfile.api.box/NTk5NmYxMDAtZjYzYi00ZjcxLWFjNzUtN2JmZWFkZGE4NDdi.mp3	2025-12-04 20:16:30.13897	f	f	completed	f	\N
699	338544009	2976a04c-2a1f-4e90-9d21-797a5573cccd	фортепиано соло, грустно, медленно	https://musicfile.api.box/MzBjNmFkOGQtZTgwOS00OTcxLWEwZTMtMzNjNGIwZDgzMTRm.mp3	2025-12-06 15:02:43.567356	f	f	completed	f	\N
179	338544009	ade220f8-fa62-4320-aafa-1c1afb887579	Нескольк гитар вместе. Ритмично и энергично	\N	2025-11-28 15:26:41.246654	f	f	error	f	\N
187	338544009	e25a411b-3670-42f1-bb12-1888b445158b	📄 Документы	\N	2025-11-28 15:29:17.575945	f	f	error	f	\N
188	338544009	ba9dc8fe-5dbe-4a5b-b0d4-e0fb7220911e	Несколько гитар жестко	\N	2025-11-28 15:29:49.084503	f	f	error	f	\N
220	338544009	14ab3f27-4a04-489b-bfab-391435ffcfe8	жесткий рок, с ударниками для тренажерного зала.	\N	2025-11-28 21:58:02.909502	f	f	error	f	\N
710	338544009	eda55ec7-7bd2-495a-8b4b-c198cb0c3d5d	рок с электрогитарой и мужским вокалом	\N	2025-12-07 10:52:36.632676	f	f	error	f	\N
201	338544009	7e29380b-c569-4921-b094-51e4f52f0c48	Орган. Быстро для тренировки	\N	2025-11-28 15:41:57.796689	f	f	error	f	\N
845	338544009	c1613ea9-00d9-44d1-b166-2027add388a9	🎵 Создать песню	https://musicfile.api.box/OWMwY2Y2MTEtMjY2Zi00ZTU0LTliZjAtOGI0YjNhNTMxNjFh.mp3	2025-12-11 10:03:09.637827	f	f	completed	f	\N
714	338544009	f8bd0dd7-5a5e-4858-9f69-40b8ffeae27e	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/YzRlNjEwOWQtN2RiNS00MmUzLTg4MjQtYzIyNjJkZjNhNTdj.mp3	2025-12-07 11:01:17.044397	f	f	completed	f	\N
718	338544009	16e3d436-1696-471c-8046-34bb736eba4f	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/NWNjMDE1ZmUtMDcwOS00ZGUwLWFlMTktMjJhMzgwNDAzZDhl.mp3	2025-12-07 11:05:47.079988	f	f	completed	f	\N
722	338544009	1f3f75a8-6a96-46bd-bd71-f569338e3f19	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/ZWFjZGE5NGItYWFiZS00NTYwLTg5MDYtYjU0ZjlkZmNkZTcz.mp3	2025-12-07 13:49:49.232548	f	f	completed	f	\N
989	338544009	965efdaf-7c47-4062-9920-5e2b08b5ba43	Music in the style of Gheorghe Zamfir's "The Lonely Shepherd". Featured instrument: a expressive pan flute playing a beautiful, melancholic folk melody. Accompaniment: two Spanish acoustic guitars playing arpeggios and chords in a slow, 6/8 rhythm. The song is purely instrumental, cinematic, and evokes a sense of wide, open landscapes and gentle sadness.	https://musicfile.api.box/YmVjMmU2NDgtZmI1NS00YzM1LWI5OTctZTMwZmQ5NzAzYzVk.mp3	2025-12-25 11:34:47.184564	f	f	completed	f	\N
992	6034993673	9c260547-ceab-4d9d-add5-dc3feabcba78	Стиль: мужской \nзвук днями и ночами в твоем тг канале. Текст: "У-у-у, я знаю, что ты ищешь,\nУ-у-у, в наших взглядах нежных.\nМои мысли — лишь о тебе одной,\nНеужели...	https://musicfile.api.box/NjM2OTMyNTEtYmY0ZC00YTk5LWFjYWUtOTFmYmY1M2I4Yjg5.mp3	2025-12-25 20:32:15.665852	f	f	completed	f	\N
995	7810060820	25683c02-e7d1-434d-a95f-6c402bc04a76	Стиль: рок \nженский \nнастроение. Текст: Я днями и ночами.\nНе сплю, не ем спокойно.\nЛистаю сообщения, мне без тебя так больно.\nКаждое утро вс...	https://musicfile.api.box/ODNkZTNiZjktMWRmOC00Mzg4LThlZGQtNmYzZTE2NzAyZGU5.mp3	2025-12-25 20:42:20.97112	f	f	completed	f	\N
848	338544009	78df0165-af12-4cdc-8802-38e6fdfdb6eb	A breathtakingly beautiful classical chamber piece in the Romantic style. A soulful, melancholic violin melody begins, answered by a deep, warm cello. A grand piano provides delicate arpeggios and chords. The music flows like a conversation between the instruments, with gentle swells, graceful decays, and seamless continuations. The mood is deeply emotional, lyrical, and elegantly sad, like a memory of lost love. [style: romantic era, chamber music, classical]	https://musicfile.api.box/ODhmYmY0ZDctOTg3Ni00ZDljLTllODktNmY2OGFmM2JlYTdj.mp3	2025-12-11 10:10:50.007233	f	f	completed	f	\N
594	338544009	6bb07c53-c1a0-4d58-b8c8-0daeaca61ed5	[Куплет 1]\nУтро начинается с первого луча,\nСолнце касается спящих полей.\nВ этом мире так много, что значит для нас,\nВсе наши мечты, все надежды, затей.\n\n[Припев]\nИ мы идем по дороге вперед,\nНе зная куда, но туда, где свет.\nВ каждом шаге есть капля удачи,\nВ каждом вздохе - частичка надежды.\n\n[Куплет 2]\nГород просыпается в шуме машин,\nЛюди спешат по своим же делам.\nНо среди суеты и бегущих картин,\nЕсть место для тех, кто мечтает и ждет.\n\n[Припев]\nИ мы идем по дороге вперед,\nНе зная куда, но туда, где свет.\nВ каждом шаге есть капля удачи,\nВ каждом вздохе - частичка надежды.\n\n[Бридж]\nВремя летит, как река вдалеке,\nУнося с собой все печали и грусть.\nНо остаются в душе человека,\nТе моменты, что хочется в сердце нести.\n\n[Финальный припев]\nИ мы идем по дороге вперед,\nНе зная куда, но туда, где свет.\nВ каждом шаге есть капля удачи,\nВ каждом вздохе - частичка надежды.\nВечная дорога, вечный полет. [Длина песни: 3 минуты]	https://musicfile.api.box/MmI1YjhkMzAtN2NkNC00ZWY5LWJmODUtOTc0ZWYxOGQ0ZmM3.mp3	2025-12-04 19:54:34.131105	f	f	completed	f	\N
851	338544009	0c52c837-8197-44fa-87ec-2281fb58708a	Complex and captivating lo-fi hip hop beat for deep focus. A warm, dusty vinyl crackle sits under a intricate, jazzy piano sample. The drum break is crisp and head-nodding, with a subtle, melodic bassline. Layers of abstract, filtered city sounds (rain, distant train) weave in and out. Creates a "brain cafe" atmosphere perfect for studying or creative work. [жанр: lo-fi hip hop, chillhop, jazzhop]	https://musicfile.api.box/NzVmYzhjMWYtOGIzNC00OGM1LTk3OGYtYzkxMTA1YzY3OGQ1.mp3	2025-12-11 13:50:20.395438	f	f	completed	f	\N
854	338544009	19bddfff-07b9-42aa-84c7-96f6f922a5bd	A dynamic and evolving lo-fi hip hop track. Starts with a warm vinyl crackle and a simple jazzy piano loop. At 0:30, a crisp, head-nodding drum break and a melodic bassline enter. At 1:15, the piano changes to a melancholic electric guitar sample, and subtle synth pads swell in the background. The final minute introduces a smooth saxophone melody that carries the track to a fade-out. The mood is cozy yet thoughtfully melancholic. [style: lo-fi hip hop, chillhop, jazzhop]	https://musicfile.api.box/N2Q3Y2U5ZGItMGYzOS00MDkwLWIzZjMtZDY4YTYyNjEwOTIw.mp3	2025-12-11 13:55:32.629033	f	f	completed	f	\N
857	338544009	b2c2c288-041b-4302-bde5-4a7278326995	An experimental art-pop ballad exploring AI emotion. A delicate, glitchy electronic beat supports a hauntingly beautiful, synthesized female voice singing in Spanish about digital dreams and electric love. The voice should sound almost human but with subtle, uncanny digital artifacts. The music blends organic harp sounds with glitchy electronics, creating a feeling of fragile beauty in a digital age. "Sueño en bits y tu recuerdo... en la nube guardado..." [стиль: art pop, glitch, electronic]	https://musicfile.api.box/YzMxZTdiZGMtYmYyMy00ZmY4LWI0M2UtOWUzMzY3NmE4NWE2.mp3	2025-12-11 14:01:48.695443	f	f	completed	f	\N
860	5458312673	fafd35ef-9b58-4844-8e69-03f31b5b7a6e	Жанр классика\nИнструменты скрипа, флейта, арфа, тромбон \nТемп умеренный \nАтмосфера чарующая, завораживающая	https://musicfile.api.box/NjlmZDI1MzgtNzMwZC00ZWU1LThmNjMtOWIyMmU0MzdmYTEz.mp3	2025-12-11 20:22:40.851416	f	f	completed	f	\N
1004	7277147192	fc0d02a3-92a6-4279-869b-e8530f147a21	Стиль: /start ref_1776435167. Текст: Рок, хип-хоп.\nПианино, живые барабаны.\nЖенский голос....	https://musicfile.api.box/ZjkwNjRjMTMtOGU5Yi00NWNhLWIxOTAtNmU3NjhhMmZjZDkw.mp3	2025-12-30 10:59:25.731641	f	f	completed	f	\N
612	338544009	89d346be-ca04-4567-bd59-757573ba40ba	[Instrumental] Starts with a catchy, funky breakbeat (wah-wah guitar, deep bass). The main silly synth hook enters, but played on a smoother, funkier lead. Music suddenly cuts, leaving only a tense drum loop. After a pause, it SLAMS back with the same hook, but now played on heavy, slow-tempo distorted rock guitars and thunderous drums. Groovy and powerful.	https://musicfile.api.box/ZTY0ZGQzZDgtYWM2Zi00ODFhLTgwMzctZWEwZjFlYzNlM2Fj.mp3	2025-12-04 21:13:22.417104	f	f	completed	f	\N
616	338544009	b28d230e-09fd-4bca-b3df-b9c83297f82f	Я люблю и грозу и ненастье,\nИногда и в дождях утопаю,\nВот такое вот - ты мое счастье!\nТы умеешь быть разной, я знаю!\n\nИ любви твоей яркие вспышки,\nИ эмоций когда через край!\nЯ люблю тебя разную, слышишь?\nПусть останется так, продолжай!\n\nТы прости меня милая в мыслях!\nВ сердце добром своем ты прости,\nЗа обиды которые были,\nЗа ошибки, что ждут впереди!	https://musicfile.api.box/MzdiY2JiNWEtNmNkNS00ZjljLWE1NGUtMWZkM2Y2N2FmODJh.mp3	2025-12-05 10:08:25.284874	f	f	completed	f	\N
620	338544009	8b6cff4b-799b-4ef7-b6e9-9b3a2622737d	Я люблю и грозу и ненастье,\nИногда и в дождях утопаю,\nВот такое вот - ты мое счастье!\nТы умеешь быть разной, я знаю!\n\nИ любви твоей яркие вспышки,\nИ эмоций когда через край!\nЯ люблю тебя разную, слышишь?\nПусть останется так, продолжай!\n\nТы прости меня милая в мыслях!\nВ сердце добром своем ты прости,\nЗа обиды которые были,\nЗа ошибки, что ждут впереди! [Длина песни: 3 минуты]	https://musicfile.api.box/ZjI2MTkxNjMtMzg1MC00ZmY1LWE5YmEtZmVmZDNmNjM2ZGE4.mp3	2025-12-05 10:13:03.652821	f	f	completed	f	\N
887	338544009	1d58d9a1-4444-44bc-9954-169aa97449f7	Стиль: Epic symphony for full orchestra: strings, woodwinds, brass, timpani, harp, piano. Powerful opening, virtuosic solos, dramatic cello/horn dialogue, colossal polyphonic finale with thunderous percussion. Grandiose, awe-inspiring masterpiece. [style: romantic symphony, dramatic, virtuosic]	ERROR_NOTIFIED	2025-12-12 21:09:56.928425	f	f	error	f	\N
968	1921555192	63b1eee2-5d40-4462-abfb-bcc49d8d93ec	Стиль: Поп, женский голос. Настроение позитивное. Текст: Я Юлия нутрициолог. Более 50 клиентов со мной стали стройнее и счастливее....	https://musicfile.api.box/NmIyMGZhMjEtOWZjMC00YTZiLThlMGEtNWZjZGI5YmQ5ZWI3.mp3	2025-12-20 18:41:45.029524	f	f	completed	f	\N
624	338544009	d8edf5ca-b7bc-4cb1-ae67-4c6c891c7f53	Ты прости меня милая в мыслях!\nВ сердце добром своем ты прости,\nЗа обиды которые были,\nЗа ошибки, что ждут впереди!\n\nЯ хочу, чтобы счастье и радость\nПоселились на веки с тобой! \nЧтоб не сделал тебе никто гадость,\nОт невзгод я укрою собой!\n\nС каждым годом все больше и больше\nПогружаюсь в тебя и ценю!\nЯ хочу чтобы долгие годы\nМы шептали друг другу - «Люблю!» [Длина песни: 3 минуты]	https://musicfile.api.box/MWUwYWZhMmItMjBiOS00MTdhLTljYTktOWFlYjA2OTQ3YWU2.mp3	2025-12-05 19:40:36.620293	f	f	completed	f	\N
863	7221460591	f33c2f07-c67e-4610-84a3-fca7d5758246	В толпе, не стоит труда найти цвет твоих волос,\nВ холодном поту, по телу моему дрожь.\nСерые будни, но всему вопреки,\nЗнаю ты рядом, хотя мы далеки.\nЕщё одна ночь в этой квартире пустой,\nДни идут чредом, какой же отстой.\nАккорды гитары на струнах души,\nПролетают года, время всё больше спешит.\n\nС первым снегом на рассвете буду ждать тебя,\nВсё пройдёт, ведь всё не вечно, жди, ну а пока,\nЗабудь, не впоминай о нас, сейчас. (2х)\n \nВетер в лицо, он всё развеит,\nВсё поменяет и всё изменит.\nБыстро растём, меняемся внешне,\nВсё как у всех, вся та же спешка.\nКак в этом мире, в том самом моменте,\nВсё изменить, или оставить прежним.\nТак много мыслей, но так мало времени,\nВсё изменить и обдумать уверенно.\n\nС первым снегом на рассвете буду ждать тебя,\nВсё пройдёт, ведь всё не вечно, жди, ну а пока,\nЗабудь, не впоминай о нас, сейчас.	\N	2025-12-11 21:09:50.061948	f	f	error	f	\N
628	338544009	3a813ba0-b74d-424d-89e7-0cbef4987bf6	👨‍💻 Админ панель [Длина песни: 3 минуты]	https://musicfile.api.box/NzJlZmZkYTMtZDRjNC00ZThjLWEwNmEtZjEyZjE5MTQyNWRh.mp3	2025-12-05 19:50:07.78188	f	f	completed	f	\N
866	6087618099	12aa7f37-df33-489b-bec9-9f1d41a84918	Лирический\nФортепиано\n3/4 темп andante\nЧто то лёгкое ,воздушное и грусно	https://musicfile.api.box/NWMwMTNmMzgtNTZjNS00Mzc0LWE5NDYtNTU2NTdhMzdiZjVi.mp3	2025-12-11 21:26:30.924987	f	f	completed	f	\N
632	338544009	805e6f92-83a6-4d99-9670-635cdbfea08a	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу. [Длина песни: 3 минуты]	https://musicfile.api.box/NWNlZTY4YzctMjY1My00ZWE5LTlmYjMtMzdmNDg2NGQxMTAz.mp3	2025-12-05 19:53:04.192033	f	f	completed	f	\N
640	338544009	2992f858-d44d-4b64-af45-1b5ccb1700b1	Ты, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!\n\nЯ люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим! [Длина песни: 3 минуты]	https://musicfile.api.box/YmE4MzllMTAtNzEzYi00MmU3LTkxN2YtMDU1YWYzMTIxZDI2.mp3	2025-12-06 12:58:29.746949	f	f	completed	f	\N
869	6166536566	be41485a-5d9f-4aba-bcd7-40119b37e530	Жанр и направление: Цыганская полька (или "Рома-полька").\n• Музыкальные инструменты: Какие инструменты вы представляете? Обычно это может быть скрипка, аккордеон, гитара, кларнет, контрабас/бас.\n• Ритм и темп: Поскольку она танцевальная, темп должен быть быстрым (например, 140-160 BPM), ритм энергичный, зажигательный.\n• Настроение и атмосфера: Радостное, веселое, энергичное, страстное, праздничное.	https://musicfile.api.box/MzhhZTFjMDgtMTM0NS00MDk2LThmOTUtZDE1ZWZiOGNmMmM0.mp3	2025-12-12 02:06:38.759877	f	f	completed	f	\N
726	338544009	63276d96-2849-4555-9233-2e7adcd4d471	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/NGJhYTEwN2YtMTI1Ni00MGZlLTk2MjAtOTc3MTZiZjY3ZTZl.mp3	2025-12-07 13:55:47.915223	f	f	completed	f	\N
872	5499320998	50552d80-ac78-4ab5-b72d-95371c579bb7	Жила-была козявка	https://musicfile.api.box/Y2Y0NjAzZmYtNjdkMS00MTNkLTk0ODctMWU5Njc5OTMwZTFm.mp3	2025-12-12 08:23:50.839814	f	f	completed	f	\N
730	338544009	2bc747bb-f86d-4933-bcd9-d74d3a52652d	рок музыка с гитарой	https://musicfile.api.box/ZTZlZjkyYTAtOGJlMS00ZWU3LTgyZTctOWY3NjJjMjQ3N2Fj.mp3	2025-12-07 14:05:14.093472	f	f	completed	f	\N
970	338544009	1cc57a7a-1391-4391-b41f-5aabe1c67c33	Стиль: Рок гитара. Текст: Я люблю и грозу и ненастье,\nИногда и в дождях утопаю,\nВот такое вот - ты мое счастье!\nТы умеешь быть...	https://musicfile.api.box/Y2ExM2Q0MGEtNjE3Ny00NjRmLTg2ZmEtOTc1OGI5YjlmOTRl.mp3	2025-12-20 18:51:11.575345	f	f	completed	f	\N
636	338544009	a7d53926-cf9f-4369-ae32-4c4e89d0157d	Ты, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!\n\nЯ люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!	https://musicfile.api.box/NmMzZjRjMDctODUwYi00YmQwLTlkODQtMDEzNjk1MGNkYjI2.mp3	2025-12-06 12:55:25.787139	f	f	completed	f	\N
644	338544009	9271e8b6-a4b5-4578-b4d3-e9334edd497a	Ты, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!\n\nЯ люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!	https://musicfile.api.box/NGM4NWY1MGMtNTIzMS00MjVhLWE5MDUtZTlmOWQ5NzlhZDZh.mp3	2025-12-06 13:01:06.506167	f	f	completed	f	\N
648	338544009	536f3b6f-9e1c-4ffa-830d-9c90346bf8c8	Ты, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!\n\nЯ люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!	https://musicfile.api.box/NDkzODVjODMtMjk1Mi00ODVkLWJhMDYtMjI3ODc0ODNmYmY5.mp3	2025-12-06 13:26:40.278167	f	f	completed	f	\N
652	338544009	03375345-7324-403e-9985-2798dbd7fa76	Ты, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!\n\nЯ люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!	https://musicfile.api.box/YmMwNGExYjAtNDA3Ni00MWUzLThjOTctMDM3YzdhMjRjZWEw.mp3	2025-12-06 13:35:29.838133	f	f	completed	f	\N
656	338544009	47fb6b52-b732-4624-964a-558d82d87a0d	Ты, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!\n\nЯ люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!	https://musicfile.api.box/N2FkMmRjNWUtMmEyZS00NDc1LThhMzAtNGNiNzM5NzdiYjQ5.mp3	2025-12-06 13:41:54.247873	f	f	completed	f	\N
953	6046799885	4dbed268-8564-4faa-bed9-cdfccb47ae7b	Стиль: Жанр: поп\nМузыкальные инструменты: электрогитара, барабаны, басс гитара, фонограмма\nЖенский голос\nТемп: средний \nНастроение: тяжёлое. Текст: Куплет 1\nНочь давит стены, как будто бетон,\nГород молчит, но кричит мой балкон.\nЯ улыбаюсь — привычн...	https://musicfile.api.box/OGYyY2I4ZjMtM2M1MC00YWE0LTg1NDctYmJlMjE4MjllNGY4.mp3	2025-12-15 20:20:49.40365	f	f	completed	f	\N
665	338544009	4c110d3b-ea32-480c-9ec8-5ec497aeffed	Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!	https://musicfile.api.box/YWFmM2NhNjctNTZkOC00YmIzLWE0MmUtZjQyZjA3YmJkMjg5.mp3	2025-12-06 14:06:34.751023	f	f	completed	f	\N
956	8519721721	2d02638f-ebf2-42fb-ae23-3bd504ad4296	Стиль: рок\nгитара, барабан\nмужской \nнастроение темп. Текст: ЛАВА ЛАВА МАТЬ ШАЛАВААААА \n\nмать шалава у Стасика пидорасика взорвали пукан \nСтасик громко плачет он...	https://musicfile.api.box/ZDNhNmI2YjUtMTJmNy00YjQwLWI3NjgtMmJhNjdiOTI2MTUw.mp3	2025-12-15 20:44:32.040722	f	f	completed	f	\N
673	338544009	12f58fc7-93c4-41d1-a832-99cabf19b05f	Пианино и скрипка. Грустно. Тест ручной 3	https://musicfile.api.box/OTQ2YmMzNmQtNDhhNi00MjJhLTg3NTEtMWY4OGM4MTU5ZmY2.mp3	2025-12-06 14:23:08.110604	f	f	completed	f	\N
678	338544009	1c156a62-42ab-4d6c-a7fe-61cc7752d266	🎵 Создать песню	https://musicfile.api.box/NTJhOGIwYjAtNWQ1NS00ZmMzLTg1MmUtODE4NmI4ZGY4OWNm.mp3	2025-12-06 14:30:24.795187	f	f	completed	f	\N
959	338544009	130a4a1f-9931-4b1e-bf84-03264b32427f	Стиль: Два голоса мужской и женский. Романс.. Текст: Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, ...	https://musicfile.api.box/M2YxZDI4MTEtOWJjOS00ODgwLWE4YTYtOWVmNWQxYjY2MzJj.mp3	2025-12-16 18:25:39.271533	f	f	completed	f	\N
688	338544009	301a878e-c84b-4499-9a9a-799cc793da80	Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!	https://musicfile.api.box/ZTAyMjUwZWEtYTFhNi00OTljLTlkMGYtZmFkMDkzMWVmYjRk.mp3	2025-12-06 14:44:24.826494	f	f	completed	f	\N
971	338544009	b06866ec-bd98-4616-a697-35d45369cc01	Стиль: Рок гитара и флейта. Текст: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!\n\nЯ люблю и грозу и ненастье,\nИногда и в дождях утопаю,\nВот такое вот - ты мое счастье!\nТы умеешь быть разной, я знаю!	timeout_auto_cleanup	2025-12-20 19:10:14.945997	f	t	failed	f	\N
692	338544009	3718cdfd-f18d-42eb-a987-28ba4443d649	Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!	https://musicfile.api.box/M2YwNDcwMWQtY2Y1ZC00NTZmLWFjYzQtOTNiNjcwMDU5MmNj.mp3	2025-12-06 14:50:22.933797	f	f	completed	f	\N
998	6800086488	a9caec96-0d59-436a-8017-e2a19d4d03af	Стиль: грустная песня жанр \nмужской \nнастроение. Текст: Тихо падает дождь за окном,\nИ весь мир замирает во сне.\nЯ сижу, погружен в альбом,\nВижу образ твой, ...	https://musicfile.api.box/OGJmZTUxZGUtOGE4NS00YjY5LWI0NWMtN2M1NTI0Njc4ZWRh.mp3	2025-12-25 20:58:58.96577	f	f	completed	f	\N
875	7355021499	966598f3-7e9d-4f55-a14c-5530c164febf	Стучит, стучит железный молот, \nВбивает гвозди в плоть Христа. \nСклонился низко стар и молод \nК подножью этого креста. \n \nПрохожий, слышишь ли, прохожий, \nО, человек, остановись! \nВзгляни на гору, на Голгофу: \nРаспятый Бог в венце висит. \n \nПронзили гвозди руки ,ноги, \nиз ран текла святая кровь. \nНикто не разделял с Ним горя, \nНикто не клал к подножью роз. \n \nПрохожий слышишь ли всмотрись ты \nB Его прекрасное лицо \nПрощая зло,коварство мира \nХристос молился горячо \n \nВзгляни в глаза... в них столько ласки, \nТепла, прощенья, доброты. \nКак я хочу, мой друг, сегодня, \nЧтоб виден в них был я и ты. \n \nПрохожий, слышишь ли, прохожий, \nО, человек, остановись! \nВзгляни на гору, на Голгофу: \nРаспятый Бог в венце висит.	https://musicfile.api.box/MTgyMDNiZTMtMTI1MC00OGE1LTg4OWUtNWQyZDRmOTUzMGU4.mp3	2025-12-12 09:43:26.144326	f	f	completed	f	\N
659	338544009	51bb45b2-bd0e-40b5-996a-9277b0e5dded	Piano and violin. Sad.. Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!	https://musicfile.api.box/MzgwYzYxYjctNDI1OC00MTJlLTgyNWMtNGU5OTEyZTc3YTQ3.mp3	2025-12-06 13:46:04.073404	f	f	completed	f	\N
661	338544009	f66f8511-bb63-4f85-b22a-adb1c4908768	electronicguitar solo, drums, bass, bass guitar, drum kit. Тест ручной отправки	https://musicfile.api.box/MTIwZDNlODQtY2ZhYS00ZDc0LTg3MGMtYjMzMWNkNzhmODA1.mp3	2025-12-06 13:50:38.831946	f	f	completed	f	\N
878	7904260275	96e921dd-2b0d-4b8b-9f48-656809ab4f68	Lo-fi \nБас, барабаны, клавиши и гитара. \nТемп спокойный 4:4\nНастроение немного грустное	https://musicfile.api.box/NDkwNjcxMzMtZTExYS00MDdjLWJlMTctZjBmYmUwNWJiMDk5.mp3	2025-12-12 10:10:43.553173	f	f	completed	f	\N
668	338544009	5a99f41b-f420-4758-aa82-d9ffc9b0e479	piano and violin. sad, melancholic.. Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!	https://musicfile.api.box/ZjFhYTkwYzItMmIxMC00ZDFmLThhMjItMjA1Zjk1YjdhMzNj.mp3	2025-12-06 14:19:07.047718	f	f	completed	f	\N
881	338544009	f11884cb-454c-4b0d-8572-818cea60cd17	🎵 Создать песню	https://musicfile.api.box/NGNjZWM4MzMtMGVmMC00ZjE1LTk5YWMtNGVjZWU2ZTE5ZGRk.mp3	2025-12-12 20:47:37.502928	f	f	completed	f	\N
674	338544009	1a6351df-5dc3-4845-b502-4e57bb455723	piano. violin. sad, melancholic.. Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!	https://musicfile.api.box/MTVmNTVjZGYtMmNjZi00MThkLTgyMTItOGFiYWMyZGZiZTYw.mp3	2025-12-06 14:23:11.781766	f	f	completed	f	\N
681	338544009	f90f6069-92bc-498a-92a9-af759a9b18e1	piano. violin. sad, melancholic.. Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!	https://musicfile.api.box/NTFjZmEyMDAtZmM0OS00ZTVkLTg0OTktMjdjMzZmNGQ0OTYz.mp3	2025-12-06 14:35:38.927368	f	f	completed	f	\N
884	338544009	7d2d58b8-9612-40fc-be7d-13c48dc34a58	🎵 Создать песню	https://musicfile.api.box/MDVhNmZlZGUtMDAxYi00ODk0LTkxMzAtNmQ5OTBkYTZhZWU4.mp3	2025-12-12 21:03:11.873009	f	f	completed	f	\N
886	338544009	fffa4950-9710-4c4e-bb67-8f18c0aaae8a	💰 Баланс	timeout_auto_cleanup	2025-12-12 21:09:47.831357	f	f	failed	f	\N
890	338544009	5320962f-20e5-419f-9011-8020b80ddb84	Epic symphony for full orchestra: strings, woodwinds, brass, timpani, harp, piano. Powerful opening, virtuosic solos, dramatic cello/horn dialogue, colossal polyphonic finale with thunderous percussion. Grandiose, awe-inspiring masterpiece. [style: romantic symphony, dramatic, virtuosic]	https://musicfile.api.box/MDJmYjc4Y2YtMjhiYy00NjIwLWExOTctODVhN2NmNGNhMzEy.mp3	2025-12-12 21:35:09.415884	f	f	completed	f	\N
684	338544009	648c4c6b-e174-4657-be01-9416840d56ea	piano. violin. sad, melancholic.. Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!	https://musicfile.api.box/NTMxMGYxNzktYzcwYi00ODA3LTkzYmItYmRjNTM3MWRlZWY4.mp3	2025-12-06 14:40:11.269402	f	f	completed	f	\N
893	836959709	7495c944-c9f4-4064-8b92-c71ffb590baf	Стиль: Рэп \nБарабаны ,гитара \nМужской \nБыстрый. Текст: Сколько потеряно лет \nСколько погублено жизней \nЯ душу вкладывал в куплет \nЧтоб на моменте тут выжит...	https://musicfile.api.box/MTI4MjY1N2UtMjA0Zi00NmIyLWFiZGUtZGVlM2MwYmQzNzlj.mp3	2025-12-13 10:05:04.12457	f	f	completed	f	\N
895	5448180514	3803818e-2065-4c2f-9bc6-a3dd546f05a8	Хип-хоп\nСкрипка\nСредний\nНегативное и жуткая	timeout_auto_cleanup	2025-12-13 10:05:45.776909	f	f	failed	f	\N
696	338544009	f826fbae-ea24-4f54-9ac1-a45ce38bb814	Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.\n\nТы, советы даёшь осторожно.\nКогда стыдно, умеешь простить.\nКогда холодно, трудно и сложно\nТы умеешь меня подхватить!	https://musicfile.api.box/MzFiN2I5MjItZTMxNS00MjhiLTgxMWEtNzM0N2Q4ZGQ3MjYz.mp3	2025-12-06 14:56:42.443176	f	f	completed	f	\N
735	338544009	91210908-58a4-4ca9-bf58-e021f3d27332	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/MGZkZGUyZWEtYTQ0ZS00Yzc3LTk4NDMtYWYzODc2MjIyZDg2.mp3	2025-12-07 14:12:35.155864	f	f	completed	f	\N
739	338544009	c17a63dd-5b45-4512-9d9d-deca4fcdc661	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/NWMyZjg0M2ItOWM0MS00ODY0LTk5MWUtY2RkMzBiYmMwZWRj.mp3	2025-12-07 14:24:36.98277	f	f	completed	f	\N
745	338544009	283b91e4-35f2-4df7-98ab-b4ee8033087f	rock, electric guitar, guitar, male, vocal. Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/ZjYxZGU3ZmEtYjU4OC00NmEzLTk3MzMtYjYwNTA1ZGQ4Y2Vi.mp3	2025-12-07 17:10:28.341706	f	f	completed	f	\N
974	338544009	a575f938-e6d9-40b3-bac7-6360c3bde37f	Стиль: Рок гитара и флейта. Текст: Ты прости меня милая в мыслях!\nВ сердце добром своем ты прости,\nЗа обиды которые были,\nЗа ошибки, чт...	https://musicfile.api.box/MWE3ODM1ODUtMGQwZi00ZDQ2LWIxOTAtMmI4ZWZmMGQ4Zjdi.mp3	2025-12-20 19:33:37.351583	f	f	completed	f	\N
749	338544009	1733a314-c688-4ce6-970d-3f969d39455f	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/MTIyOTg3MjktNzdkZS00ZWMxLWFlNjMtZmYzOGI5NzliZmI0.mp3	2025-12-07 17:18:38.483205	f	f	completed	f	\N
977	338544009	f55ea992-b3b8-48ac-8f1c-a369f4b8fb94	Красивая мелодия скрипка, виолончель, фортепиано, флейта, ударники.	https://musicfile.api.box/NWRhNjQyZTAtNzgyMC00NzViLTg5NjMtNjljYzRhZWUzZDQ4.mp3	2025-12-24 16:51:40.583016	f	f	completed	f	\N
703	338544009	d496776c-cf51-4333-b53c-8fa6aa7ce08a	Я люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу	https://musicfile.api.box/YzE4M2Y2ZDgtM2U0NC00NTE2LWJhMTktZTZkZjI4ZjE3Y2U3.mp3	2025-12-06 19:40:37.376276	f	f	completed	f	\N
742	338544009	3da336c8-0929-485d-a216-9db6b3d6183a	электрогитара и скрипка (electric guitar, guitar, violin). Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу	https://musicfile.api.box/ODI4NDBkOWUtM2RmNC00YWU5LWEwYWQtNTFlZDgyMGRjNmIx.mp3	2025-12-07 14:31:23.825289	f	f	completed	f	\N
753	338544009	89e1ea94-b7ad-4720-b0f1-e80b83a0f300	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/YjQyMTVmMDktNDRiYi00NmQ4LWE3YzctMzY0NzkwNDNhMDc5.mp3	2025-12-07 17:33:31.508209	f	f	completed	f	\N
757	338544009	66a9eccb-96d4-4ccb-b0dc-0f88cd96a833	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/Yjg2YTJmYTktYWExMy00YWI0LWJmOTYtYmIxMjA4ZDZmNTM0.mp3	2025-12-07 18:26:07.320902	f	f	completed	f	\N
762	338544009	875f4490-04e7-437f-b0ea-c75a2ea32988	Тест женского вокала	https://musicfile.api.box/NzUzMzNiYjktZmE3NC00ZjdlLWExOGEtM2MxMGM4NzBkZDQx.mp3	2025-12-07 18:35:10.587297	f	f	completed	f	\N
899	8481179879	c4bb4e85-07bb-459f-b3a2-709f537d136e	Стиль: Жанр хип-хоп \nИнструменты гитара \nМужской голос \nНапористый темп, настроение агрессивное. Текст: Две ложки сахаоа,\nИ бит длиною в жизнь \nИ что бы не делали делаем заебись \nНа сцене подзавис \nНас вс...	https://musicfile.api.box/MWNhZjJkMjMtNzA1OS00NDdjLThjY2EtYzVmNmQyZThmZDIy.mp3	2025-12-13 10:08:41.102254	f	f	completed	f	\N
766	338544009	59079c0d-ad5a-4f89-baea-6906c54ab015	Когда луна касается воды, и звезды танцуют в вышине, мы слушаем джазовые аккорды, что льются в тишине. Саксофон поет о любви, о мечтах, о весне, женский голос словно шепчет о забытой стране.	https://musicfile.api.box/ODg3YTFjNjgtZGNhMi00ODRmLWIxOWUtY2Q0NDMyNWRjNjI4.mp3	2025-12-07 18:40:51.572101	f	f	completed	f	\N
769	338544009	6c173fc3-85b4-4134-94df-851fb49ede8e	Текст для теста вокала должен быть достаточно длинным чтобы не создавать превью коротких песен	https://musicfile.api.box/NzZkODM5NTgtMjdjMC00NWY2LWI4MDYtNjNmZDJhOTNiZGNj.mp3	2025-12-07 18:44:20.799241	f	f	completed	f	\N
773	338544009	5b78fe89-6114-4e96-bf13-803be37d3339	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/OTdlNmIxNTQtMDQxZC00MDBiLWIxNWItYjQ1OTlhMzZkMjc4.mp3	2025-12-07 19:00:01.630744	f	f	completed	f	\N
777	338544009	1dcf00c8-b08f-4552-902d-9cd0042d21d0	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/MGI2Y2UyM2MtNmE0Zi00ZGEzLTliM2MtZWE5M2ZkMjFlYjJm.mp3	2025-12-07 19:05:42.612751	f	f	completed	f	\N
781	338544009	9a7e6650-aa81-4d05-b09b-28878f8c0e24	Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/MTkzMDY1NGItZjliNS00NDg2LTkyYzQtZmMyZDQ1NDQzYTNl.mp3	2025-12-07 19:09:55.472217	f	f	completed	f	\N
902	7389088862	47afeca1-1774-413a-8742-418f5b6ace4f	Поп рок	https://musicfile.api.box/MzQ1YTFiYzItYTVmNS00OTZkLTg0YzQtYTJlNDJjNmQyNmQx.mp3	2025-12-13 10:27:50.186135	f	f	completed	f	\N
905	6823266776	84fbddd8-f285-4454-b3a3-56b6cf713c12	Стиль: Хип хоп. Текст: Душу рвёт как Стаффорд плоть, сам себя увёл ты в топь, нехуй тут винить кого, сиди ной беспалево, ка...	ERROR_NOTIFIED	2025-12-13 10:29:50.449676	f	f	error	f	\N
908	6815844608	48b4e4dc-c42d-4767-955a-0cc06f692a1c	Рэп андерграунд\nФрути лупс\n90\nУлица	https://musicfile.api.box/NWExZmIxMGMtODZmMy00ZTFmLTg0NjUtZTY3YWU3ZjIwMzVj.mp3	2025-12-13 10:55:57.2626	f	f	completed	f	\N
911	7261354302	6c6f675b-188f-4d94-9770-7cb38f1b498b	Стиль: Гуф the chemodan. Текст: Я иду по улице...	https://musicfile.api.box/MDVlMThhZWQtYzE0YS00Y2ZmLWI2ODktMDc5ZmNlYTBlNTY4.mp3	2025-12-13 11:20:32.088283	f	f	completed	f	\N
914	8271140130	3858485f-2e04-42f8-b441-a0167c26c9f8	🎵 Создать песню	https://musicfile.api.box/ZjY4ZWM0OWYtZTg4OC00ZDE1LWIzNmEtNzNiYWM2YTE5ZTM0.mp3	2025-12-13 12:19:43.838272	f	f	completed	f	\N
784	338544009	bb5d6358-951c-4eea-a3c5-0d24e7b94cbe	vocal, female, jazz, saxophone. Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/ZjM3MjQ4NmUtOGNkMy00ZDJhLTg4OWEtZjNkYzA3OWU4MmJl.mp3	2025-12-07 19:13:20.980909	f	f	completed	f	\N
787	338544009	bc042ec7-7b57-4f8d-9d6d-7a96fd75d41b	vocal, female, jazz, saxophone. Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	https://musicfile.api.box/YzE2NDViMDEtNjE1OS00YTFhLWJlYmUtZmRmZWJjYzMxNzJm.mp3	2025-12-07 19:27:21.154566	f	f	completed	f	\N
494	338544009	141e372b-04d1-415e-b4f0-9f3a0b1f24e9	Стиль: Рок-баллада. Текст: Солнце светит ярко	timeout	2025-12-03 17:44:02.132616	f	t	failed	f	\N
501	338544009	7e2dce8e-265a-4868-9ae7-8eac957d16e7	Стиль: Мужской хор. Народная песня.. Текст: Я люблю всё сильней с каждым взглядом -\nСтрогим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!\n\nЯ люблю и грозу и ненастье,\nИногда и в дождях утопаю,\nВот такое вот - ты мое счастье!\nТы умеешь быть разной, я знаю!	timeout	2025-12-03 18:52:00.715935	f	t	failed	f	\N
502	338544009	dca992dc-9426-400c-ba70-7445b01e6c23	Стиль: Мужской хор. Народное исполнение.. Текст: Я люблю всё сильней с каждым взглядом - Строгим, милым и очень родным!\nС каждой грядкой, поездкой иль стадом,\nС каждым выбором в жизни твоим!\n\nЯ люблю и грозу и ненастье,\nИногда и в дождях утопаю,\nВот такое вот - ты мое счастье!\nТы умеешь быть разной, я знаю!	timeout	2025-12-03 19:08:22.650265	f	t	failed	f	\N
342	338544009	d747d69f-0531-4208-88e2-21ab9df7453d	Стиль: рэп. Текст: И любви твоей яркие вспышки,\nИ эмоций когда через край!\nЯ люблю тебя разную, слышишь?\nПусть останется так, продолжай!	timeout	2025-12-01 21:36:12.541339	f	f	failed	f	\N
482	338544009	3dff8e70-f59e-4acd-a470-4fd18ee25a80	ФИНАЛЬНЫЙ ТЕСТ ТЕКСТА: Солнце светит ярко	timeout	2025-12-03 17:19:06.818011	f	f	failed	f	\N
524	338544009	df574404-c83b-4756-8361-14aee2cc7657	Стиль: Мужской хор. Народные песнси.. Текст: Ты прости меня милая в мыслях!\nВ сердце добром своем ты прости,\nЗа обиды которые были,\nЗа ошибки, что ждут впереди!	timeout	2025-12-04 06:57:09.959265	f	t	failed	f	\N
486	338544009	d141a309-9c5f-4168-abe3-dba70fbede3f	ДЕТАЛЬНЫЙ ТЕСТ ТЕКСТА	timeout	2025-12-03 17:28:49.787541	f	f	failed	f	\N
707	338544009	7bf6c245-a439-4bbe-a0a3-a34a93444d04	Стиль: рок с электрогитарой и мужским вокалом. Текст: Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	timeout	2025-12-07 10:35:41.309383	f	t	failed	f	\N
487	338544009	ea690722-2d28-4d3c-8c43-56348c70449d	ДЕТАЛЬНЫЙ ТЕСТ ТЕКСТА	timeout	2025-12-03 17:30:49.693597	f	f	failed	f	\N
529	338544009	7503a1e5-6f53-4e25-90a0-7d455d3d7958	рок-баллада. Это тест финального исправления\nКуплет 1: Тестируем систему\nПрипев: Всё должно работать!	timeout	2025-12-04 07:13:31.110077	f	f	failed	f	\N
515	338544009	c504e37f-6270-484f-9d85-5462c25fec07	Стиль: Мужской хор.. Текст: Ты прости меня милая в мыслях!\nВ сердце добром своем ты прости,\nЗа обиды которые были,\nЗа ошибки, что ждут впереди!	timeout	2025-12-03 21:59:47.013469	f	t	failed	f	\N
437	338544009	test-task-999	Стиль: Мужской хор. Текст: И любви твоей яркие вспышки, И эмоций когда через край! Я люблю тебя разную, слышишь? Пусть останется так, продолжай!	timeout	2025-12-03 08:37:54.002903	f	t	failed	f	\N
727	338544009	8f3373cd-796e-4f3a-8ff1-7dfc75ccf59f	Стиль: Рок гитара. Мужской вокал. Текст: Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	timeout	2025-12-07 14:00:40.70221	f	t	failed	f	\N
731	338544009	49b8b744-e0f4-42e5-b0e8-5228d56e4585	Стиль: рок с электрогитарой и мужским вокалом. Текст: Я люблю, с каждым годом сильней,\nРаскрывая масштабы Вселенной,\nВосхищаясь душою твоей -\nОбнимающей, мудрой и верной!\n\nЯ люблю с каждом годом сильней,\nПогружаясь в горячее сердце,\nВ справедливость серьёзных речей,\nОткрывая любви твоей  дверцу.	timeout	2025-12-07 14:07:52.27991	f	t	failed	f	\N
965	381251762	248050d4-f471-47ee-864c-7057e44d1561	Стиль: Жанр спортивный\nМужской голос\nСпорт футбол. Текст: Похоже, это был очень насыщенный и успешный турнир! Вот краткий пересказ:\n\nФутбольный турнир "Я - Си...	ERROR_NOTIFIED	2025-12-20 18:18:42.696455	f	f	error	f	\N
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.payments (id, user_id, amount, status, payment_id, created_at) FROM stdin;
1	338544009	50	pending	30df02c5-000f-5001-9000-1251a9dd1a20	2025-12-25 11:00:05.864649
2	1776435167	50	pending	30e59b23-000f-5001-9000-18e9c4a63038	2025-12-30 11:03:47.473429
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
6034993673	myrolil	ㅤ	2025-12-25 20:26:21.443544	t	\N	0
1460772542	\N	andrey	2025-12-13 15:08:52.887597	t	\N	0
7108317408	aaandrey23	Андрей	2025-11-19 07:33:33	f	\N	1
8341832184	\N	Ирина	2025-11-16 10:49:17	f	\N	1
781459029	\N	Ольга	2025-11-30 20:42:23.530121	f	\N	1
999999	test_user	\N	2025-12-01 21:55:12.10602	f	\N	1
896769788	\N	Артём	2025-12-13 16:52:06.374153	t	\N	0
5696467892	Lubov_Bibina	Lubov	2025-12-01 10:32:43.18648	t	338544009	0
5319854535	\N	лариса	2025-12-02 16:30:39.265912	f	\N	1
1024266028	\N	Татьяна	2025-12-02 22:53:23.304281	f	\N	1
1307197823	ZlataKarlova	Zlata	2025-12-09 19:28:50.699913	t	\N	0
1163979411	ttt6512	Yurii	2025-12-09 19:42:38.534798	f	\N	1
5180165536	Fokin24prc	Фокин	2025-12-09 20:43:17.11677	f	\N	1
1309603196	Deep_blue_sea	🌊_𝓜𝓸𝓮_𝓶𝓸𝓻𝓮_ 🌊	2025-12-09 22:22:32.142861	f	\N	1
7866183841	gg1291	.. ..	2025-12-13 10:02:09.573241	t	\N	0
807201256	Nojpdr	Михаил Владимирович 𝒞𝒽𝒽𝓎𝒻𝐿𝑒𝓇𝒶𝓃	2025-12-10 12:25:53.073007	t	\N	0
7810060820	\N	𝓅𝓇𝒾𝓃𝓉𝓈ℯ𝓈𝓈𝒶	2025-12-25 20:39:18.659398	t	6034993673	0
1776435167	\N	Евгений	2025-12-13 18:27:20.914083	t	\N	0
5458312673	Varya_dEr	Varvara	2025-12-11 20:19:40.233779	t	\N	0
7221460591	kerryyyyyyyyy	♪ kerry ♪	2025-12-11 21:04:28.914611	t	\N	0
6087618099	dianka7580	Диана	2025-12-11 21:22:54.064088	t	\N	0
1895249696	Saharok197	S T	2025-12-13 19:00:14.706057	t	\N	0
6166536566	dianaa2109	𝑫𝒊𝒂𝒏𝒂_𝟎𝟏	2025-12-12 02:03:58.813789	t	\N	0
5499320998	\N	OLEG	2025-12-12 08:20:35.858185	t	\N	0
7941065432	anatoly_khokhlov	Толик	2025-12-25 20:51:35.900783	f	6034993673	1
7355021499	Holop_q	Туманов🍁	2025-12-12 09:26:38.795868	t	\N	0
325564447	Fikona	Татьяна	2025-12-12 10:01:18.424271	f	\N	1
5429189658	AsuraSun	Ивасык	2025-12-13 19:13:46.808421	t	\N	0
7904260275	\N	Артем	2025-12-12 10:06:17.857318	t	\N	0
5288263174	\N	Соня	2025-12-12 19:58:50.709395	f	\N	1
338544009	Igor_Bibin	Игорь	2025-11-16 08:17:43	f	\N	6
836959709	marketrelations20	Миша	2025-12-13 10:02:06.341827	t	\N	0
5448180514	Translator174	XXX	2025-12-13 10:03:01.318809	t	\N	0
2044499510	\N	Максим	2025-12-13 19:28:54.487921	t	\N	0
8481179879	\N	Реп 3000	2025-12-13 10:02:31.479016	t	\N	0
6143533780	Andrechistik	Andre	2025-12-13 10:07:30.005214	f	\N	1
8251010413	mad13691	Art	2025-12-13 10:20:13.255012	f	\N	1
7389088862	sany58914	Саня	2025-12-13 10:24:56.360293	t	\N	0
6800086488	milakaahi	.	2025-12-25 20:48:58.423769	t	6034993673	0
6823266776	THUG_LIFE_1988	Thug life	2025-12-13 10:06:13.337287	t	\N	0
5226511367	\N	Денис	2025-12-14 00:57:16.215223	t	\N	0
6815844608	\N	!.!.!	2025-12-13 10:23:01.828197	t	\N	0
7261354302	Ramilka3125	Ramil👁	2025-12-13 11:18:38.031966	t	\N	0
856978600	dimpetr1	Дмитрий Макаров	2025-12-29 21:17:57.686139	f	\N	1
8271140130	MutaFukaz13	Mutafukaz	2025-12-13 10:24:01.581818	t	\N	0
303300629	IvanSh_n	Ivan	2025-12-13 12:56:17.609335	f	\N	1
1202215259	zmz2929	M	2025-12-13 13:12:00.588796	f	\N	1
986061438	pgp_90	G	2025-12-13 13:34:44.474635	f	\N	1
1709723311	bells1703	Запретное	2025-12-13 13:41:53.552993	f	\N	1
684367352	SenorVladislav	Vladislav	2025-12-14 08:46:33.457612	t	\N	0
817684210	natalitali163	Наташа	2025-12-13 14:27:37.661697	t	\N	0
2105097253	thesatey	𝑺𝑨𝑻𝑬𝒀	2025-12-13 14:32:07.112692	f	\N	1
5604433321	Lenocka_Penochka	Elena	2025-12-13 14:36:10.091304	f	\N	1
7867618181	llina_900	Хз кто я	2025-12-15 19:01:35.925744	f	\N	1
8342815012	fluflapinparadise	wearxx	2025-12-15 19:03:57.888336	f	\N	1
5926679424	Nikiteks17	Никита Д.	2025-12-15 19:01:58.977701	t	\N	0
7596080666	Moon_Ilover	야옹_야옹	2025-12-15 19:25:51.390467	t	\N	0
7277147192	\N	Димитрий	2025-12-30 10:51:30.553507	t	1776435167	0
6046799885	Koitz_v1rus	🕊️✧˖° 𝒜𝓃𝑔𝑒𝓁𝑜𝓊𝓀 °˖✧🕊️	2025-12-15 20:15:40.261735	t	\N	0
8519721721	mooonbmm	skripnichenko🌒	2025-12-15 20:31:57.700502	t	\N	0
7623671532	Dashe_Lavin	Dasha🎀	2025-12-15 23:05:02.563407	f	6046799885	1
7509693986	Wendy_Chaiwawa	Zaha	2025-12-16 12:38:10.377692	f	\N	1
5445330449	Mars_is_here	🦴💿Mars 🪐🌺	2025-12-16 13:20:59.424009	f	\N	1
1167891553	DashulyaNovik	Dasha	2025-12-16 18:36:39.8759	f	\N	1
381251762	OlgaL_Buh	Ольга/Бухгалтер	2025-12-20 18:16:51.146992	t	\N	0
1921555192	nutriciolog_barnaul	Юлия	2025-12-20 18:37:12.961068	t	381251762	0
\.


--
-- Name: channel_posts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.channel_posts_id_seq', 1, false);


--
-- Name: generations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.generations_id_seq', 1004, true);


--
-- Name: payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.payments_id_seq', 2, true);


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
-- Name: generations unique_user_task; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.generations
    ADD CONSTRAINT unique_user_task UNIQUE (user_id, task_id);


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
-- Name: idx_generations_audio_url_not_null; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_generations_audio_url_not_null ON public.generations USING btree (audio_url) WHERE (audio_url IS NOT NULL);


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
-- Name: idx_generations_status_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_generations_status_created ON public.generations USING btree (status, created_at);


--
-- Name: idx_generations_task_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_generations_task_id ON public.generations USING btree (task_id);


--
-- Name: idx_generations_user_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_generations_user_created ON public.generations USING btree (user_id, created_at DESC);


--
-- Name: idx_generations_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_generations_user_id ON public.generations USING btree (user_id);


--
-- Name: idx_generations_user_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_generations_user_status ON public.generations USING btree (user_id, status);


--
-- Name: idx_payments_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payments_status ON public.payments USING btree (status);


--
-- Name: idx_payments_status_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payments_status_created ON public.payments USING btree (status, created_at DESC);


--
-- Name: idx_payments_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payments_user_id ON public.payments USING btree (user_id);


--
-- Name: idx_payments_user_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_payments_user_status ON public.payments USING btree (user_id, status);


--
-- Name: idx_referrals_referred_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_referrals_referred_id ON public.referrals USING btree (referred_id);


--
-- Name: idx_referrals_referrer_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_referrals_referrer_id ON public.referrals USING btree (referrer_id);


--
-- Name: idx_users_balance; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_balance ON public.users USING btree (balance);


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

\unrestrict k1FcP5ZbjV3Ed2dx4bjWlAjiJJte8G10rxbVhaxbZJ5kNUf6xr1Os1IpdmfeYg0

