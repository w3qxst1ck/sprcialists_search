--Профессии
INSERT INTO professions (title, tag) VALUES ('Разработчик', 'develop');
INSERT INTO professions (title, tag) VALUES ('Дизайнер', 'design');
INSERT INTO professions (title, tag) VALUES ('Видео-монтажер', 'video');
INSERT INTO professions (title, tag) VALUES ('SMM', 'smm');
--Jobs
INSERT INTO jobs (title, profession_id, tag) VALUES ('Backend', 1, 'backend');
INSERT INTO jobs (title, profession_id, tag) VALUES ('Frontend', 1, 'fronted');
INSERT INTO jobs (title, profession_id, tag) VALUES ('Devops', 1, 'devops');
INSERT INTO jobs (title, profession_id, tag) VALUES ('CloudDev', 1, 'cloud');
INSERT INTO jobs (title, profession_id, tag) VALUES ('SQL', 1, 'sql');
INSERT INTO jobs (title, profession_id, tag) VALUES ('UXUI', 2, 'uiux');
INSERT INTO jobs (title, profession_id, tag) VALUES ('Лендинги', 2, 'landing');
INSERT INTO jobs (title, profession_id, tag) VALUES ('Веб-сайты', 2, 'web');
INSERT INTO jobs (title, profession_id, tag) VALUES ('Figma', 2, 'figma');
INSERT INTO jobs (title, profession_id, tag) VALUES ('Монтаж видео', 3, 'videomaker');
INSERT INTO jobs (title, profession_id, tag) VALUES ('Редакция фото', 3, 'photos');
INSERT INTO jobs (title, profession_id, tag) VALUES ('ReelsMaker', 3, 'reels');
INSERT INTO jobs (title, profession_id, tag) VALUES ('SEO', 4, 'seo');
INSERT INTO jobs (title, profession_id, tag) VALUES ('Продвижение сайтов', 4, 'seo2');
INSERT INTO jobs (title, profession_id, tag) VALUES ('Раскрутка инстаграм', 4, 'inst');
--RejectReasons
INSERT INTO reject_reasons(reason, text) VALUES('Недопустимая фотография', 'Необходимо поменять фотографию профиля');
INSERT INTO reject_reasons(reason, text) VALUES('Недостаточно информации', 'Указано слишком мало информации о профиле');
INSERT INTO reject_reasons(reason, text) VALUES('Мало опыта', 'Указано слишком мало информации о профиле');
